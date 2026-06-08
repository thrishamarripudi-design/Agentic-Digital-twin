# System Architecture — Agentic Digital Twin for Grocery Store Decision Making

## Overview

```
                        ┌─────────────────────────────────┐
                        │     Streamlit Frontend           │
                        │  Business Profile Form           │
                        │  What-If Question Input          │
                        │  Scenario Dashboard              │
                        │  Risk Indicators & Charts        │
                        └────────────┬────────────────────┘
                                     │ POST /api/v1/analyze
                        ┌────────────▼────────────────────┐
                        │       FastAPI Backend            │
                        │   /api/v1/analyze               │
                        └────────────┬────────────────────┘
                                     │
                        ┌────────────▼────────────────────┐
                        │      Orchestrator                │
                        │   (LangGraph-style pipeline)    │
                        └────────────┬────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
    ┌────▼─────┐              ┌──────▼──────┐            ┌──────▼──────┐
    │ Planner  │              │  Data Agent  │            │Twin Builder │
    │  Agent   │              │             │            │   Agent     │
    │          │              │ - Festival  │            │             │
    │ Decides: │              │   calendar  │            │ Builds      │
    │ question │              │ - Weather   │            │ DigitalTwin │
    │ type &   │              │   risk      │            │ State       │
    │ task plan│              │ - Financial │            │             │
    └────┬─────┘              │   KPIs      │            └──────┬──────┘
         │                    └─────────────┘                   │
         │                                                       │
    ┌────▼──────────────────────────────────────────────────────▼────┐
    │                    Forecasting Agent                            │
    │   - Seasonal demand decomposition (12-month index)             │
    │   - Monte Carlo revenue simulation (500 runs, P10–P90)         │
    │   - 3-month forward projections                                │
    └────────────────────────────────┬───────────────────────────────┘
                                     │
    ┌────────────────────────────────▼───────────────────────────────┐
    │                    Simulation Agent                             │
    │   Runs 3 scenarios per question type:                          │
    │                                                                │
    │   inventory  → base / stock-up optimistic / overstock pess    │
    │   loan       → no-loan / loan+growth / loan+slow-growth       │
    │   expansion  → single / second-outlet-success / struggles     │
    │   weather    → normal / good-monsoon / drought                │
    │   staffing   → current / hire+ROI / hire+low-ROI             │
    │                                                                │
    │   Each scenario outputs: projected P&L, 3-month curve,        │
    │   risk scores, opportunity score, drivers, warnings            │
    └────────────────────────────────┬───────────────────────────────┘
                                     │
    ┌────────────────────────────────▼───────────────────────────────┐
    │                      Risk Agent                                 │
    │   Scores 6 dimensions:                                         │
    │   1. Cash Shortage Risk    4. Inventory Overstock Risk         │
    │   2. Debt Stress Risk      5. Demand Shortfall Risk            │
    │   3. Stockout Risk         6. Weather Shock Risk               │
    │   → Produces weighted composite score + mitigations            │
    └────────────────────────────────┬───────────────────────────────┘
                                     │
    ┌────────────────────────────────▼───────────────────────────────┐
    │                 Recommendation Agent (LLM)                      │
    │   Input: twin summary + scenarios + risks + forecasts          │
    │   LLM: Claude / GPT-4o-mini / Ollama llama3                   │
    │   Output: primary recommendation, action plan, do-not-do,     │
    │           key insight, explanation, confidence score           │
    └────────────────────────────────────────────────────────────────┘
```

## Digital Twin State Schema

```
DigitalTwinState
├── twin_id                    (unique ID)
├── created_at
├── business_profile
│   ├── business_name
│   ├── business_type          (grocery_store | kirana_shop | small_retail)
│   ├── location
│   ├── monthly_revenue
│   ├── monthly_expenses
│   ├── inventory_value
│   ├── employee_count
│   ├── rent_per_month
│   ├── existing_loan_emi
│   ├── years_in_business
│   ├── avg_daily_customers
│   └── peak_season_months
├── financial_snapshot
│   ├── monthly_profit
│   ├── profit_margin_pct
│   ├── monthly_cash_flow
│   ├── debt_to_revenue_ratio
│   ├── inventory_turnover_days
│   ├── break_even_revenue
│   └── current_liquidity_score
├── seasonal_context
│   ├── current_month
│   ├── upcoming_festivals
│   ├── expected_demand_multiplier
│   ├── weather_risk_level
│   └── weather_notes
├── monthly_savings
├── runway_months
├── stock_risk_pct
├── is_profitable
├── is_cash_flow_positive
├── has_debt_stress
├── confidence_in_inputs
└── data_completeness_pct
```

## Simulation Scenarios

For each user question, 3 scenarios are generated:

| Scenario | Demand Change | Risk Focus | Opportunity Focus |
|----------|--------------|------------|-------------------|
| Base Case | 0% (seasonal) | Reference | Reference |
| Optimistic | +10–30% | Low-Medium | High |
| Pessimistic | -15–25% | High | Low |

## Risk Scoring Model

| Risk Dimension | Weight | Key Driver |
|---------------|--------|------------|
| Cash Shortage | 30% | Monthly cash flow vs expenses |
| Debt Stress | 20% | Debt-to-revenue ratio |
| Stockout | 20% | Inventory turnover vs demand mult |
| Overstock | 10% | Inventory turnover vs 30-day target |
| Demand Shortfall | 10% | Pessimistic scenario cash flow |
| Weather Shock | 10% | Month + location |

## Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Backend API | FastAPI + Python | Fast, async, auto-docs |
| Agent Orchestration | Sequential pipeline (LangGraph-compatible) | Simple, debuggable |
| LLM | Anthropic Claude / OpenAI / Ollama | Pluggable via env var |
| Forecasting | Seasonal decomposition + Monte Carlo | No training data needed |
| Database | SQLite (SQLAlchemy) | Zero-config for hackathon |
| Frontend | Streamlit | Rapid dashboard prototyping |

## Why Is This Different from a Chatbot/RAG?

| Capability | Chatbot/RAG | This System |
|-----------|------------|-------------|
| Output | Text answer | Structured analysis |
| Business model | None | Digital twin state |
| Future simulation | No | 3 scenarios per question |
| Risk scoring | No | 6 risk dimensions |
| Scenario comparison | No | Base / Optimistic / Pessimistic |
| Local India context | Generic | Festival calendar + weather |
| Explainability | Limited | Confidence + explanation + drivers |
| Monte Carlo uncertainty | No | P10–P90 revenue distribution |
