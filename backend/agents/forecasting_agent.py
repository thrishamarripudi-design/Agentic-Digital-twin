"""
Forecasting Agent
Predicts near-future demand, revenue, and cash flow.
Uses rule-based + statistical forecasting (no Prophet/XGBoost required for demo).
Falls back gracefully when historical data is limited.
"""

import math
import random
from typing import Dict, List, Any
from backend.models.business_state import DigitalTwinState


# Month-over-month demand index relative to Jan baseline
MONTHLY_DEMAND_INDEX = [
    1.0,   # Jan
    0.92,  # Feb
    1.05,  # Mar (Holi)
    1.02,  # Apr
    0.88,  # May
    0.82,  # Jun (monsoon dip)
    0.84,  # Jul
    0.90,  # Aug
    1.10,  # Sep (Ganesh)
    1.35,  # Oct (Navratri/Dussehra)
    1.55,  # Nov (Diwali peak)
    1.20,  # Dec
]


def forecast_next_3_months(twin: DigitalTwinState) -> Dict[str, Any]:
    """
    Lightweight seasonal decomposition forecast.
    Returns 3-month projections for revenue, demand, and cash flow.
    """
    current_month = twin.seasonal_context.current_month
    base_revenue = twin.business_profile.monthly_revenue
    base_expenses = twin.business_profile.monthly_expenses
    emi = twin.business_profile.existing_loan_emi

    forecasts = []
    for delta in range(1, 4):
        future_month = ((current_month - 1 + delta) % 12)
        demand_idx = MONTHLY_DEMAND_INDEX[future_month]

        # Add slight noise ±5% to simulate uncertainty
        noise = 1 + (random.uniform(-0.05, 0.05))
        projected_revenue = base_revenue * demand_idx * noise

        # Expenses scale slightly with revenue (variable costs)
        projected_expenses = base_expenses * (1 + (demand_idx - 1) * 0.4)
        projected_profit = projected_revenue - projected_expenses
        projected_cash_flow = projected_profit - emi

        forecasts.append({
            "month_offset": delta,
            "month_index": future_month + 1,
            "demand_multiplier": round(demand_idx, 2),
            "projected_revenue": round(projected_revenue, 2),
            "projected_expenses": round(projected_expenses, 2),
            "projected_profit": round(projected_profit, 2),
            "projected_cash_flow": round(projected_cash_flow, 2),
        })

    # Trend direction
    avg_growth = sum(f["projected_revenue"] for f in forecasts) / (3 * base_revenue)
    trend = "upward" if avg_growth > 1.05 else "downward" if avg_growth < 0.95 else "stable"

    return {
        "monthly_forecasts": forecasts,
        "trend_direction": trend,
        "avg_demand_multiplier": round(sum(MONTHLY_DEMAND_INDEX[(current_month + d) % 12] for d in range(3)) / 3, 2),
        "peak_month_ahead": max(range(3), key=lambda d: MONTHLY_DEMAND_INDEX[(current_month + d) % 12]) + 1,
        "forecast_confidence": 0.72,
        "method": "seasonal_decomposition_rule_based",
    }


def monte_carlo_revenue(
    base_revenue: float,
    demand_multiplier: float,
    n_simulations: int = 500,
    volatility: float = 0.12,
) -> Dict[str, float]:
    """
    Simple Monte Carlo simulation for revenue uncertainty.
    Returns percentile distribution.
    """
    simulations = []
    for _ in range(n_simulations):
        # Log-normal noise to simulate real-world randomness
        noise = math.exp(random.gauss(0, volatility))
        simulated = base_revenue * demand_multiplier * noise
        simulations.append(simulated)

    simulations.sort()
    n = len(simulations)

    return {
        "p10": round(simulations[int(n * 0.10)], 2),   # pessimistic
        "p25": round(simulations[int(n * 0.25)], 2),
        "p50": round(simulations[int(n * 0.50)], 2),   # expected
        "p75": round(simulations[int(n * 0.75)], 2),
        "p90": round(simulations[int(n * 0.90)], 2),   # optimistic
        "mean": round(sum(simulations) / n, 2),
        "std_dev": round(
            math.sqrt(sum((x - sum(simulations)/n)**2 for x in simulations) / n), 2
        ),
    }


def run_forecasting_agent(twin: DigitalTwinState) -> Dict[str, Any]:
    """Main entry point for forecasting."""
    base_forecast = forecast_next_3_months(twin)
    demand_mult = twin.seasonal_context.expected_demand_multiplier

    monte_carlo = monte_carlo_revenue(
        base_revenue=twin.business_profile.monthly_revenue,
        demand_multiplier=demand_mult,
        volatility=0.12,
    )

    return {
        "base_forecast": base_forecast,
        "monte_carlo_distribution": monte_carlo,
        "current_demand_multiplier": demand_mult,
        "forecast_summary": (
            f"Revenue is trending {base_forecast['trend_direction']} over the next 3 months. "
            f"Peak demand expected in month {base_forecast['peak_month_ahead']}. "
            f"Expected revenue range: ₹{monte_carlo['p25']:,.0f} – ₹{monte_carlo['p75']:,.0f}."
        ),
    }
