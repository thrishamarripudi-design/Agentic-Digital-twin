"""
Planner Agent
Decomposes the user's question into a structured task plan.
Falls back to rule-based classification if no LLM API key is configured.
"""

import os
import json
from typing import Dict, Any
from backend.core.llm_client import call_llm, safe_parse_json, is_llm_available

SYSTEM_PROMPT = """You are the Planner Agent for a digital twin system for small grocery stores in India.

Your job is to:
1. Understand the user's what-if question about their business.
2. Decompose it into 2-4 concrete analysis tasks.
3. Decide which agents are needed: forecasting, simulation, risk analysis.
4. Identify any external signals needed (weather, festivals, seasonality).

Always respond with valid JSON only. No explanation text outside the JSON.

Output format:
{
  "reasoning": "Brief explanation of what the user is asking",
  "tasks": [
    {
      "task_id": "T1",
      "agent": "forecasting|simulation|risk|twin_builder",
      "description": "What this task does",
      "inputs_needed": ["list", "of", "inputs"]
    }
  ],
  "scenarios_to_simulate": ["base_case", "optimistic", "pessimistic"],
  "external_signals_needed": ["weather", "festival_calendar", "inflation"],
  "key_question_type": "inventory|loan|expansion|weather|staffing|general",
  "urgency": "immediate|within_a_month|long_term"
}
"""


def _rule_based_plan(user_question: str) -> Dict[str, Any]:
    """
    Rule-based fallback planner — no LLM needed.
    Classifies question type by keyword matching.
    """
    q = user_question.lower()

    if any(w in q for w in ["loan", "borrow", "debt", "emi", "finance", "credit"]):
        qtype = "loan"
        reasoning = "User is asking about taking a loan or financing decision."
    elif any(w in q for w in ["expand", "branch", "outlet", "second", "new shop", "open another"]):
        qtype = "expansion"
        reasoning = "User is asking about expanding the business or opening a new outlet."
    elif any(w in q for w in ["rain", "weather", "monsoon", "drought", "flood", "rainfall"]):
        qtype = "weather"
        reasoning = "User is asking about weather or climate impact on business."
    elif any(w in q for w in ["hire", "staff", "employee", "worker", "labor", "labour"]):
        qtype = "staffing"
        reasoning = "User is asking about hiring or workforce decisions."
    elif any(w in q for w in ["inventory", "stock", "festival", "season", "diwali", "ugadi", "holi", "stocking"]):
        qtype = "inventory"
        reasoning = "User is asking about inventory or seasonal stocking decisions."
    else:
        qtype = "general"
        reasoning = "User is asking a general business decision question."

    return {
        "reasoning": reasoning,
        "tasks": [
            {"task_id": "T1", "agent": "twin_builder", "description": "Build digital twin state", "inputs_needed": ["business_profile"]},
            {"task_id": "T2", "agent": "forecasting", "description": "Forecast demand and revenue", "inputs_needed": ["twin_state"]},
            {"task_id": "T3", "agent": "simulation", "description": f"Run {qtype} scenarios", "inputs_needed": ["twin_state", "forecast"]},
            {"task_id": "T4", "agent": "risk", "description": "Assess risk dimensions", "inputs_needed": ["twin_state", "scenarios"]},
        ],
        "scenarios_to_simulate": ["base_case", "optimistic", "pessimistic"],
        "external_signals_needed": ["festival_calendar", "weather"],
        "key_question_type": qtype,
        "urgency": "within_a_month",
    }


async def run_planner_agent(
    user_question: str,
    business_context: str,
) -> Dict[str, Any]:
    """
    Takes the user's question and business summary,
    returns a structured task plan.
    Uses LLM if available, otherwise falls back to rule-based classification.
    """
    if not is_llm_available():
        return _rule_based_plan(user_question)

    user_message = f"""
Business Context:
{business_context}

User's Question:
{user_question}

Decompose this into analysis tasks.
"""
    try:
        raw = await call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message,
            max_tokens=800,
            temperature=0.2,
            json_mode=True,
        )
        plan = safe_parse_json(raw)
        return plan
    except Exception:
        return _rule_based_plan(user_question)