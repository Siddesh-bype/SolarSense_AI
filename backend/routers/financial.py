"""
Financial Router — Quick financial estimate endpoint (no scan required).
"""
import logging
from typing import Optional

from fastapi import APIRouter, Query

logger = logging.getLogger("solarsense.financial")
router = APIRouter()


@router.get("/estimate")
async def quick_estimate(
    panels: int = Query(10, ge=1, le=100, description="Number of panels"),
    city: str = Query("pune", description="City for cost lookup"),
    monthly_bill: float = Query(3000.0, ge=0, description="Monthly electricity bill in INR"),
):
    """
    Quick financial estimate without a scan — for the landing page calculator.
    """
    from services.financial_engine import FinancialEngine
    from utils.pvgis_client import PVGISClient

    # Get irradiance for city
    pvgis = PVGISClient(offline_mode=True)
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
    lat, lon = city_coords.get(city.lower(), (18.52, 73.85))
    irradiance = pvgis.get_monthly_irradiance(lat, lon, city)

    # Calculate
    engine = FinancialEngine()
    result = engine.calculate(
        total_panels=panels,
        monthly_irradiance=irradiance["values"],
        city=city,
        monthly_electricity_bill_inr=monthly_bill,
    )

    return result
