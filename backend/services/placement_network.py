"""
Placement Network — Neural panel placement model trained on synthetic rooftop data.
Loads the PlacementNet architecture and weights from backend/weights/.
"""
import logging
import os
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

_placement_model = None
_model_device = None

WEIGHTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "weights", "placement_net.pth"
)


def _get_placement_model(device: str = "cpu"):
    """Lazy-load the PlacementNet model from disk."""
    global _placement_model, _model_device

    if _placement_model is not None and _model_device == device:
        return _placement_model

    if not os.path.isfile(WEIGHTS_PATH):
        logger.warning(
            f"[PlacementNet] Weights not found at {WEIGHTS_PATH}. "
            "Neural placement disabled — using algorithmic fallback."
        )
        return None

    try:
        import torch
        import torch.nn as nn

        class PlacementNet(nn.Module):
            """U-Net-style encoder-decoder for panel placement probability."""

            def __init__(self) -> None:
                super().__init__()
                self.encoder = nn.Sequential(
                    nn.Conv2d(1, 32, 3, padding=1),
                    nn.BatchNorm2d(32),
                    nn.ReLU(),
                    nn.Conv2d(32, 64, 3, padding=1),
                    nn.BatchNorm2d(64),
                    nn.ReLU(),
                    nn.MaxPool2d(2),
                    nn.Conv2d(64, 128, 3, padding=1),
                    nn.BatchNorm2d(128),
                    nn.ReLU(),
                    nn.Conv2d(128, 128, 3, padding=1),
                    nn.BatchNorm2d(128),
                    nn.ReLU(),
                    nn.MaxPool2d(2),
                    nn.Conv2d(128, 256, 3, padding=1),
                    nn.BatchNorm2d(256),
                    nn.ReLU(),
                )
                self.decoder = nn.Sequential(
                    nn.ConvTranspose2d(256, 128, 2, stride=2),
                    nn.BatchNorm2d(128),
                    nn.ReLU(),
                    nn.Conv2d(128, 64, 3, padding=1),
                    nn.BatchNorm2d(64),
                    nn.ReLU(),
                    nn.ConvTranspose2d(64, 32, 2, stride=2),
                    nn.BatchNorm2d(32),
                    nn.ReLU(),
                    nn.Conv2d(32, 1, 1),
                    nn.Sigmoid(),
                )

            def forward(self, x: torch.Tensor) -> torch.Tensor:
                return self.decoder(self.encoder(x))

        torch_device = torch.device(device)
        model = PlacementNet()
        state_dict = torch.load(WEIGHTS_PATH, map_location=torch_device, weights_only=True)
        model.load_state_dict(state_dict)
        model = model.to(torch_device).eval()

        _placement_model = model
        _model_device = device
        logger.info("[PlacementNet] Model loaded successfully from %s", WEIGHTS_PATH)
        return model

    except Exception as e:
        logger.warning("[PlacementNet] Failed to load model: %s", e)
        return None


def predict_placement(
    irradiance_map: np.ndarray,
    device: str = "cpu",
) -> Optional[np.ndarray]:
    """
    Run the neural placement model on an irradiance map.

    Args:
        irradiance_map: 2D float32 array (any size, will be resized to 256x256).
        device: torch device string ("cpu" or "cuda:0").

    Returns:
        Probability map (same size as input) with values in [0, 1],
        or None if model is unavailable.
    """
    model = _get_placement_model(device)
    if model is None:
        return None

    try:
        import torch

        h, w = irradiance_map.shape[:2]

        # Normalize irradiance to [0, 1]
        irr = irradiance_map.astype(np.float32)
        irr_max = irr.max()
        if irr_max > 0:
            irr = irr / irr_max

        # Resize to 256x256 (model input size)
        irr_resized = cv2.resize(irr, (256, 256), interpolation=cv2.INTER_LINEAR)

        # Create tensor: [1, 1, 256, 256]
        tensor = torch.tensor(irr_resized).float().unsqueeze(0).unsqueeze(0)
        tensor = tensor.to(device)

        # Inference
        with torch.no_grad():
            prob = model(tensor).squeeze().cpu().numpy()

        # Resize back to original dimensions
        prob_full = cv2.resize(
            prob.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR
        )

        return prob_full

    except Exception as e:
        logger.warning("[PlacementNet] Inference failed: %s", e)
        return None
