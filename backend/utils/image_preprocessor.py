"""
Image Preprocessor — Validates, enhances, and normalizes rooftop images.
"""
import logging
from dataclasses import dataclass, field
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ExifTags

logger = logging.getLogger(__name__)

TARGET_SIZE = 1024


@dataclass
class ValidationResult:
    is_valid: bool
    reason: str = "ok"
    confidence: float = 1.0


@dataclass
class PreprocessedImageData:
    """In-memory preprocessed image with tensor and metadata."""
    tensor: np.ndarray  # H x W x 3, float32 [0, 1]
    original_size: Tuple[int, int]  # (width, height)
    gps_coords: Optional[Tuple[float, float]] = None  # (lat, lon)
    quality_score: float = 1.0


class ImagePreprocessor:
    """Validates and preprocesses rooftop images for the scan pipeline."""

    VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    MIN_WIDTH = 640
    MIN_HEIGHT = 480
    MIN_BRIGHTNESS = 30
    MIN_BLUR_VARIANCE = 20

    def validate(self, image_path: str) -> ValidationResult:
        """
        Validate an image for quality requirements:
        - Valid format (JPEG/PNG/WEBP)
        - Resolution >= 640x480
        - Not too dark (mean pixel > 30)
        - Not too blurry (Laplacian variance > 80)
        """
        import os
        ext = os.path.splitext(image_path)[1].lower()
        if ext not in self.VALID_EXTENSIONS:
            return ValidationResult(
                is_valid=False,
                reason="invalid_format",
                confidence=1.0,
            )

        try:
            img = cv2.imread(image_path)
            if img is None:
                return ValidationResult(is_valid=False, reason="unreadable_file", confidence=1.0)
        except Exception:
            return ValidationResult(is_valid=False, reason="unreadable_file", confidence=1.0)

        h, w = img.shape[:2]
        if w < self.MIN_WIDTH or h < self.MIN_HEIGHT:
            return ValidationResult(
                is_valid=False,
                reason="resolution_too_low",
                confidence=1.0,
            )

        # Brightness check
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean_brightness = float(np.mean(gray))
        if mean_brightness < self.MIN_BRIGHTNESS:
            return ValidationResult(
                is_valid=False,
                reason="image_too_dark",
                confidence=round(mean_brightness / self.MIN_BRIGHTNESS, 2),
            )

        # Blur check (Laplacian variance)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if laplacian_var < self.MIN_BLUR_VARIANCE:
            return ValidationResult(
                is_valid=False,
                reason="image_too_blurry",
                confidence=round(laplacian_var / self.MIN_BLUR_VARIANCE, 2),
            )

        quality = min(1.0, (mean_brightness / 128) * 0.5 + (min(laplacian_var, 500) / 500) * 0.5)
        return ValidationResult(is_valid=True, reason="ok", confidence=round(quality, 2))

    def preprocess(self, image_path: str) -> PreprocessedImageData:
        """
        Full preprocessing pipeline:
        1. Extract EXIF GPS if present
        2. Resize to 1024x1024 with aspect-ratio padding
        3. Normalize to [0, 1] float32
        4. Apply CLAHE contrast enhancement
        """
        gps = self.extract_gps(image_path)

        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")

        original_size = (img.shape[1], img.shape[0])  # (w, h)

        # Resize maintaining aspect ratio, pad with black
        img_resized = self._resize_with_padding(img, TARGET_SIZE)

        # Convert to float32 [0, 1]
        img_float = img_resized.astype(np.float32) / 255.0

        # Apply CLAHE contrast enhancement
        img_enhanced = self._apply_clahe(img_float)

        # Quality score
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean_b = float(np.mean(gray))
        lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        quality = min(1.0, (mean_b / 128) * 0.5 + (min(lap_var, 500) / 500) * 0.5)

        return PreprocessedImageData(
            tensor=img_enhanced,
            original_size=original_size,
            gps_coords=gps,
            quality_score=round(quality, 2),
        )

    def extract_gps(self, image_path: str) -> Optional[Tuple[float, float]]:
        """Extract (latitude, longitude) from EXIF data. Returns None if absent."""
        try:
            pil_img = Image.open(image_path)
            exif_data = pil_img._getexif()
            if exif_data is None:
                return None

            gps_info = {}
            for tag_id, value in exif_data.items():
                tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                if tag_name == "GPSInfo":
                    for gps_tag_id, gps_value in value.items():
                        gps_tag_name = ExifTags.GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_info[gps_tag_name] = gps_value

            if "GPSLatitude" not in gps_info or "GPSLongitude" not in gps_info:
                return None

            lat = self._dms_to_decimal(
                gps_info["GPSLatitude"],
                gps_info.get("GPSLatitudeRef", "N"),
            )
            lon = self._dms_to_decimal(
                gps_info["GPSLongitude"],
                gps_info.get("GPSLongitudeRef", "E"),
            )
            return (lat, lon)
        except Exception as e:
            logger.warning(f"[ImagePreprocessor] EXIF GPS extraction failed: {e}")
            return None

    # ---------- Private helpers ----------

    @staticmethod
    def _dms_to_decimal(dms_tuple, ref: str) -> float:
        """Convert EXIF DMS (degrees, minutes, seconds) to decimal degrees."""
        d, m, s = [float(x) for x in dms_tuple]
        decimal = d + m / 60.0 + s / 3600.0
        if ref in ("S", "W"):
            decimal = -decimal
        return decimal

    @staticmethod
    def _resize_with_padding(img: np.ndarray, target: int) -> np.ndarray:
        """Resize image to target x target, maintaining aspect ratio, padded with black."""
        h, w = img.shape[:2]
        scale = min(target / w, target / h)
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        canvas = np.zeros((target, target, 3), dtype=np.uint8)
        y_off = (target - new_h) // 2
        x_off = (target - new_w) // 2
        canvas[y_off : y_off + new_h, x_off : x_off + new_w] = resized
        return canvas

    @staticmethod
    def _apply_clahe(img_float: np.ndarray) -> np.ndarray:
        """Apply CLAHE to the L channel in LAB colour space."""
        img_uint8 = (img_float * 255).astype(np.uint8)
        lab = cv2.cvtColor(img_uint8, cv2.COLOR_BGR2LAB)
        l_channel, a, b = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l_channel)

        lab_enhanced = cv2.merge([l_enhanced, a, b])
        img_enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
        return img_enhanced.astype(np.float32) / 255.0
