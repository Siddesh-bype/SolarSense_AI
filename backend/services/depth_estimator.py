"""
Depth Estimator — Uses Depth Anything V2 for monocular depth estimation,
then segments roof area and identifies obstructions via K-means clustering.
"""
import logging
from typing import Optional, Tuple

import cv2
import numpy as np
from scipy import ndimage

logger = logging.getLogger(__name__)

# Lazy-load heavy imports
_depth_pipeline = None


def _get_depth_pipeline(device: str = "cpu"):
    """Lazy-load the Depth Anything V2 model."""
    global _depth_pipeline
    if _depth_pipeline is not None:
        return _depth_pipeline

    try:
        from transformers import pipeline as hf_pipeline
        logger.info("[Depth] Loading Depth Anything V2 Small model...")
        _depth_pipeline = hf_pipeline(
            task="depth-estimation",
            model="depth-anything/Depth-Anything-V2-Small-hf",
            device=0 if "cuda" in device else -1,
        )
        logger.info("[Depth] Model loaded successfully.")
    except Exception as e:
        logger.warning(f"[Depth] Failed to load model: {e}. Using synthetic fallback.")
        _depth_pipeline = None
    return _depth_pipeline


class DepthEstimator:
    """Estimates depth from a single rooftop image, segments roof and obstructions."""

    def __init__(self, device: str = "cpu"):
        self.device = device

    def estimate(
        self,
        image_bgr: np.ndarray,
        roof_hint: Optional[np.ndarray] = None,
    ) -> dict:
        """
        Run full depth estimation pipeline.
        Returns dict with: depth_map, roof_mask, obstruction_mask, obstruction_boxes,
        estimated_roof_area_m2, tilt_angle_degrees, confidence.
        """
        depth_map = self._run_depth_model(image_bgr)

        # Bilateral filter to smooth noise while preserving edges
        depth_smooth = cv2.bilateralFilter(
            (depth_map * 255).astype(np.uint8), d=9, sigmaColor=75, sigmaSpace=75
        ).astype(np.float32) / 255.0

        # Segment via K-means clustering
        roof_mask, obstruction_mask = self._segment_roof(depth_smooth)

        # Find obstruction bounding boxes
        obstruction_boxes = self._find_obstruction_boxes(obstruction_mask)

        # Estimate roof area
        h, w = image_bgr.shape[:2]
        roof_area = self._estimate_roof_area(depth_smooth, roof_mask, (w, h))

        # Estimate tilt
        tilt = self._estimate_tilt(depth_smooth, roof_mask)

        # Confidence score
        roof_pct = float(np.sum(roof_mask > 0)) / (h * w)
        confidence = min(1.0, max(0.1, roof_pct * 3))  # Boost if roof covers >33%

        return {
            "depth_map": depth_smooth,
            "roof_mask": roof_mask,
            "obstruction_mask": obstruction_mask,
            "obstruction_boxes": obstruction_boxes,
            "estimated_roof_area_m2": round(roof_area, 1),
            "tilt_angle_degrees": round(tilt, 1),
            "confidence": round(confidence, 2),
        }

    def _run_depth_model(self, image_bgr: np.ndarray) -> np.ndarray:
        """Run Depth Anything V2 or generate synthetic depth."""
        from PIL import Image as PILImage

        pipe = _get_depth_pipeline(self.device)

        if pipe is not None:
            try:
                rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
                pil_img = PILImage.fromarray(rgb)
                result = pipe(pil_img)
                depth_pil = result["depth"]
                depth_np = np.array(depth_pil).astype(np.float32)

                # Normalize to [0, 1]
                d_min, d_max = depth_np.min(), depth_np.max()
                if d_max - d_min > 0:
                    depth_np = (depth_np - d_min) / (d_max - d_min)
                else:
                    depth_np = np.zeros_like(depth_np)

                # Resize to match input
                h, w = image_bgr.shape[:2]
                depth_np = cv2.resize(depth_np, (w, h), interpolation=cv2.INTER_LINEAR)
                return depth_np
            except Exception as e:
                logger.warning(f"[Depth] Model inference failed: {e}. Using synthetic fallback.")

        # Synthetic fallback — simulate depth with gradient + noise
        return self._synthetic_depth(image_bgr)

    def _synthetic_depth(self, image_bgr: np.ndarray) -> np.ndarray:
        """Generate a synthetic depth map from image brightness for fallback."""
        h, w = image_bgr.shape[:2]
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0

        # Use brightness as proxy for depth (brighter = closer for roofs)
        # Add a vertical gradient (top = farther)
        vert_grad = np.linspace(0.3, 0.7, h).reshape(-1, 1) * np.ones((1, w))
        depth = gray * 0.6 + vert_grad.astype(np.float32) * 0.4

        # Normalize
        d_min, d_max = depth.min(), depth.max()
        if d_max - d_min > 0:
            depth = (depth - d_min) / (d_max - d_min)

        # Smooth
        depth = cv2.GaussianBlur(depth, (15, 15), 0)
        return depth

    def _segment_roof(self, depth_map: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Segment roof and obstructions using K-means clustering (k=3)."""
        h, w = depth_map.shape
        flat = depth_map.flatten().reshape(-1, 1).astype(np.float32)

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.5)
        try:
            _, labels, centers = cv2.kmeans(
                flat, 3, None, criteria, 5, cv2.KMEANS_PP_CENTERS
            )
        except cv2.error:
            # Fallback to threshold-based segmentation
            return self._threshold_segmentation(depth_map)

        labels = labels.reshape(h, w)
        centers = centers.flatten()

        # Sort cluster indices by depth center value
        sorted_idx = np.argsort(centers)

        # Assign: lowest depth = sky/background, middle = roof, highest = obstructions
        # (Depth Anything: higher values = closer objects)
        sky_label = sorted_idx[0]
        roof_label = sorted_idx[1]
        obstruction_label = sorted_idx[2]

        roof_mask = ((labels == roof_label) | (labels == obstruction_label)).astype(np.uint8) * 255
        obstruction_mask = (labels == obstruction_label).astype(np.uint8) * 255

        # Clean up masks with morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        roof_mask = cv2.morphologyEx(roof_mask, cv2.MORPH_CLOSE, kernel, iterations=3)
        roof_mask = cv2.morphologyEx(roof_mask, cv2.MORPH_OPEN, kernel, iterations=2)

        obstruction_mask = cv2.morphologyEx(obstruction_mask, cv2.MORPH_OPEN, kernel, iterations=2)

        return roof_mask, obstruction_mask

    def _threshold_segmentation(self, depth_map: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Fallback: simple percentile-based segmentation."""
        p20 = np.percentile(depth_map, 20)
        p70 = np.percentile(depth_map, 70)
        p85 = np.percentile(depth_map, 85)

        roof_mask = ((depth_map >= p20) & (depth_map <= p85)).astype(np.uint8) * 255
        obstruction_mask = (depth_map > p85).astype(np.uint8) * 255
        return roof_mask, obstruction_mask

    def _find_obstruction_boxes(self, obstruction_mask: np.ndarray) -> list:
        """Find bounding boxes of obstruction regions."""
        contours, _ = cv2.findContours(
            obstruction_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        boxes = []
        min_area = 100  # Ignore tiny contours
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= min_area:
                x, y, w, h = cv2.boundingRect(cnt)
                boxes.append({"x": int(x), "y": int(y), "width": int(w), "height": int(h)})
        return boxes

    def _estimate_roof_area(
        self, depth_map: np.ndarray, roof_mask: np.ndarray, image_size: Tuple[int, int]
    ) -> float:
        """
        Estimate real-world roof area using pinhole camera model.
        Assumes standard smartphone: focal length ~4.2mm, sensor 1/2.3".
        """
        w, h = image_size
        roof_pixels = float(np.sum(roof_mask > 0))
        total_pixels = float(h * w)
        roof_fraction = roof_pixels / total_pixels

        # Assume mean roof depth → typical rooftop photo covers ~80-200 m²
        # Scale factor: assume photo at ~10m distance covers ~15m width
        assumed_photo_width_m = 15.0
        pixel_to_m = assumed_photo_width_m / w
        roof_area_m2 = roof_pixels * (pixel_to_m ** 2)

        # Clamp to reasonable range
        return max(10.0, min(500.0, roof_area_m2))

    def _estimate_tilt(self, depth_map: np.ndarray, roof_mask: np.ndarray) -> float:
        """
        Estimate roof tilt angle from depth gradient using PCA.
        Returns degrees from horizontal.
        """
        try:
            # Get roof pixel coordinates and their depth values
            ys, xs = np.where(roof_mask > 0)
            if len(ys) < 100:
                return 10.0  # Default flat-ish roof

            # Sample points for speed
            n_samples = min(5000, len(ys))
            indices = np.random.choice(len(ys), n_samples, replace=False)
            xs_s = xs[indices].astype(np.float64)
            ys_s = ys[indices].astype(np.float64)
            zs_s = depth_map[ys[indices], xs[indices]].astype(np.float64)

            # Stack into point cloud
            points = np.stack([xs_s, ys_s, zs_s * 100], axis=1)  # Scale Z
            centroid = points.mean(axis=0)
            points_centered = points - centroid

            # PCA — the smallest eigenvalue direction is the surface normal
            cov = np.cov(points_centered.T)
            eigenvalues, eigenvectors = np.linalg.eigh(cov)
            normal = eigenvectors[:, 0]  # Smallest eigenvalue

            # Tilt angle: angle between normal and vertical (0,0,1)
            cos_angle = abs(normal[2]) / np.linalg.norm(normal)
            tilt_rad = np.arccos(np.clip(cos_angle, -1, 1))
            tilt_deg = float(np.degrees(tilt_rad))

            return max(0.0, min(60.0, tilt_deg))  # Clamp
        except Exception as e:
            logger.warning(f"[Depth] Tilt estimation failed: {e}")
            return 10.0  # Default


def save_depth_visualizations(
    image_bgr: np.ndarray,
    depth_result: dict,
    output_dir: str,
) -> dict:
    """Save debug visualizations of depth estimation results."""
    import os
    os.makedirs(output_dir, exist_ok=True)

    urls = {}

    # 1. Depth map colour-coded (near=red, far=blue)
    depth_map = depth_result["depth_map"]
    depth_colored = cv2.applyColorMap(
        (depth_map * 255).astype(np.uint8), cv2.COLORMAP_JET
    )
    path = os.path.join(output_dir, "depth_map.png")
    cv2.imwrite(path, depth_colored)
    urls["depth_map"] = "depth_map.png"

    # 2. Roof mask overlay
    roof_mask = depth_result["roof_mask"]
    overlay = image_bgr.copy()
    green_mask = np.zeros_like(image_bgr)
    green_mask[:, :, 1] = roof_mask  # Green channel
    overlay = cv2.addWeighted(overlay, 0.7, green_mask, 0.3, 0)
    path = os.path.join(output_dir, "roof_mask.png")
    cv2.imwrite(path, overlay)
    urls["roof_mask"] = "roof_mask.png"

    # 3. Obstruction boxes on original
    obstructions_viz = image_bgr.copy()
    for box in depth_result["obstruction_boxes"]:
        x, y, w, h = box["x"], box["y"], box["width"], box["height"]
        cv2.rectangle(obstructions_viz, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.putText(obstructions_viz, "Obstruction", (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    path = os.path.join(output_dir, "obstructions.png")
    cv2.imwrite(path, obstructions_viz)
    urls["obstructions"] = "obstructions.png"

    return urls
