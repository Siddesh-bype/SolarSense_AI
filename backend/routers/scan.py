"""
Scan Router — Upload rooftop photos and run the full analysis pipeline.
"""
import logging
import os
import uuid
import time
from typing import Optional

import cv2
import numpy as np
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

logger = logging.getLogger("solarsense.scan")
router = APIRouter()

# In-memory scan storage (for demo — no database needed)
_scans: dict = {}


@router.post("/upload")
async def upload_scan(
    file: UploadFile = File(...),
    city: str = Form("pune"),
    monthly_bill: float = Form(3000.0),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    demo: bool = Form(False),
):
    """
    Upload a rooftop photo and run the full analysis pipeline synchronously.
    Returns scan_id and complete results.
    """
    scan_id = str(uuid.uuid4())[:8]

    # Set default coords for city if not provided
    if latitude is None or longitude is None:
        city_coords = {
            "pune": (18.52, 73.85),
            "mumbai": (19.08, 72.88),
            "delhi": (28.61, 77.21),
            "jaipur": (26.91, 75.79),
            "bangalore": (12.97, 77.59),
            "chennai": (13.08, 80.27),
            "hyderabad": (17.39, 78.49),
            "kolkata": (22.57, 88.36),
        }
        coords = city_coords.get(city.lower(), (18.52, 73.85))
        latitude, longitude = coords

    # Create output directory
    output_dir = os.path.join("scan_outputs", scan_id)
    os.makedirs(output_dir, exist_ok=True)

    # Save uploaded image
    image_bytes = await file.read()
    image_path = os.path.join(output_dir, "original.jpg")
    with open(image_path, "wb") as f:
        f.write(image_bytes)

    # Initialize scan status
    _scans[scan_id] = {
        "scan_id": scan_id,
        "status": "processing",
        "progress_percent": 0,
        "current_step": "preprocessing",
        "city": city,
        "monthly_bill": monthly_bill,
        "latitude": latitude,
        "longitude": longitude,
    }

    try:
        result = await run_in_threadpool(
            _run_pipeline,
            scan_id,
            image_path,
            city,
            monthly_bill,
            latitude,
            longitude,
            output_dir,
        )
        _scans[scan_id].update({
            "status": "complete",
            "progress_percent": 100,
            "current_step": "complete",
            "result": result,
        })
        return JSONResponse(content={
            "scan_id": scan_id,
            "status": "complete",
            "result": result,
        })
    except Exception as e:
        logger.exception(f"[Scan {scan_id}] Pipeline failed")
        _scans[scan_id].update({
            "status": "failed",
            "error_message": str(e),
        })
        raise HTTPException(status_code=500, detail=f"Scan pipeline failed: {str(e)}")


