"""
Orchestrator — LangGraph-style sequential pipeline.
Wires all agents in order and tracks processing steps.

Flow:
  Input → Planner → Data Agent → Twin Builder → Forecasting
       → Simulation → Risk → Recommendation → Output
"""

import asyncio
from typing import List, Dict, Any, Tuple
from backend.models.business_state import (
    AnalysisRequest, AnalysisResponse, DigitalTwinState
)
from backend.agents.planner_agent import run_planner_agent
from backend.agents.data_agent import run_data_agent
from backend.agents.twin_builder_agent import build_digital_twin, twin_to_summary_text
from backend.agents.forecasting_agent import run_forecasting_agent
from backend.agents.simulation_agent import run_simulation_agent
from backend.agents.risk_agent import run_risk_agent
from backend.agents.recommendation_agent import run_recommendation_agent


async def run_analysis_pipeline(request: AnalysisRequest) -> AnalysisResponse:
    """
    Full multi-agent pipeline execution.
    Returns a complete AnalysisResponse with all agent outputs.
    """
    steps: List[str] = []

    # ── Step 1: Planner Agent ──────────────────────────────────────────────
    steps.append("🧭 Planner Agent: Decomposing your question into analysis tasks...")
    profile_summary = (
        f"{request.business_profile.business_name} in {request.business_profile.location}, "
        f"₹{request.business_profile.monthly_revenue:,.0f}/month revenue"
    )
    planner_plan = await run_planner_agent(
        user_question=request.user_question,
        business_context=profile_summary,
    )
    question_type = planner_plan.get("key_question_type", "inventory")
    steps.append(f"   → Question type: {question_type} | Tasks: {len(planner_plan.get('tasks', []))}")

    # ── Step 2: Data Agent ────────────────────────────────────────────────
    steps.append("📊 Data Agent: Normalizing business inputs and enriching with seasonal context...")
    data_package = run_data_agent(request.business_profile)
    seasonal = data_package["seasonal_context"]
    steps.append(
        f"   → Festivals ahead: {', '.join(seasonal.upcoming_festivals[:2]) or 'None'} | "
        f"Demand multiplier: {seasonal.expected_demand_multiplier}x | "
        f"Weather: {seasonal.weather_risk_level}"
    )

    # ── Step 3: Twin Builder Agent ────────────────────────────────────────
    steps.append("🏗️  Twin Builder Agent: Constructing digital twin state...")
    twin = build_digital_twin(request.business_profile, data_package)
    steps.append(
        f"   → Twin ID: {twin.twin_id} | "
        f"Profitable: {twin.is_profitable} | "
        f"Cash Flow Positive: {twin.is_cash_flow_positive} | "
        f"Completeness: {twin.data_completeness_pct:.0%}"
    )

    # ── Step 4: Forecasting Agent ─────────────────────────────────────────
    steps.append("📈 Forecasting Agent: Predicting 3-month demand and revenue trajectory...")
    forecast_data = run_forecasting_agent(twin)
    fc = forecast_data["base_forecast"]
    steps.append(
        f"   → Trend: {fc['trend_direction']} | "
        f"Peak month ahead: Month +{fc['peak_month_ahead']} | "
        f"Confidence: {fc['forecast_confidence']:.0%}"
    )

    # ── Step 5: Simulation Agent ──────────────────────────────────────────
    steps.append("🔬 Simulation Agent: Running base, optimistic, and pessimistic scenarios...")
    scenarios = run_simulation_agent(twin, question_type, forecast_data)
    for s in scenarios:
        steps.append(
            f"   [{s.label}] Profit: ₹{s.projected_profit:,.0f} | "
            f"Risk: {s.risk_score:.0%} | Opportunity: {s.opportunity_score:.0%}"
        )

    # ── Step 6: Risk Agent ────────────────────────────────────────────────
    steps.append("⚠️  Risk Agent: Evaluating risk dimensions...")
    risk_analysis = run_risk_agent(twin, scenarios, forecast_data)
    steps.append(
        f"   → Overall Risk: {risk_analysis.risk_level.upper()} ({risk_analysis.overall_risk_score:.0%}) | "
        f"Cash: {risk_analysis.cash_shortage_risk:.0%} | Debt: {risk_analysis.debt_stress_risk:.0%}"
    )

    # ── Step 7: Recommendation Agent ─────────────────────────────────────
    steps.append("💡 Recommendation Agent: Generating final recommendation with LLM reasoning...")
    recommendation = await run_recommendation_agent(
        twin=twin,
        scenarios=scenarios,
        risk_analysis=risk_analysis,
        user_question=request.user_question,
        forecast_data=forecast_data,
        planner_plan=planner_plan,
    )
    steps.append(f"   → Confidence: {recommendation.confidence_score:.0%} | Timeline: {recommendation.recommended_timeline}")
    steps.append("✅ Analysis complete!")

    return AnalysisResponse(
        twin_state=twin,
        scenarios=scenarios,
        risk_analysis=risk_analysis,
        recommendation=recommendation,
        planner_reasoning=planner_plan.get("reasoning", ""),
        processing_steps=steps,
    )
