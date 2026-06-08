"""
Recommendation Agent
Uses the LLM to synthesize all agent outputs into a final recommendation.
Falls back to rule-based recommendation if no LLM is configured.
"""

import uuid
import json
from datetime import datetime
from typing import List, Dict, Any
from backend.models.business_state import (
    DigitalTwinState, ScenarioResult, RiskAnalysis, RecommendationReport
)
from backend.core.llm_client import call_llm, safe_parse_json, is_llm_available
from backend.agents.twin_builder_agent import twin_to_summary_text


SYSTEM_PROMPT = """You are an expert business advisor for small grocery stores and kirana shops in India.

You have been given:
1. A digital twin summary of the business
2. Three scenario simulation results (base, optimistic, pessimistic)
3. A risk analysis

Your job is to produce a concise, actionable recommendation in JSON format.

Rules:
- Be specific and practical. Use actual numbers from the data.
- Speak directly to the shop owner in plain language.
- Do NOT give generic advice. Reference the specific business data.
- Always mention risks AND opportunities.
- Confidence score should reflect genuine data quality, not be artificially high.

Respond ONLY with valid JSON. No preamble, no explanation outside JSON.

Output format:
{
  "primary_recommendation": "One clear sentence: what should the owner do?",
  "action_plan": [
    "Step 1: specific action with timeline",
    "Step 2: ...",
    "Step 3: ..."
  ],
  "do_not_do": [
    "Risk to avoid 1",
    "Risk to avoid 2"
  ],
  "key_insight": "The most important single insight from the analysis",
  "explanation": "2-3 sentences explaining the reasoning behind the recommendation",
  "recommended_timeline": "e.g. Act within 2 weeks before Diwali",
  "expected_roi_pct": 15.5
}
"""


async def run_recommendation_agent(
    twin: DigitalTwinState,
    scenarios: List[ScenarioResult],
    risk_analysis: RiskAnalysis,
    user_question: str,
    forecast_data: Dict[str, Any],
    planner_plan: Dict[str, Any],
) -> RecommendationReport:
    """
    Calls the LLM with full context and parses structured recommendation.
    Falls back to a rule-based recommendation if LLM is not available or fails.
    """
    avg_confidence = sum(s.confidence_score for s in scenarios) / len(scenarios)

    if is_llm_available():
        twin_summary = twin_to_summary_text(twin)
        scenario_text = _format_scenarios(scenarios)
        risk_text = _format_risk(risk_analysis)
        forecast_text = _format_forecast(forecast_data)

        user_message = f"""
USER QUESTION: {user_question}

{twin_summary}

FORECAST SUMMARY:
{forecast_text}

SCENARIO RESULTS:
{scenario_text}

RISK ANALYSIS:
{risk_text}

Planner's reasoning: {planner_plan.get('reasoning', 'N/A')}

Generate the final recommendation JSON.
"""
        try:
            raw = await call_llm(
                system_prompt=SYSTEM_PROMPT,
                user_message=user_message,
                max_tokens=1200,
                temperature=0.25,
                json_mode=True,
            )
            data = safe_parse_json(raw)
        except Exception:
            data = _rule_based_recommendation(twin, scenarios, risk_analysis, user_question)
    else:
        data = _rule_based_recommendation(twin, scenarios, risk_analysis, user_question)

    return RecommendationReport(
        recommendation_id=str(uuid.uuid4())[:8],
        generated_at=datetime.utcnow(),
        primary_recommendation=data.get("primary_recommendation", "Proceed with caution"),
        action_plan=data.get("action_plan", []),
        do_not_do=data.get("do_not_do", []),
        overall_risk_score=risk_analysis.overall_risk_score,
        confidence_score=round(avg_confidence, 2),
        expected_roi_pct=data.get("expected_roi_pct"),
        risk_analysis=risk_analysis,
        scenario_comparison=scenarios,
        key_insight=data.get("key_insight", ""),
        explanation=data.get("explanation", ""),
        recommended_timeline=data.get("recommended_timeline", "Within the next 2-4 weeks"),
    )


