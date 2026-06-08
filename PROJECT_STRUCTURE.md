# Agentic Digital Twin for Grocery Store Decision Making
## Project Structure

```
digital_twin/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── requirements.txt           # Python dependencies
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── planner_agent.py       # Decomposes user questions into tasks
│   │   ├── data_agent.py          # Normalizes business inputs
│   │   ├── twin_builder_agent.py  # Creates digital twin state
│   │   ├── forecasting_agent.py   # Predicts future demand/sales/cash flow
│   │   ├── simulation_agent.py    # Runs scenario simulations
│   │   ├── risk_agent.py          # Risk identification and scoring
│   │   └── recommendation_agent.py# Final recommendations
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py              # FastAPI route definitions
│   │   └── schemas.py             # Pydantic request/response models
│   ├── core/
│   │   ├── __init__.py
│   │   ├── orchestrator.py        # LangGraph workflow orchestrator
│   │   ├── llm_client.py          # LLM API client (Claude/OpenAI/Ollama)
│   │   └── database.py            # SQLite DB setup
│   └── models/
│       ├── __init__.py
│       ├── business_state.py      # Digital twin state schema
│       └── simulation_models.py   # Simulation data models
├── frontend/
│   └── app.py                     # Streamlit dashboard
├── data/
│   └── sample_grocery_store.json  # Demo data
├── docs/
│   └── architecture.md            # System architecture diagram
└── README.md
```
