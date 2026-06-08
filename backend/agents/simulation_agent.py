"""
Simulation Agent
Runs best-case, expected-case, and worst-case simulations
for the user's what-if question.
Produces 3 ScenarioResult objects for comparison.
"""

import uuid
import math
from typing import List, Dict, Any, Tuple
from backend.models.business_state import (
    DigitalTwinState, ScenarioInput, ScenarioResult, ScenarioType
)
from backend.agents.forecasting_agent import monte_carlo_revenue


def build_scenarios_for_question(
    twin: DigitalTwinState,
    question_type: str,
    forecast_data: Dict[str, Any],
) -> List[ScenarioInput]:
    """
    Given the question type (inventory, loan, expansion, weather, staffing),
    build 3 scenario inputs: base, optimistic, pessimistic.
    """
    p = twin.business_profile
    base_demand_mult = twin.seasonal_context.expected_demand_multiplier

    scenarios = []

    if question_type in ("inventory", "general"):
        # Scenario 1: Base — do nothing
        scenarios.append(ScenarioInput(
            scenario_type=ScenarioType.BASE_CASE,
            label="Current Trajectory",
            description="No changes — business as usual with seasonal demand",
            demand_change_pct=(base_demand_mult - 1) * 100,
            inventory_increase_pct=0,
        ))
        # Scenario 2: Optimistic — stock up for festival
        inv_increase_cost = p.inventory_value * 0.30
        scenarios.append(ScenarioInput(
            scenario_type=ScenarioType.OPTIMISTIC,
            label="Increase Inventory (Festival Ready)",
            description="Stock up 30% before festival season — capture full demand",
            demand_change_pct=(base_demand_mult - 1) * 100 + 10,
            inventory_increase_pct=30,
            inventory_increase_cost=inv_increase_cost,
        ))
        # Scenario 3: Pessimistic — demand disappoints
        scenarios.append(ScenarioInput(
            scenario_type=ScenarioType.PESSIMISTIC,
            label="Demand Disappoints",
            description="Stock up but festival demand is 20% below expectation — overstock risk",
            demand_change_pct=(base_demand_mult - 1) * 100 - 20,
            inventory_increase_pct=30,
            inventory_increase_cost=inv_increase_cost,
        ))

    elif question_type == "loan":
        loan_amount = p.monthly_revenue * 6  # ~6 months revenue
        loan_emi = loan_amount / 36           # 3-year term
        scenarios.append(ScenarioInput(
            scenario_type=ScenarioType.BASE_CASE,
            label="Current (No Loan)",
            description="Continue without taking a loan",
            demand_change_pct=0,
        ))
        scenarios.append(ScenarioInput(
            scenario_type=ScenarioType.OPTIMISTIC,
            label="Loan — Strong Business Growth",
            description="Take loan, revenue grows 25% from expansion",
            demand_change_pct=25,
            loan_amount=loan_amount,
            loan_emi=loan_emi,
            revenue_change_pct=25,
        ))
        scenarios.append(ScenarioInput(
            scenario_type=ScenarioType.PESSIMISTIC,
            label="Loan — Growth Slower Than Expected",
            description="Take loan but revenue grows only 5% — debt stress rises",
            demand_change_pct=5,
            loan_amount=loan_amount,
            loan_emi=loan_emi,
            revenue_change_pct=5,
        ))

    elif question_type == "expansion":
        setup_cost = p.monthly_revenue * 8
        new_rev = p.monthly_revenue * 0.6    # new branch starts at 60% of current
        new_exp = p.monthly_expenses * 0.75  # new branch expenses
        scenarios.append(ScenarioInput(
            scenario_type=ScenarioType.BASE_CASE,
            label="No Expansion",
            description="Continue with single outlet",
            demand_change_pct=0,
        ))
        scenarios.append(ScenarioInput(
            scenario_type=ScenarioType.OPTIMISTIC,
            label="Second Outlet — Success",
            description="Open second outlet, reaches 80% revenue in 3 months",
            demand_change_pct=15,
            new_branch_setup_cost=setup_cost,
            new_branch_monthly_revenue=new_rev * 1.3,
            new_branch_monthly_expenses=new_exp,
            loan_amount=setup_cost,
            loan_emi=setup_cost / 36,
        ))
        scenarios.append(ScenarioInput(
            scenario_type=ScenarioType.PESSIMISTIC,
            label="Second Outlet — Struggles",
            description="New outlet gets only 40% of expected revenue in first 3 months",
            demand_change_pct=5,
            new_branch_setup_cost=setup_cost,
            new_branch_monthly_revenue=new_rev * 0.4,
            new_branch_monthly_expenses=new_exp,
            loan_amount=setup_cost,
            loan_emi=setup_cost / 36,
        ))

    elif question_type == "weather":
        scenarios.append(ScenarioInput(
            scenario_type=ScenarioType.BASE_CASE,
            label="Normal Season",
            description="Normal rainfall, no weather disruption",
            demand_change_pct=0,
            weather_shock_factor=1.0,
        ))
        scenarios.append(ScenarioInput(
            scenario_type=ScenarioType.OPTIMISTIC,
            label="Good Monsoon — Strong Harvest",
            description="Good rainfall boosts rural purchasing power by 15%",
            demand_change_pct=15,
            weather_shock_factor=1.15,
        ))
        scenarios.append(ScenarioInput(
            scenario_type=ScenarioType.PESSIMISTIC,
            label="Drought / Poor Monsoon",
            description="Below-average rainfall — rural demand drops 25%, supply chain disrupted",
            demand_change_pct=-25,
            weather_shock_factor=0.75,
            supply_disruption_factor=0.85,
        ))

    elif question_type == "staffing":
        worker_cost = 10000  # ₹10k/month
        productivity_gain = p.monthly_revenue * 0.08  # 8% revenue boost per worker
        scenarios.append(ScenarioInput(
            scenario_type=ScenarioType.BASE_CASE,
            label="Current Staff",
            description="No additional hiring",
        ))
        scenarios.append(ScenarioInput(
            scenario_type=ScenarioType.OPTIMISTIC,
            label="Hire 1 Worker — High ROI",
            description="New worker enables faster service; revenue increases 10%",
            additional_employees=1,
            employee_cost_per_month=worker_cost,
            revenue_change_pct=10,
        ))
        scenarios.append(ScenarioInput(
            scenario_type=ScenarioType.PESSIMISTIC,
            label="Hire 1 Worker — Low ROI",
            description="New worker adds cost but revenue increases only 3%",
            additional_employees=1,
            employee_cost_per_month=worker_cost,
            revenue_change_pct=3,
        ))

    else:
        # Fallback: generic 3 scenarios
        return build_scenarios_for_question(twin, "inventory", forecast_data)

    return scenarios


