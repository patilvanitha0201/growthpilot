# 🚀 GrowthPilot — AI Customer Health Agent

> Built by Vanitha Patil | PM + AI Builder

**Live Demo → [growthpilot.streamlit.app](https://growthpilot.streamlit.app)**

---

## The Problem

In B2B SaaS, churn rarely announces itself.

83% of CSMs manage 40–80 accounts using Excel and gut feel.
By the time a customer says "we're not renewing" — the decision
was made weeks ago. The signals were always there.
They just weren't connected.

---

## The Solution

GrowthPilot is a signal detection agent that:

- Ingests product telemetry across 4 dimensions
- Computes a dynamic Customer Health Score (0–100)
- Auto-classifies accounts → 🟢 Healthy / 🟡 At-Risk / 🔴 Critical
- Uses Claude AI to explain *why* an account is at risk
- Surfaces a prioritized **Top 5 accounts needing action today**

---

## The Real Behavior Change

**Without GrowthPilot** — a CSM starts Monday sorting 60 accounts
from memory, calls the ones they remember, and misses the quietly
disengaging account that sends a cancellation email on Thursday.

**With GrowthPilot** — Monday morning looks like this:

> "⚠️ Acme Corp dropped from 68 → 31. Logins down 70%,
> 3 high-severity tickets, renewal in 28 days. Call them first."

The CSM doesn't decide who to call. GrowthPilot already decided.

---

## Health Score Model

| Signal | What It Tracks | Weight |
|---|---|---|
| Engagement | Login frequency, days since last login | 35% |
| Adoption | Features used vs available | 25% |
| Sentiment | NPS score, ticket volume + severity | 25% |
| Lifecycle | Days to renewal, champion changes | 15% |

**Risk Tiers:**
- 🟢 70–100 → Healthy
- 🟡 40–69 → At-Risk
- 🔴 0–39 → Critical

---

## Tech Stack

| Layer | Tool |
|---|---|
| Data processing | Python + Pandas |
| Scoring engine | Python (transparent weighted math) |
| AI Insights | Claude API (claude-sonnet-4-6) |
| Dashboard | Streamlit |
| Hosting | Streamlit Cloud |

---

## Run Locally

```bash
git clone https://github.com/YOUR_USERNAME/growthpilot
cd growthpilot
pip install -r requirements.txt
```

Create a `.env` file:
```
ANTHROPIC_API_KEY=your_key_here
```

Run:
```bash
streamlit run app.py
```

---

## Project Structure

```
growthpilot/
├── app.py          # Streamlit UI — dashboard + detail view
├── scoring.py      # Health score engine (4 signals, weighted)
├── insights.py     # Claude API — risk reason + action
├── data/
│   └── accounts.csv
├── requirements.txt
└── .env            # Never committed
```

---

## Key Design Decisions

**Why weighted scoring, not ML**
V1 needs to be explainable to CSMs — not just accurate.
A CSM who can't understand why an account is flagged won't act on it.

**Why Claude for insights, not rules**
Rule-based systems can flag risk. They can't explain it in plain
English or tell a CSM exactly what to do next.

**Why Top 5, not a ranked list of 60**
The highest-leverage moment in a CSM's week is the first hour of
Monday. Five accounts with reasons is a plan. Sixty is noise.

---

## Projected Impact

A CSM team managing 50 accounts that catches 3 additional
at-risk accounts/month at $30K ACV →
**$1.08M ARR protected annually**

---

## Roadmap

| Version | What it unlocks |
|---|---|
| V1 ✅ | Signal detection + health scoring + AI digest |
| V2 | HubSpot API integration — real data, no CSV |
| V3 | Slack alert when account drops a tier |
| V4 | Auto-draft outreach email per at-risk account |
| V5 | Outcome tracking — did the intervention work? |
