"""Tests for the shadow simulator."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from services.shadow_simulator import calculate_sun_position


def test_sun_position_pune_summer():
    """Sun position for Pune on June 21 (summer solstice) at noon."""
    altitude, azimuth = calculate_sun_position(18.52, 73.85, 172, 12.0)  # June 21
    # Sun should be high in the sky (altitude > 60°) near zenith
    assert 50 < altitude < 90, f"Expected altitude ~75°, got {altitude:.1f}°"
    print(f"✅ Pune June 21 noon: altitude={altitude:.1f}°, azimuth={azimuth:.1f}°")


def test_sun_position_pune_winter():
    """Sun position for Pune on Dec 21 (winter solstice) at noon."""
    altitude, azimuth = calculate_sun_position(18.52, 73.85, 355, 12.0)  # Dec 21
    # Sun should be lower (altitude ~48°)
    assert 30 < altitude < 70, f"Expected altitude ~48°, got {altitude:.1f}°"
    print(f"✅ Pune Dec 21 noon: altitude={altitude:.1f}°, azimuth={azimuth:.1f}°")


def test_sun_below_horizon_night():
    """Sun should be below horizon at midnight."""
    altitude, azimuth = calculate_sun_position(18.52, 73.85, 172, 0.0)
    assert altitude < 0, f"Expected negative altitude at midnight, got {altitude:.1f}°"
    print(f"✅ Pune midnight: altitude={altitude:.1f}° (below horizon)")


def test_shadow_simulation_basic():
    """Basic shadow simulation should produce valid irradiance map."""
    from services.shadow_simulator import ShadowSimulator

    # Create simple test data
    depth_map = np.random.rand(100, 100).astype(np.float32)
    roof_mask = np.ones((100, 100), dtype=np.uint8) * 255
    obstruction_mask = np.zeros((100, 100), dtype=np.uint8)

    sim = ShadowSimulator()
    result = sim.simulate_annual_shadow(
        depth_map=depth_map,
        roof_mask=roof_mask,
        obstruction_mask=obstruction_mask,
        latitude=18.52,
        longitude=73.85,
        base_irradiance_kwh=5.0,
        resolution_hours=24,
    )

    assert "irradiance_map" in result
    assert "heatmap_rgba" in result
    assert result["avg_irradiance_kwh_m2_year"] > 0
    print(f"✅ Shadow sim: avg irradiance = {result['avg_irradiance_kwh_m2_year']:.1f} kWh/m²/yr")


if __name__ == "__main__":
    test_sun_position_pune_summer()
    test_sun_position_pune_winter()
    test_sun_below_horizon_night()
    test_shadow_simulation_basic()
    print("\nAll shadow tests passed!")
