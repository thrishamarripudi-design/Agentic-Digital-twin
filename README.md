# 🏪 Agentic Digital Twin for Grocery Store Decision Making

> **A multi-agent AI system that builds a living virtual model of a small grocery store and simulates the future consequences of business decisions.**

---

## 🚀 What Is This?

This is **not a chatbot**. It is not a RAG assistant.

It is a **multi-agent AI system** that:
1. Builds a **digital twin** — a structured virtual model of your grocery store
2. **Forecasts** near-future demand using seasonal decomposition + Monte Carlo simulation
3. **Simulates 3 scenarios** (base, optimistic, pessimistic) for any what-if question
4. **Scores 6 risk dimensions** across cash, debt, inventory, demand, and weather
5. **Generates an explainable recommendation** with confidence score and action plan

---

## 🎯 Target Users

- **Kirana / grocery shop owners** in rural and semi-urban India
- **Small retail business owners** — Mandya, Mysore, tier-2/3 cities
- **Local manufacturers** and seasonal farmers (extensible)

---

## 🏗️ Architecture

```
User Question + Business Profile
         │
    ┌────▼──────────────────────────────────────────┐
    │  7-Agent Pipeline (Orchestrator)               │
    │                                                │
    │  1. Planner Agent    → Task decomposition     │
    │  2. Data Agent       → Seasonal enrichment    │
    │  3. Twin Builder     → DigitalTwinState       │
    │  4. Forecasting      → 3-month projections    │
    │  5. Simulation       → 3 scenarios            │
    │  6. Risk Agent       → 6-dimension scoring    │
    │  7. Recommendation   → LLM final output       │
    └───────────────────────────────────────────────┘
         │
    Complete Analysis Response
    (twin + scenarios + risks + recommendation)
```

See [`docs/architecture.md`](docs/architecture.md) for detailed diagrams.

---

## 📁 Project Structure

```
digital_twin/
├── backend/
│   ├── main.py                        # FastAPI entry point
│   ├── requirements.txt
│   ├── agents/
│   │   ├── planner_agent.py           # LLM: decomposes question → task plan
│   │   ├── data_agent.py              # Rule-based: seasonal + financial enrichment
│   │   ├── twin_builder_agent.py      # Builds DigitalTwinState
│   │   ├── forecasting_agent.py       # Seasonal decomposition + Monte Carlo
│   │   ├── simulation_agent.py        # 3-scenario simulation engine
│   │   ├── risk_agent.py              # 6-dimension risk scoring
│   │   └── recommendation_agent.py    # LLM: final recommendation report
│   ├── api/
│   │   └── routes.py                  # FastAPI endpoints
│   ├── core/
│   │   ├── orchestrator.py            # Agent pipeline coordinator
│   │   └── llm_client.py             # Pluggable LLM client
│   └── models/
│       └── business_state.py          # All Pydantic schemas
├── frontend/
│   └── app.py                         # Streamlit dashboard
├── data/
│   └── sample_grocery_store.json      # Demo business profile
├── docs/
│   └── architecture.md
├── .env.example
└── README.md
```

---

## ⚡ Quick Start

### 1. Clone & Install

```bash
git clone <repo-url>
cd digital_twin

# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependency
pip install streamlit
```

### 2. Configure LLM

```bash
cp .env.example .env
# Edit .env — set LLM_PROVIDER and your API key
```

**Option A: Anthropic Claude (recommended)**
```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

**Option B: OpenAI**
```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

**Option C: Ollama (free, local)**
```bash
ollama pull llama3
# In .env:
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

### 3. Start the Backend

```bash
uvicorn backend.main:app --reload --port 8000
```

Visit: http://localhost:8000/docs for interactive API docs.

### 4. Start the Frontend

```bash
streamlit run frontend/app.py
```

Visit: http://localhost:8501

---

## 🎮 Demo Scenario

**Business:** Lakshmi Kirana & General Store, Mandya, Karnataka
- Monthly Revenue: ₹1,80,000
- Monthly Expenses: ₹1,40,000
- Inventory Value: ₹85,000
- Employees: 3 | Rent: ₹12,000/month | EMI: ₹5,000/month

**Ask:** *"Should I increase inventory before festival season?"*

**System outputs:**
| | Base Case | Optimistic | Pessimistic |
|--|-----------|------------|-------------|
| Revenue | ₹1,98,000 | ₹2,34,000 | ₹1,62,000 |
| Profit | ₹47,000 | ₹76,000 | ₹18,000 |
| Risk Score | 22% | 18% | 61% |
| Recommendation | Stock up 20–25% on non-perishables 2 weeks before Diwali |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/analyze` | Full analysis pipeline |
| `POST` | `/api/v1/twin/build` | Build twin only (no simulation) |
| `GET` | `/api/v1/demo/sample-profile` | Demo business profile |
| `GET` | `/api/v1/demo/sample-questions` | Sample what-if questions |

