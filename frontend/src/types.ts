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
    status: "pending" | "preprocessing" | "depth_estimation" | "shadow_simulation" | "panel_placement" | "financial_calculation" | "generating_report" | "complete" | "failed";
    progress_percent: number;
    current_step: string;
    error_message?: string;
}

export interface PanelPlacement {
    panel_id: number;
    x: number;
    y: number;
    width: number;
    height: number;
    real_x_m: number;
    real_y_m: number;
    tilt_degrees: number;
    irradiance_pct: number;
}

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

export interface CompleteScanResult {
    scan_id: string;
    processing_time_seconds: number;
    depth: {
        estimated_roof_area_m2: number;
        tilt_angle_degrees: number;
        obstruction_count: number;
        confidence: number;
        depth_map_url: string;
    };
    shadow: {
        avg_irradiance_kwh_m2_year: number;
        heatmap_url: string;
    };
    placement: {
        panels: PanelPlacement[];
        total_panels: number;
        total_area_m2: number;
        system_capacity_kw: number;
        estimated_annual_kwh: number;
        coverage_percentage: number;
        placement_url: string;
    };
    financial: FinancialReport;
    summary: string;
    original_image_url: string;
    city: string;
    location: GPSCoords;
}