def _format_scenarios(scenarios: List[ScenarioResult]) -> str:
    lines = []
    for s in scenarios:
        lines.append(
            f"[{s.label}]\n"
            f"  Revenue: Rs{s.projected_revenue:,.0f} | Profit: Rs{s.projected_profit:,.0f}\n"
            f"  Risk: {s.risk_score:.0%} | Opportunity: {s.opportunity_score:.0%}\n"
            f"  Drivers: {', '.join(s.key_drivers[:2])}\n"
            f"  Warnings: {', '.join(s.warnings[:2])}\n"
        )
    return "\n".join(lines)


def _format_risk(risk: RiskAnalysis) -> str:
    return (
        f"Overall Risk: {risk.risk_level.upper()} ({risk.overall_risk_score:.0%})\n"
        f"Cash Shortage: {risk.cash_shortage_risk:.0%} | Debt Stress: {risk.debt_stress_risk:.0%}\n"
        f"Stockout: {risk.inventory_stockout_risk:.0%} | Overstock: {risk.inventory_overstock_risk:.0%}\n"
        f"Top Risks: {'; '.join(risk.top_risks[:2])}\n"
        f"Mitigations: {'; '.join(risk.mitigations[:2])}"
    )


def _format_forecast(forecast_data: Dict[str, Any]) -> str:
    fc = forecast_data.get("base_forecast", {})
    mc = forecast_data.get("monte_carlo_distribution", {})
    return (
        f"Trend: {fc.get('trend_direction', 'stable')} | "
        f"Avg demand multiplier: {fc.get('avg_demand_multiplier', 1.0)}x\n"
        f"Revenue range (P25-P75): Rs{mc.get('p25', 0):,.0f} - Rs{mc.get('p75', 0):,.0f}"
    )


