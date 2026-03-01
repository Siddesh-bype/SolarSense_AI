"""
Pydantic models for financial data — costs, subsidies, and reports.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class MonthlyIrradiance(BaseModel):
    """Monthly average daily irradiance in kWh/m²/day for 12 months (Jan..Dec)."""
    values: list[float] = Field(..., min_length=12, max_length=12)
    source: str = "offline_fallback"


class CostBreakdown(BaseModel):
    panel_cost_inr: float = 0.0
    inverter_cost_inr: float = 0.0
    mounting_wiring_inr: float = 0.0
    installation_cost_inr: float = 0.0
    gross_cost_inr: float = 0.0
    subsidy_inr: float = 0.0
    net_cost_inr: float = 0.0


class EMIResult(BaseModel):
    monthly_emi_inr: float = 0.0
    total_payable_inr: float = 0.0
    annual_rate_pct: float = 8.5
    tenure_months: int = 84


class FinancialReport(BaseModel):
    system_capacity_kw: float = 0.0
    annual_generation_kwh: float = 0.0
    monthly_generation_kwh: list[float] = Field(default_factory=list)

    cost_breakdown: CostBreakdown = Field(default_factory=CostBreakdown)

    annual_savings_inr: float = 0.0
    payback_years: float = 0.0
    savings_25yr_inr: float = 0.0
    bill_offset_pct: float = 0.0

    emi: Optional[EMIResult] = None

    # For charts
    cumulative_savings_by_year: list[float] = Field(default_factory=list)
