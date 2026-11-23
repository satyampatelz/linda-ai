"""Approval gate — a user-controlled switch, nothing hardcoded.

APPROVAL_MODE=auto (default)
    The agent runs every action immediately. No prompts, no pauses.
    This is the default because the user asked for full obedience.

APPROVAL_MODE=ask
    Only the three external actions below pause and wait for a one-click
    Approve / Reject in the UI. Everything else still runs immediately.
    Set this from the Settings screen (⚙️) in the app — no file editing,
    no restart.

No other restrictions exist anywhere in the agent.
"""
import threading
import time
import uuid

from .config import settings

# Actions that leave the machine. Only these ever pause, and only in ask mode.
EXTERNAL_ACTIONS = {"github_push", "github_clone", "kaggle_submit"}

# How long (seconds) an approval waits in ask mode before counting as "no".
APPROVAL_TIMEOUT = 300


class ApprovalManager:
    def __init__(self, mode: str | None = None):
        # mode=None means "follow settings.approval_mode live" — so a change
        # in the Settings screen applies immediately, no restart. Tests may
        # pass an explicit mode to pin it.
        self._mode = (mode or "").strip().lower() or None
        self._pending: dict = {}
        self._lock = threading.Lock()

    @property
    def mode(self) -> str:
        return self._mode or settings.approval_mode or "auto"

    @mode.setter
    def mode(self, value: str):
        self._mode = (value or "").strip().lower() or None

    @property
    def is_auto(self) -> bool:
        return self.mode != "ask"

    def request(self, task_id: str, action: str, detail: str,
                timeout: int = APPROVAL_TIMEOUT) -> bool:
        """Return True if the action may proceed.

        In auto mode, or for non-external actions, this returns instantly.
        In ask mode it blocks until the user clicks Approve/Reject in the UI
        (or the timeout passes, which counts as Reject).
        """
        if action not in EXTERNAL_ACTIONS or self.is_auto:
            return True

        approval_id = uuid.uuid4().hex[:8]
        event = threading.Event()
        record = {
            "id": approval_id,
            "task_id": task_id,
            "action": action,
            "detail": detail,
            "decision": None,
            "event": event,
            "created_at": time.time(),
        }
        with self._lock:
            self._pending[approval_id] = record

        decided = event.wait(timeout=timeout)

        with self._lock:
            record = self._pending.pop(approval_id, record)

        if not decided:
            return False
        return bool(record.get("decision"))

    def pending_for_task(self, task_id: str):
        """The pending approval for a task, if any (safe to send to the UI)."""
        with self._lock:
            for rec in self._pending.values():
                if rec["task_id"] == task_id:
                    return {
                        "id": rec["id"],
                        "task_id": task_id,
                        "action": rec["action"],
                        "detail": rec["detail"],
                    }
        return None

    def decide(self, approval_id: str, approve: bool) -> bool:
        """Record the user's decision. Returns False if no such approval."""
        with self._lock:
            rec = self._pending.get(approval_id)
        if not rec:
            return False
        rec["decision"] = bool(approve)
        rec["event"].set()
        return True

    def cancel_for_task(self, task_id: str) -> int:
        """Reject every pending approval for a task (used by Stop) so a
        waiting agent loop wakes up immediately instead of waiting out the
        timeout. Returns how many were cancelled."""
        cancelled = 0
        with self._lock:
            recs = [r for r in self._pending.values() if r["task_id"] == task_id]
        for rec in recs:
            rec["decision"] = False
            rec["event"].set()
            cancelled += 1
        return cancelled


# Shared instance used by the agent loop and the API.
approvals = ApprovalManager()
