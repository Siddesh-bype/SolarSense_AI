"""
GPU Manager — Auto-detects AMD ROCm, CUDA, or CPU and exposes get_device().
"""
import logging
import torch

logger = logging.getLogger(__name__)


def get_device() -> torch.device:
    """
    Detect the best available compute device.
    Priority: AMD ROCm (HIP) → NVIDIA CUDA → CPU
    """
    # Check AMD ROCm
    if hasattr(torch.version, "hip") and torch.version.hip is not None:
        if torch.cuda.is_available():
            device = torch.device("cuda:0")  # ROCm uses CUDA API under the hood
            logger.info("[GPU Manager] AMD ROCm detected — using: hip:0")
            return device

    # Check NVIDIA CUDA
    if torch.cuda.is_available():
        device = torch.device("cuda:0")
        gpu_name = torch.cuda.get_device_name(0)
        logger.info(f"[GPU Manager] CUDA detected — using: cuda:0 ({gpu_name})")
        return device

    # Fallback to CPU
    logger.warning("[GPU Manager] No GPU detected — using: CPU (demo mode)")
    return torch.device("cpu")


def get_device_info() -> dict:
    """Return device information for diagnostics."""
    device = get_device()
    info = {
        "device": str(device),
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "rocm_available": hasattr(torch.version, "hip") and torch.version.hip is not None,
    }
    if torch.cuda.is_available():
        info["gpu_name"] = torch.cuda.get_device_name(0)
        info["gpu_memory_gb"] = round(torch.cuda.get_device_properties(0).total_mem / 1e9, 2)
    return info


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    device = get_device()
    print(f"Active device: {device}")
    print(f"Device info: {get_device_info()}")