### Sample Request

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "business_profile": {
      "business_name": "Lakshmi Kirana Store",
      "business_type": "grocery_store",
      "location": "Mandya, Karnataka",
      "monthly_revenue": 180000,
      "monthly_expenses": 140000,
      "inventory_value": 85000,
      "employee_count": 3,
      "rent_per_month": 12000,
      "existing_loan_emi": 5000,
      "years_in_business": 7,
      "peak_season_months": [10, 11, 3]
    },
    "user_question": "Should I increase inventory before festival season?"
  }'
```

---

## 🧠 Agent Details

### 1. Planner Agent (LLM)
Classifies the user's question into: `inventory | loan | expansion | weather | staffing | general`
and produces a structured task plan for downstream agents.

### 2. Data Agent (Rule-based)
- Computes financial KPIs: profit margin, cash flow, debt ratio, inventory turnover, break-even
- Enriches with Indian festival calendar (12-month lookup)
- Adds Karnataka/South India weather risk by month
- Outputs seasonal demand multiplier (range: 0.82x to 1.55x)

### 3. Twin Builder Agent
Assembles the `DigitalTwinState` — a structured, queryable virtual model with 20+ fields including financial snapshot, seasonal context, risk flags, and confidence scores.

### 4. Forecasting Agent
- **Seasonal decomposition**: 12-month demand index calibrated to India's retail cycle
- **Monte Carlo simulation**: 500 runs with log-normal noise (±12% volatility)
- **Output**: P10/P25/P50/P75/P90 revenue distribution + 3-month projections

### 5. Simulation Agent
Generates 3 scenarios per question type:

| Question Type | Scenarios |
|--------------|-----------|
| Inventory | Base / Stock-up for festival / Overstock risk |
| Loan | No loan / Loan + strong growth / Loan + slow growth |
| Expansion | Single outlet / Second outlet success / Second outlet struggles |
| Weather | Normal / Good monsoon / Drought/poor monsoon |
| Staffing | Current / Hire + high ROI / Hire + low ROI |

Each scenario outputs: projected P&L, 3-month profit curve, stockout/cash/debt probabilities, risk score, opportunity score.

### 6. Risk Agent
Scores 6 dimensions with calibrated thresholds and produces weighted composite risk score:

| Dimension | Weight | Method |
|-----------|--------|--------|
| Cash Shortage | 30% | Cash flow vs expense ratio |
| Debt Stress | 20% | Annual EMI / Annual revenue |
| Stockout | 20% | Inventory turnover × demand multiplier |
| Overstock | 10% | Turnover days vs 30-day target |
| Demand Shortfall | 10% | Pessimistic scenario cash flow |
| Weather Shock | 10% | Month + location lookup |

### 7. Recommendation Agent (LLM)
Sends the complete context — twin summary, all 3 scenarios, risk analysis, and forecasts — to the LLM and extracts a structured recommendation with: primary recommendation, action plan, do-not-do list, key insight, explanation, timeline, and expected ROI.

---

## 💡 Why Is This Innovative?

| Capability | Generic Chatbot | RAG System | **This System** |
|-----------|----------------|-----------|-----------------|
| Output | Text answer | Retrieved text | Structured analysis |
| Business model | None | None | Digital twin state |
| Future simulation | No | No | 3 scenarios per question |
| Risk scoring | No | No | 6 weighted dimensions |
| Scenario comparison | No | No | Base/Optimistic/Pessimistic |
| Monte Carlo uncertainty | No | No | P10–P90 revenue range |
| India-specific context | Generic | Generic | Festival calendar + weather |
| Confidence score | No | No | Per recommendation |
| Explainable reasoning | No | Limited | Full driver explanation |

---

## ✅ Hackathon Feasibility

- **No training required** — uses pre-trained LLM + rule-based forecasting
- **No external APIs needed** — festival calendar and weather risk are built-in lookup tables
- **Runs locally** — Ollama support means zero LLM cost
- **Single domain** — focused on grocery stores only, making it deep rather than generic
- **Demo-ready** — sample data + quick questions pre-loaded in UI
- **~2 hours to set up** from scratch on any laptop

---

## 📊 Evaluation Checklist

- [x] ≥3 scenarios per user query
- [x] Comparison between current state and simulated outcomes
- [x] Explainable reasoning (drivers, warnings, opportunities)
- [x] Risk score (6 dimensions + composite)
- [x] Confidence score (per scenario + final recommendation)
- [x] Final action recommendation with timeline

---

## 🧩 Extensions (Post-Hackathon)

- Add Prophet/XGBoost forecasting when historical CSV data is available
- Extend to crop planning for farmers (same architecture, different domain schema)
- Add voice input for rural users (Whisper API)
- Multi-language support (Kannada, Hindi)
- Historical analysis from uploaded sales CSV

---

## 📄 License

MIT License — built for the Agentic AI Hackathon.
