"""
Scan Router — Two-phase approach:
  Phase 1: Upload & analyze roof (depth, shadow, heatmap)
  Phase 2: User places panels interactively, then submits for financial calc
"""
import logging
import os
import uuid
import time
from typing import Optional, List

import cv2
import numpy as np
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger("solarsense.scan")
router = APIRouter()

# In-memory scan storage (for demo — no database needed)
_scans: dict = {}

# Panel spec constants (must match frontend)
PANEL_WATTAGE = 540  # Watts per panel
PANEL_WIDTH_M = 1.7
PANEL_HEIGHT_M = 1.0


# ──────────────────────────────────────────────
#  Phase 2 request model
# ──────────────────────────────────────────────

class UserPanel(BaseModel):
    x: float        # percentage x (0-100)
    y: float        # percentage y (0-100)
    width: float    # percentage width
    height: float   # percentage height


class CalculateRequest(BaseModel):
    scan_id: str
    panels: List[UserPanel]
    city: str = "pune"
    monthly_bill: float = 3000.0


# ──────────────────────────────────────────────
#  Phase 1: Upload & Analyze
# ──────────────────────────────────────────────

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
    Phase 1: Upload a rooftop photo, run depth + shadow analysis.
    Returns roof analysis data so user can place panels interactively.
    """
    scan_id = str(uuid.uuid4())[:8]

    # Set default coords for city
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
            _run_analysis,
            scan_id, image_path, city, latitude, longitude, output_dir,
        )
        _scans[scan_id].update({
            "status": "analyzed",
            "progress_percent": 100,
            "current_step": "ready_for_placement",
            "result": result,
        })
        return JSONResponse(content={
            "scan_id": scan_id,
            "status": "analyzed",
            "result": result,
        })
    except Exception as e:
        logger.exception(f"[Scan {scan_id}] Analysis failed")
        _scans[scan_id].update({
            "status": "failed",
            "error_message": str(e),
        })
        raise HTTPException(status_code=500, detail=f"Scan pipeline failed: {str(e)}")


# ──────────────────────────────────────────────
#  Phase 2: Calculate from user's panel placement
# ──────────────────────────────────────────────

@router.post("/calculate")
async def calculate_from_placement(req: CalculateRequest):
    """
    Phase 2: User has placed panels interactively.
    Calculate financial results based on their layout.
    """
    scan = _scans.get(req.scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan["status"] not in ("analyzed", "complete"):
        raise HTTPException(status_code=400, detail=f"Scan is {scan['status']}, analysis not ready")

    analysis = scan.get("result", {})
    city = req.city or scan.get("city", "pune")
    monthly_bill = req.monthly_bill or scan.get("monthly_bill", 3000.0)
    latitude = scan.get("latitude", 18.52)
    longitude = scan.get("longitude", 73.85)
    total_panels = len(req.panels)

    if total_panels == 0:
        raise HTTPException(status_code=400, detail="Please place at least one panel on the roof")

    try:
        result = await run_in_threadpool(
            _run_financial_calc,
            total_panels, city, monthly_bill, latitude, longitude, analysis,
        )

        _scans[req.scan_id].update({
            "status": "complete",
            "current_step": "complete",
            "financial_result": result,
        })

        return JSONResponse(content=result)

    except Exception as e:
        logger.exception(f"[Scan {req.scan_id}] Financial calc failed")
        raise HTTPException(status_code=500, detail=str(e))


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
    """Get the analysis result of a scan."""
    scan = _scans.get(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan["status"] not in ("analyzed", "complete"):
        raise HTTPException(status_code=400, detail=f"Scan is {scan['status']}")
    return scan.get("result", {})


# ──────────────────────────────────────────────
#  Phase 1 pipeline: Analyze roof only
# ──────────────────────────────────────────────

def _update_status(scan_id: str, step: str, progress: int):
    if scan_id in _scans:
        _scans[scan_id]["current_step"] = step
        _scans[scan_id]["progress_percent"] = progress
    logger.info(f"[Scan {scan_id}] {step} ({progress}%)")


def _run_analysis(
    scan_id: str,
    image_path: str,
    city: str,
    latitude: float,
    longitude: float,
    output_dir: str,
) -> dict:
    """Phase 1: Preprocessing + Depth + Shadow — no panel placement yet."""
    start_time = time.time()
    base_url = f"/static/{scan_id}"

    # ---------- 1. Preprocessing ----------
    _update_status(scan_id, "preprocessing", 15)
    from backend.utils.image_preprocessor import ImagePreprocessor

    preprocessor = ImagePreprocessor()
    validation = preprocessor.validate(image_path)
    if not validation.is_valid:
        raise ValueError(f"Image validation failed: {validation.reason}")

    preprocessed = preprocessor.preprocess(image_path)

    if preprocessed.gps_coords and latitude == 18.52:
        latitude, longitude = preprocessed.gps_coords

    image_bgr = cv2.imread(image_path)
    if image_bgr is None:
        raise ValueError("Failed to read uploaded image")

    max_dim = 1024
    h, w = image_bgr.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        image_bgr = cv2.resize(image_bgr, (int(w * scale), int(h * scale)))

    # ---------- 2. Depth Estimation ----------
    _update_status(scan_id, "depth_estimation", 40)
    from backend.services.depth_estimator import DepthEstimator, save_depth_visualizations

    try:
        from backend.utils.gpu_manager import get_device
        device = str(get_device())
    except Exception:
        device = "cpu"

    depth_estimator = DepthEstimator(device=device)
    depth_result = depth_estimator.estimate(image_bgr)
    save_depth_visualizations(image_bgr, depth_result, output_dir)

    # ---------- 3. Shadow Simulation ----------
    _update_status(scan_id, "shadow_simulation", 70)
    from backend.services.shadow_simulator import ShadowSimulator, save_heatmap_overlay
    from backend.utils.pvgis_client import PVGISClient

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
        resolution_hours=24,
    )

    heatmap_path = os.path.join(output_dir, "heatmap.png")
    save_heatmap_overlay(image_bgr, shadow_result["heatmap_rgba"], heatmap_path)

    _update_status(scan_id, "ready_for_placement", 100)

    elapsed = time.time() - start_time
    logger.info(f"[Scan {scan_id}] Analysis complete in {elapsed:.1f}s")

    # Compute pixel-to-meter scale for frontend
    h_img, w_img = image_bgr.shape[:2]
    roof_area_m2 = depth_result["estimated_roof_area_m2"]
    roof_pixels = float(np.sum(depth_result["roof_mask"] > 0))
    if roof_pixels > 0:
        pixel_to_m = np.sqrt(roof_area_m2 / roof_pixels)
    else:
        pixel_to_m = 0.015

    # Panel size in pixels (for frontend to draw correctly)
    panel_w_px = max(10, int(round(PANEL_WIDTH_M / pixel_to_m)))
    panel_h_px = max(6, int(round(PANEL_HEIGHT_M / pixel_to_m)))

    return {
        "scan_id": scan_id,
        "processing_time_seconds": round(elapsed, 1),
        "image_width": w_img,
        "image_height": h_img,
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
        "panel_spec": {
            "width_px": panel_w_px,
            "height_px": panel_h_px,
            "wattage": PANEL_WATTAGE,
            "width_m": PANEL_WIDTH_M,
            "height_m": PANEL_HEIGHT_M,
        },
        "original_image_url": f"{base_url}/original.jpg",
        "city": city,
        "location": {"latitude": latitude, "longitude": longitude},
        "irradiance_source": irradiance_data["source"],
    }


# ──────────────────────────────────────────────
#  Phase 2 pipeline: Financial calculation
# ──────────────────────────────────────────────

def _run_financial_calc(
    total_panels: int,
    city: str,
    monthly_bill: float,
    latitude: float,
    longitude: float,
    analysis: dict,
) -> dict:
    """Phase 2: Run financial calc based on the user's panel count."""
    from backend.services.financial_engine import FinancialEngine
    from backend.services.report_generator import ReportGenerator
    from backend.utils.pvgis_client import PVGISClient

    pvgis = PVGISClient()
    irradiance_data = pvgis.get_monthly_irradiance(latitude, longitude, city)

    engine = FinancialEngine()
    financial = engine.calculate(
        total_panels=total_panels,
        monthly_irradiance=irradiance_data["values"],
        city=city,
        monthly_electricity_bill_inr=monthly_bill,
    )

    # Generate report
    reporter = ReportGenerator()
    summary = reporter.generate_summary({
        "city": city,
        "usable_area_m2": analysis.get("depth", {}).get("estimated_roof_area_m2", 50),
        "total_panels": total_panels,
        "system_capacity_kw": financial["system_capacity_kw"],
        "annual_kwh": financial["annual_generation_kwh"],
        "monthly_bill": monthly_bill,
        "bill_offset_pct": financial["bill_offset_pct"],
        "gross_cost": financial["cost_breakdown"]["gross_cost_inr"],
        "subsidy": financial["cost_breakdown"]["subsidy_inr"],
        "net_cost": financial["cost_breakdown"]["net_cost_inr"],
        "payback_years": financial["payback_years"],
        "savings_25yr": financial["savings_25yr_inr"],
    })

    return {
        "total_panels": total_panels,
        "financial": financial,
        "summary": summary,
    }
