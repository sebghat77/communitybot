import sqlite3
import json
from datetime import datetime
from config import DB_NAME


def now():
    return datetime.now().isoformat(timespec="seconds")


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT,
        persona_json TEXT DEFAULT '{}',
        onboarding_completed INTEGER DEFAULT 0,
        created_at TEXT,
        last_active TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        username TEXT,
        event_type TEXT,
        event_value TEXT,
        channel_id TEXT,
        channel_name TEXT,
        timestamp TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        username TEXT,
        channel_name TEXT,
        reason TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT,
        engaged_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS nudges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        username TEXT,
        nudge_type TEXT,
        interest TEXT,
        target TEXT,
        status TEXT DEFAULT 'sent',
        created_at TEXT,
        engaged_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def log_event(user_id, username, event_type, event_value="", channel_id="", channel_name=""):
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO user_logs (
        user_id, username, event_type, event_value, channel_id, channel_name, timestamp
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        str(user_id or ""),
        str(username or ""),
        str(event_type or ""),
        str(event_value or ""),
        str(channel_id or ""),
        str(channel_name or ""),
        now()
    ))

    conn.commit()
    conn.close()


def create_or_touch_user(user_id, username):
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    current = now()

    cur.execute("""
    INSERT OR IGNORE INTO users (
        user_id, username, persona_json, onboarding_completed, created_at, last_active
    )
    VALUES (?, ?, '{}', 0, ?, ?)
    """, (str(user_id), str(username), current, current))

    cur.execute("""
    UPDATE users
    SET username = ?, last_active = ?
    WHERE user_id = ?
    """, (str(username), current, str(user_id)))

    conn.commit()
    conn.close()


def save_persona(user_id, username, persona):
    init_db()
    create_or_touch_user(user_id, username)

    conn = get_connection()
    cur = conn.cursor()
    current = now()

    cur.execute("""
    UPDATE users
    SET username = ?,
        persona_json = ?,
        onboarding_completed = 1,
        last_active = ?
    WHERE user_id = ?
    """, (
        str(username),
        json.dumps(persona, ensure_ascii=False),
        current,
        str(user_id)
    ))

    conn.commit()
    conn.close()
    log_event(user_id, username, "onboarding_completed", json.dumps(persona, ensure_ascii=False))


def get_persona(user_id):
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT username, persona_json, onboarding_completed, created_at, last_active
    FROM users
    WHERE user_id = ?
    """, (str(user_id),))

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    username, persona_json, completed, created_at, last_active = row

    try:
        persona = json.loads(persona_json or "{}")
    except Exception:
        persona = {}

    return {
        "username": username,
        "persona": persona,
        "onboarding_completed": int(completed or 0),
        "created_at": created_at,
        "last_active": last_active
    }


def load_completed_profiles():
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT user_id, username, persona_json
    FROM users
    WHERE onboarding_completed = 1
    """)

    rows = cur.fetchall()
    conn.close()

    result = []
    for user_id, username, persona_json in rows:
        try:
            persona = json.loads(persona_json or "{}")
        except Exception:
            persona = {}

        result.append({
            "user_id": str(user_id),
            "username": username,
            "persona": persona
        })

    return result


def save_recommendation(user_id, username, channel_name, reason):
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO recommendations (
        user_id, username, channel_name, reason, status, created_at, engaged_at
    )
    VALUES (?, ?, ?, ?, 'pending', ?, NULL)
    """, (str(user_id), str(username), str(channel_name), str(reason), now()))

    conn.commit()
    conn.close()
    log_event(user_id, username, "recommendation_sent", channel_name, "", channel_name)


def mark_recommendation_engaged(user_id, username, channel_name):
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    current = now()

    cur.execute("""
    UPDATE recommendations
    SET status = 'engaged',
        engaged_at = ?
    WHERE user_id = ?
      AND channel_name = ?
      AND status = 'pending'
    """, (current, str(user_id), str(channel_name)))

    changed = cur.rowcount
    conn.commit()
    conn.close()

    if changed > 0:
        log_event(user_id, username, "recommendation_engaged", channel_name, "", channel_name)


def save_nudge(user_id, username, nudge_type, interest, target):
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO nudges (
        user_id, username, nudge_type, interest, target, status, created_at, engaged_at
    )
    VALUES (?, ?, ?, ?, ?, 'sent', ?, NULL)
    """, (str(user_id), str(username), str(nudge_type), str(interest), str(target), now()))

    conn.commit()
    conn.close()
    log_event(user_id, username, "nudge_sent", f"{nudge_type}: {target}")


