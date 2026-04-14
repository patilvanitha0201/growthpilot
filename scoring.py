import pandas as pd

# ── Weights ──────────────────────────────────────────────
W_ENGAGEMENT  = 0.35
W_ADOPTION    = 0.25
W_SENTIMENT   = 0.25
W_LIFECYCLE   = 0.15

def _clamp(val, lo=0, hi=100):
    """Keep any score between 0 and 100."""
    return max(lo, min(hi, val))


# ── 4 Signal Scorers ─────────────────────────────────────

def engagement_score(row):
    """
    Rewards frequent logins, penalises days of absence.
    Max possible raw = 100 + (10*5) = 150 → clamped to 100.
    """
    base  = 100 - (row["days_since_last_login"] * 2.5)
    bonus = row["weekly_logins_last_30d"] * 5
    return _clamp(base + bonus)


def adoption_score(row):
    """
    Simple ratio: features used / features available.
    """
    if row["total_features_available"] == 0:
        return 0
    ratio = row["features_used"] / row["total_features_available"]
    return _clamp(ratio * 100)


def sentiment_score(row):
    """
    NPS drives the base; open tickets and their severity drag it down.
    NPS is 0-10 → scale to 0-100, then subtract ticket penalty.
    """
    nps_base       = (row["nps_score"] / 10) * 100
    ticket_penalty = (row["open_support_tickets"] * 8) + \
                     (row["avg_ticket_severity"] * 4)
    return _clamp(nps_base - ticket_penalty)


def lifecycle_score(row):
    """
    Penalises champion changes heavily.
    Penalises proximity to renewal (< 30 days = danger zone).
    """
    champion_penalty = 35 if row["champion_changed"] == 1 else 0
    days_left        = row["days_to_renewal"]
    renewal_penalty  = max(0, (30 - days_left) * 1.5) if days_left < 30 else 0
    return _clamp(100 - champion_penalty - renewal_penalty)


# ── Master Scorer ─────────────────────────────────────────

def compute_health_score(row):
    """Weighted aggregate of the 4 signal scores → 0-100."""
    e = engagement_score(row)
    a = adoption_score(row)
    s = sentiment_score(row)
    l = lifecycle_score(row)

    score = (e * W_ENGAGEMENT) + \
            (a * W_ADOPTION)   + \
            (s * W_SENTIMENT)  + \
            (l * W_LIFECYCLE)

    return round(_clamp(score), 1)


def assign_tier(score):
    if score >= 70:
        return "🟢 Healthy"
    elif score >= 40:
        return "🟡 At-Risk"
    else:
        return "🔴 Critical"


# ── Score Breakdown (for detail view) ────────────────────

def get_score_breakdown(row):
    """Returns each signal score individually for the bar chart."""
    return {
        "Engagement"  : round(engagement_score(row), 1),
        "Adoption"    : round(adoption_score(row), 1),
        "Sentiment"   : round(sentiment_score(row), 1),
        "Lifecycle"   : round(lifecycle_score(row), 1),
    }


# ── Main Entry Point ──────────────────────────────────────

def score_accounts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes the raw CSV dataframe.
    Returns it enriched with health_score, tier, and breakdown columns.
    """
    df = df.copy()

    df["health_score"] = df.apply(compute_health_score, axis=1)
    df["tier"]         = df["health_score"].apply(assign_tier)

    # Individual signal scores (used in detail view)
    df["score_engagement"] = df.apply(engagement_score, axis=1).round(1)
    df["score_adoption"]   = df.apply(adoption_score,   axis=1).round(1)
    df["score_sentiment"]  = df.apply(sentiment_score,  axis=1).round(1)
    df["score_lifecycle"]  = df.apply(lifecycle_score,  axis=1).round(1)

    # Sort: Critical first, then by health_score ascending
    df = df.sort_values("health_score", ascending=True).reset_index(drop=True)

    return df