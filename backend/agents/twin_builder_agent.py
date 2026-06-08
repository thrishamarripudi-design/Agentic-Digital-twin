"""
Twin Builder Agent
Creates the DigitalTwinState — the structured virtual model of the business.
Combines user profile + data agent outputs into a coherent state object.
"""

import uuid
from datetime import datetime
from typing import Dict, Any
from backend.models.business_state import (
    BusinessProfile, DigitalTwinState, FinancialSnapshot, SeasonalContext
)


def build_digital_twin(
    profile: BusinessProfile,
    data_package: Dict[str, Any],
) -> DigitalTwinState:
    """
    Assembles the DigitalTwinState from the business profile
    and data agent enrichment package.
    """
    fin = data_package["financials"]
    seasonal: SeasonalContext = data_package["seasonal_context"]

    # Compute input completeness
    completeness = _compute_completeness(profile)

    financial_snapshot = FinancialSnapshot(
        monthly_profit=fin["monthly_profit"],
        profit_margin_pct=fin["profit_margin_pct"],
        monthly_cash_flow=fin["monthly_cash_flow"],
        debt_to_revenue_ratio=fin["debt_to_revenue_ratio"],
        inventory_turnover_days=fin["inventory_turnover_days"],
        break_even_revenue=fin["break_even_revenue"],
        current_liquidity_score=fin["current_liquidity_score"],
    )

    twin = DigitalTwinState(
        twin_id=str(uuid.uuid4())[:8],
        created_at=datetime.utcnow(),
        business_profile=profile,
        financial_snapshot=financial_snapshot,
        seasonal_context=seasonal,
        monthly_savings=fin["monthly_savings"],
        runway_months=fin["runway_months"],
        stock_risk_pct=data_package["stock_risk_pct"],
        is_profitable=data_package["is_profitable"],
        is_cash_flow_positive=data_package["is_cash_flow_positive"],
        has_debt_stress=data_package["has_debt_stress"],
        confidence_in_inputs=min(1.0, 0.6 + completeness * 0.4),
        data_completeness_pct=completeness,
    )

    return twin


def _compute_completeness(profile: BusinessProfile) -> float:
    """Simple completeness score based on how many optional fields are filled."""
    total = 8
    filled = 0
    if profile.rent_per_month > 0: filled += 1
    if profile.existing_loan_emi > 0: filled += 1
    if profile.seasonal_demand_notes: filled += 1
    if profile.avg_daily_customers: filled += 1
    if profile.peak_season_months: filled += 1
    if profile.years_in_business > 0: filled += 1
    if profile.employee_count > 0: filled += 1
    if profile.inventory_value > 0: filled += 1
    return round(filled / total, 2)


def twin_to_summary_text(twin: DigitalTwinState) -> str:
    """Converts the digital twin to a readable text summary for LLM prompts."""
    p = twin.business_profile
    f = twin.financial_snapshot
    s = twin.seasonal_context
    return f"""
=== DIGITAL TWIN SUMMARY ===
Business: {p.business_name} ({p.business_type.value}) in {p.location}
Years operating: {p.years_in_business} | Employees: {p.employee_count}

FINANCIALS:
- Monthly Revenue: ₹{p.monthly_revenue:,.0f}
- Monthly Expenses: ₹{p.monthly_expenses:,.0f}
- Monthly Profit: ₹{f.monthly_profit:,.0f} ({f.profit_margin_pct:.1f}% margin)
- Cash Flow after EMI: ₹{f.monthly_cash_flow:,.0f}
- Inventory Value: ₹{p.inventory_value:,.0f} ({f.inventory_turnover_days:.0f} day turnover)
- Existing Loan EMI: ₹{p.existing_loan_emi:,.0f}/month
- Debt-to-Revenue: {f.debt_to_revenue_ratio:.1%}
- Break-even Revenue: ₹{f.break_even_revenue:,.0f}/month

STATUS:
- Profitable: {twin.is_profitable} | Cash Flow Positive: {twin.is_cash_flow_positive}
- Debt Stress: {twin.has_debt_stress} | Runway: {twin.runway_months:.1f} months
- Stock Risk: {twin.stock_risk_pct:.0%}

SEASONAL CONTEXT:
- Current Month: {s.current_month} | Demand Multiplier: {s.expected_demand_multiplier}x
- Upcoming Festivals: {', '.join(s.upcoming_festivals) or 'None'}
- Weather Risk: {s.weather_risk_level} | {s.weather_notes}
=== END TWIN ===
"""
