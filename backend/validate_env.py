"""
SolarSense AI — Environment Validation Script
Run:  python validate_env.py
"""
import sys, importlib, os

CHECKS: list[tuple[str, callable]] = []

def check(name):
    def decorator(fn):
        CHECKS.append((name, fn))
        return fn
    return decorator

# ── checks ─────────────────────────────────────

@check("Python >= 3.10")
def _():
    v = sys.version_info
    assert v >= (3, 10), f"Got {v.major}.{v.minor}"

@check("PyTorch installed")
def _():
    import torch  # noqa: F401

@check("Compute device")
def _():
    from backend.utils.gpu_manager import get_device, get_device_info
    info = get_device_info()
    device = get_device()
    print(f"  → device={device}  name={info.get('gpu_name', 'CPU')}")

@check("FastAPI & Uvicorn")
def _():
    import fastapi, uvicorn  # noqa: F401

@check("Pillow / OpenCV / NumPy")
def _():
    from PIL import Image  # noqa: F401
    import cv2, numpy  # noqa: F401

@check("Transformers (HuggingFace)")
def _():
    import transformers  # noqa: F401

@check("Pydantic")
def _():
    import pydantic  # noqa: F401

@check(".env file exists")
def _():
    from dotenv import load_dotenv
    load_dotenv()
    if not os.path.exists(os.path.join(os.path.dirname(__file__), '..', '.env')):
        print("  ⚠ .env not found – using defaults (copy .env.example → .env)")

@check("Static data files")
def _():
    import json
    for name in ("city_costs.json", "subsidy_table.json", "panel_specs.json"):
        path = os.path.join(os.path.dirname(__file__), "data", name)
        assert os.path.exists(path), f"Missing {name}"
        with open(path) as f:
            json.load(f)

# ── runner ──────────────────────────────────────

def main():
    print("=" * 50)
    print("  SolarSense AI — Environment Validation")
    print("=" * 50)
    passed = failed = 0
    for name, fn in CHECKS:
        try:
            fn()
            print(f"  ✅  {name}")
            passed += 1
        except Exception as e:
            print(f"  ❌  {name}: {e}")
            failed += 1
    print("-" * 50)
    print(f"  {passed} passed, {failed} failed")
    if failed:
        sys.exit(1)
    print("  🚀  All checks passed — ready to start!")

if __name__ == "__main__":
    main()
