"""
Energy Calculator — Monthly/annual energy yield using PVGIS irradiance + system specs.
"""
import logging

logger = logging.getLogger(__name__)

PERFORMANCE_RATIO = 0.78
DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def calculate_annual_yield(
    capacity_kw: float,
    monthly_irradiance: list[float],
) -> dict:
    """
    Calculate monthly and annual energy yield.
    monthly_irradiance: list of 12 kWh/m²/day average values.
    Returns: { monthly_kwh: [12], annual_kwh: float }
    """
    monthly_kwh = []
    for i in range(12):
        gen = capacity_kw * monthly_irradiance[i] * DAYS_IN_MONTH[i] * PERFORMANCE_RATIO
        monthly_kwh.append(round(gen, 1))

    return {
        "monthly_kwh": monthly_kwh,
        "annual_kwh": round(sum(monthly_kwh), 0),
    }
