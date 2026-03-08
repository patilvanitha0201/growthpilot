import pandas as pd

def clamp(value, min_val=0, max_val=100):
    """Keep any score between 0 and 100."""
    return max(min_val, min(max_val, value))


def compute_engagement_score(row):
    """
    Engagement = how actively is the user logging in?
    Signals: days_since_last_login, weekly_logins_last_30d
    Weight in final score: 35%
    """
    login_recency  = clamp(100 - (row["days_since_last_login"] * 4))
    login_freq     = clamp(row["weekly_logins_last_30d"] * 10)
    score          = (login_recency * 0.5) + (login_freq * 0.5)
    return clamp(score)


def compute_adoption_score(row):
    """
    Adoption = how much of the product are they actually using?
    Signals: features_used vs total_features_available
    Weight in final score: 25%
    """
    if row["total_features_available"] == 0:
        return 0
    ratio = row["features_used"] / row["total_features_available"]
    return clamp(ratio * 100)


def compute_sentiment_score(row):
    """
    Sentiment = how happy is the customer?
    Signals: nps_score, open_support_tickets, avg_ticket_severity
    Weight in final score: 25%
    """
    nps_component      = clamp(row["nps_score"] * 10)
    ticket_penalty     = row["open_support_tickets"] * 8
    severity_penalty   = row["avg_ticket_severity"] * 5
    score              = nps_component - ticket_penalty - severity_penalty
    return clamp(score)


def compute_lifecycle_score(row):
    """
    Lifecycle = where are they in the customer journey?
    Signals: days_to_renewal, champion_changed
    Weight in final score: 15%
    """
    # Penalty ramps up as renewal approaches inside 60 days
    renewal_penalty    = clamp((60 - row["days_to_renewal"]) * 1.5, 0, 60) \
                         if row["days_to_renewal"] < 60 else 0
    champion_penalty   = 35 if row["champion_changed"] == 1 else 0
    score              = 100 - renewal_penalty - champion_penalty
    return clamp(score)


def compute_health_score(row):
    """
    Final weighted health score (0–100).
    """
    e = compute_engagement_score(row)
    a = compute_adoption_score(row)
    s = compute_sentiment_score(row)
    l = compute_lifecycle_score(row)

    score = (e * 0.35) + (a * 0.25) + (s * 0.25) + (l * 0.15)
    return round(clamp(score), 1)


def assign_tier(score):
    if score >= 70:
        return "🟢 Healthy"
    elif score >= 40:
        return "🟡 At-Risk"
    else:
        return "🔴 Critical"


def score_accounts(df):
    """
    Takes the raw accounts dataframe.
    Returns the same dataframe with 5 new columns added:
    engagement_score, adoption_score, sentiment_score,
    lifecycle_score, health_score, risk_tier
    """
    df = df.copy()

    df["engagement_score"] = df.apply(compute_engagement_score, axis=1)
    df["adoption_score"]   = df.apply(compute_adoption_score,   axis=1)
    df["sentiment_score"]  = df.apply(compute_sentiment_score,  axis=1)
    df["lifecycle_score"]  = df.apply(compute_lifecycle_score,  axis=1)
    df["health_score"]     = df.apply(compute_health_score,     axis=1)
    df["risk_tier"]        = df["health_score"].apply(assign_tier)

    # Sort by health score ascending so most at-risk are first
    df = df.sort_values("health_score", ascending=True).reset_index(drop=True)

    return df