"""
FastAPI Routes
Exposes the digital twin analysis pipeline as REST endpoints.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from backend.models.business_state import AnalysisRequest, AnalysisResponse
from backend.core.orchestrator import run_analysis_pipeline

router = APIRouter(prefix="/api/v1", tags=["Digital Twin"])


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "Agentic Digital Twin for Grocery Store"}


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_business(request: AnalysisRequest):
    """
    Main endpoint: takes a business profile + user question,
    runs the full multi-agent pipeline, returns complete analysis.
    """
    try:
        response = await run_analysis_pipeline(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis pipeline failed: {str(e)}")


@router.post("/twin/build")
async def build_twin_only(request: AnalysisRequest):
    """
    Quick endpoint: just build the digital twin state without full simulation.
    Useful for the profile preview step in the UI.
    """
    from backend.agents.data_agent import run_data_agent
    from backend.agents.twin_builder_agent import build_digital_twin, twin_to_summary_text
    try:
        data_package = run_data_agent(request.business_profile)
        twin = build_digital_twin(request.business_profile, data_package)
        return {
            "twin": twin.dict(),
            "summary": twin_to_summary_text(twin),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demo/sample-profile")
async def get_sample_profile():
    """Returns sample grocery store profile for demo purposes."""
    return {
        "business_name": "Lakshmi Kirana & General Store",
        "business_type": "grocery_store",
        "location": "Mandya, Karnataka",
        "monthly_revenue": 180000,
        "monthly_expenses": 140000,
        "inventory_value": 85000,
        "employee_count": 3,
        "rent_per_month": 12000,
        "existing_loan_emi": 5000,
        "seasonal_demand_notes": "Diwali and Ugadi are peak seasons. Monsoon months see a 15-20% drop in footfall.",
        "years_in_business": 7,
        "avg_daily_customers": 120,
        "peak_season_months": [10, 11, 3],
    }


@router.get("/demo/sample-questions")
async def get_sample_questions():
    """Returns sample what-if questions for the demo."""
    return {
        "questions": [
            "Should I increase inventory before festival season?",
            "What if rainfall is lower this season?",
            "What if I take a loan of ₹5 lakhs and open a second outlet?",
            "Should I hire one more employee before the festive rush?",
            "What happens to my business if demand drops by 25% next month?",
        ]
    }
