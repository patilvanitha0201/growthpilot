import sqlite3
from memory import get_trajectory, get_interventions, analyze_trajectory

DB_PATH = "growthpilot_memory.db"

# ── Raw account store (loaded once from scoring) ──────────
_accounts = {}

def load_accounts(df):
    """Call this once at startup with your scored dataframe."""
    global _accounts
    for _, row in df.iterrows():
        _accounts[row["account_id"]] = row.to_dict()


# ── Tool Functions (called by Claude) ─────────────────────

def get_health_signals(account_id: str) -> dict:
    """Returns current health signals for an account."""
    acc = _accounts.get(account_id)
    if not acc:
        return {"error": f"Account {account_id} not found"}
    return {
        "account_id":            account_id,
        "company_name":          acc["company_name"],
        "health_score":          acc["health_score"],
        "tier":                  acc["tier"],
        "engagement_score":      acc["score_engagement"],
        "adoption_score":        acc["score_adoption"],
        "sentiment_score":       acc["score_sentiment"],
        "lifecycle_score":       acc["score_lifecycle"],
        "days_since_last_login": acc["days_since_last_login"],
        "weekly_logins":         acc["weekly_logins_last_30d"],
        "features_used":         acc["features_used"],
        "total_features":        acc["total_features_available"],
    }


def get_score_trajectory(account_id: str, weeks: int = 8) -> dict:
    """Returns historical score trend + trajectory analysis."""
    trajectory = get_trajectory(account_id, weeks)
    if not trajectory:
        return {"account_id": account_id, "status": "no_history",
                "message": "No historical data yet — first week of tracking."}
    signals = analyze_trajectory(trajectory)
    return {
        "account_id": account_id,
        "trajectory": trajectory,
        "analysis":   signals
    }


def get_support_tickets(account_id: str) -> dict:
    """Returns support ticket signals for an account."""
    acc = _accounts.get(account_id)
    if not acc:
        return {"error": f"Account {account_id} not found"}
    return {
        "account_id":        account_id,
        "open_tickets":      acc["open_support_tickets"],
        "avg_severity":      acc["avg_ticket_severity"],
        "severity_label":    _severity_label(acc["avg_ticket_severity"]),
    }


def get_champion_status(account_id: str) -> dict:
    """Returns whether the key contact has changed."""
    acc = _accounts.get(account_id)
    if not acc:
        return {"error": f"Account {account_id} not found"}
    changed = acc["champion_changed"] == 1
    return {
        "account_id":      account_id,
        "champion_changed": changed,
        "risk_note":       "Key contact recently changed — relationship at risk." if changed else "Champion stable."
    }


def get_renewal_date(account_id: str) -> dict:
    """Returns renewal urgency for an account."""
    acc = _accounts.get(account_id)
    if not acc:
        return {"error": f"Account {account_id} not found"}
    days = acc["days_to_renewal"]
    return {
        "account_id":     account_id,
        "days_to_renewal": days,
        "contract_value": acc["contract_value"],
        "urgency":        _urgency_label(days)
    }


def get_last_touchpoint(account_id: str) -> dict:
    """Returns last CSM intervention on this account."""
    interventions = get_interventions(account_id)
    if not interventions:
        return {"account_id": account_id, "status": "no_interventions",
                "message": "No logged CSM actions yet."}
    last = interventions[0]
    return {
        "account_id":   account_id,
        "last_action":  last["action"],
        "summary":      last["summary"],
        "score_at_time": last["score"],
        "date":         last["date"],
        "all_recent":   interventions
    }


# ── Helpers ───────────────────────────────────────────────

def _severity_label(severity: float) -> str:
    if severity >= 4.5: return "Critical"
    if severity >= 3.0: return "High"
    if severity >= 1.5: return "Medium"
    return "Low"

def _urgency_label(days: int) -> str:
    if days <= 14:  return "URGENT — renewal imminent"
    if days <= 30:  return "High — renewal within a month"
    if days <= 60:  return "Medium — renewal approaching"
    return "Low — renewal not imminent"


# ── Tool Dispatcher (called by agent loop) ─────────────────

TOOL_MAP = {
    "get_health_signals":    get_health_signals,
    "get_score_trajectory":  get_score_trajectory,
    "get_support_tickets":   get_support_tickets,
    "get_champion_status":   get_champion_status,
    "get_renewal_date":      get_renewal_date,
    "get_last_touchpoint":   get_last_touchpoint,
}

def dispatch_tool(tool_name: str, tool_input: dict):
    """Routes Claude's tool call to the right function."""
    fn = TOOL_MAP.get(tool_name)
    if not fn:
        return {"error": f"Unknown tool: {tool_name}"}
    return fn(**tool_input)


# ── Claude Tool Definitions (passed to API) ────────────────

TOOL_DEFINITIONS = [
    {
        "name": "get_health_signals",
        "description": "Get current health signals and scores for an account.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "The account ID"}
            },
            "required": ["account_id"]
        }
    },
    {
        "name": "get_score_trajectory",
        "description": "Get historical score trend for an account. Use this to detect sustained declines vs one-week dips.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "weeks":      {"type": "integer", "description": "How many weeks of history to retrieve", "default": 8}
            },
            "required": ["account_id"]
        }
    },
    {
        "name": "get_support_tickets",
        "description": "Get open support ticket volume and severity for an account.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"}
            },
            "required": ["account_id"]
        }
    },
    {
        "name": "get_champion_status",
        "description": "Check if the key contact/champion has recently changed at this account.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"}
            },
            "required": ["account_id"]
        }
    },
    {
        "name": "get_renewal_date",
        "description": "Get days to renewal and contract value for urgency assessment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"}
            },
            "required": ["account_id"]
        }
    },
    {
        "name": "get_last_touchpoint",
        "description": "Get the last CSM action taken on this account and whether it worked.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"}
            },
            "required": ["account_id"]
        }
    },
]