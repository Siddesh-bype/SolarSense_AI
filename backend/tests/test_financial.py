"""Tests for the financial engine."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.financial_engine import FinancialEngine
from utils.pvgis_client import PVGISClient


def test_financial_10_panels_pune():
    """10-panel system in Pune should produce reasonable financials."""
    pvgis = PVGISClient(offline_mode=True)
    irradiance = pvgis.get_monthly_irradiance(18.52, 73.85, "pune")

    engine = FinancialEngine()
    result = engine.calculate(
        total_panels=10,
        monthly_irradiance=irradiance["values"],
        city="pune",
        monthly_electricity_bill_inr=3000,
    )

    # System capacity: 10 × 540W = 5.4 kW
    assert 5.0 <= result["system_capacity_kw"] <= 6.0

    # Annual generation should be > 0
    assert result["annual_generation_kwh"] > 0

    # Payback should be between 3 and 15 years
    assert 3.0 <= result["payback_years"] <= 15.0

    # 25-year savings should be positive
    assert result["savings_25yr_inr"] > 0

    # Subsidy should be applied
    assert result["cost_breakdown"]["subsidy_inr"] > 0

    # Net cost should be less than gross cost
    assert result["cost_breakdown"]["net_cost_inr"] < result["cost_breakdown"]["gross_cost_inr"]

    print(f"✅ 10-panel Pune: {result['system_capacity_kw']:.1f} kW, "
          f"payback {result['payback_years']:.1f} yrs, "
          f"savings ₹{result['savings_25yr_inr']:,.0f}")


def test_financial_1_panel():
    """Single panel should produce valid but smaller numbers."""
    pvgis = PVGISClient(offline_mode=True)
    irradiance = pvgis.get_monthly_irradiance(28.61, 77.21, "delhi")

    engine = FinancialEngine()
    result = engine.calculate(
        total_panels=1,
        monthly_irradiance=irradiance["values"],
        city="delhi",
        monthly_electricity_bill_inr=1000,
    )

    assert result["system_capacity_kw"] > 0
    assert result["annual_generation_kwh"] > 0
    print(f"✅ 1-panel Delhi: {result['system_capacity_kw']:.2f} kW, "
          f"generation {result['annual_generation_kwh']:.0f} kWh/yr")


if __name__ == "__main__":
    test_financial_10_panels_pune()
    test_financial_1_panel()
    print("\nAll financial tests passed!")
