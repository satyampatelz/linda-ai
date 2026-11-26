"""Model router — the agent's brain.

Two providers, picked by MODEL_PROVIDER in .env:
  * "ollama" (default) — local model on your own laptop, free, no API key.
  * "gemini"           — Google Gemini free-tier API via plain HTTPS (httpx).

Both expose the same chat() function, so the agent never cares which one
is behind it. Add a new provider by adding one more _chat_* function.
"""
import logging
import time

import httpx

from .config import settings

logger = logging.getLogger("linda.brain")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# If the configured Gemini model id is gone (404 — Google retires free-tier
# model ids from time to time), try these known free-tier ids next, in
# order. Whichever one answers is saved as the new configured model.
GEMINI_FALLBACK_MODELS = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]

# One retry after a short pause, for errors that are usually temporary
# (network hiccup, model still loading, rate limit). Permanent errors
# (no key, unknown model, bad request) are never retried.
RETRY_BACKOFF_SECONDS = 1.5


class BrainError(Exception):
    """Raised when the model cannot be reached or refuses the request.

    `transient=True` means "worth retrying once" (network/timeout/5xx/429).
    The message is always user-facing English — never a raw traceback.
    """

    def __init__(self, message: str, transient: bool = False):
        super().__init__(message)
        self.transient = transient


def chat(messages: list, temperature: float = 0.2, timeout: int = 180) -> str:
    """Send a chat history ([{"role": ..., "content": ...}, ...]) and get text.

    Transient failures are retried once after a short backoff.
    """
    try:
        return _chat_once(messages, temperature, timeout)
    except BrainError as e:
        if not e.transient:
            raise
        logger.warning("Brain call failed (transient), retrying once: %s", e)
        time.sleep(RETRY_BACKOFF_SECONDS)
        return _chat_once(messages, temperature, timeout)


def _chat_once(messages: list, temperature: float, timeout: int) -> str:
    if settings.model_provider == "gemini":
        return _chat_gemini(messages, temperature, timeout=90)
    return _chat_ollama(messages, temperature, timeout)


def describe() -> str:
    """Human-readable description of the active brain, for the UI status line."""
    if settings.model_provider == "gemini":
        return f"Gemini ({settings.gemini_model})"
    return f"Ollama ({settings.ollama_model})"


# ---------------------------------------------------------------------------
# Ollama (local)
# ---------------------------------------------------------------------------
def _chat_ollama(messages: list, temperature: float, timeout: int) -> str:
    url = f"{settings.ollama_url}/api/chat"
    try:
        # trust_env=False: Ollama is on localhost — it must never go through
        # a system HTTP proxy, and some proxy configs break httpx parsing.
        with httpx.Client(timeout=timeout, trust_env=False) as client:
            resp = client.post(
                url,
                json={
                    "model": settings.ollama_model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": temperature},
                },
            )
    except httpx.ConnectError:
        raise BrainError(
            f"Couldn't connect to Ollama ({settings.ollama_url}). "
            "Is Ollama running? Open the Ollama app or run 'ollama serve' in the terminal, "
            f"then download the model with 'ollama pull {settings.ollama_model}'. "
            "Or pick the Gemini brain in Settings (⚙️).",
            transient=True,
        )
    except httpx.TimeoutException:
        raise BrainError(
            "Ollama took too long to reply (timeout). "
            "If the model is loading for the first time, wait a bit and try again.",
            transient=True,
        )
    except BrainError:
        raise
    except Exception as e:  # noqa: BLE001 — any transport/config error, cleanly
        logger.exception("Ollama transport error")
        raise BrainError(
            "An error occurred while talking to Ollama. Is Ollama running? "
            "Check by tapping Status in the header.",
            transient=True,
        )

    if resp.status_code == 404:
        raise BrainError(
            f"Model '{settings.ollama_model}' not found in Ollama. "
            f"Run this in the terminal: ollama pull {settings.ollama_model}"
        )
    if resp.status_code >= 500:
        raise BrainError(
            f"Ollama server error ({resp.status_code}). Restart Ollama and "
            "try again.",
            transient=True,
        )
    if resp.status_code != 200:
        raise BrainError(
            f"Ollama error {resp.status_code}. Restart Ollama and try again."
        )

    try:
        return resp.json()["message"]["content"]
    except (KeyError, ValueError):
        logger.warning("Unparseable Ollama response: %s", resp.text[:500])
        raise BrainError(
            "Couldn't understand Ollama's reply. Restart Ollama and try again."
        )


