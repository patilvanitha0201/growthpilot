import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def get_insight(row) -> dict:
    """
    Calls Claude with the account's signals.
    Returns a dict with 'risk_reason' and 'recommended_action'.
    """

    champion_text = "Yes — key contact recently changed" \
                    if row["champion_changed"] == 1 \
                    else "No"

    prompt = f"""
You are GrowthPilot, an AI assistant for B2B SaaS Customer Success teams.
Your job is to help CSMs act fast on at-risk accounts.

Here is the account data:

Company         : {row['company_name']}
Industry        : {row['industry']}
Contract Value  : ${row['contract_value']:,}
Health Score    : {row['health_score']}/100 ({row['tier']})

Product Usage
  Days since last login    : {row['days_since_last_login']} days
  Weekly logins (last 30d) : {row['weekly_logins_last_30d']}

Feature Adoption
  Features used            : {row['features_used']} of {row['total_features_available']}

Support Activity
  Open tickets             : {row['open_support_tickets']}
  Avg ticket severity      : {row['avg_ticket_severity']} / 5

Customer Sentiment
  NPS score                : {row['nps_score']} / 10
  Days since last NPS      : {row['days_since_nps']} days

Account Lifecycle
  Days since onboarding    : {row['days_since_onboarding']}
  Days to renewal          : {row['days_to_renewal']}
  Champion changed         : {champion_text}

Respond in EXACTLY this format — nothing else:

RISK REASON:
[2 sentences max. Be specific about which signals are most alarming. Mention the contract value if it is above $50,000.]

RECOMMENDED ACTION:
[1 sentence. Tell the CSM exactly what to do THIS WEEK. Be direct — no fluff.]
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    return _parse_insight(raw)


def _parse_insight(raw: str) -> dict:
    """
    Splits Claude's response into risk_reason and recommended_action.
    Falls back gracefully if format is unexpected.
    """
    risk_reason         = "Unable to generate risk reason."
    recommended_action  = "Please review this account manually."

    try:
        if "RISK REASON:" in raw and "RECOMMENDED ACTION:" in raw:
            parts              = raw.split("RECOMMENDED ACTION:")
            risk_reason        = parts[0].replace("RISK REASON:", "").strip()
            recommended_action = parts[1].strip()
    except Exception:
        pass

    return {
        "risk_reason"        : risk_reason,
        "recommended_action" : recommended_action
    }


def get_bulk_insights(df, top_n=5) -> dict:
    """
    Generates insights for the top N at-risk accounts only.
    Returns a dict keyed by account_id.
    Used to pre-load the Top 5 digest panel.
    """
    insights = {}
    top_accounts = df.head(top_n)

    for _, row in top_accounts.iterrows():
        insights[row["account_id"]] = get_insight(row)

    return insights