@router.get("/{scan_id}/status")
async def get_scan_status(scan_id: str):
    """Get the current status of a scan."""
    scan = _scans.get(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {
        "scan_id": scan["scan_id"],
        "status": scan["status"],
        "progress_percent": scan.get("progress_percent", 0),
        "current_step": scan.get("current_step", ""),
        "error_message": scan.get("error_message"),
    }


@router.get("/{scan_id}/result")
async def get_scan_result(scan_id: str):
    """Get the complete result of a scan."""
    scan = _scans.get(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan["status"] != "complete":
        raise HTTPException(status_code=400, detail=f"Scan is {scan['status']}")
    return scan.get("result", {})


# ──────────────────────────────────────────────
#  Pipeline execution
# ──────────────────────────────────────────────

def _update_status(scan_id: str, step: str, progress: int):
    """Update scan status in memory."""
    if scan_id in _scans:
        _scans[scan_id]["current_step"] = step
        _scans[scan_id]["progress_percent"] = progress
    logger.info(f"[Scan {scan_id}] {step} ({progress}%)")


def _run_pipeline(
    scan_id: str,
    image_path: str,
    city: str,
    monthly_bill: float,
    latitude: float,
    longitude: float,
    output_dir: str,
) -> dict:
    """Run the complete SolarSense scan pipeline synchronously."""
    start_time = time.time()
    base_url = f"/static/{scan_id}"

    # ---------- 1. Preprocessing ----------
    _update_status(scan_id, "preprocessing", 10)
    from utils.image_preprocessor import ImagePreprocessor

    preprocessor = ImagePreprocessor()
    validation = preprocessor.validate(image_path)
    if not validation.is_valid:
        raise ValueError(f"Image validation failed: {validation.reason}")

    preprocessed = preprocessor.preprocess(image_path)

    # Use EXIF GPS if available
    if preprocessed.gps_coords and latitude == 18.52:
        latitude, longitude = preprocessed.gps_coords

    # Load original image for processing
    image_bgr = cv2.imread(image_path)
    if image_bgr is None:
        raise ValueError("Failed to read uploaded image")

    # Resize to manageable size for processing
    max_dim = 1024
    h, w = image_bgr.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        image_bgr = cv2.resize(image_bgr, (int(w * scale), int(h * scale)))

    # ---------- 2. Depth Estimation ----------
    _update_status(scan_id, "depth_estimation", 25)
    from services.depth_estimator import DepthEstimator, save_depth_visualizations

    try:
        from utils.gpu_manager import get_device
        device = str(get_device())
    except Exception:
        device = "cpu"

    depth_estimator = DepthEstimator(device=device)
    depth_result = depth_estimator.estimate(image_bgr)

    # Save depth visualizations
    depth_urls = save_depth_visualizations(image_bgr, depth_result, output_dir)

    # ---------- 3. Shadow Simulation ----------
    _update_status(scan_id, "shadow_simulation", 50)
    from services.shadow_simulator import ShadowSimulator, save_heatmap_overlay
    from utils.pvgis_client import PVGISClient

    pvgis = PVGISClient()
    irradiance_data = pvgis.get_monthly_irradiance(latitude, longitude, city)
    avg_daily_irr = sum(irradiance_data["values"]) / 12.0

    shadow_sim = ShadowSimulator()
    shadow_result = shadow_sim.simulate_annual_shadow(
        depth_map=depth_result["depth_map"],
        roof_mask=depth_result["roof_mask"],
        obstruction_mask=depth_result["obstruction_mask"],
        latitude=latitude,
        longitude=longitude,
        base_irradiance_kwh=avg_daily_irr,
        resolution_hours=24,  # Fast mode for demo
    )

    # Save heatmap overlay
    heatmap_path = os.path.join(output_dir, "heatmap.png")
    save_heatmap_overlay(image_bgr, shadow_result["heatmap_rgba"], heatmap_path)

    # ---------- 4. Panel Placement ----------
    _update_status(scan_id, "panel_placement", 70)
    from services.panel_optimizer import PanelOptimizer, save_placement_visualization

    optimizer = PanelOptimizer()
    placement_result = optimizer.optimize_placement(
        irradiance_map=shadow_result["irradiance_map"],
        roof_mask=depth_result["roof_mask"],
        obstruction_mask=depth_result["obstruction_mask"],
        depth_result=depth_result,
        latitude=latitude,
    )

    # Save placement visualization
    placement_path = os.path.join(output_dir, "placement.png")
    save_placement_visualization(
        image_bgr, shadow_result["heatmap_rgba"], placement_result["panels"], placement_path
    )

    # ---------- 5. Financial Calculation ----------
    _update_status(scan_id, "financial_calculation", 85)
    from services.financial_engine import FinancialEngine

    fin_engine = FinancialEngine()
    financial = fin_engine.calculate(
        total_panels=placement_result["total_panels"],
        monthly_irradiance=irradiance_data["values"],
        city=city,
        monthly_electricity_bill_inr=monthly_bill,
    )

    # ---------- 6. Report Generation ----------
    _update_status(scan_id, "generating_report", 95)
    from services.report_generator import ReportGenerator

    reporter = ReportGenerator()
    summary = reporter.generate_summary({
        "city": city,
        "usable_area_m2": depth_result["estimated_roof_area_m2"],
        "total_panels": placement_result["total_panels"],
        "system_capacity_kw": placement_result["system_capacity_kw"],
        "annual_kwh": financial["annual_generation_kwh"],
        "monthly_bill": monthly_bill,
        "bill_offset_pct": financial["bill_offset_pct"],
        "gross_cost": financial["cost_breakdown"]["gross_cost_inr"],
        "subsidy": financial["cost_breakdown"]["subsidy_inr"],
        "net_cost": financial["cost_breakdown"]["net_cost_inr"],
        "payback_years": financial["payback_years"],
        "savings_25yr": financial["savings_25yr_inr"],
    })

    elapsed = time.time() - start_time
    logger.info(f"[Scan {scan_id}] Pipeline complete in {elapsed:.1f}s")

    # ---------- Assemble result ----------
    return {
        "scan_id": scan_id,
        "processing_time_seconds": round(elapsed, 1),
        "depth": {
            "estimated_roof_area_m2": depth_result["estimated_roof_area_m2"],
            "tilt_angle_degrees": depth_result["tilt_angle_degrees"],
            "obstruction_count": len(depth_result["obstruction_boxes"]),
            "obstruction_boxes": depth_result["obstruction_boxes"],
            "confidence": depth_result["confidence"],
            "depth_map_url": f"{base_url}/depth_map.png",
            "roof_mask_url": f"{base_url}/roof_mask.png",
        },
        "shadow": {
            "avg_irradiance_kwh_m2_year": shadow_result["avg_irradiance_kwh_m2_year"],
            "peak_irradiance_zone": shadow_result["peak_irradiance_zone"],
            "heatmap_url": f"{base_url}/heatmap.png",
        },
        "placement": {
            **placement_result,
            "placement_url": f"{base_url}/placement.png",
            "image_width": image_bgr.shape[1],
            "image_height": image_bgr.shape[0],
        },
        "financial": financial,
        "summary": summary,
        "original_image_url": f"{base_url}/original.jpg",
        "city": city,
        "location": {"latitude": latitude, "longitude": longitude},
        "irradiance_source": irradiance_data["source"],
    }
