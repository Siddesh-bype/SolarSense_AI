"""
Pydantic models for scan data — request/response schemas for the entire pipeline.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------- Enums ----------

class ScanStatus(str, Enum):
    PENDING = "pending"
    PREPROCESSING = "preprocessing"
    DEPTH_ESTIMATION = "depth_estimation"
    SHADOW_SIMULATION = "shadow_simulation"
    PANEL_PLACEMENT = "panel_placement"
    FINANCIAL_CALCULATION = "financial_calculation"
    GENERATING_REPORT = "generating_report"
    COMPLETE = "complete"
    FAILED = "failed"


# ---------- Primitives ----------

class BBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class GPSCoords(BaseModel):
    latitude: float
    longitude: float


# ---------- Image Preprocessing ----------

class ValidationResult(BaseModel):
    is_valid: bool
    reason: str = "ok"
    confidence: float = 1.0


class PreprocessedImage(BaseModel):
    """Metadata for a preprocessed image (tensor stored separately in memory)."""
    original_width: int
    original_height: int
    gps_coords: Optional[GPSCoords] = None
    quality_score: float = 1.0


# ---------- Depth Estimation ----------

class DepthResult(BaseModel):
    """Depth estimation output (numpy arrays stored in memory, only metadata here)."""
    obstruction_boxes: list[BBox] = Field(default_factory=list)
    estimated_roof_area_m2: float = 0.0
    tilt_angle_degrees: float = 0.0
    confidence: float = 0.0
    depth_map_url: Optional[str] = None
    roof_mask_url: Optional[str] = None


# ---------- Shadow Simulation ----------

class ShadowResult(BaseModel):
    """Shadow simulation output."""
    avg_irradiance_kwh_m2_year: float = 0.0
    peak_irradiance_zone: Optional[BBox] = None
    heatmap_url: Optional[str] = None


class SunPosition(BaseModel):
    azimuth_degrees: float
    elevation_degrees: float
    is_daytime: bool


# ---------- Panel Placement ----------

class PanelPlacement(BaseModel):
    panel_id: int
    x: int  # pixel x
    y: int  # pixel y
    width: int  # pixel width
    height: int  # pixel height
    real_x_m: float = 0.0
    real_y_m: float = 0.0
    tilt_degrees: float = 0.0
    irradiance_pct: float = 0.0


class PlacementResult(BaseModel):
    panels: list[PanelPlacement] = Field(default_factory=list)
    total_panels: int = 0
    total_area_m2: float = 0.0
    system_capacity_kw: float = 0.0
    estimated_annual_kwh: float = 0.0
    coverage_percentage: float = 0.0
    placement_visualization_url: Optional[str] = None


# ---------- Complete Scan ----------

class ScanStatusResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    progress_percent: int = 0
    current_step: str = ""
    error_message: Optional[str] = None


class ScanUploadResponse(BaseModel):
    scan_id: str
    status: ScanStatus = ScanStatus.PENDING


class CompleteScanResult(BaseModel):
    scan_id: str
    depth: DepthResult
    shadow: ShadowResult
    placement: PlacementResult
    financial: Optional[dict] = None  # FinancialReport as dict
    summary: str = ""
    original_image_url: Optional[str] = None
    heatmap_url: Optional[str] = None
    placement_url: Optional[str] = None
    city: str = "pune"
    monthly_bill: float = 3000.0
