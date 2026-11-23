"""SQLite memory for Satyam.

Three simple tables, stored in data/satyam.db (git-ignored):
  * memories — key/value facts the user told the agent ("my GitHub username is ...")
  * tasks    — history of every task the agent ran, with its result and status
  * messages — the chat transcript (user messages + agent replies), so the
    chat survives closing and reopening the app (v0.9). Capped at the
    newest 200 messages — old ones are pruned automatically.
"""
import sqlite3
from datetime import datetime, timezone

from .config import settings

DB_PATH = settings.data_dir / "satyam.db"

# The chat transcript never grows past this — the desktop icon reopens
# "the same chat", not a year's worth of it.
MAX_CHAT_MESSAGES = 200


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS memories (
                   key TEXT PRIMARY KEY,
                   value TEXT NOT NULL,
                   updated_at TEXT NOT NULL)"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                   id TEXT PRIMARY KEY,
                   task TEXT NOT NULL,
                   result TEXT,
                   status TEXT NOT NULL,
                   created_at TEXT NOT NULL)"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS messages (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   role TEXT NOT NULL,
                   text TEXT NOT NULL,
                   created_at TEXT NOT NULL)"""
        )


def _now():
    return datetime.now(timezone.utc).isoformat()


def remember(key: str, value: str):
    """Save a fact. Overwrites the same key."""
    init_db()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO memories(key, value, updated_at) VALUES(?,?,?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value,
               updated_at=excluded.updated_at""",
            (key, value, _now()),
        )


def recall(key: str):
    """Return a saved fact, or None."""
    init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT value FROM memories WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None


def list_memories():
    """All saved facts, newest first. Returns a list of (key, value)."""
    init_db()
    with _conn() as conn:
        return [
            (r["key"], r["value"])
            for r in conn.execute(
                "SELECT key, value FROM memories ORDER BY updated_at DESC"
            )
        ]


def log_task(task_id: str, task: str, result: str, status: str):
    """Record a finished task (status: done / error / stopped)."""
    init_db()
    with _conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO tasks(id, task, result, status, created_at)
               VALUES(?,?,?,?,?)""",
            (task_id, task, result or "", status, _now()),
        )


def recent_tasks(limit: int = 10):
    """Most recent tasks, newest first."""
    init_db()
    with _conn() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)
            )
        ]


def log_message(role: str, text: str):
    """Save one chat message (role: "user" or "agent") to the transcript.

    Callers MUST redact one-time codes before calling (agent.redact_otp_text)
    — an SMS OTP the user typed in chat is never persisted. Only the
    messages the user actually sees are saved: user messages + the agent's
    final reply. Tool internals and step logs are never chat messages.
    Oldest messages past MAX_CHAT_MESSAGES are pruned on every insert,
    so the table stays small forever."""
    init_db()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO messages(role, text, created_at) VALUES(?,?,?)",
            (role, text or "", _now()),
        )
        conn.execute(
            """DELETE FROM messages WHERE id NOT IN (
                   SELECT id FROM messages ORDER BY id DESC LIMIT ?)""",
            (MAX_CHAT_MESSAGES,),
        )


def recent_messages(limit: int = MAX_CHAT_MESSAGES):
    """The chat transcript, OLDEST first (chat order), newest `limit`
    messages. Returns a list of {"role", "text", "created_at"}."""
    init_db()
    with _conn() as conn:
        rows = conn.execute(
            """SELECT role, text, created_at FROM messages
               ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]