def _rule_based_recommendation(
    twin: DigitalTwinState,
    scenarios: List[ScenarioResult],
    risk: RiskAnalysis,
    question: str,
) -> Dict[str, Any]:
    """Full rule-based recommendation — works with zero API key."""
    p = twin.business_profile
    f = twin.financial_snapshot
    q = question.lower()

    # Determine question type for targeted advice
    if any(w in q for w in ["loan", "borrow", "credit"]):
        if risk.debt_stress_risk > 0.4:
            primary = f"Avoid taking a new loan right now. Your current debt ratio is {f.debt_to_revenue_ratio:.0%} — repay existing EMI first before adding more burden."
            actions = [
                "Focus on increasing revenue by 10-15% over the next 3 months",
                "Reduce non-essential expenses to improve cash flow",
                "Revisit loan option after 6 months when debt ratio improves",
            ]
            avoid = ["Taking any new loan until cash flow improves", "Expanding inventory on credit"]
            timeline = "Reassess in 6 months"
            roi = None
        else:
            primary = f"You can consider a small loan — your debt ratio is healthy at {f.debt_to_revenue_ratio:.0%}. Ensure EMI does not exceed 25% of monthly revenue."
            actions = [
                f"Keep total EMI below Rs{p.monthly_revenue * 0.25:,.0f}/month (25% of revenue)",
                "Use loan for high-ROI investments like inventory or equipment, not working capital",
                "Maintain 2 months of expenses as cash buffer before taking the loan",
            ]
            avoid = ["Using loan for recurring expenses", "Taking loan without a clear revenue growth plan"]
            timeline = "Can proceed within 2-4 weeks"
            roi = 12.0

    elif any(w in q for w in ["inventory", "stock", "festival", "season"]):
        festivals = twin.seasonal_context.upcoming_festivals
        fest_str = festivals[0] if festivals else "upcoming festival"
        dm = twin.seasonal_context.expected_demand_multiplier
        if dm > 1.2:
            primary = f"Yes — stock up 20-25% on fast-moving items before {fest_str}. Demand is expected {dm:.1f}x above normal."
            actions = [
                f"Increase inventory of rice, oil, pulses, and snacks by 25% (cost ~Rs{p.inventory_value * 0.25:,.0f})",
                f"Order 2-3 weeks before {fest_str} to avoid last-minute price hikes",
                "Clear slow-moving stock with small discounts to free up shelf space",
            ]
            avoid = [
                "Over-stocking perishables — they won't last beyond the festival window",
                "Buying on credit if cash flow is already tight",
            ]
            timeline = f"Stock up 2-3 weeks before {fest_str}"
            roi = 18.0
        else:
            primary = "Maintain current inventory levels — demand is not significantly elevated this period."
            actions = [
                "Review which items sold fastest last festival season",
                "Stock a 10% buffer on top 5 best-selling items only",
                "Negotiate with suppliers for flexible return on slow movers",
            ]
            avoid = ["Large upfront inventory purchases in a low-demand period"]
            timeline = "No urgent action needed"
            roi = 5.0

    elif any(w in q for w in ["expand", "branch", "outlet", "second"]):
        if f.monthly_cash_flow < p.monthly_expenses * 0.3:
            primary = "Delay expansion — current cash flow is too thin to support a second outlet without significant risk."
            actions = [
                f"Build cash reserves to at least Rs{p.monthly_expenses * 3:,.0f} (3 months expenses) first",
                "Improve current store profitability to 25%+ margin before expanding",
                "Research target location for 3-6 months while building capital",
            ]
            avoid = ["Opening a second outlet while cash flow is below 30% of expenses"]
            timeline = "Revisit in 6-12 months"
            roi = None
        else:
            primary = "Expansion is feasible but requires careful planning. Start small with a lean second outlet."
            actions = [
                "Choose a location within 5km of current store to share supply chain",
                "Start with 60-70% of current store's inventory to reduce upfront cost",
                f"Ensure combined EMI stays below Rs{(p.monthly_revenue * 2) * 0.25:,.0f}/month",
            ]
            avoid = ["Full-scale expansion in year 1 — ramp up gradually"]
            timeline = "Plan for 3-6 months, launch in 6-9 months"
            roi = 20.0

    elif any(w in q for w in ["rain", "weather", "monsoon", "drought"]):
        primary = "Build a weather buffer — maintain 15% extra non-perishable stock and a cash reserve of 1.5x monthly expenses."
        actions = [
            "Stock up on non-perishables (rice, dal, oil) by 15% before monsoon",
            f"Maintain cash buffer of Rs{p.monthly_expenses * 1.5:,.0f} for lean monsoon months",
            "Reduce perishable orders by 20% during peak monsoon (Jun-Aug)",
        ]
        avoid = ["Large investments in perishables during high weather-risk months"]
        timeline = "Prepare 2 weeks before monsoon season"
        roi = None

    else:
        # General advice based on risk level
        if risk.overall_risk_score < 0.35:
            primary = f"Business is in good health. Focus on capturing the upcoming demand boost ({twin.seasonal_context.expected_demand_multiplier:.1f}x) with targeted inventory increase."
            actions = risk.mitigations[:3] or ["Monitor cash flow weekly", "Review top-selling items monthly"]
            avoid = ["Complacency — use this profitable period to build reserves"]
            timeline = "Act within 2 weeks"
            roi = 10.0
        elif risk.overall_risk_score < 0.6:
            primary = "Moderate risk — strengthen cash position before making any new investments."
            actions = risk.mitigations[:3]
            avoid = [risk.top_risks[0]] if risk.top_risks else []
            timeline = "Address within 1 month"
            roi = None
        else:
            primary = "High risk detected — prioritise cash flow stability above all else."
            actions = risk.mitigations[:3]
            avoid = risk.top_risks[:2]
            timeline = "Immediate action required"
            roi = None

    return {
        "primary_recommendation": primary,
        "action_plan": actions,
        "do_not_do": avoid,
        "key_insight": risk.top_risks[0] if risk.top_risks else f"Demand multiplier is {twin.seasonal_context.expected_demand_multiplier:.1f}x — plan accordingly.",
        "explanation": (
            f"Based on monthly cash flow of Rs{f.monthly_cash_flow:,.0f}, "
            f"profit margin of {f.profit_margin_pct:.1f}%, "
            f"and overall risk score of {risk.overall_risk_score:.0%}. "
            f"Seasonal demand multiplier is {twin.seasonal_context.expected_demand_multiplier:.1f}x this period."
        ),
        "recommended_timeline": timeline,
        "expected_roi_pct": roi,
    }