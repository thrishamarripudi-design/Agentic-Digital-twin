"""
Data Agent
Takes raw business profile input, enriches it with seasonal/weather context,
and returns a normalized, analysis-ready data package.
"""

import json
from datetime import datetime
from typing import Dict, Any, List
from backend.models.business_state import BusinessProfile, SeasonalContext


# Festival calendar for India (month → festivals)
INDIAN_FESTIVAL_CALENDAR: Dict[int, List[str]] = {
    1: ["Pongal", "Makar Sankranti", "Republic Day"],
    2: ["Basant Panchami"],
    3: ["Holi"],
    4: ["Ram Navami", "Baisakhi"],
    5: [],
    6: [],
    7: [],
    8: ["Independence Day", "Janmashtami", "Onam"],
    9: ["Ganesh Chaturthi", "Navratri"],
    10: ["Navratri", "Dussehra", "Durga Puja"],
    11: ["Diwali", "Bhai Dooj", "Chhath Puja"],
    12: ["Christmas", "Year End"],
}

# Festival demand multiplier by season
DEMAND_MULTIPLIERS: Dict[int, float] = {
    1: 1.2,  2: 1.0,  3: 1.3,  4: 1.2,
    5: 0.9,  6: 0.85, 7: 0.9,  8: 1.1,
    9: 1.25, 10: 1.4, 11: 1.6, 12: 1.3,
}

# Karnataka/South India weather risk by month
WEATHER_RISK: Dict[int, str] = {
    1: "low",  2: "low",  3: "low",  4: "medium",
    5: "medium", 6: "high", 7: "high", 8: "high",
    9: "medium", 10: "medium", 11: "low", 12: "low",
}


def get_seasonal_context(location: str, peak_months: List[int]) -> SeasonalContext:
    """
    Build seasonal context based on current date and location.
    Uses rule-based logic — no external API needed for hackathon demo.
    """
    now = datetime.now()
    current_month = now.month

    # Look 2 months ahead for festivals
    upcoming = []
    for delta in range(3):
        m = ((current_month - 1 + delta) % 12) + 1
        upcoming.extend(INDIAN_FESTIVAL_CALENDAR.get(m, []))

    demand_mult = DEMAND_MULTIPLIERS.get(current_month, 1.0)

    # Boost if user's peak months include current or upcoming months
    if current_month in peak_months or (current_month % 12 + 1) in peak_months:
        demand_mult = min(demand_mult * 1.1, 2.0)

    weather_risk = WEATHER_RISK.get(current_month, "low")
    weather_notes = _get_weather_notes(location, current_month)

    return SeasonalContext(
        current_month=current_month,
        upcoming_festivals=list(set(upcoming))[:5],
        expected_demand_multiplier=round(demand_mult, 2),
        weather_risk_level=weather_risk,
        weather_notes=weather_notes,
    )


def _get_weather_notes(location: str, month: int) -> str:
    location_lower = location.lower()
    if month in [6, 7, 8, 9]:
        if any(x in location_lower for x in ["karnataka", "kerala", "goa", "mandya", "mysore"]):
            return "Southwest monsoon active. Expect reduced footfall on heavy rain days. Stock waterproofing and seasonal items."
        elif any(x in location_lower for x in ["maharashtra", "gujarat"]):
            return "Monsoon season. Supply chain may face disruptions. Maintain buffer stock."
        else:
            return "Monsoon season. Footfall may reduce on rainy days."
    elif month in [10, 11]:
        return "Post-monsoon. Festival season approaching — good time to increase inventory."
    elif month in [12, 1, 2]:
        return "Winter/cool season. Stable weather for operations."
    return "Normal weather conditions expected."


def compute_financial_snapshot(profile: BusinessProfile) -> Dict[str, float]:
    """Compute derived financial KPIs from the business profile."""
    monthly_profit = profile.monthly_revenue - profile.monthly_expenses
    profit_margin = (monthly_profit / profile.monthly_revenue * 100) if profile.monthly_revenue > 0 else 0

    # Monthly cash flow after loan EMI
    cash_flow = monthly_profit - profile.existing_loan_emi

    # Debt to revenue ratio
    annual_emi = profile.existing_loan_emi * 12
    annual_revenue = profile.monthly_revenue * 12
    debt_ratio = annual_emi / annual_revenue if annual_revenue > 0 else 0

    # Inventory turnover: assume COGS ≈ 70% of revenue
    cogs_monthly = profile.monthly_revenue * 0.70
    turnover_days = (profile.inventory_value / cogs_monthly * 30) if cogs_monthly > 0 else 30

    # Break-even (fixed costs only: rent + staff + EMI)
    avg_employee_cost = profile.employee_count * 10000  # ₹10k/employee avg
    fixed_costs = profile.rent_per_month + avg_employee_cost + profile.existing_loan_emi
    gross_margin_pct = 0.30  # assume 30% gross margin for grocery
    break_even = fixed_costs / gross_margin_pct if gross_margin_pct > 0 else 0

    # Liquidity score 0–1
    liquidity_score = min(1.0, max(0.0, cash_flow / (profile.monthly_expenses + 1) * 0.5 + 0.5))

    # Savings buffer
    monthly_savings = cash_flow
    runway = (profile.inventory_value * 0.3) / abs(cash_flow) if cash_flow < 0 else 99.0
    runway = min(runway, 99.0)

    return {
        "monthly_profit": round(monthly_profit, 2),
        "profit_margin_pct": round(profit_margin, 2),
        "monthly_cash_flow": round(cash_flow, 2),
        "debt_to_revenue_ratio": round(debt_ratio, 3),
        "inventory_turnover_days": round(turnover_days, 1),
        "break_even_revenue": round(break_even, 2),
        "current_liquidity_score": round(liquidity_score, 2),
        "monthly_savings": round(monthly_savings, 2),
        "runway_months": round(runway, 1),
    }


def run_data_agent(profile: BusinessProfile) -> Dict[str, Any]:
    """
    Main entry point for the Data Agent.
    Returns enriched data package ready for twin builder.
    """
    financials = compute_financial_snapshot(profile)
    seasonal = get_seasonal_context(
        location=profile.location,
        peak_months=profile.peak_season_months or [10, 11, 12],
    )

    # Simple stock risk estimate
    turnover_days = financials["inventory_turnover_days"]
    stock_risk_pct = max(0.0, min(1.0, (30 - turnover_days) / 30)) if turnover_days < 30 else 0.05

    return {
        "financials": financials,
        "seasonal_context": seasonal,
        "stock_risk_pct": round(stock_risk_pct, 2),
        "is_profitable": financials["monthly_profit"] > 0,
        "is_cash_flow_positive": financials["monthly_cash_flow"] > 0,
        "has_debt_stress": financials["debt_to_revenue_ratio"] > 0.3,
    }
