"""
Risk Agent
Identifies and scores all risk dimensions for the business.
Produces a structured RiskAnalysis report.
"""

from typing import List, Dict, Any
from backend.models.business_state import DigitalTwinState, RiskAnalysis, ScenarioResult


WEATHER_RISK_SCORES = {"low": 0.10, "medium": 0.35, "high": 0.65}


def run_risk_agent(
    twin: DigitalTwinState,
    scenarios: List[ScenarioResult],
    forecast_data: Dict[str, Any],
) -> RiskAnalysis:
    """Compute risk analysis from the digital twin state and scenario results."""

    p = twin.business_profile
    f = twin.financial_snapshot
    s = twin.seasonal_context

    # ---- Individual risk scores ----

    # Inventory overstock risk (too much stock relative to turnover)
    inv_turnover = f.inventory_turnover_days
    overstock_risk = 0.0
    if inv_turnover > 45:
        overstock_risk = 0.80
    elif inv_turnover > 30:
        overstock_risk = 0.45
    elif inv_turnover > 20:
        overstock_risk = 0.20
    else:
        overstock_risk = 0.08

    # Inventory stockout risk (too little stock for demand)
    demand_mult = s.expected_demand_multiplier
    if inv_turnover < 7 and demand_mult > 1.2:
        stockout_risk = 0.85
    elif inv_turnover < 14 and demand_mult > 1.1:
        stockout_risk = 0.55
    elif inv_turnover < 21:
        stockout_risk = 0.30
    else:
        stockout_risk = 0.10

    # Cash shortage risk
    cash_flow = f.monthly_cash_flow
    if cash_flow < 0:
        cash_risk = 0.85
    elif cash_flow < p.monthly_expenses * 0.10:
        cash_risk = 0.60
    elif cash_flow < p.monthly_expenses * 0.20:
        cash_risk = 0.35
    else:
        cash_risk = 0.10

    # Debt stress risk
    debt_risk = min(0.95, f.debt_to_revenue_ratio * 2)

    # Demand shortfall risk — based on pessimistic scenario
    pess_scenario = next((r for r in scenarios if r.scenario_type.value == "pessimistic"), None)
    demand_shortfall_risk = 0.25
    if pess_scenario:
        demand_shortfall_risk = pess_scenario.cash_shortage_probability

    # Weather risk
    weather_risk = WEATHER_RISK_SCORES.get(s.weather_risk_level, 0.20)

    # ---- Composite risk score ----
    # Weighted average of individual risks
    weights = {
        "cash": 0.30,
        "debt": 0.20,
        "stockout": 0.20,
        "overstock": 0.10,
        "demand": 0.10,
        "weather": 0.10,
    }
    overall = (
        cash_risk * weights["cash"]
        + debt_risk * weights["debt"]
        + stockout_risk * weights["stockout"]
        + overstock_risk * weights["overstock"]
        + demand_shortfall_risk * weights["demand"]
        + weather_risk * weights["weather"]
    )
    overall = round(min(1.0, overall), 2)

    risk_level = _risk_level(overall)

    top_risks = _identify_top_risks(
        cash_risk, debt_risk, stockout_risk, overstock_risk,
        demand_shortfall_risk, weather_risk, twin
    )

    mitigations = _suggest_mitigations(top_risks, twin)

    return RiskAnalysis(
        overall_risk_score=overall,
        risk_level=risk_level,
        inventory_overstock_risk=round(overstock_risk, 2),
        inventory_stockout_risk=round(stockout_risk, 2),
        cash_shortage_risk=round(cash_risk, 2),
        debt_stress_risk=round(debt_risk, 2),
        demand_shortfall_risk=round(demand_shortfall_risk, 2),
        weather_shock_risk=round(weather_risk, 2),
        top_risks=top_risks,
        mitigations=mitigations,
    )


def _risk_level(score: float) -> str:
    if score >= 0.70:
        return "critical"
    elif score >= 0.50:
        return "high"
    elif score >= 0.30:
        return "medium"
    else:
        return "low"


def _identify_top_risks(
    cash_risk, debt_risk, stockout_risk, overstock_risk,
    demand_risk, weather_risk, twin: DigitalTwinState
) -> List[str]:
    risks = []
    p = twin.business_profile
    f = twin.financial_snapshot

    if cash_risk > 0.5:
        risks.append(f"Cash flow is critically low (₹{f.monthly_cash_flow:,.0f}/month). Less than 1 month buffer.")
    if debt_risk > 0.45:
        risks.append(f"Debt burden is high ({f.debt_to_revenue_ratio:.0%} of revenue goes to EMI)")
    if stockout_risk > 0.5:
        risks.append(f"Stockout risk during upcoming demand peak — only {f.inventory_turnover_days:.0f} days of inventory")
    if overstock_risk > 0.5:
        risks.append(f"Inventory turnover is slow ({f.inventory_turnover_days:.0f} days) — risk of spoilage/tied-up capital")
    if demand_risk > 0.5:
        risks.append("Demand shortfall risk high — pessimistic scenario shows negative cash flow")
    if weather_risk > 0.5:
        risks.append(f"Weather risk elevated (monsoon season) — footfall may drop on heavy rain days")

    if not risks:
        risks.append("No critical risks identified — business is in stable condition")

    return risks[:4]


def _suggest_mitigations(top_risks: List[str], twin: DigitalTwinState) -> List[str]:
    mitigations = []
    p = twin.business_profile
    f = twin.financial_snapshot

    if f.monthly_cash_flow < p.monthly_expenses * 0.2:
        mitigations.append("Build a cash buffer of at least 1.5x monthly expenses before any new investment")

    if f.inventory_turnover_days > 30:
        mitigations.append("Reduce slow-moving inventory; negotiate with suppliers for shorter payment cycles")

    if f.inventory_turnover_days < 14 and twin.seasonal_context.expected_demand_multiplier > 1.2:
        mitigations.append("Stock up key fast-moving items (rice, oil, pulses) 2–3 weeks before peak season")

    if f.debt_to_revenue_ratio > 0.3:
        mitigations.append("Avoid new loans until existing EMI drops below 20% of monthly revenue")

    if twin.seasonal_context.weather_risk_level in ("medium", "high"):
        mitigations.append("Maintain 10–15% extra stock of non-perishables as monsoon buffer")

    if twin.seasonal_context.upcoming_festivals:
        mitigations.append(
            f"Promote festive combos and bulk buy offers ahead of "
            f"{twin.seasonal_context.upcoming_festivals[0]} to capture demand early"
        )

    return mitigations[:4]
