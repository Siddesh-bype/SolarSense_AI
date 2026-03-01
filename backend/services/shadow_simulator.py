"""
Shadow Simulator — Sun position calculation + vectorised annual shadow simulation.
Generates irradiance heatmaps for rooftop solar planning.
"""
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
#  Sun Position Calculator (simplified NREL SPA)
# ──────────────────────────────────────────────

def calculate_sun_position(
    latitude: float, longitude: float, dt_utc: datetime
) -> dict:
    """
    Calculate solar azimuth and elevation using simplified NREL algorithm.
    Returns: { azimuth_degrees, elevation_degrees, is_daytime }
    """
    # Day of year
    doy = dt_utc.timetuple().tm_yday

    # Solar declination (radians)
    declination = math.radians(23.45 * math.sin(math.radians(360 / 365 * (284 + doy))))

    # Equation of time (minutes)
    B = math.radians(360 / 365 * (doy - 81))
    eot = 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)

    # Solar time
    hour_utc = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    solar_time = hour_utc + longitude / 15.0 + eot / 60.0

    # Hour angle (degrees, then radians)
    hour_angle_deg = (solar_time - 12.0) * 15.0
    hour_angle = math.radians(hour_angle_deg)

    lat_rad = math.radians(latitude)

    # Solar elevation
    sin_elevation = (
        math.sin(lat_rad) * math.sin(declination)
        + math.cos(lat_rad) * math.cos(declination) * math.cos(hour_angle)
    )
    elevation_rad = math.asin(max(-1.0, min(1.0, sin_elevation)))
    elevation_deg = math.degrees(elevation_rad)

    # Solar azimuth
    cos_azimuth = (
        (math.sin(declination) - math.sin(lat_rad) * sin_elevation)
        / (math.cos(lat_rad) * math.cos(elevation_rad) + 1e-10)
    )
    azimuth_rad = math.acos(max(-1.0, min(1.0, cos_azimuth)))
    azimuth_deg = math.degrees(azimuth_rad)

    # Correct azimuth for afternoon
    if hour_angle > 0:
        azimuth_deg = 360.0 - azimuth_deg

    return {
        "azimuth_degrees": round(azimuth_deg, 2),
        "elevation_degrees": round(elevation_deg, 2),
        "is_daytime": elevation_deg > 0,
    }


# ──────────────────────────────────────────────
#  Shadow Simulator
# ──────────────────────────────────────────────

