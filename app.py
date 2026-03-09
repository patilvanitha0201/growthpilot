import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from scoring import score_accounts
from insights import get_insight

# ─── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GrowthPilot",
    page_icon="🚀",
    layout="wide"
)

# ─── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .action-card {
        background: white;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 10px;
        border-left: 4px solid #ff4b4b;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .insight-box {
        background: #f0f7ff;
        padding: 16px;
        border-radius: 10px;
        margin-top: 10px;
    }
    .action-box {
        background: #f0fff4;
        padding: 16px;
        border-radius: 10px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ─── Load & score data ─────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "data", "accounts.csv")
    df = pd.read_csv(csv_path)
    return score_accounts(df)


# ─── Helper: donut chart ───────────────────────────────────────────────────────
def make_donut(critical, at_risk, healthy):
    fig = go.Figure(go.Pie(
        labels=["🔴 Critical", "🟡 At-Risk", "🟢 Healthy"],
        values=[critical, at_risk, healthy],
        hole=0.6,
        marker_colors=["#ff4b4b", "#ffa500", "#00c48c"],
        textinfo="label+value",
        hoverinfo="label+percent"
    ))
    fig.update_layout(
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20),
        height=260
    )
    return fig


# ─── Helper: score bar ─────────────────────────────────────────────────────────
def score_bar(label, value, color):
    st.markdown(f"**{label}**")
    st.progress(int(value) / 100)
    st.caption(f"{value}/100")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

df = load_data()

# ─── Session state: track selected account ────────────────────────────────────
if "selected_account" not in st.session_state:
    st.session_state.selected_account = None


# ══════════════════════════════════════════════════════════════════════════════
#  VIEW 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.selected_account is None:

    # Header
    st.markdown("## 🚀 GrowthPilot")
    st.markdown("##### AI-powered churn detection for B2B SaaS Customer Success teams")
    st.divider()

    # Summary counts
    n_critical = len(df[df["risk_tier"] == "🔴 Critical"])
    n_at_risk  = len(df[df["risk_tier"] == "🟡 At-Risk"])
    n_healthy  = len(df[df["risk_tier"] == "🟢 Healthy"])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card">
            <h1 style="color:#ff4b4b">{n_critical}</h1>
            <p>🔴 Critical</p></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card">
            <h1 style="color:#ffa500">{n_at_risk}</h1>
            <p>🟡 At-Risk</p></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card">
            <h1 style="color:#00c48c">{n_healthy}</h1>
            <p>🟢 Healthy</p></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card">
            <h1 style="color:#333">{len(df)}</h1>
            <p>Total Accounts</p></div>""", unsafe_allow_html=True)

    st.markdown("")

    # Two column layout: donut + top 5
    left, right = st.columns([1, 1.6])

    with left:
        st.markdown("### Account Health Overview")
        fig = make_donut(n_critical, n_at_risk, n_healthy)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("### ⚠️ Action Needed Today")
        st.caption("Top 5 accounts requiring immediate CSM attention")

        top5 = df.head(5)
        for _, row in top5.iterrows():
            tier_color = "#ff4b4b" if "Critical" in row["risk_tier"] else "#ffa500"
            if st.button(
                f"{row['risk_tier']}  {row['company_name']}  —  Score: {row['health_score']}  |  Renewal in {row['days_to_renewal']}d  |  ${row['contract_value']:,}",
                key=row["account_id"],
                use_container_width=True
            ):
                st.session_state.selected_account = row["account_id"]
                st.rerun()

    st.divider()

    # Full accounts table
    st.markdown("### All Accounts")

    tier_filter = st.selectbox(
        "Filter by tier",
        ["All", "🔴 Critical", "🟡 At-Risk", "🟢 Healthy"]
    )

    filtered = df if tier_filter == "All" else df[df["risk_tier"] == tier_filter]

    display_cols = [
        "company_name", "industry", "contract_value",
        "health_score", "risk_tier", "days_to_renewal",
        "weekly_logins_last_30d", "open_support_tickets", "nps_score"
    ]

    st.dataframe(
        filtered[display_cols].rename(columns={
            "company_name": "Company",
            "industry": "Industry",
            "contract_value": "Contract ($)",
            "health_score": "Health Score",
            "risk_tier": "Risk Tier",
            "days_to_renewal": "Days to Renewal",
            "weekly_logins_last_30d": "Weekly Logins",
            "open_support_tickets": "Open Tickets",
            "nps_score": "NPS"
        }),
        use_container_width=True,
        hide_index=True
    )


# ══════════════════════════════════════════════════════════════════════════════
#  VIEW 2 — ACCOUNT DETAIL
# ══════════════════════════════════════════════════════════════════════════════

else:
    account_id = st.session_state.selected_account
    row = df[df["account_id"] == account_id].iloc[0]

    # Back button
    if st.button("← Back to Dashboard"):
        st.session_state.selected_account = None
        st.rerun()

    st.divider()

    # Account header
    tier_emoji = "🔴" if "Critical" in row["risk_tier"] else ("🟡" if "At-Risk" in row["risk_tier"] else "🟢")
    st.markdown(f"## {tier_emoji} {row['company_name']}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Health Score", f"{row['health_score']}/100")
    col2.metric("Contract Value", f"${row['contract_value']:,}")
    col3.metric("Days to Renewal", row['days_to_renewal'])
    col4.metric("Risk Tier", row['risk_tier'])

    st.divider()

    # Score breakdown + AI insight side by side
    left, right = st.columns([1, 1.4])

    with left:
        st.markdown("### 📊 Score Breakdown")
        score_bar("Engagement", row["engagement_score"], "#4a90e2")
        score_bar("Adoption",   row["adoption_score"],   "#7b68ee")
        score_bar("Sentiment",  row["sentiment_score"],  "#f5a623")
        score_bar("Lifecycle",  row["lifecycle_score"],  "#50c878")

        st.markdown("")
        st.markdown("**Raw Signals**")
        signals = {
            "Days since last login": row["days_since_last_login"],
            "Weekly logins (30d)": row["weekly_logins_last_30d"],
            "Features used": f"{row['features_used']}/{row['total_features_available']}",
            "Open tickets": row["open_support_tickets"],
            "Avg ticket severity": f"{row['avg_ticket_severity']}/5",
            "NPS Score": f"{row['nps_score']}/10",
            "Champion changed": "Yes" if row["champion_changed"] == 1 else "No"
        }
        for k, v in signals.items():
            st.markdown(f"- **{k}:** {v}")

    with right:
        st.markdown("### 🤖 AI Insight")
        st.caption("Powered by Claude — analyzing all signals to explain risk and recommend action")

        with st.spinner("Generating insight..."):
            insight = get_insight(row.to_dict())

        st.markdown(f"""<div class="insight-box">
            <strong>⚠️ Why this account is at risk</strong><br><br>
            {insight['risk_reason']}
        </div>""", unsafe_allow_html=True)

        st.markdown("")

        st.markdown(f"""<div class="action-box">
            <strong>✅ Recommended action this week</strong><br><br>
            {insight['recommended_action']}
        </div>""", unsafe_allow_html=True)