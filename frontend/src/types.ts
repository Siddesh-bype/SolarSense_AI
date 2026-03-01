export interface GPSCoords {
    latitude: number;
    longitude: number;
}

export interface BBox {
    x: number;
    y: number;
    width: number;
    height: number;
}

export interface ScanStatusResponse {
    scan_id: string;
    status: "pending" | "preprocessing" | "depth_estimation" | "shadow_simulation" | "analyzed" | "complete" | "failed";
    progress_percent: number;
    current_step: string;
    error_message?: string;
}

/* ── Phase 1: Analysis Result (from POST /api/scan/upload) ── */

export interface PanelSpec {
    width_px: number;
    height_px: number;
    wattage: number;
    width_m: number;
    height_m: number;
}

export interface AnalysisResult {
    scan_id: string;
    processing_time_seconds: number;
    image_width: number;
    image_height: number;
    depth: {
        estimated_roof_area_m2: number;
        tilt_angle_degrees: number;
        obstruction_count: number;
        obstruction_boxes: BBox[];
        confidence: number;
        depth_map_url: string;
        roof_mask_url: string;
    };
    shadow: {
        avg_irradiance_kwh_m2_year: number;
        peak_irradiance_zone: number[];
        heatmap_url: string;
    };
    panel_spec: PanelSpec;
    original_image_url: string;
    city: string;
    location: GPSCoords;
    irradiance_source: string;
}

/* ── Phase 2: Financial Calc Result (from POST /api/scan/calculate) ── */

export interface CostBreakdown {
    panel_cost_inr: number;
    inverter_cost_inr: number;
    mounting_wiring_inr: number;
    installation_cost_inr: number;
    gross_cost_inr: number;
    subsidy_inr: number;
    net_cost_inr: number;
}

export interface EMIResult {
    monthly_emi_inr: number;
    total_payable_inr: number;
    annual_rate_pct: number;
    tenure_months: number;
}

export interface FinancialReport {
    system_capacity_kw: number;
    annual_generation_kwh: number;
    monthly_generation_kwh: number[];
    cost_breakdown: CostBreakdown;
    annual_savings_inr: number;
    payback_years: number;
    savings_25yr_inr: number;
    bill_offset_pct: number;
    emi: EMIResult;
    cumulative_savings_by_year: number[];
}

export interface FinancialCalcResult {
    total_panels: number;
    financial: FinancialReport;
    summary: string;
}
