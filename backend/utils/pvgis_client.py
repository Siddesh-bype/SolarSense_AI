"""
PVGIS Client — Fetches solar irradiance data from the EU PVGIS API.
Includes offline fallback data for major Indian cities.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Monthly average daily irradiance (kWh/m²/day) for major Indian cities
OFFLINE_FALLBACK = {
    "pune":      [5.2, 6.1, 6.8, 6.4, 5.9, 4.2, 3.8, 3.9, 5.1, 5.8, 5.6, 5.1],
    "mumbai":    [5.0, 5.9, 6.5, 6.2, 5.7, 3.9, 3.5, 3.7, 4.9, 5.6, 5.4, 4.9],
    "delhi":     [4.1, 5.0, 6.0, 6.8, 7.0, 6.5, 5.5, 5.3, 5.5, 5.5, 4.5, 4.0],
    "jaipur":    [4.5, 5.5, 6.5, 7.0, 7.2, 6.8, 5.8, 5.6, 5.8, 5.8, 4.8, 4.3],
    "bangalore": [5.3, 6.0, 6.7, 6.3, 5.8, 4.5, 4.0, 4.2, 5.0, 5.4, 5.2, 5.0],
    "chennai":   [4.8, 5.6, 6.3, 6.5, 6.4, 5.5, 5.0, 5.2, 5.3, 4.8, 4.2, 4.2],
    "hyderabad": [5.1, 5.9, 6.6, 6.8, 6.5, 5.0, 4.3, 4.4, 5.1, 5.5, 5.3, 4.9],
    "kolkata":   [4.3, 5.0, 5.8, 6.0, 5.5, 4.0, 3.5, 3.8, 4.5, 4.8, 4.5, 4.1],
    "default":   [5.0, 5.8, 6.5, 6.6, 6.5, 5.2, 4.5, 4.5, 5.2, 5.6, 5.2, 4.8],
}

# GPS coords for nearest-city matching
CITY_COORDS = {
    "pune":      (18.52, 73.85),
    "mumbai":    (19.08, 72.88),
    "delhi":     (28.61, 77.21),
    "jaipur":    (26.91, 75.79),
    "bangalore": (12.97, 77.59),
    "chennai":   (13.08, 80.27),
    "hyderabad": (17.39, 78.49),
    "kolkata":   (22.57, 88.36),
}


class PVGISClient:
    """Fetches monthly irradiance data, with offline fallback for Indian cities."""

    def __init__(self, offline_mode: Optional[bool] = None):
        if offline_mode is None:
            self.offline_mode = os.environ.get("PVGIS_OFFLINE_MODE", "true").lower() == "true"
        else:
            self.offline_mode = offline_mode

    def get_monthly_irradiance(
        self, lat: float, lon: float, city: Optional[str] = None
    ) -> dict:
        """
        Get monthly average daily irradiance (kWh/m²/day).
        Returns: { values: [12 floats], source: str }
        """
        if not self.offline_mode:
            result = self._fetch_from_api(lat, lon)
            if result is not None:
                return result
            logger.warning("[PVGIS] API unreachable, using offline fallback.")

        # Offline fallback
        return self._get_offline_data(lat, lon, city)

    def _fetch_from_api(self, lat: float, lon: float) -> Optional[dict]:
        """Attempt to fetch from the PVGIS API."""
        try:
            import httpx

            url = "https://re.jrc.ec.europa.eu/api/v5_2/MRcalc"
            params = {
                "lat": lat,
                "lon": lon,
                "outputformat": "json",
                "startyear": 2020,
                "endyear": 2020,
            }
            resp = httpx.get(url, params=params, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()

            # Extract monthly irradiance
            monthly = data.get("outputs", {}).get("monthly", {}).get("fixed", [])
            if len(monthly) >= 12:
                values = [m.get("H(i)_m", 5.0) for m in monthly[:12]]
                return {"values": values, "source": "pvgis_api"}

        except Exception as e:
            logger.warning(f"[PVGIS] API error: {e}")
        return None

    def _get_offline_data(
        self, lat: float, lon: float, city: Optional[str] = None
    ) -> dict:
        """Return offline fallback data for the nearest known city."""
        if city and city.lower() in OFFLINE_FALLBACK:
            return {
                "values": OFFLINE_FALLBACK[city.lower()],
                "source": f"offline_{city.lower()}",
            }

        # Find nearest city by coordinates
        nearest_city = self._find_nearest_city(lat, lon)
        return {
            "values": OFFLINE_FALLBACK[nearest_city],
            "source": f"offline_{nearest_city}",
        }

    @staticmethod
    def _find_nearest_city(lat: float, lon: float) -> str:
        """Find the nearest city with offline data."""
        min_dist = float("inf")
        nearest = "default"
        for city, (clat, clon) in CITY_COORDS.items():
            dist = (lat - clat) ** 2 + (lon - clon) ** 2
            if dist < min_dist:
                min_dist = dist
                nearest = city
        return nearest
