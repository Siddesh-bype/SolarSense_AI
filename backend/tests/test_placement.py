"""Tests for the panel placement optimizer."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from services.panel_optimizer import PanelOptimizer


def test_placement_basic():
    """Placement on a clear roof should produce panels."""
    # Large clear roof with good irradiance
    irradiance_map = np.ones((200, 200), dtype=np.float32) * 5.0
    roof_mask = np.ones((200, 200), dtype=np.uint8) * 255
    obstruction_mask = np.zeros((200, 200), dtype=np.uint8)

    depth_result = {
        "estimated_roof_area_m2": 100.0,
        "tilt_angle_degrees": 15.0,
    }

    optimizer = PanelOptimizer()
    result = optimizer.optimize_placement(
        irradiance_map=irradiance_map,
        roof_mask=roof_mask,
        obstruction_mask=obstruction_mask,
        depth_result=depth_result,
        latitude=18.52,
    )

    assert result["total_panels"] >= 3, f"Expected ≥3 panels, got {result['total_panels']}"
    assert result["system_capacity_kw"] > 0
    assert len(result["panels"]) == result["total_panels"]
    print(f"✅ Basic placement: {result['total_panels']} panels, {result['system_capacity_kw']:.1f} kW")


def test_no_overlap():
    """Panels should not overlap."""
    irradiance_map = np.ones((300, 300), dtype=np.float32) * 5.0
    roof_mask = np.ones((300, 300), dtype=np.uint8) * 255
    obstruction_mask = np.zeros((300, 300), dtype=np.uint8)

    depth_result = {
        "estimated_roof_area_m2": 150.0,
        "tilt_angle_degrees": 15.0,
    }

    optimizer = PanelOptimizer()
    result = optimizer.optimize_placement(
        irradiance_map=irradiance_map,
        roof_mask=roof_mask,
        obstruction_mask=obstruction_mask,
        depth_result=depth_result,
        latitude=18.52,
    )

    panels = result["panels"]
    for i, p1 in enumerate(panels):
        for j, p2 in enumerate(panels):
            if i >= j:
                continue
            # Check bounding box overlap
            overlap_x = (p1["x"] < p2["x"] + p2["width"]) and (p1["x"] + p1["width"] > p2["x"])
            overlap_y = (p1["y"] < p2["y"] + p2["height"]) and (p1["y"] + p1["height"] > p2["y"])
            assert not (overlap_x and overlap_y), f"Panels {i} and {j} overlap!"

    print(f"✅ No overlaps among {len(panels)} panels")


if __name__ == "__main__":
    test_placement_basic()
    test_no_overlap()
    print("\nAll placement tests passed!")
