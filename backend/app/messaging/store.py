"""SQLite storage for messaging — dedupe, per-contact history, 24h window,
and the chat-controlled ON/OFF state (v0.7).

Same database as the rest of Linda (data/satyam.db), four tables:
  * msg_seen     — every inbound message id already handled (dedupe)
  * msg_history  — short per-contact chat history (reply context)
  * msg_contacts — last inbound message time per contact (24h window)
  * msg_control  — per-platform auto-reply ON/OFF, set by chat commands
                   ("ab se Instagram ke messages dekhna" / "WhatsApp band
                   kar do"). No row = OFF: a platform only starts
                   auto-replying when the user says so in chat.
"""
import sqlite3
from datetime import datetime, timedelta, timezone

from ..memory import DB_PATH

HISTORY_LIMIT = 10      # turns of context the brain sees per contact
HISTORY_KEEP = 50       # turns kept per contact before pruning


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS msg_seen (
                   message_id TEXT PRIMARY KEY,
                   platform TEXT NOT NULL,
                   received_at TEXT NOT NULL)"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS msg_history (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   platform TEXT NOT NULL,
                   contact_id TEXT NOT NULL,
                   role TEXT NOT NULL,
                   text TEXT NOT NULL,
                   created_at TEXT NOT NULL)"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS msg_contacts (
                   platform TEXT NOT NULL,
                   contact_id TEXT NOT NULL,
                   last_incoming_at REAL NOT NULL,
                   PRIMARY KEY (platform, contact_id))"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS msg_control (
                   platform TEXT PRIMARY KEY,
                   enabled INTEGER NOT NULL,
                   updated_at TEXT NOT NULL)"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS msg_pending_credential (
                   platform TEXT PRIMARY KEY,
                   fields TEXT NOT NULL,
                   created_at TEXT NOT NULL)"""
        )


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def seen_message(platform: str, message_id: str) -> bool:
    """Record an inbound message id. Returns True if this is the FIRST
    time we've seen it, False if it was already handled (a duplicate
    delivery — Meta redelivers webhooks sometimes). The INSERT OR IGNORE
    is atomic, so two threads racing on the same id can't both win."""
    init_db()
    with _conn() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO msg_seen(message_id, platform, received_at)"
            " VALUES(?,?,?)",
            (message_id, platform, _now_iso()),
        )
        return cur.rowcount == 1


def record_message(platform: str, contact_id: str, role: str, text: str):
    """Append one turn (role: "user" = them, "assistant" = our reply)."""
    init_db()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO msg_history(platform, contact_id, role, text, created_at)"
            " VALUES(?,?,?,?,?)",
            (platform, contact_id, role, text, _now_iso()),
        )
        # Prune: keep the last HISTORY_KEEP turns per contact so the
        # table stays small forever.
        conn.execute(
            """DELETE FROM msg_history WHERE id IN (
                   SELECT id FROM msg_history
                   WHERE platform=? AND contact_id=?
                   ORDER BY id DESC LIMIT -1 OFFSET ?)""",
            (platform, contact_id, HISTORY_KEEP),
        )


def get_history(platform: str, contact_id: str, limit: int = HISTORY_LIMIT):
    """Last `limit` turns, oldest first, as [{"role", "content"}] — the
    exact shape the brain's chat() takes."""
    init_db()
    with _conn() as conn:
        rows = conn.execute(
            """SELECT role, text FROM msg_history
               WHERE platform=? AND contact_id=?
               ORDER BY id DESC LIMIT ?""",
            (platform, contact_id, limit),
        ).fetchall()
    return [{"role": r["role"], "content": r["text"]} for r in reversed(rows)]


def update_last_incoming(platform: str, contact_id: str, ts: float):
    """Remember the newest inbound timestamp for a contact. MAX() means
    an old redelivered message can never move the window backwards."""
    init_db()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO msg_contacts(platform, contact_id, last_incoming_at)
               VALUES(?,?,?)
               ON CONFLICT(platform, contact_id) DO UPDATE SET
               last_incoming_at=MAX(last_incoming_at, excluded.last_incoming_at)""",
            (platform, contact_id, ts),
        )


def get_last_incoming(platform: str, contact_id: str):
    """Epoch seconds of the contact's newest inbound message, or None."""
    init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT last_incoming_at FROM msg_contacts"
            " WHERE platform=? AND contact_id=?",
            (platform, contact_id),
        ).fetchone()
    return row["last_incoming_at"] if row else None


def count_recent_replies(platform: str, contact_id: str, hours: int = 1) -> int:
    """How many replies we sent this contact in the last `hours` hours
    (the loop guard). ISO timestamps sort lexicographically, so a plain
    string comparison is a correct time comparison here."""
    init_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    with _conn() as conn:
        row = conn.execute(
            """SELECT COUNT(*) AS n FROM msg_history
               WHERE platform=? AND contact_id=? AND role='assistant'
               AND created_at >= ?""",
            (platform, contact_id, cutoff),
        ).fetchone()
    return row["n"]


# ---------------------------------------------------------------------------
# Chat control (v0.7) — ON/OFF per platform, set by talking to Linda.
# ---------------------------------------------------------------------------
def set_platform_enabled(platform: str, enabled: bool):
    """Persist the auto-reply switch for one platform. Survives restarts
    (it lives in the same SQLite DB as everything else)."""
    init_db()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO msg_control(platform, enabled, updated_at)
               VALUES(?,?,?)
               ON CONFLICT(platform) DO UPDATE SET
               enabled=excluded.enabled, updated_at=excluded.updated_at""",
            (platform, 1 if enabled else 0, _now_iso()),
        )


def get_platform_enabled(platform: str) -> bool:
    """True only if the user turned this platform ON in chat. No row =
    OFF — a platform never starts auto-replying on its own."""
    init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT enabled FROM msg_control WHERE platform=?",
            (platform,),
        ).fetchone()
    return bool(row and row["enabled"])


# ---------------------------------------------------------------------------
# Secure-box pending requests (v0.7) — when the user enables a platform
# whose credentials are missing, the missing field names are recorded
# here so the chat UI can show a secure masked input card for them.
# Only FIELD NAMES are stored here — never any secret value.
# ---------------------------------------------------------------------------
def set_pending_credential(platform: str, fields):
    """Record that `fields` (e.g. ["token", "target_id"]) are still
    needed for this platform. Replaces any older request for it."""
    init_db()
    fields = sorted(set(fields))
    with _conn() as conn:
        conn.execute(
            """INSERT INTO msg_pending_credential(platform, fields, created_at)
               VALUES(?,?,?)
               ON CONFLICT(platform) DO UPDATE SET
               fields=excluded.fields, created_at=excluded.created_at""",
            (platform, ",".join(fields), _now_iso()),
        )


def get_pending_credentials() -> list:
    """All outstanding credential requests, as
    [{"platform": ..., "fields": [...]}]. Empty list = none pending."""
    init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT platform, fields FROM msg_pending_credential"
            " ORDER BY created_at"
        ).fetchall()
    return [
        {"platform": r["platform"],
         "fields": [f for f in r["fields"].split(",") if f]}
        for r in rows
    ]


def get_pending_credential(platform: str):
    """The outstanding credential request for one platform, as a list
    of field names — or None when nothing is pending for it."""
    for req in get_pending_credentials():
        if req["platform"] == platform:
            return req["fields"]
    return None


def clear_pending_credential(platform: str):
    """Drop the pending request for a platform (its credentials are
    now complete, or the user enabled it another way)."""
    init_db()
    with _conn() as conn:
        conn.execute(
            "DELETE FROM msg_pending_credential WHERE platform=?",
            (platform,),
        )
