import sqlite3
from datetime import datetime

DB_PATH = "growthpilot_memory.db"

def init_db():
    """Creates the database and tables if they don't exist yet."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Stores a health score snapshot for every account, every week
    c.execute("""
        CREATE TABLE IF NOT EXISTS score_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL,
            account_name TEXT NOT NULL,
            score INTEGER NOT NULL,
            tier TEXT NOT NULL,
            engagement_score INTEGER,
            adoption_score INTEGER,
            sentiment_score INTEGER,
            lifecycle_score INTEGER,
            snapshot_date TEXT NOT NULL,
            week_number INTEGER NOT NULL
        )
    """)

    # Stores every action a CSM takes on an account
    c.execute("""
        CREATE TABLE IF NOT EXISTS interventions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL,
            account_name TEXT NOT NULL,
            action_type TEXT NOT NULL,
            action_summary TEXT,
            score_at_intervention INTEGER,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database ready")


def save_snapshot(accounts: list):
    """
    Call this once per week with your current account list.
    accounts = list of dicts, each with account health data.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.now().date().isoformat()
    week_num = datetime.now().isocalendar()[1]

    for acct in accounts:
        c.execute("""
            INSERT INTO score_history
            (account_id, account_name, score, tier,
             engagement_score, adoption_score, sentiment_score,
             lifecycle_score, snapshot_date, week_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            acct["account_id"],
            acct["account_name"],
            acct["score"],
            acct["tier"],
            acct.get("engagement_score"),
            acct.get("adoption_score"),
            acct.get("sentiment_score"),
            acct.get("lifecycle_score"),
            today,
            week_num
        ))

    conn.commit()
    conn.close()
    print(f"✅ Saved {len(accounts)} snapshots for week {week_num}")


def get_trajectory(account_id: str, weeks: int = 8) -> list:
    """Returns the last N weeks of scores for one account."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT snapshot_date, score, tier
        FROM score_history
        WHERE account_id = ?
        ORDER BY snapshot_date DESC
        LIMIT ?
    """, (account_id, weeks))
    rows = c.fetchall()
    conn.close()
    return [{"date": r[0], "score": r[1], "tier": r[2]} for r in rows]


def get_interventions(account_id: str) -> list:
    """Returns past actions taken on this account."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT action_type, action_summary, score_at_intervention, created_at
        FROM interventions
        WHERE account_id = ?
        ORDER BY created_at DESC
        LIMIT 5
    """, (account_id,))
    rows = c.fetchall()
    conn.close()
    return [{"action": r[0], "summary": r[1], "score": r[2], "date": r[3]} for r in rows]


def log_intervention(account_id, account_name, action_type, summary, score):
    """Call this when a CSM takes an action on an account."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO interventions
        (account_id, account_name, action_type, action_summary,
         score_at_intervention, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (account_id, account_name, action_type, summary, score,
          datetime.now().isoformat()))
    conn.commit()
    conn.close()


def analyze_trajectory(trajectory: list) -> dict:
    """
    Takes raw score history and computes meaningful signals.
    This is what tells Claude 'this account has been declining 3 weeks in a row'
    instead of just 'this account is at 31'.
    """
    if not trajectory:
        return {"status": "no_history"}

    scores = [t["score"] for t in trajectory]
    current = scores[0]

    # Count how many weeks in a row the score has dropped
    consecutive_declines = 0
    for i in range(len(scores) - 1):
        if scores[i] < scores[i + 1]:
            consecutive_declines += 1
        else:
            break

    week_delta  = current - scores[1] if len(scores) > 1 else 0
    month_delta = current - scores[3] if len(scores) > 3 else 0

    # Classify the trend
    if consecutive_declines >= 3:
        trend = "sustained decline"
    elif consecutive_declines >= 1:
        trend = "declining"
    elif week_delta > 5:
        trend = "improving"
    else:
        trend = "stable"

    alert = None
    if week_delta <= -20:
        alert = "sharp drop this week"
    elif month_delta <= -30:
        alert = "severe erosion over past month"

    return {
        "current_score": current,
        "prev_score": scores[1] if len(scores) > 1 else None,
        "score_4w_ago": scores[3] if len(scores) > 3 else None,
        "week_delta": week_delta,
        "month_delta": month_delta,
        "consecutive_declines": consecutive_declines,
        "trend": trend,
        "alert": alert,
    }

if __name__ == "__main__":
    init_db()

    # Fake 2 weeks of data for one account
    week1 = [{"account_id": "acme_001", "account_name": "Acme Corp",
               "score": 74, "tier": "Healthy",
               "engagement_score": 80, "adoption_score": 75,
               "sentiment_score": 70, "lifecycle_score": 72}]

    week2 = [{"account_id": "acme_001", "account_name": "Acme Corp",
               "score": 31, "tier": "Critical",
               "engagement_score": 30, "adoption_score": 28,
               "sentiment_score": 35, "lifecycle_score": 31}]

    save_snapshot(week1)
    save_snapshot(week2)

    trajectory = get_trajectory("acme_001")
    signals = analyze_trajectory(trajectory)

    print("\n--- Trajectory ---")
    for t in trajectory:
        print(f"  {t['date']}: {t['score']} ({t['tier']})")

    print("\n--- Signals ---")
    for k, v in signals.items():
        print(f"  {k}: {v}")