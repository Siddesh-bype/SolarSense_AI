"""
SolarSense AI — Pipeline Benchmark Script
Usage:  python benchmark.py [image_path]
"""
import sys, os, time, json
import numpy as np

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))


def create_test_image(path: str = "test_rooftop.jpg"):
    """Create a synthetic test rooftop image if none provided."""
    import cv2
    img = np.zeros((800, 800, 3), dtype=np.uint8)
    # Sky region (top)
    img[:200, :] = [180, 140, 100]
    # Roof region (middle) — brown/terracotta
    cv2.rectangle(img, (100, 200), (700, 650), (60, 80, 140), -1)
    # Chimney obstruction
    cv2.rectangle(img, (500, 250), (580, 350), (40, 40, 40), -1)
    # Ground (bottom)
    img[650:, :] = [80, 100, 60]
    cv2.imwrite(path, img)
    return path


def benchmark(image_path: str):
    results = {"phases": {}, "total_seconds": 0}

    # Phase 1: Preprocessing
    t0 = time.perf_counter()
    from utils.image_preprocessor import ImagePreprocessor
    preprocessor = ImagePreprocessor()
    validation = preprocessor.validate(image_path)
    assert validation.is_valid, f"Validation failed: {validation.reason}"
    preprocessed = preprocessor.preprocess(image_path)
    results["phases"]["preprocessing"] = round(time.perf_counter() - t0, 3)

    # Load image
    import cv2
    image_bgr = cv2.imread(image_path)
    image_bgr = cv2.resize(image_bgr, (1024, 1024))

    # Phase 2: Depth Estimation
    t0 = time.perf_counter()
    from services.depth_estimator import DepthEstimator
    estimator = DepthEstimator(device="cpu")
    depth_result = estimator.estimate(image_bgr)
    results["phases"]["depth_estimation"] = round(time.perf_counter() - t0, 3)
    results["roof_area_m2"] = depth_result["estimated_roof_area_m2"]

    # Phase 3: Shadow Simulation
    t0 = time.perf_counter()
    from services.shadow_simulator import ShadowSimulator
    simulator = ShadowSimulator()
    shadow_result = simulator.simulate_annual_shadow(
        depth_map=depth_result["depth_map"],
        roof_mask=depth_result["roof_mask"],
        obstruction_mask=depth_result["obstruction_mask"],
        latitude=18.52, longitude=73.85,
        base_irradiance_kwh=5.2,
        resolution_hours=24,
    )
    results["phases"]["shadow_simulation"] = round(time.perf_counter() - t0, 3)

    # Phase 4: Panel Placement
    t0 = time.perf_counter()
    from services.panel_optimizer import PanelOptimizer
    optimizer = PanelOptimizer()
    placement = optimizer.optimize_placement(
        irradiance_map=shadow_result["irradiance_map"],
        roof_mask=depth_result["roof_mask"],
        obstruction_mask=depth_result["obstruction_mask"],
        depth_result=depth_result,
        latitude=18.52,
    )
    results["phases"]["panel_placement"] = round(time.perf_counter() - t0, 3)
    results["panels_placed"] = placement["total_panels"]
    results["system_capacity_kw"] = placement["system_capacity_kw"]

    # Phase 5: Financial
    t0 = time.perf_counter()
    from services.financial_engine import FinancialEngine
    from utils.pvgis_client import PVGISClient
    pvgis = PVGISClient(offline_mode=True)
    irradiance = pvgis.get_monthly_irradiance(18.52, 73.85, "pune")
    engine = FinancialEngine()
    financial = engine.calculate(
        total_panels=placement["total_panels"],
        monthly_irradiance=irradiance["values"],
        city="pune",
        monthly_electricity_bill_inr=3000,
    )
    results["phases"]["financial"] = round(time.perf_counter() - t0, 3)
    results["payback_years"] = financial["payback_years"]
    results["savings_25yr"] = financial["savings_25yr_inr"]

    # Phase 6: Report
    t0 = time.perf_counter()
    from services.report_generator import ReportGenerator
    reporter = ReportGenerator()
    summary = reporter.generate_summary({
        "city": "Pune",
        "total_panels": placement["total_panels"],
        "system_capacity_kw": placement["system_capacity_kw"],
        "annual_kwh": financial["annual_generation_kwh"],
        "monthly_bill": 3000,
        "bill_offset_pct": financial["bill_offset_pct"],
        "net_cost": financial["cost_breakdown"]["net_cost_inr"],
        "payback_years": financial["payback_years"],
        "savings_25yr": financial["savings_25yr_inr"],
    })
    results["phases"]["report_generation"] = round(time.perf_counter() - t0, 3)

    # Totals
    results["total_seconds"] = round(sum(results["phases"].values()), 3)

    return results


def main():
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    if image_path is None or not os.path.exists(image_path):
        print("No image provided — generating synthetic test image...")
        image_path = create_test_image()

    print("=" * 50)
    print("  SolarSense AI — Pipeline Benchmark")
    print("=" * 50)

    results = benchmark(image_path)

    for phase, duration in results["phases"].items():
        bar = "█" * int(duration * 10)
        print(f"  {phase:<22s}  {duration:>6.3f}s  {bar}")

    print("-" * 50)
    print(f"  TOTAL: {results['total_seconds']:.3f}s")
    print(f"  Panels: {results.get('panels_placed', 0)} | Capacity: {results.get('system_capacity_kw', 0):.1f} kW")
    print(f"  Payback: {results.get('payback_years', 0):.1f} yrs | 25yr savings: ₹{results.get('savings_25yr', 0):,.0f}")

    out_path = "benchmark_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to {out_path}")


if __name__ == "__main__":
    main()
