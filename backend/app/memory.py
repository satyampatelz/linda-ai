"""SQLite memory for Linda.

Four simple tables, stored in data/satyam.db (git-ignored):
  * memories      — key/value facts the user told the agent ("my GitHub username is ...")
  * tasks         — history of every task the agent ran, with its result and status
  * conversations — separate chats (side chats), each with its own transcript
  * messages      — the chat transcript (user messages + agent replies), so the
    chat survives closing and reopening the app (v0.9). Capped at the
    newest 200 messages per conversation — old ones are pruned automatically.
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
            """CREATE TABLE IF NOT EXISTS conversations (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   title TEXT NOT NULL DEFAULT 'New chat',
                   created_at TEXT NOT NULL,
                   updated_at TEXT NOT NULL)"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS messages (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   role TEXT NOT NULL,
                   text TEXT NOT NULL,
                   created_at TEXT NOT NULL,
                   conversation_id INTEGER)"""
        )
        # Migration for databases created before conversations existed:
        # add the column if missing, then group any orphan messages
        # into a single conversation so no history is lost.
        cols = [r[1] for r in conn.execute("PRAGMA table_info(messages)")]
        if "conversation_id" not in cols:
            conn.execute(
                "ALTER TABLE messages ADD COLUMN conversation_id INTEGER")
        orphans = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE conversation_id IS NULL"
        ).fetchone()[0]
        if orphans:
            first = conn.execute(
                """SELECT text FROM messages
                   WHERE conversation_id IS NULL AND role = 'user'
                   ORDER BY id ASC LIMIT 1"""
            ).fetchone()
            title = _title_from(first[0]) if first else "Chat"
            cur = conn.execute(
                """INSERT INTO conversations(title, created_at, updated_at)
                   VALUES(?,?,?)""",
                (title, _now(), _now()),
            )
            conn.execute(
                "UPDATE messages SET conversation_id = ? "
                "WHERE conversation_id IS NULL",
                (cur.lastrowid,),
            )


def _title_from(text: str) -> str:
    """A short chat title from the first user message (one line)."""
    title = " ".join((text or "").split())[:40].strip()
    return title or "New chat"


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


# ---------------------------------------------------------------------------
# Conversations (side chats) — separate chats, each with its own transcript.
# ---------------------------------------------------------------------------
def create_conversation(title: str = "New chat") -> int:
    """Start a new conversation. Returns its id."""
    init_db()
    with _conn() as conn:
        cur = conn.execute(
            """INSERT INTO conversations(title, created_at, updated_at)
               VALUES(?,?,?)""",
            (title or "New chat", _now(), _now()),
        )
        return cur.lastrowid


def list_conversations():
    """All conversations, most recently active first, with message counts."""
    init_db()
    with _conn() as conn:
        return [
            dict(r)
            for r in conn.execute(
                """SELECT c.id, c.title, c.created_at, c.updated_at,
                          COUNT(m.id) AS message_count
                   FROM conversations c
                   LEFT JOIN messages m ON m.conversation_id = c.id
                   GROUP BY c.id
                   ORDER BY c.updated_at DESC, c.id DESC"""
            )
        ]


def get_conversation(conversation_id: int):
    """One conversation row as a dict, or None."""
    init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT id, title, created_at, updated_at FROM conversations "
            "WHERE id = ?",
            (conversation_id,),
        ).fetchone()
        return dict(row) if row else None


def rename_conversation(conversation_id: int, title: str) -> bool:
    init_db()
    with _conn() as conn:
        cur = conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            ((title or "New chat").strip()[:80] or "New chat",
             _now(), conversation_id),
        )
        return cur.rowcount > 0


def delete_conversation(conversation_id: int) -> bool:
    """Delete a conversation and all its messages."""
    init_db()
    with _conn() as conn:
        conn.execute(
            "DELETE FROM messages WHERE conversation_id = ?",
            (conversation_id,),
        )
        cur = conn.execute(
            "DELETE FROM conversations WHERE id = ?", (conversation_id,)
        )
        return cur.rowcount > 0


def resolve_conversation(conversation_id=None) -> int:
    """Return a valid conversation id to use.

    A given id is used as-is if it exists. Otherwise the most recently
    active conversation is used, creating one if there are none yet —
    so older clients that don't know about conversations keep working
    on "the current chat".
    """
    init_db()
    if conversation_id is not None:
        try:
            cid = int(conversation_id)
        except (TypeError, ValueError):
            cid = None
        if cid is not None and get_conversation(cid):
            return cid
    convs = list_conversations()
    if convs:
        return convs[0]["id"]
    return create_conversation()


def log_message(role: str, text: str, conversation_id=None):
    """Save one chat message (role: "user" or "agent") to the transcript.

    Callers MUST redact one-time codes before calling (agent.redact_otp_text)
    — an SMS OTP the user typed in chat is never persisted. Only the
    messages the user actually sees are saved: user messages + the agent's
    final reply. Tool internals and step logs are never chat messages.
    Oldest messages past MAX_CHAT_MESSAGES are pruned on every insert
    (per conversation), so the table stays small forever. The first user
    message in a chat also becomes its title (unless renamed already)."""
    init_db()
    cid = resolve_conversation(conversation_id)
    with _conn() as conn:
        conn.execute(
            "INSERT INTO messages(role, text, created_at, conversation_id) "
            "VALUES(?,?,?,?)",
            (role, text or "", _now(), cid),
        )
        conn.execute(
            """DELETE FROM messages WHERE conversation_id = ? AND id NOT IN (
                   SELECT id FROM messages WHERE conversation_id = ?
                   ORDER BY id DESC LIMIT ?)""",
            (cid, cid, MAX_CHAT_MESSAGES),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (_now(), cid),
        )
        if role == "user":
            row = conn.execute(
                "SELECT title FROM conversations WHERE id = ?", (cid,)
            ).fetchone()
            if row and row["title"] == "New chat":
                conn.execute(
                    "UPDATE conversations SET title = ? WHERE id = ?",
                    (_title_from(text), cid),
                )
    return cid


def recent_messages(conversation_id=None, limit: int = MAX_CHAT_MESSAGES):
    """One conversation's transcript, OLDEST first (chat order), newest
    `limit` messages. With no conversation_id, the most recently active
    conversation is used. Returns {"role", "text", "created_at"} dicts."""
    init_db()
    cid = resolve_conversation(conversation_id)
    with _conn() as conn:
        rows = conn.execute(
            """SELECT role, text, created_at FROM messages
               WHERE conversation_id = ?
               ORDER BY id DESC LIMIT ?""",
            (cid, limit),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]
