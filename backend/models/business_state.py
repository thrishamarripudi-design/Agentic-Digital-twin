"""
Digital Twin State Schema for Grocery Store / Small Retail Business
This is the core data model that represents a living snapshot of a business.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class BusinessType(str, Enum):
    GROCERY_STORE = "grocery_store"
    KIRANA_SHOP = "kirana_shop"
    SMALL_RETAIL = "small_retail"


class SeasonalityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BusinessProfile(BaseModel):
    """User-provided business profile input"""
    business_name: str
    business_type: BusinessType = BusinessType.GROCERY_STORE
    location: str
    monthly_revenue: float = Field(..., description="Average monthly revenue in INR")
    monthly_expenses: float = Field(..., description="Average monthly expenses in INR")
    inventory_value: float = Field(..., description="Current inventory value in INR")
    employee_count: int = Field(..., ge=0)
    rent_per_month: float = Field(default=0.0)
    existing_loan_emi: float = Field(default=0.0, description="Existing loan EMI in INR")
    seasonal_demand_notes: Optional[str] = None
    years_in_business: int = Field(default=1, ge=0)
    avg_daily_customers: Optional[int] = None
    peak_season_months: Optional[List[int]] = Field(
        default=[10, 11, 12], description="Months with high demand (1=Jan)"
    )


class FinancialSnapshot(BaseModel):
    """Computed financial state of the business"""
    monthly_profit: float
    profit_margin_pct: float
    monthly_cash_flow: float
    debt_to_revenue_ratio: float
    inventory_turnover_days: float  # days to sell current inventory
    break_even_revenue: float
    current_liquidity_score: float  # 0–1


class SeasonalContext(BaseModel):
    """Current and upcoming seasonal factors"""
    current_month: int
    upcoming_festivals: List[str]
    expected_demand_multiplier: float  # 1.0 = normal, 1.3 = 30% above normal
    weather_risk_level: str  # low / medium / high
    weather_notes: Optional[str] = None


class DigitalTwinState(BaseModel):
    """
    The core Digital Twin — a structured virtual model of the business.
    Combines user inputs, computed financials, and contextual signals.
    """
    twin_id: str
    created_at: datetime
    business_profile: BusinessProfile
    financial_snapshot: FinancialSnapshot
    seasonal_context: SeasonalContext

    # Derived KPIs
    monthly_savings: float  # profit - loan EMI
    runway_months: float    # how long they can survive on current savings
    stock_risk_pct: float   # % chance of stockout given current inventory

    # State flags
    is_profitable: bool
    is_cash_flow_positive: bool
    has_debt_stress: bool

    # Meta
    confidence_in_inputs: float = Field(default=0.8, ge=0.0, le=1.0)
    data_completeness_pct: float = Field(default=1.0, ge=0.0, le=1.0)


class ScenarioType(str, Enum):
    BASE_CASE = "base_case"
    OPTIMISTIC = "optimistic"
    PESSIMISTIC = "pessimistic"


class ScenarioInput(BaseModel):
    """What-if parameters for a single scenario"""
    scenario_type: ScenarioType
    label: str
    description: str

    # Demand & revenue levers
    demand_change_pct: float = 0.0        # e.g. +30 for festival boost
    revenue_change_pct: float = 0.0

    # Inventory levers
    inventory_increase_pct: float = 0.0
    inventory_increase_cost: float = 0.0

    # Operational levers
    additional_employees: int = 0
    employee_cost_per_month: float = 8000.0

    # Loan / expansion
    loan_amount: float = 0.0
    loan_emi: float = 0.0
    new_branch_setup_cost: float = 0.0
    new_branch_monthly_revenue: float = 0.0
    new_branch_monthly_expenses: float = 0.0

    # Risk factors
    weather_shock_factor: float = 1.0    # 1.0 = no effect, 0.8 = 20% demand drop
    supply_disruption_factor: float = 1.0


class ScenarioResult(BaseModel):
    """Outcome of simulating a single scenario"""
    scenario_type: ScenarioType
    label: str
    description: str

    # Projected monthly P&L
    projected_revenue: float
    projected_expenses: float
    projected_profit: float
    projected_cash_flow: float

    # 3-month projection
    month_1_profit: float
    month_2_profit: float
    month_3_profit: float

    # Risk indicators
    stockout_probability: float   # 0–1
    cash_shortage_probability: float
    debt_stress_probability: float

    # Composite scores
    risk_score: float             # 0–1 (1 = highest risk)
    opportunity_score: float      # 0–1 (1 = highest opportunity)
    confidence_score: float       # 0–1

    # Explanation
    key_drivers: List[str]
    warnings: List[str]
    opportunities: List[str]


class RiskAnalysis(BaseModel):
    """Structured risk report for the business"""
    overall_risk_score: float        # 0–1
    risk_level: str                  # low / medium / high / critical

    inventory_overstock_risk: float
    inventory_stockout_risk: float
    cash_shortage_risk: float
    debt_stress_risk: float
    demand_shortfall_risk: float
    weather_shock_risk: float

    top_risks: List[str]
    mitigations: List[str]


class RecommendationReport(BaseModel):
    """Final output from the Recommendation Agent"""
    recommendation_id: str
    generated_at: datetime

    # Answer to the original question
    primary_recommendation: str
    action_plan: List[str]
    do_not_do: List[str]

    # Scores
    overall_risk_score: float
    confidence_score: float
    expected_roi_pct: Optional[float] = None

    # Supporting context
    risk_analysis: RiskAnalysis
    scenario_comparison: List[ScenarioResult]
    key_insight: str
    explanation: str

    # Timeline
    recommended_timeline: str  # e.g. "Act within 2 weeks before festival"


class AnalysisRequest(BaseModel):
    """Full request object from the frontend"""
    business_profile: BusinessProfile
    user_question: str
    additional_context: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Full response object returned to the frontend"""
    twin_state: DigitalTwinState
    scenarios: List[ScenarioResult]
    risk_analysis: RiskAnalysis
    recommendation: RecommendationReport
    planner_reasoning: str
    processing_steps: List[str]