# ---------------------------------------------------------------------------
# Google Gemini (free tier, REST)
# ---------------------------------------------------------------------------
def _to_gemini_contents(messages: list):
    """Convert OpenAI-style messages to Gemini's contents + system instruction."""
    system_text = None
    contents = []
    for msg in messages:
        role = msg.get("role")
        text = msg.get("content", "")
        if role == "system":
            system_text = text
            continue
        # Gemini uses "model" where others use "assistant".
        gemini_role = "model" if role == "assistant" else "user"
        # Gemini requires alternating roles; merge consecutive same-role turns.
        if contents and contents[-1]["role"] == gemini_role:
            contents[-1]["parts"][0]["text"] += "\n\n" + text
        else:
            contents.append({"role": gemini_role, "parts": [{"text": text}]})
    return system_text, contents


def _gemini_reply_text(data: dict):
    """Pull the reply text out of a Gemini generateContent response.

    Returns (text, problem): text is the joined reply (or None), problem is
    None on success or a short reason — "blocked: <reason>" when the safety
    filter refused the prompt (retrying the same prompt won't help), or
    "empty" when the model returned no text (usually transient — worth one
    retry). Gemini sometimes returns 200 with no candidates at all, a
    candidate with finishReason SAFETY and no parts, or parts with no text;
    the old code crashed on all of those and killed the whole task.
    """
    feedback = data.get("promptFeedback") or {}
    block = feedback.get("blockReason")
    if block:
        return None, f"blocked: {block}"
    candidates = data.get("candidates") or []
    if not candidates:
        return None, "empty"
    cand = candidates[0] or {}
    parts = (cand.get("content") or {}).get("parts") or []
    # Gemini 3 thinking models can put a "thought" part first — the reply
    # text lives in the non-thought parts. (The old code read parts[0] only
    # and called every such reply "empty".)
    text = "".join(
        p.get("text", "") for p in parts
        if isinstance(p, dict) and not p.get("thought")
    )
    if text.strip():
        return text, None
    if cand.get("finishReason") == "SAFETY":
        return None, "blocked: SAFETY"
    finish = cand.get("finishReason")
    return None, f"empty (finishReason: {finish})" if finish else "empty"


