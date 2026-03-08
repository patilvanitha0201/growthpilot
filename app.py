import streamlit as st
import pandas as pd
import plotly.express as px
from scoring import score_accounts
from insights import get_insight

# ── Page Config ───────────────────────────────────────────
st.set_page_config(
    page_title="GrowthPilot",
    page_icon="🚀",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────
st.markdown("""
<style>
    .big-metric { font-size: 2rem; font-weight: 700; }
    .card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        border-left: 5px solid #dee2e6;
    }
    .card-critical { border-left-color: #dc3545; }
    .card-atrisk   { border-left-color: #ffc107; }
    .card-healthy  { border-left-color: #28a745; }
    .score-bar-label { font-size: 0.85rem; color: #6c757d; }
</style>
""", unsafe_allow_html=True)


# ── Session State ─────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = None
if "selected_account" not in st.session_state:
    st.session_state.selected_account = None
if "insight_cache" not in st.session_state:
    st.session_state.insight_cache = {}


# ── Helper ────────────────────────────────────────────────
def load_default():
    try:
        df = pd.read_csv("data/accounts.csv")
        st.session_state.df = score_accounts(df)
    except FileNotFoundError:
        st.session_state.df = None


def tier_color(tier):
    if "Critical" in tier: return "#dc3545"
    if "At-Risk"  in tier: return "#ffc107"
    return "#28a745"


def tier_css(tier):
    if "Critical" in tier: return "card-critical"
    if "At-Risk"  in tier: return "card-atrisk"
    return "card-healthy"


# ── Auto-load on first run ────────────────────────────────
if st.session_state.df is None:
    load_default()


# ════════════════════════════════════════════════════════════
# DETAIL VIEW
# ════════════════════════════════════════════════════════════
if st.session_state.selected_account is not None:
    df  = st.session_state.df
    acc = df[df["account_id"] == st.session_state.selected_account].iloc[0]

    # Back button
    if st.button("← Back to Dashboard"):
        st.session_state.selected_account = None
        st.rerun()

    st.markdown(f"## {acc['company_name']}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Health Score", f"{acc['health_score']} / 100")
    col2.metric("Risk Tier",    acc['tier'])
    col3.metric("Days to Renewal", acc['days_to_renewal'])

    st.markdown("---")

    # ── Score Breakdown ───────────────────────────────────
    st.markdown("### 📊 Score Breakdown")
    breakdown = {
        "Signal"  : ["Engagement (35%)", "Adoption (25%)", "Sentiment (25%)", "Lifecycle (15%)"],
        "Score"   : [
            acc["score_engagement"],
            acc["score_adoption"],
            acc["score_sentiment"],
            acc["score_lifecycle"]
        ]
    }
    fig = px.bar(
        breakdown,
        x="Score", y="Signal",
        orientation="h",
        range_x=[0, 100],
        color="Score",
        color_continuous_scale=["#dc3545", "#ffc107", "#28a745"],
        text="Score"
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        height=220,
        margin=dict(l=0, r=40, t=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ── Raw Signals ───────────────────────────────────────
    st.markdown("### 📋 Account Signals")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Days Since Login",   acc["days_since_last_login"])
    c2.metric("Weekly Logins",      acc["weekly_logins_last_30d"])
    c3.metric("Features Used",      f"{acc['features_used']} / {acc['total_features_available']}")
    c4.metric("Open Tickets",       acc["open_support_tickets"])

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Ticket Severity",    acc["avg_ticket_severity"])
    c6.metric("NPS Score",          f"{acc['nps_score']} / 10")
    c7.metric("Days to Renewal",    acc["days_to_renewal"])
    c8.metric("Champion Changed",   "Yes ⚠️" if acc["champion_changed"] == 1 else "No ✅")

    st.markdown("---")

    # ── AI Insight ────────────────────────────────────────
    st.markdown("### 🤖 AI Insight")
    acc_id = acc["account_id"]

    if acc_id not in st.session_state.insight_cache:
        with st.spinner("Generating insight..."):
            st.session_state.insight_cache[acc_id] = get_insight(acc)

    insight = st.session_state.insight_cache[acc_id]

    st.error(f"**⚠️ Risk Reason**\n\n{insight['risk_reason']}")
    st.success(f"**✅ Recommended Action**\n\n{insight['recommended_action']}")


# ════════════════════════════════════════════════════════════
# DASHBOARD VIEW
# ════════════════════════════════════════════════════════════
else:
    # ── Header ────────────────────────────────────────────
    st.markdown("# 🚀 GrowthPilot")
    st.markdown("##### AI-powered customer health monitoring for B2B SaaS CSMs")
    st.markdown("---")

    # ── File Upload ───────────────────────────────────────
    with st.sidebar:
        st.markdown("### 📂 Upload Data")
        uploaded = st.file_uploader("Upload accounts CSV", type=["csv"])
        if uploaded:
            df_raw = pd.read_csv(uploaded)
            st.session_state.df = score_accounts(df_raw)
            st.session_state.insight_cache = {}
            st.success("Data loaded!")
        else:
            st.info("Using default dataset")

        st.markdown("---")
        st.markdown("### 🔍 Filter")
        tier_filter = st.selectbox(
            "Show accounts",
            ["All", "🔴 Critical", "🟡 At-Risk", "🟢 Healthy"]
        )

    df = st.session_state.df

    if df is None:
        st.warning("No data found. Please upload a CSV or add accounts.csv to the data/ folder.")
        st.stop()

    # ── Summary Metrics ───────────────────────────────────
    n_critical = len(df[df["tier"] == "🔴 Critical"])
    n_atrisk   = len(df[df["tier"] == "🟡 At-Risk"])
    n_healthy  = len(df[df["tier"] == "🟢 Healthy"])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Accounts",  len(df))
    m2.metric("🔴 Critical",     n_critical, delta=f"-{n_critical} need action", delta_color="inverse")
    m3.metric("🟡 At-Risk",      n_atrisk)
    m4.metric("🟢 Healthy",      n_healthy)

    st.markdown("---")

    # ── Donut Chart + Top 5 Panel ─────────────────────────
    left, right = st.columns([1, 2])

    with left:
        st.markdown("### Account Health Overview")
        donut_data = pd.DataFrame({
            "Tier"  : ["🔴 Critical", "🟡 At-Risk", "🟢 Healthy"],
            "Count" : [n_critical, n_atrisk, n_healthy]
        })
        fig_donut = px.pie(
            donut_data, values="Count", names="Tier",
            hole=0.55,
            color="Tier",
            color_discrete_map={
                "🔴 Critical" : "#dc3545",
                "🟡 At-Risk"  : "#ffc107",
                "🟢 Healthy"  : "#28a745"
            }
        )
        fig_donut.update_traces(textposition="outside", textinfo="percent+label")
        fig_donut.update_layout(
            showlegend=False,
            margin=dict(l=0, r=0, t=20, b=0),
            height=280
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with right:
        st.markdown("### ⚠️ Action Needed Today — Top 5")
        top5 = df.head(5)

        for _, row in top5.iterrows():
            css = tier_css(row["tier"])
            st.markdown(f"""
            <div class="card {css}">
                <strong>{row['company_name']}</strong>
                &nbsp;&nbsp;{row['tier']}
                &nbsp;&nbsp;Score: <strong>{row['health_score']}</strong>
                &nbsp;&nbsp;|&nbsp;&nbsp;Renewal in <strong>{row['days_to_renewal']} days</strong>
                &nbsp;&nbsp;|&nbsp;&nbsp;Contract: <strong>${row['contract_value']:,}</strong>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"View {row['company_name']} →", key=f"top5_{row['account_id']}"):
                st.session_state.selected_account = row["account_id"]
                st.rerun()

    st.markdown("---")

    # ── Full Accounts Table ───────────────────────────────
    st.markdown("### 📋 All Accounts")

    # Apply filter
    display_df = df.copy()
    if tier_filter != "All":
        display_df = display_df[display_df["tier"] == tier_filter]

    # Show table columns only
    table_cols = [
        "company_name", "industry", "contract_value",
        "health_score", "tier", "days_to_renewal",
        "days_since_last_login", "open_support_tickets", "nps_score"
    ]
    st.dataframe(
        display_df[table_cols].rename(columns={
            "company_name"         : "Company",
            "industry"             : "Industry",
            "contract_value"       : "Contract ($)",
            "health_score"         : "Score",
            "tier"                 : "Tier",
            "days_to_renewal"      : "Days to Renewal",
            "days_since_last_login": "Days Since Login",
            "open_support_tickets" : "Open Tickets",
            "nps_score"            : "NPS"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # ── Click to View Account ─────────────────────────────
    st.markdown("### 🔎 View Account Detail")
    selected_name = st.selectbox(
        "Select an account to view full detail + AI insight",
        options=display_df["company_name"].tolist()
    )

    if st.button("View Account →"):
        acc_id = df[df["company_name"] == selected_name]["account_id"].values[0]
        st.session_state.selected_account = acc_id
        st.rerun()