def mark_nudge_engaged(user_id, username, target):
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    current = now()

    cur.execute("""
    UPDATE nudges
    SET status = 'engaged',
        engaged_at = ?
    WHERE user_id = ?
      AND target = ?
      AND status = 'sent'
    """, (current, str(user_id), str(target)))

    changed = cur.rowcount
    conn.commit()
    conn.close()

    if changed > 0:
        log_event(user_id, username, "nudge_engaged", target)


def log_message_activity(user_id, username, channel_id, channel_name, content=""):
    create_or_touch_user(user_id, username)
    content = str(content or "").strip()

    if len(content) >= 2:
        log_event(user_id, username, "message_sent", content[:300], channel_id, channel_name)

    if channel_name not in ["Direct Message", "DM"]:
        mark_recommendation_engaged(user_id, username, channel_name)


def get_channel_activity(limit=10):
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT channel_name, COUNT(*)
    FROM user_logs
    WHERE event_type = 'message_sent'
      AND channel_name != ''
      AND channel_name != 'Direct Message'
    GROUP BY channel_name
    ORDER BY COUNT(*) DESC
    LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_user_activity(limit=10):
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT username, COUNT(*)
    FROM user_logs
    WHERE event_type = 'message_sent'
    GROUP BY user_id, username
    ORDER BY COUNT(*) DESC
    LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_user_activity_by_channel(channel_name, limit=10):
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT username, COUNT(*)
    FROM user_logs
    WHERE event_type = 'message_sent'
      AND channel_name = ?
    GROUP BY user_id, username
    ORDER BY COUNT(*) DESC
    LIMIT ?
    """, (str(channel_name), limit))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_recommendation_stats():
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT status, COUNT(*)
    FROM recommendations
    GROUP BY status
    """)

    rows = cur.fetchall()
    conn.close()
    return rows


def get_nudge_stats():
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT nudge_type, status, COUNT(*)
    FROM nudges
    GROUP BY nudge_type, status
    ORDER BY COUNT(*) DESC
    """)

    rows = cur.fetchall()
    conn.close()
    return rows


def get_event_counts():
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT event_type, COUNT(*)
    FROM user_logs
    GROUP BY event_type
    ORDER BY COUNT(*) DESC
    """)

    rows = cur.fetchall()
    conn.close()
    return rows


def get_recent_logs(limit=20):
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT username, event_type, event_value, channel_name, timestamp
    FROM user_logs
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_evaluation_summary():
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    summary = {}

    cur.execute("SELECT COUNT(DISTINCT user_id) FROM users")
    summary["users_total"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT user_id) FROM users WHERE onboarding_completed = 1")
    summary["onboarding_completed"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM recommendations")
    summary["recommendations_sent"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM recommendations WHERE status = 'engaged'")
    summary["recommendations_engaged"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM nudges")
    summary["nudges_sent"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM nudges WHERE status = 'engaged'")
    summary["nudges_engaged"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM user_logs WHERE event_type = 'message_sent'")
    summary["messages_logged"] = cur.fetchone()[0]

    summary["onboarding_rate"] = round((summary["onboarding_completed"] / summary["users_total"]) * 100, 1) if summary["users_total"] else 0
    summary["recommendation_engagement_rate"] = round((summary["recommendations_engaged"] / summary["recommendations_sent"]) * 100, 1) if summary["recommendations_sent"] else 0
    summary["nudge_engagement_rate"] = round((summary["nudges_engaged"] / summary["nudges_sent"]) * 100, 1) if summary["nudges_sent"] else 0

    conn.close()
    return summary


init_db()