def _chat_gemini(messages: list, temperature: float, timeout: int) -> str:
    if not settings.gemini_api_key:
        raise BrainError(
            "Gemini API key not set. Open Settings (⚙️) in the app and add a "
            "Gemini key — a free key is available at aistudio.google.com "
            "(needs a Google account, no card). Or pick the Ollama brain in Settings."
        )

    system_text, contents = _to_gemini_contents(messages)
    payload = {
        "contents": contents,
        "generationConfig": {"temperature": temperature},
    }
    if system_text:
        payload["system_instruction"] = {"parts": [{"text": system_text}]}

    # Nudge variant for empty-reply retries: the same conversation plus one
    # short instruction. Re-sending an identical prompt that just came back
    # empty usually fails identically; a slightly different prompt (and,
    # after that, a different model) often breaks through.
    _, nudge_contents = _to_gemini_contents(
        messages + [{"role": "user", "content":
                     "Reply with ONLY the JSON object for the next step — "
                     "no other text."}]
    )
    nudge_payload = dict(payload, contents=nudge_contents)

    # Try the configured model first; if Google says it doesn't exist
    # (404 — free-tier model ids get retired), fall back to the other
    # known free-tier ids and remember whichever one works.
    candidates = [settings.gemini_model] + [
        m for m in GEMINI_FALLBACK_MODELS if m != settings.gemini_model
    ]
    last_404_model = None
    last_problem = None
    for model in candidates:
        url = f"{GEMINI_API_URL}/{model}:generateContent"
        empty_attempts = 0
        while True:
            try:
                # trust_env=False: ignore proxy env vars (same as the Ollama
                # path) — a malformed NO_PROXY entry (e.g. bracketed IPv6)
                # otherwise crashes Client construction before any request.
                with httpx.Client(timeout=timeout, trust_env=False) as client:
                    resp = client.post(
                        url,
                        params={"key": settings.gemini_api_key},
                        # First try: the plain prompt. Retry after an empty
                        # reply: the nudged prompt (see nudge_payload above).
                        json=nudge_payload if empty_attempts else payload,
                    )
            except httpx.ConnectError:
                raise BrainError(
                    "Couldn't connect to the Gemini API. Check your internet.",
                    transient=True,
                )
            except httpx.TimeoutException:
                raise BrainError(
                    "The Gemini API took too long to reply (timeout).",
                    transient=True,
                )
            except BrainError:
                raise
            except Exception as e:  # noqa: BLE001 — any transport/config error, cleanly
                logger.exception("Gemini transport error")
                raise BrainError(
                    "An error occurred while talking to the Gemini API. Check your "
                    "internet and try again.",
                    transient=True,
                )

            if resp.status_code == 404:
                # Model id not found for this key/API version — try the next one.
                logger.warning(
                    "Gemini model %s returned 404; trying next candidate", model
                )
                last_404_model = model
                break
            if resp.status_code == 400:
                raise BrainError(
                    f"Gemini rejected the request (400). The model id "
                    f"'{model}' may no longer be on the free tier — in "
                    "Settings (⚙️), change the Gemini model and try gemini-3.8-flash "
                    "or gemini-3.5-flash-lite."
                )
            if resp.status_code in (401, 403):
                raise BrainError(
                    "The Gemini key looks wrong (auth failed). Enter the correct key "
                    "in Settings (⚙️) — a free key is available at aistudio.google.com."
                )
            if resp.status_code == 429:
                raise BrainError(
                    "Gemini free-tier quota is used up (rate limit). Try again in a "
                    "little while, or pick the Ollama brain in Settings (⚙️).",
                    transient=True,
                )
            if resp.status_code >= 500:
                raise BrainError(
                    f"Gemini server error ({resp.status_code}). Try again in a little while.",
                    transient=True,
                )
            if resp.status_code != 200:
                logger.warning("Gemini unexpected status %s: %s", resp.status_code, resp.text[:300])
                raise BrainError(
                    f"Gemini error {resp.status_code}. Try again in a little while."
                )

            try:
                data = resp.json()
            except ValueError:
                data = {}
            text, problem = _gemini_reply_text(data)
            if text:
                # Success. If a fallback model answered, remember it so the
                # next call goes straight to a model that works.
                if model != settings.gemini_model:
                    logger.info(
                        "Gemini model %s works; saving it as the configured model", model
                    )
                    try:
                        from .config import save_settings

                        save_settings({"gemini_model": model})
                    except Exception:  # noqa: BLE001 — reply matters more than the save
                        logger.exception("Couldn't persist the working Gemini model")
                return text
            if problem and problem.startswith("blocked"):
                # The safety filter refused this exact prompt — an identical
                # retry would be refused too, so don't burn one.
                raise BrainError(
                    "Gemini's safety filter blocked this step. Try the task "
                    "again with slightly different wording."
                )
            # Empty reply with no block reason. First retry: same model,
            # nudged prompt. Still empty: fall through to the next model —
            # an empty reply can be a quirk of one model on one prompt
            # (this used to kill the whole task mid-way, e.g. right after
            # the browser opened a login page).
            logger.warning(
                "Gemini empty reply (model %s, %s): %s",
                model, problem, resp.text[:500],
            )
            empty_attempts += 1
            if empty_attempts > 1:
                last_problem = problem
                break
            logger.warning(
                "Retrying model %s with a nudged prompt", model
            )

    if last_problem:
        raise BrainError(
            f"Gemini's reply was empty on every model ({last_problem}). "
            "Try the task again in a little while.",
            transient=True,
        )
    # Every candidate model 404'd.
    raise BrainError(
        f"Gemini couldn't find any of these models for your key: "
        f"{', '.join(candidates)}. They may have been retired from the free "
        "tier. Open Settings (⚙️) and set a current Gemini model name, or "
        "pick the Ollama brain (works offline, no key)."
    )