def simulate_scenario(
    twin: DigitalTwinState,
    scenario: ScenarioInput,
    mc_distribution: Dict[str, float],
) -> ScenarioResult:
    """
    Runs a single scenario simulation and returns detailed results.
    """
    p = twin.business_profile
    f = twin.financial_snapshot

    # Compute projected revenue
    demand_factor = 1 + scenario.demand_change_pct / 100
    revenue_factor = 1 + scenario.revenue_change_pct / 100
    base_revenue = p.monthly_revenue * demand_factor * revenue_factor * scenario.weather_shock_factor * scenario.supply_disruption_factor

    # Add branch revenue if applicable
    total_revenue = base_revenue + scenario.new_branch_monthly_revenue

    # Compute projected expenses
    extra_labor = scenario.additional_employees * scenario.employee_cost_per_month
    extra_inventory_cost = scenario.inventory_increase_cost  # one-time hit in month 1
    branch_expenses = scenario.new_branch_monthly_expenses
    total_emi = p.existing_loan_emi + scenario.loan_emi

    total_expenses = (p.monthly_expenses + extra_labor + branch_expenses) * demand_factor * 0.8 + p.monthly_expenses * 0.2

    # Month-by-month 3-month projection
    inv_ramp = [1.0, 0.5, 0.0]  # inventory stocking cost fades after month 1
    branch_ramp = [0.4, 0.7, 1.0]  # new branch revenue ramps up

    monthly_profits = []
    for m in range(3):
        m_revenue = total_revenue * (0.9 + m * 0.05)  # slight ramp
        if scenario.new_branch_monthly_revenue > 0:
            m_revenue = (base_revenue + scenario.new_branch_monthly_revenue * branch_ramp[m])
        m_extra_inv = extra_inventory_cost * inv_ramp[m]
        m_expenses = total_expenses + m_extra_inv
        m_profit = m_revenue - m_expenses - total_emi
        monthly_profits.append(round(m_profit, 2))

    projected_profit = sum(monthly_profits) / 3
    projected_cash_flow = projected_profit  # already net of EMI

    # Risk computations
    new_debt_ratio = (total_emi * 12) / (total_revenue * 12 + 1)
    inventory_after = p.inventory_value * (1 + scenario.inventory_increase_pct / 100)
    new_turnover = inventory_after / (total_revenue * 0.7 / 30 + 1)

    stockout_prob = _compute_stockout_probability(new_turnover, demand_factor)
    cash_shortage_prob = _compute_cash_shortage_probability(projected_cash_flow, p.monthly_expenses)
    debt_stress_prob = _compute_debt_stress_probability(new_debt_ratio)

    risk_score = (stockout_prob * 0.3 + cash_shortage_prob * 0.4 + debt_stress_prob * 0.3)
    risk_score = round(min(1.0, risk_score), 2)

    # Opportunity score
    profit_gain = projected_profit - f.monthly_profit
    opportunity_score = round(min(1.0, max(0.0, profit_gain / (p.monthly_revenue * 0.2 + 1) * 0.5 + 0.5)), 2)

    # Confidence score — higher when inputs are complete and scenario is moderate
    confidence_score = round(twin.confidence_in_inputs * (1 - abs(scenario.demand_change_pct) / 100 * 0.3), 2)

    # Key drivers and warnings
    drivers, warnings, opportunities = _generate_narrative(
        scenario, twin, projected_profit, f.monthly_profit,
        stockout_prob, cash_shortage_prob, debt_stress_prob
    )

    return ScenarioResult(
        scenario_type=scenario.scenario_type,
        label=scenario.label,
        description=scenario.description,
        projected_revenue=round(total_revenue, 2),
        projected_expenses=round(total_expenses + total_emi, 2),
        projected_profit=round(projected_profit, 2),
        projected_cash_flow=round(projected_cash_flow, 2),
        month_1_profit=monthly_profits[0],
        month_2_profit=monthly_profits[1],
        month_3_profit=monthly_profits[2],
        stockout_probability=round(stockout_prob, 2),
        cash_shortage_probability=round(cash_shortage_prob, 2),
        debt_stress_probability=round(debt_stress_prob, 2),
        risk_score=risk_score,
        opportunity_score=opportunity_score,
        confidence_score=confidence_score,
        key_drivers=drivers,
        warnings=warnings,
        opportunities=opportunities,
    )


