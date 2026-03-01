"""Tests for image preprocessing."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
import numpy as np
import tempfile
from utils.image_preprocessor import ImagePreprocessor


def _make_test_image(w=800, h=800, brightness=128):
    """Create a test image with given dimensions and brightness."""
    img = np.full((h, w, 3), brightness, dtype=np.uint8)
    # Add some texture to pass blur check
    for i in range(0, h, 20):
        cv2.line(img, (0, i), (w, i), (brightness // 2, brightness // 2, brightness // 2), 1)
    for j in range(0, w, 20):
        cv2.line(img, (j, 0), (j, h), (brightness // 2, brightness // 2, brightness // 2), 1)
    return img


def test_valid_image():
    """A proper-sized, well-lit image should pass validation."""
    img = _make_test_image(800, 800, 128)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        cv2.imwrite(f.name, img)
        preprocessor = ImagePreprocessor()
        result = preprocessor.validate(f.name)
        assert result.is_valid, f"Expected valid, got: {result.reason}"
        print(f"✅ Valid image accepted")
        os.unlink(f.name)


def test_tiny_image_rejected():
    """A tiny image should fail the resolution check."""
    img = _make_test_image(100, 100, 128)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        cv2.imwrite(f.name, img)
        preprocessor = ImagePreprocessor()
        result = preprocessor.validate(f.name)
        assert not result.is_valid, "Tiny image should be rejected"
        print(f"✅ Tiny image rejected: {result.reason}")
        os.unlink(f.name)


def test_dark_image_rejected():
    """A very dark image should fail the brightness check."""
    img = _make_test_image(800, 800, 10)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        cv2.imwrite(f.name, img)
        preprocessor = ImagePreprocessor()
        result = preprocessor.validate(f.name)
        assert not result.is_valid, "Dark image should be rejected"
        print(f"✅ Dark image rejected: {result.reason}")
        os.unlink(f.name)


if __name__ == "__main__":
    test_valid_image()
    test_tiny_image_rejected()
    test_dark_image_rejected()
    print("\nAll preprocessing tests passed!")
