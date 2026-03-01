"""
Panel Placement Optimizer — Greedy algorithm for optimal solar panel placement
on a rooftop given irradiance and depth data.
"""
import logging
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Standard panel dimensions (meters)
PANEL_WIDTH_M = 1.7
PANEL_HEIGHT_M = 1.0
MAINTENANCE_GAP_M = 0.3
PANEL_WATTAGE = 540  # Watts per panel


class PanelOptimizer:
    """Greedy panel placement on rooftop irradiance maps."""

    def __init__(self, grid_resolution_m: float = 0.1):
        self.grid_res = grid_resolution_m
        self.panel_w_cells = int(round(PANEL_WIDTH_M / grid_resolution_m))
        self.panel_h_cells = int(round(PANEL_HEIGHT_M / grid_resolution_m))
        self.gap_cells = int(round(MAINTENANCE_GAP_M / grid_resolution_m))

    def optimize_placement(
        self,
        irradiance_map: np.ndarray,
        roof_mask: np.ndarray,
        obstruction_mask: np.ndarray,
        depth_result: dict,
        latitude: float,
        max_panels: Optional[int] = None,
    ) -> dict:
        """
        Greedy panel placement algorithm.
        Returns dict with: panels, total_panels, total_area_m2, system_capacity_kw,
                          estimated_annual_kwh, coverage_percentage
        """
        h_img, w_img = roof_mask.shape[:2]
        roof_area_m2 = depth_result.get("estimated_roof_area_m2", 50.0)

        # Compute pixel-to-meter scale
        roof_pixels = float(np.sum(roof_mask > 0))
        if roof_pixels > 0:
            pixel_area_m2 = roof_area_m2 / roof_pixels
            pixel_to_m = np.sqrt(pixel_area_m2)
        else:
            pixel_to_m = 0.015  # fallback

        # Panel size in pixels
        panel_w_px = max(10, int(round(PANEL_WIDTH_M / pixel_to_m)))
        panel_h_px = max(6, int(round(PANEL_HEIGHT_M / pixel_to_m)))
        gap_px = max(2, int(round(MAINTENANCE_GAP_M / pixel_to_m)))

        # Edge buffer
        edge_buffer_px = gap_px

        # Create usable area mask (roof minus obstructions minus edge buffer)
        usable = roof_mask.copy()
        if obstruction_mask is not None:
            # Dilate obstructions by gap
            kernel = np.ones((gap_px * 2 + 1, gap_px * 2 + 1), dtype=np.uint8)
            dilated_obs = cv2.dilate(obstruction_mask, kernel)
            usable[dilated_obs > 0] = 0

        # Erode usable area by edge buffer
        kern_edge = np.ones((edge_buffer_px * 2 + 1, edge_buffer_px * 2 + 1), dtype=np.uint8)
        usable = cv2.erode(usable, kern_edge)

        # Score cells by irradiance (normalise to [0, 1])
        irr = irradiance_map.copy()
        irr_max = irr.max() if irr.max() > 0 else 1.0
        irr_norm = irr / irr_max

        # Create occupancy grid (0 = free, 1 = occupied)
        occupancy = (usable == 0).astype(np.uint8)

        # Find candidate positions sorted by irradiance score
        panels = []
        panel_id = 0
        max_p = max_panels or 50

        # Sliding window over the image at intervals
        step = max(1, gap_px)
        candidates = []

        for y in range(0, h_img - panel_h_px, step):
            for x in range(0, w_img - panel_w_px, step):
                region = occupancy[y : y + panel_h_px, x : x + panel_w_px]
                if np.any(region):
                    continue
                irr_region = irr_norm[y : y + panel_h_px, x : x + panel_w_px]
                score = float(np.mean(irr_region))
                candidates.append((score, x, y))

        # Sort by irradiance score descending
        candidates.sort(key=lambda c: c[0], reverse=True)

        # Place panels greedily
        for score, x, y in candidates:
            if panel_id >= max_p:
                break

            # Check that region is still free (panels + gaps)
            y_start = max(0, y - gap_px)
            y_end = min(h_img, y + panel_h_px + gap_px)
            x_start = max(0, x - gap_px)
            x_end = min(w_img, x + panel_w_px + gap_px)

            padded_region = occupancy[y_start:y_end, x_start:x_end]
            core_region = occupancy[y : y + panel_h_px, x : x + panel_w_px]

            if np.any(core_region):
                continue

            # Place panel
            occupancy[y : y + panel_h_px, x : x + panel_w_px] = 1

            panels.append({
                "panel_id": panel_id,
                "x": int(x),
                "y": int(y),
                "width": int(panel_w_px),
                "height": int(panel_h_px),
                "real_x_m": round(x * pixel_to_m, 2),
                "real_y_m": round(y * pixel_to_m, 2),
                "tilt_degrees": round(latitude * 0.87 + 3.1, 1),
                "irradiance_pct": round(score * 100, 1),
            })
            panel_id += 1

        total_panels = len(panels)
        total_area = total_panels * PANEL_WIDTH_M * PANEL_HEIGHT_M
        system_kw = total_panels * PANEL_WATTAGE / 1000.0

        # Estimate annual generation
        avg_irr_score = float(np.mean([p["irradiance_pct"] for p in panels])) / 100.0 if panels else 0.5
        estimated_annual_kwh = system_kw * 1500 * avg_irr_score  # ~1500 kWh/kW in India (approximation)

        coverage = (total_area / max(roof_area_m2, 1)) * 100

        return {
            "panels": panels,
            "total_panels": total_panels,
            "total_area_m2": round(total_area, 1),
            "system_capacity_kw": round(system_kw, 2),
            "estimated_annual_kwh": round(estimated_annual_kwh, 0),
            "coverage_percentage": round(min(coverage, 100), 1),
        }


def save_placement_visualization(
    image_bgr: np.ndarray,
    heatmap_rgba: Optional[np.ndarray],
    panels: list,
    output_path: str,
):
    """Draw panel rectangles on top of the original image + heatmap."""
    viz = image_bgr.copy()

    # Blend heatmap if available
    if heatmap_rgba is not None:
        h, w = viz.shape[:2]
        hh, hw = heatmap_rgba.shape[:2]
        if (h, w) != (hh, hw):
            heatmap_rgba = cv2.resize(heatmap_rgba, (w, h), interpolation=cv2.INTER_NEAREST)

        alpha = heatmap_rgba[:, :, 3:4].astype(np.float32) / 255.0
        rgb = heatmap_rgba[:, :, :3].astype(np.float32)
        base = viz.astype(np.float32)
        viz = (base * (1 - alpha * 0.5) + rgb * alpha * 0.5).astype(np.uint8)

    # Draw panels
    for panel in panels:
        x, y = panel["x"], panel["y"]
        w, h = panel["width"], panel["height"]

        # Semi-transparent blue rectangle
        overlay = viz.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (255, 180, 50), -1)  # Blue fill
        viz = cv2.addWeighted(viz, 0.6, overlay, 0.4, 0)

        # White border
        cv2.rectangle(viz, (x, y), (x + w, y + h), (255, 255, 255), 2)

        # Panel number
        cv2.putText(viz, str(panel["panel_id"] + 1), (x + 3, y + h - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    # Panel count badge
    total = len(panels)
    if total > 0:
        capacity_kw = total * PANEL_WATTAGE / 1000
        badge_text = f"{total} Panels | {capacity_kw:.1f} kW"
        (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.rectangle(viz, (5, 5), (tw + 15, th + 15), (40, 40, 40), -1)
        cv2.putText(viz, badge_text, (10, th + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imwrite(output_path, viz)
