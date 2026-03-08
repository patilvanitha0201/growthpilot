import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def get_insight(row: dict) -> dict:
    """
    Takes a single account row (as a dict).
    Returns a dict with two keys:
      - risk_reason: why is this account at risk (2 sentences)
      - recommended_action: what the CSM should do this week (1 sentence)
    """

    champion_text = "Yes — champion changed recently" if row["champion_changed"] == 1 else "No"

    prompt = f"""You are GrowthPilot, an AI assistant for B2B SaaS Customer Success teams.
Your job is to help CSMs understand why an account is at risk and what to do about it.

Account Details:
- Company: {row['company_name']}
- Industry: {row['industry']}
- Contract Value: ${row['contract_value']:,}
- Health Score: {row['health_score']}/100 ({row['risk_tier']})
- Days since last login: {row['days_since_last_login']}
- Weekly logins (last 30 days): {row['weekly_logins_last_30d']}
- Features adopted: {row['features_used']} out of {row['total_features_available']} available
- Open support tickets: {row['open_support_tickets']} (avg severity: {row['avg_ticket_severity']}/5)
- NPS Score: {row['nps_score']}/10
- Days to renewal: {row['days_to_renewal']}
- Champion changed recently: {champion_text}

Respond in exactly this format and nothing else:

RISK REASON: [2 sentences maximum explaining why this account is at risk. Be specific, reference the actual numbers above.]

RECOMMENDED ACTION: [Exactly 1 sentence. Tell the CSM the single most important thing to do THIS WEEK. Be direct and specific.]"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text.strip()

    # Parse the two sections out of Claude's response
    risk_reason = ""
    recommended_action = ""

    for line in response_text.split("\n"):
        line = line.strip()
        if line.startswith("RISK REASON:"):
            risk_reason = line.replace("RISK REASON:", "").strip()
        elif line.startswith("RECOMMENDED ACTION:"):
            recommended_action = line.replace("RECOMMENDED ACTION:", "").strip()

    return {
        "risk_reason": risk_reason or "Insufficient data to generate insight.",
        "recommended_action": recommended_action or "Review account manually and schedule a check-in call."
    }


def get_insights_for_top_accounts(df, n=5):
    """
    Runs Claude insights on the top N most at-risk accounts.
    Returns the same df rows with insight columns added.
    Only runs on Critical and At-Risk accounts to save API calls.
    """
    at_risk = df[df["risk_tier"].isin(["🔴 Critical", "🟡 At-Risk"])].head(n).copy()

    insights = []
    for _, row in at_risk.iterrows():
        insight = get_insight(row.to_dict())
        insights.append(insight)

    at_risk["risk_reason"] = [i["risk_reason"] for i in insights]
    at_risk["recommended_action"] = [i["recommended_action"] for i in insights]

    return at_risk