class ShadowSimulator:
    """
    Simulates annual shadow patterns on a rooftop using depth + sun position.
    Generates an irradiance heatmap overlay.
    """

    def simulate_annual_shadow(
        self,
        depth_map: np.ndarray,
        roof_mask: np.ndarray,
        obstruction_mask: np.ndarray,
        latitude: float,
        longitude: float,
        base_irradiance_kwh: float = 5.5,
        resolution_hours: int = 24,
    ) -> dict:
        """
        Vectorised annual shadow simulation.
        Returns: { irradiance_map, shadow_hours_map, heatmap_rgba, peak_zone, avg_irradiance }
        """
        h, w = depth_map.shape[:2]
        shadow_count = np.zeros((h, w), dtype=np.float32)
        total_daytime_samples = 0

        # Sample across the year
        year = 2024
        for doy in range(1, 366, max(1, resolution_hours)):
            for hour in range(5, 20):  # 5 AM to 8 PM local approximate
                dt = datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(days=doy - 1, hours=hour)
                sun = calculate_sun_position(latitude, longitude, dt)

                if not sun["is_daytime"] or sun["elevation_degrees"] < 5:
                    continue

                total_daytime_samples += 1

                # Cast shadows from obstructions
                shadow_frame = self._cast_shadows_vectorized(
                    depth_map, obstruction_mask,
                    sun["azimuth_degrees"], sun["elevation_degrees"],
                    h, w,
                )
                shadow_count += shadow_frame

        # Irradiance fraction (1 = never shadowed, 0 = always shadowed)
        if total_daytime_samples > 0:
            irradiance_fraction = 1.0 - (shadow_count / total_daytime_samples)
        else:
            irradiance_fraction = np.ones((h, w), dtype=np.float32)

        # Apply roof mask
        irradiance_fraction[roof_mask == 0] = 0

        # Scale to kWh/m²/year
        irradiance_map = irradiance_fraction * base_irradiance_kwh * 365

        # Generate heatmap RGBA
        heatmap_rgba = self.generate_heatmap_rgba(irradiance_fraction, roof_mask)

        # Find peak irradiance zone
        peak_zone = self._find_peak_zone(irradiance_fraction, roof_mask)

        # Average irradiance on roof
        roof_pixels = roof_mask > 0
        if np.any(roof_pixels):
            avg_irradiance = float(np.mean(irradiance_map[roof_pixels]))
        else:
            avg_irradiance = base_irradiance_kwh * 365 * 0.8

        return {
            "irradiance_map": irradiance_map,
            "shadow_hours_map": shadow_count,
            "heatmap_rgba": heatmap_rgba,
            "peak_irradiance_zone": peak_zone,
            "avg_irradiance_kwh_m2_year": round(avg_irradiance, 1),
        }

    def _cast_shadows_vectorized(
        self,
        depth_map: np.ndarray,
        obstruction_mask: np.ndarray,
        azimuth_deg: float,
        elevation_deg: float,
        h: int,
        w: int,
    ) -> np.ndarray:
        """
        Fast vectorised shadow casting — shift obstruction mask in sun direction.
        """
        # Shadow direction is opposite to sun azimuth
        shadow_az = math.radians(azimuth_deg + 180)
        shadow_len = max(1, int(20 / max(math.tan(math.radians(elevation_deg)), 0.1)))
        shadow_len = min(shadow_len, 80)  # Cap shadow length

        dx = int(round(math.sin(shadow_az) * shadow_len))
        dy = int(round(-math.cos(shadow_az) * shadow_len))

        # Shift obstruction mask by shadow vector
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        shadow = cv2.warpAffine(
            obstruction_mask, M, (w, h), borderValue=0
        )
        return (shadow > 0).astype(np.float32)

    def generate_heatmap_rgba(
        self, irradiance_fraction: np.ndarray, roof_mask: np.ndarray
    ) -> np.ndarray:
        """
        Map irradiance values to RGBA heatmap colours.
        Green = high sun, Red = low sun, Transparent = off-roof.
        """
        h, w = irradiance_fraction.shape
        heatmap = np.zeros((h, w, 4), dtype=np.uint8)

        roof_px = roof_mask > 0
        if not np.any(roof_px):
            return heatmap

        vals = irradiance_fraction[roof_px]
        p20, p40, p60, p80 = np.percentile(vals, [20, 40, 60, 80])

        # Colour map: R, G, B, A
        colors = {
            "red":          (213,   0,   0, 153),  # Bottom 20%
            "orange":       (255, 109,   0, 153),  # 20-40%
            "yellow":       (255, 214,   0, 153),  # 40-60%
            "yellow_green": (174, 234,   0, 153),  # 60-80%
            "green":        (  0, 200,  83, 153),  # Top 20%
        }

        for y in range(h):
            for x in range(w):
                if not roof_px[y, x]:
                    continue
                v = irradiance_fraction[y, x]
                if v <= p20:
                    c = colors["red"]
                elif v <= p40:
                    c = colors["orange"]
                elif v <= p60:
                    c = colors["yellow"]
                elif v <= p80:
                    c = colors["yellow_green"]
                else:
                    c = colors["green"]
                heatmap[y, x] = c

        return heatmap

    def _find_peak_zone(
        self, irradiance_fraction: np.ndarray, roof_mask: np.ndarray
    ) -> Optional[dict]:
        """Find the best rectangular zone for panel placement."""
        # Threshold to top 30% irradiance on roof
        roof_px = roof_mask > 0
        if not np.any(roof_px):
            return None

        threshold = np.percentile(irradiance_fraction[roof_px], 70)
        peak_mask = ((irradiance_fraction >= threshold) & roof_px).astype(np.uint8) * 255

        contours, _ = cv2.findContours(peak_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        # Largest contour
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        return {"x": int(x), "y": int(y), "width": int(w), "height": int(h)}


def save_heatmap_overlay(
    image_bgr: np.ndarray,
    heatmap_rgba: np.ndarray,
    output_path: str,
):
    """Composite heatmap RGBA onto original image and save."""
    h, w = image_bgr.shape[:2]
    hh, hw = heatmap_rgba.shape[:2]

    if (h, w) != (hh, hw):
        heatmap_rgba = cv2.resize(heatmap_rgba, (w, h), interpolation=cv2.INTER_NEAREST)

    # Blend
    alpha = heatmap_rgba[:, :, 3:4].astype(np.float32) / 255.0
    rgb = heatmap_rgba[:, :, :3].astype(np.float32)
    base = image_bgr.astype(np.float32)

    blended = base * (1 - alpha) + rgb * alpha
    cv2.imwrite(output_path, blended.astype(np.uint8))