def _compute_stockout_probability(turnover_days: float, demand_factor: float) -> float:
    if turnover_days < 7:
        return 0.85
    elif turnover_days < 14:
        return 0.5 * demand_factor
    elif turnover_days < 21:
        return 0.25 * demand_factor
    else:
        return max(0.05, 0.15 / demand_factor)


def _compute_cash_shortage_probability(cash_flow: float, monthly_expenses: float) -> float:
    if cash_flow < 0:
        return min(0.95, 0.6 + abs(cash_flow) / (monthly_expenses + 1) * 0.3)
    elif cash_flow < monthly_expenses * 0.1:
        return 0.35
    elif cash_flow < monthly_expenses * 0.2:
        return 0.15
    else:
        return 0.05


def _compute_debt_stress_probability(debt_ratio: float) -> float:
    if debt_ratio > 0.5:
        return 0.85
    elif debt_ratio > 0.35:
        return 0.55
    elif debt_ratio > 0.20:
        return 0.25
    else:
        return 0.05


def _generate_narrative(
    scenario: ScenarioInput,
    twin: DigitalTwinState,
    projected_profit: float,
    current_profit: float,
    stockout_prob: float,
    cash_prob: float,
    debt_prob: float,
) -> Tuple[List[str], List[str], List[str]]:
    drivers = []
    warnings = []
    opps = []

    profit_delta = projected_profit - current_profit
    profit_delta_pct = (profit_delta / (abs(current_profit) + 1)) * 100

    if scenario.demand_change_pct > 0:
        drivers.append(f"Demand increase of {scenario.demand_change_pct:.0f}% boosts revenue")
    elif scenario.demand_change_pct < 0:
        drivers.append(f"Demand drop of {abs(scenario.demand_change_pct):.0f}% reduces revenue")

    if scenario.weather_shock_factor < 1.0:
        drivers.append(f"Weather shock reduces effective demand by {(1 - scenario.weather_shock_factor)*100:.0f}%")

    if scenario.inventory_increase_pct > 0:
        drivers.append(f"Inventory stocked up by {scenario.inventory_increase_pct}% (₹{scenario.inventory_increase_cost:,.0f} investment)")

    if scenario.loan_emi > 0:
        drivers.append(f"New loan EMI of ₹{scenario.loan_emi:,.0f}/month adds fixed cost burden")

    if scenario.new_branch_monthly_revenue > 0:
        drivers.append(f"New branch contributes ₹{scenario.new_branch_monthly_revenue:,.0f}/month revenue (ramping up)")

    # Warnings
    if stockout_prob > 0.5:
        warnings.append("High stockout risk — replenishment delays could hurt sales during peak demand")
    if cash_prob > 0.4:
        warnings.append("Cash flow tight — maintain at least 1 month expenses as buffer")
    if debt_prob > 0.5:
        warnings.append("Debt stress high — new loan may strain repayment capacity")
    if scenario.demand_change_pct < -15:
        warnings.append("Severe demand drop — consider reducing perishable inventory to cut wastage")

    # Opportunities
    if profit_delta > 0:
        opps.append(f"Profit could improve by ₹{profit_delta:,.0f}/month (+{profit_delta_pct:.0f}%)")
    if twin.seasonal_context.upcoming_festivals:
        opps.append(f"Upcoming festivals ({', '.join(twin.seasonal_context.upcoming_festivals[:2])}) create natural demand boost")
    if scenario.inventory_increase_pct > 0 and scenario.demand_change_pct > 0:
        opps.append("Stocking up aligns with expected demand — good timing for festival season")

    return drivers[:3], warnings[:3], opps[:3]


def run_simulation_agent(
    twin: DigitalTwinState,
    question_type: str,
    forecast_data: Dict[str, Any],
) -> List[ScenarioResult]:
    """Main entry point for simulation agent."""
    scenarios = build_scenarios_for_question(twin, question_type, forecast_data)
    mc = forecast_data.get("monte_carlo_distribution", {})

    results = [simulate_scenario(twin, s, mc) for s in scenarios]
    return results
