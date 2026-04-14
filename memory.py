import sqlite3
from datetime import datetime

DB_PATH = "growthpilot_memory.db"

# Auto-initialize DB on import
init_db() if False else None  # forward declaration placeholder

def init_db():
    """Creates the database and tables if they don't exist yet."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

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


def save_snapshot(accounts: list):
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


def get_trajectory(account_id: str, weeks: int = 8) -> list:
    init_db()
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
    init_db()
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
    init_db()
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
    if not trajectory:
        return {"status": "no_history"}

    scores = [t["score"] for t in trajectory]
    current = scores[0]

    consecutive_declines = 0
    for i in range(len(scores) - 1):
        if scores[i] < scores[i + 1]:
            consecutive_declines += 1
        else:
            break

    week_delta  = current - scores[1] if len(scores) > 1 else 0
    month_delta = current - scores[3] if len(scores) > 3 else 0

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