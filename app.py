import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from scoring import score_accounts
from insights import get_insight
from tools import load_accounts

st.set_page_config(page_title="GrowthPilot", page_icon="🚀", layout="wide")

# ── CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
.block-container { padding: 1.5rem 2rem !important; }
#MainMenu, footer, header { visibility: hidden; }

.gp-header {
    display: flex; justify-content: space-between; align-items: center;
    padding-bottom: 1.2rem; margin-bottom: 1.5rem;
    border-bottom: 1px solid #1e2638;
}
.gp-logo { font-size: 1.4rem; font-weight: 700; color: #fff; }
.gp-pill {
    font-size: 0.6rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.6px; padding: 2px 8px; border-radius: 20px;
    background: #0d2211; color: #4ade80; border: 1px solid #4ade8044;
    margin-left: 0.5rem;
}
.gp-sub { font-size: 0.8rem; color: #4b5563; }

.kpi-row { display: grid; grid-template-columns: repeat(4,1fr); gap: 0.8rem; margin-bottom: 1.5rem; }
.kpi {
    background: #111827; border: 1px solid #1e2638;
    border-radius: 12px; padding: 1rem 1.2rem;
}
.kpi-label { font-size: 0.68rem; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 0.4rem; }
.kpi-val { font-size: 1.8rem; font-weight: 700; font-family: 'DM Mono', monospace; color: #f9fafb; line-height: 1; }
.kpi-hint { font-size: 0.7rem; color: #4b5563; margin-top: 0.25rem; }
.red { color: #f87171 !important; }
.yellow { color: #fbbf24 !important; }
.green { color: #4ade80 !important; }

.sec-label {
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1px; color: #4b5563;
    border-bottom: 1px solid #1e2638; padding-bottom: 0.5rem; margin-bottom: 0.8rem;
}

.card {
    background: #111827; border: 1px solid #1e2638;
    border-radius: 12px; padding: 0.9rem 1.1rem; margin-bottom: 0.5rem;
}
.card-red    { border-left: 3px solid #f87171; }
.card-yellow { border-left: 3px solid #fbbf24; }
.card-green  { border-left: 3px solid #4ade80; }

.card-row1 { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem; }
.card-name { font-weight: 600; font-size: 0.92rem; color: #e2e8f0; }
.card-score { font-family: 'DM Mono', monospace; font-size: 1.05rem; font-weight: 700; }

.badge {
    font-size: 0.6rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.4px; padding: 1px 7px; border-radius: 20px; margin-left: 0.4rem;
}
.badge-red    { background: #2d1515; color: #f87171; border: 1px solid #f8717133; }
.badge-yellow { background: #2a1f0a; color: #fbbf24; border: 1px solid #fbbf2433; }
.badge-green  { background: #0a2010; color: #4ade80; border: 1px solid #4ade8033; }

.card-meta { display: flex; flex-wrap: wrap; gap: 0.8rem; font-size: 0.72rem; color: #6b7280; margin-bottom: 0.5rem; }

.bars { display: flex; align-items: center; gap: 0.25rem; }
.bar-label { font-size: 0.6rem; color: #4b5563; font-family: 'DM Mono', monospace; margin-right: 0.2rem; }
.bar { height: 4px; width: 26px; border-radius: 2px; }

.icard { border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 0.7rem; }
.icard-red    { background: #150d0d; border: 1px solid #f8717122; }
.icard-green  { background: #0a150c; border: 1px solid #4ade8022; }
.icard-blue   { background: #0a0f1a; border: 1px solid #3b82f622; }
.icard-label  { font-size: 0.63rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.9px; margin-bottom: 0.5rem; }
.icard-red .icard-label   { color: #f87171; }
.icard-green .icard-label { color: #4ade80; }
.icard-blue .icard-label  { color: #60a5fa; }
.icard-text { font-size: 0.87rem; color: #cbd5e1; line-height: 1.65; }

.detail-name { font-size: 1.6rem; font-weight: 700; color: #fff; }
.detail-meta { font-size: 0.78rem; color: #6b7280; margin-top: 0.2rem; }

[data-testid="stSidebar"] { background: #0a0d14 !important; border-right: 1px solid #1e2638 !important; }

.stButton > button {
    background: #111827 !important; border: 1px solid #1e2638 !important;
    color: #d1d5db !important; border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.8rem !important; font-weight: 500 !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: #1e3a8a !important; border-color: #3b82f6 !important; color: #fff !important;
}

.stTextInput input {
    background: #111827 !important; border: 1px solid #1e2638 !important;
    color: #e2e8f0 !important; border-radius: 8px !important;
    font-size: 0.85rem !important;
}
div[data-baseweb="select"] > div {
    background: #111827 !important; border-color: #1e2638 !important;
    color: #e2e8f0 !important;
}
hr { border-color: #1e2638 !important; margin: 1rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────
for k, v in [("df", None), ("selected_account", None), ("insight_cache", {})]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ───────────────────────────────────────────────
def load_default():
    try:
        df = pd.read_csv("data/accounts.csv")
        st.session_state.df = score_accounts(df)
        load_accounts(st.session_state.df)
    except FileNotFoundError:
        st.session_state.df = None

def color_class(tier):
    if "Critical" in str(tier): return "red",    "card-red",    "badge-red"
    if "At-Risk"  in str(tier): return "yellow",  "card-yellow", "badge-yellow"
    return "green", "card-green", "badge-green"

def sig_color(v):
    if v >= 70: return "#4ade80"
    if v >= 40: return "#fbbf24"
    return "#f87171"

def tier_short(tier):
    return str(tier).replace("🔴 ","").replace("🟡 ","").replace("🟢 ","")

def render_card(row, key_prefix):
    tc, cc, bc = color_class(row["tier"])
    e,a,s,l = sig_color(row["score_engagement"]), sig_color(row["score_adoption"]), sig_color(row["score_sentiment"]), sig_color(row["score_lifecycle"])
    champ = "⚠ Champion" if row["champion_changed"] == 1 else ""
    name = str(row["company_name"])
    industry = str(row["industry"])
    contract = int(row["contract_value"])
    renewal = int(row["days_to_renewal"])
    tickets = int(row["open_support_tickets"])
    nps = row["nps_score"]
    score = row["health_score"]
    ts = tier_short(row["tier"])

    st.markdown(f"""<div class="card {cc}">
  <div class="card-row1">
    <div><span class="card-name">{name}</span><span class="badge {bc}">{ts}</span></div>
    <span class="card-score {tc}">{score}</span>
  </div>
  <div class="card-meta">
    <span>🏭 {industry}</span><span>📅 {renewal}d</span>
    <span>💰 ${contract:,}</span><span>🎫 {tickets} tickets</span>
    <span>NPS {nps}</span>{f'<span style="color:#fbbf24">{champ}</span>' if champ else ''}
  </div>
  <div class="bars">
    <span class="bar-label">E·A·S·L</span>
    <div class="bar" style="background:{e}"></div>
    <div class="bar" style="background:{a}"></div>
    <div class="bar" style="background:{s}"></div>
    <div class="bar" style="background:{l}"></div>
  </div>
</div>""", unsafe_allow_html=True)

if st.session_state.df is None:
    load_default()

# ── SIDEBAR ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='font-size:1.1rem;font-weight:700;color:#fff;margin-bottom:0.2rem'>🚀 GrowthPilot</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.72rem;color:#4b5563;margin-bottom:1.2rem'>AI Agent · V2</div>", unsafe_allow_html=True)

    st.markdown("<div style='font-size:0.72rem;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.5rem'>Data</div>", unsafe_allow_html=True)
    uploaded = st.file_uploader("CSV", type=["csv"], label_visibility="collapsed")
    if uploaded:
        st.session_state.df = score_accounts(pd.read_csv(uploaded))
        st.session_state.insight_cache = {}
        load_accounts(st.session_state.df)
        st.success("✅ Loaded!")
    else:
        st.caption("Using default dataset")

    st.markdown("---")
    st.markdown("<div style='font-size:0.72rem;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.5rem'>Filter</div>", unsafe_allow_html=True)
    tier_filter = st.selectbox("Tier", ["All", "🔴 Critical", "🟡 At-Risk", "🟢 Healthy"], label_visibility="collapsed")

    if st.session_state.df is not None:
        df = st.session_state.df
        nc = len(df[df["tier"]=="🔴 Critical"])
        na = len(df[df["tier"]=="🟡 At-Risk"])
        nh = len(df[df["tier"]=="🟢 Healthy"])
        st.markdown("---")
        st.markdown("<div style='font-size:0.72rem;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.6rem'>Portfolio</div>", unsafe_allow_html=True)
        st.markdown(f"""<div style='font-size:0.82rem;line-height:2.1'>
<span style='color:#f87171'>🔴 Critical &nbsp;<b>{nc}</b></span><br>
<span style='color:#fbbf24'>🟡 At-Risk &nbsp;<b>{na}</b></span><br>
<span style='color:#4ade80'>🟢 Healthy &nbsp;<b>{nh}</b></span></div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# DETAIL VIEW
# ════════════════════════════════════════════════════════════
if st.session_state.selected_account is not None:
    df  = st.session_state.df
    acc = df[df["account_id"] == st.session_state.selected_account].iloc[0]
    ids = df["account_id"].tolist()
    idx = ids.index(st.session_state.selected_account)
    tc, cc, bc = color_class(acc["tier"])

    # Nav
    c1, c2, c3 = st.columns([1, 7, 1])
    with c1:
        if st.button("← Back"):
            st.session_state.selected_account = None
            st.rerun()
    with c2:
        name = str(acc["company_name"])
        industry = str(acc["industry"])
        contract = int(acc["contract_value"])
        account_id = str(acc["account_id"])
        ts = tier_short(acc["tier"])
        st.markdown(f"""<div style='margin-bottom:0.2rem;display:flex;align-items:center;gap:0.7rem'>
<span class='detail-name'>{name}</span>
<span class='badge {bc}'>{ts}</span></div>
<div class='detail-meta'>{industry} &nbsp;·&nbsp; ${contract:,} contract &nbsp;·&nbsp; {account_id}</div>""", unsafe_allow_html=True)
    with c3:
        if idx < len(ids) - 1:
            if st.button("Next →"):
                st.session_state.selected_account = ids[idx + 1]
                st.rerun()

    st.markdown("---")

    # KPI strip
    hs = acc["health_score"]
    dr = int(acc["days_to_renewal"])
    ot = int(acc["open_support_tickets"])
    nps = acc["nps_score"]
    champ = acc["champion_changed"] == 1

    hs_class  = "red" if hs < 40 else ("yellow" if hs < 70 else "green")
    dr_class  = "red" if dr < 30 else "green"
    ot_class  = "red" if ot > 3  else "green"
    nps_class = "red" if nps < 5 else "green"

    st.markdown(f"""<div class='kpi-row'>
<div class='kpi'><div class='kpi-label'>Health Score</div><div class='kpi-val {hs_class}'>{hs}</div><div class='kpi-hint'>out of 100</div></div>
<div class='kpi'><div class='kpi-label'>Days to Renewal</div><div class='kpi-val {dr_class}'>{dr}</div><div class='kpi-hint'>days remaining</div></div>
<div class='kpi'><div class='kpi-label'>Open Tickets</div><div class='kpi-val {ot_class}'>{ot}</div><div class='kpi-hint'>avg severity {acc["avg_ticket_severity"]}</div></div>
<div class='kpi'><div class='kpi-label'>NPS Score</div><div class='kpi-val {nps_class}'>{nps}</div><div class='kpi-hint'>out of 10</div></div>
</div>""", unsafe_allow_html=True)

    left, right = st.columns([1, 1])

    with left:
        st.markdown("<div class='sec-label'>Score Breakdown</div>", unsafe_allow_html=True)
        signals = {"Engagement (35%)": acc["score_engagement"], "Adoption (25%)": acc["score_adoption"],
                   "Sentiment (25%)": acc["score_sentiment"],   "Lifecycle (15%)": acc["score_lifecycle"]}
        fig = go.Figure()
        for label, val in signals.items():
            fig.add_trace(go.Bar(
                x=[val], y=[label], orientation='h',
                marker_color=sig_color(val), marker_line_width=0,
                showlegend=False, text=[f"{val:.0f}"], textposition='outside',
                textfont=dict(color='#6b7280', size=11, family='DM Mono')
            ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=190, margin=dict(l=0, r=45, t=5, b=5),
            xaxis=dict(range=[0,110], showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, tickfont=dict(color='#6b7280', size=11, family='DM Sans')),
            barmode='overlay'
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        st.markdown("<div class='sec-label'>Account Signals</div>", unsafe_allow_html=True)
        s1, s2 = st.columns(2)
        s1.metric("Days Since Login",  int(acc["days_since_last_login"]))
        s2.metric("Weekly Logins",     int(acc["weekly_logins_last_30d"]))
        s3, s4 = st.columns(2)
        s3.metric("Features Used", f"{int(acc['features_used'])} / {int(acc['total_features_available'])}")
        s4.metric("Champion", "Changed ⚠️" if champ else "Stable ✅")

    with right:
        st.markdown("<div class='sec-label'>AI Agent Insight</div>", unsafe_allow_html=True)
        acc_id = acc["account_id"]

        if acc_id not in st.session_state.insight_cache:
            with st.spinner("Agent reasoning..."):
                st.session_state.insight_cache[acc_id] = get_insight(acc)

        insight = st.session_state.insight_cache[acc_id]
        risk   = str(insight.get("risk_reason", "")).replace("<","&lt;").replace(">","&gt;")
        action = str(insight.get("recommended_action", "")).replace("<","&lt;").replace(">","&gt;")
        trail  = str(insight.get("reasoning_trail", "")).replace("<","&lt;").replace(">","&gt;")

        st.markdown(f"""<div class='icard icard-red'>
<div class='icard-label'>⚠ Risk Reason</div>
<div class='icard-text'>{risk}</div>
</div>
<div class='icard icard-green'>
<div class='icard-label'>✓ Recommended Action</div>
<div class='icard-text'>{action}</div>
</div>""", unsafe_allow_html=True)

        if trail:
            st.markdown(f"""<div class='icard icard-blue'>
<div class='icard-label'>◎ Agent Reasoning Trail</div>
<div class='icard-text'>{trail}</div>
</div>""", unsafe_allow_html=True)

        if st.button("🔄 Regenerate Insight"):
            st.session_state.insight_cache.pop(acc_id, None)
            st.rerun()

# ════════════════════════════════════════════════════════════
# DASHBOARD VIEW
# ════════════════════════════════════════════════════════════
else:
    df = st.session_state.df
    if df is None:
        st.warning("No data found. Add data/accounts.csv or upload a file.")
        st.stop()

    nc = len(df[df["tier"]=="🔴 Critical"])
    na = len(df[df["tier"]=="🟡 At-Risk"])
    nh = len(df[df["tier"]=="🟢 Healthy"])
    avg = df["health_score"].mean()

    st.markdown(f"""<div class='gp-header'>
<div><span class='gp-logo'>🚀 GrowthPilot</span><span class='gp-pill'>V2 · Agent</span></div>
<div class='gp-sub'>AI-powered customer health monitoring</div>
</div>
<div class='kpi-row'>
<div class='kpi'><div class='kpi-label'>Total Accounts</div><div class='kpi-val'>{len(df)}</div><div class='kpi-hint'>in portfolio</div></div>
<div class='kpi'><div class='kpi-label'>Critical</div><div class='kpi-val red'>{nc}</div><div class='kpi-hint'>need action today</div></div>
<div class='kpi'><div class='kpi-label'>At-Risk</div><div class='kpi-val yellow'>{na}</div><div class='kpi-hint'>monitor closely</div></div>
<div class='kpi'><div class='kpi-label'>Avg Health Score</div><div class='kpi-val'>{avg:.0f}</div><div class='kpi-hint'>portfolio average</div></div>
</div>""", unsafe_allow_html=True)

    left, right = st.columns([1, 1.7])

    with left:
        st.markdown("<div class='sec-label'>Portfolio Health</div>", unsafe_allow_html=True)
        fig = go.Figure(data=[go.Pie(
            labels=["Critical","At-Risk","Healthy"], values=[nc,na,nh],
            hole=0.62, marker_colors=["#f87171","#fbbf24","#4ade80"],
            textinfo="percent", textfont=dict(size=11, color="#fff", family="DM Mono"),
            hovertemplate="%{label}: %{value}<extra></extra>"
        )])
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            showlegend=True,
            legend=dict(font=dict(color="#6b7280", size=11), bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=0,r=0,t=5,b=5), height=230,
            annotations=[dict(text=f"<b>{len(df)}</b><br><span style='font-size:11px'>accounts</span>",
                              x=0.5, y=0.5, font_size=17, font_color="#fff", showarrow=False)]
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with right:
        st.markdown("<div class='sec-label'>⚠ Action Needed Today — Top 5</div>", unsafe_allow_html=True)
        for _, row in df.head(5).iterrows():
            c1, c2 = st.columns([5, 1])
            with c1:
                render_card(row, "top5")
            with c2:
                st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
                if st.button("View →", key=f"t5_{row['account_id']}"):
                    st.session_state.selected_account = row["account_id"]
                    st.rerun()

    st.markdown("---")
    st.markdown("<div class='sec-label'>All Accounts</div>", unsafe_allow_html=True)
    search = st.text_input("", placeholder="🔍  Search by company or industry...", label_visibility="collapsed")

    display_df = df.copy()
    if tier_filter != "All":
        display_df = display_df[display_df["tier"] == tier_filter]
    if search:
        display_df = display_df[
            display_df["company_name"].str.contains(search, case=False, na=False) |
            display_df["industry"].str.contains(search, case=False, na=False)
        ]

    for _, row in display_df.iterrows():
        c1, c2 = st.columns([5, 1])
        with c1:
            render_card(row, "all")
        with c2:
            st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
            if st.button("View →", key=f"all_{row['account_id']}"):
                st.session_state.selected_account = row["account_id"]
                st.rerun()