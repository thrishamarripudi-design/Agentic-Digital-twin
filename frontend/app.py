"""
Agentic Digital Twin — Streamlit Dashboard
Run with: streamlit run frontend/app.py
"""

import streamlit as st
import requests
import json
import time
from typing import Dict, Any, List

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Digital Twin — Grocery Store Advisor",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = "http://localhost:8000/api/v1"

# ─── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        border: 1px solid #e94560;
    }
    .main-header h1 { color: #e94560; font-size: 2rem; margin: 0; font-weight: 700; }
    .main-header p  { color: #a8b2d8; margin: 0.5rem 0 0; font-size: 1rem; }

    .twin-card {
        background: linear-gradient(135deg, #0f3460, #16213e);
        border: 1px solid #e94560;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .twin-card h3 { color: #e94560; margin: 0 0 1rem; font-size: 1.1rem; }

    .kpi-box {
        background: #1a1a2e;
        border: 1px solid #334;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        margin: 0.25rem;
    }
    .kpi-label { color: #7a8aa0; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; }
    .kpi-value { color: #e2e8f0; font-size: 1.5rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
    .kpi-positive { color: #48bb78; }
    .kpi-negative { color: #fc8181; }
    .kpi-neutral  { color: #90cdf4; }

    .scenario-card {
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 0.75rem;
        border-left: 4px solid;
    }
    .scenario-base     { background: #1a2332; border-color: #90cdf4; }
    .scenario-optimistic { background: #1a2e1a; border-color: #48bb78; }
    .scenario-pessimistic { background: #2e1a1a; border-color: #fc8181; }
    .scenario-label { font-weight: 700; font-size: 1rem; margin-bottom: 0.5rem; }

    .risk-bar-wrap { margin: 0.4rem 0; }
    .risk-label-row { display: flex; justify-content: space-between; margin-bottom: 3px; font-size: 0.82rem; color: #a8b2d8; }
    .risk-bar { height: 8px; border-radius: 4px; background: #1a1a2e; overflow: hidden; }
    .risk-fill { height: 100%; border-radius: 4px; }

    .recommendation-box {
        background: linear-gradient(135deg, #1a2e1a, #1e3a1e);
        border: 2px solid #48bb78;
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
    }
    .rec-primary { color: #68d391; font-size: 1.2rem; font-weight: 700; margin-bottom: 1rem; line-height: 1.5; }
    .rec-insight { color: #9ae6b4; font-style: italic; margin-bottom: 1rem; }
    .rec-explanation { color: #cbd5e0; font-size: 0.95rem; line-height: 1.6; }

    .step-item {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #7a8aa0;
        padding: 0.2rem 0;
        border-bottom: 1px solid #1a1a2e;
    }
    .step-item.done { color: #68d391; }
    .step-item.active { color: #fbb040; }

    .tag-green { background: #1c4532; color: #68d391; padding: 2px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }
    .tag-red   { background: #4a1a1a; color: #fc8181; padding: 2px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }
    .tag-blue  { background: #1a2a4a; color: #90cdf4; padding: 2px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }
    .tag-orange{ background: #3d2200; color: #f6ad55; padding: 2px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ─── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🏪 Agentic Digital Twin — Grocery Store Decision Advisor</h1>
    <p>AI-powered scenario simulation & risk analysis for small retail businesses in India</p>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar: Business Profile Form ──────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📋 Business Profile")
    st.caption("Enter your store details to build your digital twin")

    with st.expander("🏪 Basic Information", expanded=True):
        business_name = st.text_input("Store Name", value="Lakshmi Kirana & General Store")
        location = st.text_input("Location", value="Mandya, Karnataka")
        years = st.number_input("Years in Business", min_value=0, max_value=50, value=7)
        employees = st.number_input("Number of Employees", min_value=0, max_value=50, value=3)
        daily_customers = st.number_input("Avg Daily Customers", min_value=0, value=120)

    with st.expander("💰 Financials (Monthly, ₹)", expanded=True):
        monthly_revenue = st.number_input("Monthly Revenue", min_value=0, value=180000, step=5000)
        monthly_expenses = st.number_input("Monthly Expenses", min_value=0, value=140000, step=5000)
        inventory_value = st.number_input("Inventory Value", min_value=0, value=85000, step=5000)
        rent = st.number_input("Rent / Month", min_value=0, value=12000, step=1000)
        emi = st.number_input("Existing Loan EMI", min_value=0, value=5000, step=500)

    with st.expander("🌾 Seasonality", expanded=False):
        seasonal_notes = st.text_area(
            "Seasonal Demand Notes",
            value="Diwali and Ugadi are peak seasons. Monsoon months see 15-20% drop in footfall.",
            height=80,
        )
        peak_months = st.multiselect(
            "Peak Months",
            options=list(range(1, 13)),
            default=[10, 11, 3],
            format_func=lambda m: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][m-1],
        )

    st.markdown("---")
    load_demo = st.button("📦 Load Demo Data", use_container_width=True)


# ─── Main Content ─────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🔬 Analysis", "📊 Digital Twin", "📖 How It Works"])

# ─── Tab 1: Analysis ──────────────────────────────────────────────────────────
with tab1:
    col_q, col_btn = st.columns([4, 1])
    with col_q:
        question = st.text_input(
            "💬 Ask your what-if question",
            value="Should I increase inventory before festival season?",
            placeholder="e.g. What if I take a loan and open a second outlet?",
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        run_btn = st.button("▶ Run Analysis", type="primary", use_container_width=True)

    # Quick question chips
    st.caption("Quick questions:")
    qcols = st.columns(3)
    quick_qs = [
        "Should I increase inventory before festival season?",
        "What if rainfall is lower this season?",
        "What if I take a loan and open a second outlet?",
        "Should I hire one more employee?",
        "What if demand drops by 25%?",
        "Is it safe to expand to a second outlet?",
    ]
    for i, qcol in enumerate(qcols):
        for j in range(2):
            idx = i * 2 + j
            if idx < len(quick_qs):
                if qcol.button(f"💡 {quick_qs[idx][:40]}...", key=f"qbtn_{idx}", use_container_width=True):
                    question = quick_qs[idx]

    if run_btn or load_demo:
        # Build request payload
        payload = {
            "business_profile": {
                "business_name": business_name,
                "business_type": "grocery_store",
                "location": location,
                "monthly_revenue": float(monthly_revenue),
                "monthly_expenses": float(monthly_expenses),
                "inventory_value": float(inventory_value),
                "employee_count": int(employees),
                "rent_per_month": float(rent),
                "existing_loan_emi": float(emi),
                "seasonal_demand_notes": seasonal_notes,
                "years_in_business": int(years),
                "avg_daily_customers": int(daily_customers),
                "peak_season_months": peak_months or [10, 11, 3],
            },
            "user_question": question,
        }

        # ── Processing Steps Display ──────────────────────────────────────
        with st.status("🤖 Running multi-agent analysis pipeline...", expanded=True) as status:
            st.write("📡 Connecting to agent pipeline...")
            try:
                t0 = time.time()
                resp = requests.post(f"{API_BASE}/analyze", json=payload, timeout=90)
                resp.raise_for_status()
                data = resp.json()
                elapsed = time.time() - t0

                steps = data.get("processing_steps", [])
                for step in steps:
                    st.write(step)
                    time.sleep(0.05)

                status.update(label=f"✅ Analysis complete in {elapsed:.1f}s", state="complete")

            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend. Make sure FastAPI is running: `uvicorn backend.main:app --reload`")
                st.stop()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.stop()

        # ─── Planner Reasoning ────────────────────────────────────────────
        with st.expander("🧭 Planner Agent Reasoning", expanded=False):
            st.info(data.get("planner_reasoning", "N/A"))

        st.markdown("---")

        # ─── Digital Twin KPIs ────────────────────────────────────────────
        st.markdown("### 🏗️ Your Digital Twin")
        twin = data["twin_state"]
        fin = twin["financial_snapshot"]
        seasonal = twin["seasonal_context"]

        kpi_cols = st.columns(6)
        kpis = [
            ("Monthly Revenue", f"₹{twin['business_profile']['monthly_revenue']:,.0f}", "neutral"),
            ("Monthly Profit", f"₹{fin['monthly_profit']:,.0f}", "positive" if fin["monthly_profit"] > 0 else "negative"),
            ("Cash Flow", f"₹{fin['monthly_cash_flow']:,.0f}", "positive" if fin["monthly_cash_flow"] > 0 else "negative"),
            ("Inventory Turnover", f"{fin['inventory_turnover_days']:.0f} days", "neutral"),
            ("Debt Ratio", f"{fin['debt_to_revenue_ratio']:.1%}", "positive" if fin["debt_to_revenue_ratio"] < 0.2 else "negative"),
            ("Demand Multiplier", f"{seasonal['expected_demand_multiplier']}x", "positive" if seasonal["expected_demand_multiplier"] > 1.1 else "neutral"),
        ]
        for col, (label, value, color) in zip(kpi_cols, kpis):
            col.markdown(f"""
            <div class="kpi-box">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value kpi-{color}">{value}</div>
            </div>
            """, unsafe_allow_html=True)

        # Status badges
        badge_cols = st.columns(4)
        badges = [
            ("Profitable", twin["is_profitable"], "green", "red"),
            ("Cash Flow +ve", twin["is_cash_flow_positive"], "green", "red"),
            ("Debt Stress", twin["has_debt_stress"], "red", "green"),
            ("Weather Risk", seasonal["weather_risk_level"].upper(), None, None),
        ]
        for col, (label, val, yes_color, no_color) in zip(badge_cols, badges):
            if label == "Weather Risk":
                color = {"low": "green", "medium": "orange", "high": "red"}.get(seasonal["weather_risk_level"], "blue")
                col.markdown(f'<span class="tag-{color}">⛅ {label}: {val}</span>', unsafe_allow_html=True)
            else:
                color = yes_color if val else no_color
                icon = "✅" if (val and yes_color == "green") or (not val and yes_color == "red") else "❌"
                col.markdown(f'<span class="tag-{color}">{icon} {label}</span>', unsafe_allow_html=True)

        if seasonal.get("upcoming_festivals"):
            st.caption(f"🎉 Upcoming festivals: {', '.join(seasonal['upcoming_festivals'][:4])}")

        st.markdown("---")

        # ─── Scenario Comparison ──────────────────────────────────────────
        st.markdown("### 🔬 Scenario Simulations")
        scenarios = data["scenarios"]
        scen_cols = st.columns(3)
        scenario_styles = {
            "base_case": ("scenario-base", "📊", "#90cdf4"),
            "optimistic": ("scenario-optimistic", "📈", "#48bb78"),
            "pessimistic": ("scenario-pessimistic", "📉", "#fc8181"),
        }

        for col, scenario in zip(scen_cols, scenarios):
            stype = scenario["scenario_type"]
            css_class, icon, color = scenario_styles.get(stype, ("scenario-base", "📊", "#90cdf4"))
            with col:
                st.markdown(f"""
                <div class="scenario-card {css_class}">
                    <div class="scenario-label" style="color:{color}">{icon} {scenario['label']}</div>
                    <div style="color:#a8b2d8;font-size:0.82rem;margin-bottom:0.75rem">{scenario['description']}</div>
                    <table style="width:100%;font-size:0.85rem">
                        <tr><td style="color:#7a8aa0">Revenue</td><td style="color:#e2e8f0;text-align:right">₹{scenario['projected_revenue']:,.0f}</td></tr>
                        <tr><td style="color:#7a8aa0">Profit</td><td style="color:{'#48bb78' if scenario['projected_profit']>0 else '#fc8181'};text-align:right">₹{scenario['projected_profit']:,.0f}</td></tr>
                        <tr><td style="color:#7a8aa0">M1/M2/M3</td><td style="color:#e2e8f0;text-align:right;font-size:0.78rem">₹{scenario['month_1_profit']:,.0f} / ₹{scenario['month_2_profit']:,.0f} / ₹{scenario['month_3_profit']:,.0f}</td></tr>
                        <tr><td style="color:#7a8aa0">Risk Score</td><td style="color:{'#fc8181' if scenario['risk_score']>0.6 else '#f6ad55' if scenario['risk_score']>0.35 else '#48bb78'};text-align:right">{scenario['risk_score']:.0%}</td></tr>
                        <tr><td style="color:#7a8aa0">Opportunity</td><td style="color:#90cdf4;text-align:right">{scenario['opportunity_score']:.0%}</td></tr>
                        <tr><td style="color:#7a8aa0">Confidence</td><td style="color:#e2e8f0;text-align:right">{scenario['confidence_score']:.0%}</td></tr>
                    </table>
                </div>
                """, unsafe_allow_html=True)

                if scenario.get("key_drivers"):
                    st.caption("**Key drivers:** " + " · ".join(scenario["key_drivers"][:2]))
                if scenario.get("warnings"):
                    for w in scenario["warnings"][:1]:
                        st.warning(w, icon="⚠️")
                if scenario.get("opportunities"):
                    for o in scenario["opportunities"][:1]:
                        st.success(o, icon="💡")

        # ─── Revenue Chart ────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 📈 3-Month Profit Projection")

        import pandas as pd
        chart_data = {
            "Month": ["Month 1", "Month 2", "Month 3"],
        }
        for s in scenarios:
            chart_data[s["label"]] = [s["month_1_profit"], s["month_2_profit"], s["month_3_profit"]]

        df = pd.DataFrame(chart_data).set_index("Month")
        st.line_chart(df, height=280)

        # ─── Risk Analysis ────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### ⚠️ Risk Analysis")
        risk = data["risk_analysis"]

        risk_col1, risk_col2 = st.columns([1, 1])

        with risk_col1:
            risk_level_color = {
                "low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"
            }.get(risk["risk_level"], "⚪")
            st.markdown(f"**Overall Risk: {risk_level_color} {risk['risk_level'].upper()} ({risk['overall_risk_score']:.0%})**")

            risk_items = [
                ("Cash Shortage Risk", risk["cash_shortage_risk"]),
                ("Debt Stress Risk", risk["debt_stress_risk"]),
                ("Stockout Risk", risk["inventory_stockout_risk"]),
                ("Overstock Risk", risk["inventory_overstock_risk"]),
                ("Demand Shortfall", risk["demand_shortfall_risk"]),
                ("Weather Shock Risk", risk["weather_shock_risk"]),
            ]
            for label, score in risk_items:
                color = "#fc8181" if score > 0.6 else "#f6ad55" if score > 0.35 else "#48bb78"
                st.markdown(f"""
                <div class="risk-bar-wrap">
                    <div class="risk-label-row"><span>{label}</span><span style="color:{color}">{score:.0%}</span></div>
                    <div class="risk-bar"><div class="risk-fill" style="width:{score*100:.0f}%;background:{color}"></div></div>
                </div>
                """, unsafe_allow_html=True)

        with risk_col2:
            if risk.get("top_risks"):
                st.markdown("**🚨 Top Risks**")
                for r in risk["top_risks"]:
                    st.error(r, icon="⚠️")
            if risk.get("mitigations"):
                st.markdown("**🛡️ Suggested Mitigations**")
                for m in risk["mitigations"]:
                    st.info(m, icon="💡")

        # ─── Recommendation ───────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 💡 Final Recommendation")
        rec = data["recommendation"]

        st.markdown(f"""
        <div class="recommendation-box">
            <div class="rec-primary">🎯 {rec['primary_recommendation']}</div>
            <div class="rec-insight">💡 Key Insight: {rec['key_insight']}</div>
            <div class="rec-explanation">{rec['explanation']}</div>
        </div>
        """, unsafe_allow_html=True)

        rec_col1, rec_col2, rec_col3 = st.columns(3)
        with rec_col1:
            st.metric("Overall Risk", f"{rec['overall_risk_score']:.0%}")
        with rec_col2:
            st.metric("Confidence", f"{rec['confidence_score']:.0%}")
        with rec_col3:
            if rec.get("expected_roi_pct"):
                st.metric("Expected ROI", f"{rec['expected_roi_pct']:.1f}%")
            else:
                st.metric("Timeline", rec.get("recommended_timeline", "N/A"))

        act_col1, act_col2 = st.columns(2)
        with act_col1:
            if rec.get("action_plan"):
                st.markdown("**✅ Action Plan**")
                for i, action in enumerate(rec["action_plan"], 1):
                    st.markdown(f"{i}. {action}")
        with act_col2:
            if rec.get("do_not_do"):
                st.markdown("**🚫 Avoid These**")
                for item in rec["do_not_do"]:
                    st.markdown(f"- {item}")

        st.caption(f"⏰ Recommended timeline: **{rec.get('recommended_timeline', 'N/A')}**")

        # ─── Export ───────────────────────────────────────────────────────
        st.markdown("---")
        st.download_button(
            label="📥 Download Full Analysis (JSON)",
            data=json.dumps(data, indent=2, default=str),
            file_name=f"digital_twin_analysis_{business_name.replace(' ', '_')}.json",
            mime="application/json",
        )


# ─── Tab 2: Digital Twin Details ──────────────────────────────────────────────
with tab2:
    st.markdown("### 🏗️ Digital Twin Architecture")
    st.markdown("""
    The **Digital Twin** is a structured virtual model of your business updated in real-time.
    It captures the current state across 5 dimensions:
    """)

    dim_cols = st.columns(5)
    dims = [
        ("💰", "Financial", "Revenue, expenses, profit, cash flow, margins"),
        ("📦", "Inventory", "Stock value, turnover rate, reorder signals"),
        ("📅", "Seasonal", "Festival calendar, demand multipliers, weather"),
        ("⚠️", "Risk Profile", "Cash, debt, demand, weather risk scores"),
        ("🔮", "Forecast", "3-month demand and revenue projection"),
    ]
    for col, (icon, title, desc) in zip(dim_cols, dims):
        with col:
            st.markdown(f"**{icon} {title}**")
            st.caption(desc)

    st.markdown("---")
    st.markdown("### 🤖 Multi-Agent Pipeline")

    agents = [
        ("🧭", "Planner Agent", "Decomposes your question into analysis tasks. Identifies question type (inventory/loan/weather/expansion) and assigns work to downstream agents."),
        ("📊", "Data Agent", "Normalizes your business inputs. Enriches with Indian festival calendar, seasonal demand indices, and weather risk by location and month."),
        ("🏗️", "Twin Builder", "Constructs the DigitalTwinState — a structured, queryable virtual model of your business with computed KPIs and state flags."),
        ("📈", "Forecasting Agent", "Predicts 3-month demand using seasonal decomposition + Monte Carlo simulation for revenue uncertainty (P10–P90 range)."),
        ("🔬", "Simulation Agent", "Runs 3 scenarios (base/optimistic/pessimistic) for your specific question. Computes projected P&L, risk, and opportunity scores."),
        ("⚠️", "Risk Agent", "Scores 6 risk dimensions: cash shortage, debt stress, stockout, overstock, demand shortfall, weather shock."),
        ("💡", "Recommendation Agent", "Uses Claude/LLM to synthesize all outputs into an explainable recommendation with action plan and confidence score."),
    ]

    for icon, name, desc in agents:
        with st.expander(f"{icon} {name}"):
            st.write(desc)


# ─── Tab 3: How It Works ──────────────────────────────────────────────────────
with tab3:
    st.markdown("### 🚀 Why Is This Innovative?")

    points = [
        ("🤖 Not a Chatbot", "This system doesn't just answer questions — it simulates future consequences of decisions using structured business logic, forecasting, and scenario simulation."),
        ("🏗️ True Digital Twin", "The business is modeled as a structured state object (not just text). Every variable is computed, stored, and queryable — enabling simulation and comparison."),
        ("📊 Multi-Scenario Simulation", "Every question generates 3 scenarios with profit projections, risk scores, and opportunity scores — so you can compare outcomes before deciding."),
        ("🌾 Local Context", "Built specifically for Indian grocery stores: Indian festival calendar, Karnataka weather patterns, INR-based financials, monsoon risk modeling."),
        ("🔗 Multi-Agent Architecture", "7 specialized agents collaborate: Planner → Data → Twin → Forecast → Simulate → Risk → Recommend. Each agent has a single, clear responsibility."),
        ("📈 Monte Carlo Uncertainty", "Revenue projections use Monte Carlo simulation to show realistic P10–P90 uncertainty ranges — not just point estimates."),
        ("💡 Explainable Recommendations", "Every recommendation includes: what to do, why, what risks to avoid, and a confidence score — so the owner understands the reasoning."),
    ]

    for title, desc in points:
        with st.expander(title):
            st.write(desc)

    st.markdown("---")
    st.markdown("### 🆚 Vs Chatbot / RAG")

    comparison = {
        "Feature": ["Output type", "Business model", "Future simulation", "Risk scoring", "Scenario comparison", "Local context", "Explainability"],
        "Chatbot/RAG": ["Text answer", "None", "No", "No", "No", "Generic", "Limited"],
        "This System": ["Structured analysis", "Digital twin", "Yes (3 scenarios)", "6 dimensions", "Base/Opt/Pess", "India-specific", "Full with confidence"],
    }
    import pandas as pd
    st.dataframe(pd.DataFrame(comparison).set_index("Feature"), use_container_width=True)
