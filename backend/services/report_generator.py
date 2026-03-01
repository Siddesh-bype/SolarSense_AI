"""
Report Generator — LLM-based personalised solar installation summary.
Falls back to a deterministic template if the API is unavailable.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates plain-English solar installation summaries."""

    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    def generate_summary(self, scan_data: dict) -> str:
        """
        Generate a personalised summary using LLM or template fallback.
        scan_data should include: city, usable_area_m2, total_panels,
        system_capacity_kw, annual_kwh, monthly_bill, bill_offset_pct,
        gross_cost, subsidy, net_cost, payback_years, savings_25yr.
        """
        if self.api_key:
            result = self._call_llm(scan_data)
            if result:
                return result
            logger.warning("[Report] LLM API failed, using template fallback.")

        return self._template_fallback(scan_data)

    def _call_llm(self, data: dict) -> Optional[str]:
        """Call Anthropic Claude API for a personalised summary."""
        try:
            import httpx

            prompt = self._build_prompt(data)
            response = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 500,
                    "temperature": 0.7,
                    "system": (
                        "You are SolarSense AI, an expert solar energy advisor for Indian homeowners. "
                        "Write a friendly, clear, encouraging summary in 3 short paragraphs. "
                        "Use simple language. Include specific numbers from the data provided. "
                        "Do not use jargon. Write as if speaking to a homeowner. "
                        "End with one specific call to action."
                    ),
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=15.0,
            )
            response.raise_for_status()
            result = response.json()
            return result["content"][0]["text"]
        except Exception as e:
            logger.error(f"[Report] LLM API error: {e}")
            return None

    def _build_prompt(self, data: dict) -> str:
        return (
            f"Generate a personalised solar installation summary for this rooftop scan:\n"
            f"- Location: {data.get('city', 'Unknown')}\n"
            f"- Roof area analysed: {data.get('usable_area_m2', 0):.1f} square metres\n"
            f"- Panels placed: {data.get('total_panels', 0)} panels "
            f"({data.get('system_capacity_kw', 0):.1f} kW system)\n"
            f"- Annual energy generation: {data.get('annual_kwh', 0):.0f} kWh\n"
            f"- Monthly electricity bill: Rs. {data.get('monthly_bill', 0):.0f}\n"
            f"- Bill offset: {data.get('bill_offset_pct', 0):.0f}%\n"
            f"- Total system cost: Rs. {data.get('gross_cost', 0):.0f}\n"
            f"- Government subsidy: Rs. {data.get('subsidy', 0):.0f}\n"
            f"- Net cost after subsidy: Rs. {data.get('net_cost', 0):.0f}\n"
            f"- Payback period: {data.get('payback_years', 0):.1f} years\n"
            f"- 25-year savings: Rs. {data.get('savings_25yr', 0):.0f}\n\n"
            f"Write the summary now:"
        )

    @staticmethod
    def _template_fallback(data: dict) -> str:
        """Deterministic templated summary when LLM is unavailable."""
        return (
            f"Great news! Your {data.get('usable_area_m2', 0):.0f} square metre rooftop "
            f"in {data.get('city', 'your city').title()} can fit "
            f"{data.get('total_panels', 0)} solar panels — a "
            f"{data.get('system_capacity_kw', 0):.1f} kW system that will generate "
            f"approximately {data.get('annual_kwh', 0):,.0f} units of electricity every year, "
            f"covering {data.get('bill_offset_pct', 0):.0f}% of your current electricity usage.\n\n"
            f"After applying the PM Surya Ghar government subsidy of "
            f"₹{data.get('subsidy', 0):,.0f}, your total investment comes to "
            f"₹{data.get('net_cost', 0):,.0f}. With your current electricity bill, "
            f"you'll recover this investment in {data.get('payback_years', 0):.1f} years — "
            f"and save ₹{data.get('savings_25yr', 0):,.0f} over the 25-year panel lifetime.\n\n"
            f"The best areas on your roof receive over 90% of available sunlight year-round. "
            f"We recommend contacting a verified installer with this report to get an exact quote."
        )
