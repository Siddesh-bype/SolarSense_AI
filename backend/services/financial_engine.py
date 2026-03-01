"""
Financial Engine — Calculates costs, subsidies, payback, EMI, and 25-year savings.
"""
import json
import logging
import math
import os
from typing import Optional

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Constants
PANEL_WATTAGE = 540          # Watts per panel
PERFORMANCE_RATIO = 0.78     # System efficiency
PANEL_DEGRADATION = 0.005    # 0.5% per year
GRID_TARIFF_INR_KWH = 7.5   # Average Indian residential tariff
ANNUAL_TARIFF_INCREASE = 0.04  # 4% per year
PANEL_LIFETIME_YEARS = 25
DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


class FinancialEngine:
    """Calculates the full financial picture for a solar installation."""

    def __init__(self):
        self.city_costs = self._load_json("city_costs.json")
        self.subsidy_table = self._load_json("subsidy_table.json")

    def calculate(
        self,
        total_panels: int,
        monthly_irradiance: list[float],
        city: str = "default",
        monthly_electricity_bill_inr: float = 3000.0,
    ) -> dict:
        """
        Full 25-year financial calculation.
        monthly_irradiance: list of 12 kWh/m²/day values.
        """
        # System capacity
        capacity_kw = total_panels * PANEL_WATTAGE / 1000.0

        # Annual energy yield (kWh)
        monthly_kwh = []
        for month_idx in range(12):
            monthly_gen = (
                capacity_kw
                * monthly_irradiance[month_idx]
                * DAYS_IN_MONTH[month_idx]
                * PERFORMANCE_RATIO
            )
            monthly_kwh.append(round(monthly_gen, 1))

        annual_kwh = sum(monthly_kwh)

        # 25-year cumulative generation with degradation
        cumulative_gen_25yr = 0
        for year in range(PANEL_LIFETIME_YEARS):
            degradation_factor = (1 - PANEL_DEGRADATION) ** year
            cumulative_gen_25yr += annual_kwh * degradation_factor

        # Equipment costs
        costs = self.city_costs.get(city.lower(), self.city_costs.get("default", {}))
        panel_per_watt = costs.get("panel_per_watt", 38)
        installation_per_kw = costs.get("installation_per_kw", 8500)
        inverter_per_kw = costs.get("inverter_per_kw", 6000)

        panel_cost = capacity_kw * 1000 * panel_per_watt
        inverter_cost = capacity_kw * inverter_per_kw
        mounting_wiring = panel_cost * 0.15
        installation_cost = capacity_kw * installation_per_kw
        gross_cost = panel_cost + inverter_cost + mounting_wiring + installation_cost

        # Subsidy
        subsidy = self._calculate_subsidy(capacity_kw)

        # Net cost
        net_cost = max(0, gross_cost - subsidy)

        # Annual savings
        current_tariff = GRID_TARIFF_INR_KWH
        annual_savings_yr1 = annual_kwh * current_tariff

        # Bill offset
        monthly_usage_kwh = monthly_electricity_bill_inr / current_tariff
        annual_usage_kwh = monthly_usage_kwh * 12
        bill_offset_pct = min(100, (annual_kwh / max(annual_usage_kwh, 1)) * 100)

        # Payback period with tariff escalation
        payback_years = self._calculate_payback(net_cost, annual_kwh, current_tariff)

        # 25-year cumulative savings
        cumulative_savings_by_year = []
        cumulative_savings = -net_cost  # Start negative (investment)
        tariff = current_tariff
        for year in range(PANEL_LIFETIME_YEARS):
            degradation_factor = (1 - PANEL_DEGRADATION) ** year
            year_gen = annual_kwh * degradation_factor
            year_savings = year_gen * tariff
            cumulative_savings += year_savings
            cumulative_savings_by_year.append(round(cumulative_savings, 0))
            tariff *= (1 + ANNUAL_TARIFF_INCREASE)

        total_savings_25yr = cumulative_savings

        # EMI
        emi = self.calculate_emi(net_cost)

        return {
            "system_capacity_kw": round(capacity_kw, 2),
            "annual_generation_kwh": round(annual_kwh, 0),
            "monthly_generation_kwh": monthly_kwh,
            "cost_breakdown": {
                "panel_cost_inr": round(panel_cost, 0),
                "inverter_cost_inr": round(inverter_cost, 0),
                "mounting_wiring_inr": round(mounting_wiring, 0),
                "installation_cost_inr": round(installation_cost, 0),
                "gross_cost_inr": round(gross_cost, 0),
                "subsidy_inr": round(subsidy, 0),
                "net_cost_inr": round(net_cost, 0),
            },
            "annual_savings_inr": round(annual_savings_yr1, 0),
            "payback_years": round(payback_years, 1),
            "savings_25yr_inr": round(total_savings_25yr, 0),
            "bill_offset_pct": round(bill_offset_pct, 1),
            "emi": emi,
            "cumulative_savings_by_year": cumulative_savings_by_year,
        }

    def _calculate_subsidy(self, capacity_kw: float) -> float:
        """Calculate PM Surya Ghar subsidy based on system capacity."""
        pm = self.subsidy_table.get("pm_surya_ghar", {})
        if capacity_kw <= 1.0:
            return pm.get("up_to_1kw", {}).get("subsidy_inr", 30000)
        elif capacity_kw <= 2.0:
            return pm.get("1kw_to_2kw", {}).get("subsidy_inr", 60000)
        elif capacity_kw <= 3.0:
            return pm.get("2kw_to_3kw", {}).get("subsidy_inr", 78000)
        else:
            return pm.get("above_3kw", {}).get("subsidy_inr", 78000)

    def _calculate_payback(
        self, net_cost: float, annual_kwh: float, start_tariff: float
    ) -> float:
        """Calculate payback period accounting for tariff escalation and degradation."""
        cumulative = 0.0
        tariff = start_tariff
        for year in range(1, PANEL_LIFETIME_YEARS + 1):
            degradation = (1 - PANEL_DEGRADATION) ** (year - 1)
            yearly_savings = annual_kwh * degradation * tariff
            cumulative += yearly_savings
            if cumulative >= net_cost:
                # Interpolate within the year
                overshoot = cumulative - net_cost
                fraction = 1 - (overshoot / yearly_savings)
                return year - 1 + fraction
            tariff *= (1 + ANNUAL_TARIFF_INCREASE)
        return PANEL_LIFETIME_YEARS  # Never pays back within 25 years

    @staticmethod
    def calculate_emi(
        principal: float,
        annual_rate: float = 0.085,
        tenure_months: int = 84,
    ) -> dict:
        """Standard EMI formula: P * r * (1+r)^n / ((1+r)^n - 1)"""
        if principal <= 0:
            return {
                "monthly_emi_inr": 0,
                "total_payable_inr": 0,
                "annual_rate_pct": annual_rate * 100,
                "tenure_months": tenure_months,
            }
        r = annual_rate / 12  # Monthly rate
        n = tenure_months
        emi = principal * r * (1 + r) ** n / ((1 + r) ** n - 1)
        return {
            "monthly_emi_inr": round(emi, 0),
            "total_payable_inr": round(emi * n, 0),
            "annual_rate_pct": round(annual_rate * 100, 1),
            "tenure_months": tenure_months,
        }

    @staticmethod
    def _load_json(filename: str) -> dict:
        """Load a JSON data file from the data directory."""
        filepath = os.path.join(DATA_DIR, filename)
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"[Financial] Data file not found: {filepath}")
            return {}
