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

# One retry after a short pause, for errors that are usually temporary
# (network hiccup, model still loading, rate limit). Permanent errors
# (no key, unknown model, bad request) are never retried.
RETRY_BACKOFF_SECONDS = 1.5


class BrainError(Exception):
    """Raised when the model cannot be reached or refuses the request.

    `transient=True` means "worth retrying once" (network/timeout/5xx/429).
    The message is always user-facing Hinglish — never a raw traceback.
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
            f"Ollama se connect nahi ho paya ({settings.ollama_url}). "
            "Ollama chal raha hai? Ollama app kholo ya terminal me 'ollama serve' chalao, "
            f"phir 'ollama pull {settings.ollama_model}' se model download karo. "
            "Ya Settings (⚙️) me Gemini brain chuno.",
            transient=True,
        )
    except httpx.TimeoutException:
        raise BrainError(
            "Ollama ne jawab dene me bahut der kar di (timeout). "
            "Model pehli baar load ho raha ho toh thoda wait karke dobara try karo.",
            transient=True,
        )
    except BrainError:
        raise
    except Exception as e:  # noqa: BLE001 — any transport/config error, cleanly
        logger.exception("Ollama transport error")
        raise BrainError(
            "Ollama se baat karte waqt error aaya. Ollama chal raha hai? "
            "Header me Status dabake check karo.",
            transient=True,
        )

    if resp.status_code == 404:
        raise BrainError(
            f"Model '{settings.ollama_model}' Ollama me nahi mila. "
            f"Terminal me ye chalao: ollama pull {settings.ollama_model}"
        )
    if resp.status_code >= 500:
        raise BrainError(
            f"Ollama server error ({resp.status_code}). Ollama restart karke "
            "dobara try karo.",
            transient=True,
        )
    if resp.status_code != 200:
        raise BrainError(
            f"Ollama error {resp.status_code}. Ollama restart karke dobara try karo."
        )

    try:
        return resp.json()["message"]["content"]
    except (KeyError, ValueError):
        logger.warning("Unparseable Ollama response: %s", resp.text[:500])
        raise BrainError(
            "Ollama ka jawab samajh nahi aaya. Ollama restart karke dobara try karo."
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


def _chat_gemini(messages: list, temperature: float, timeout: int) -> str:
    if not settings.gemini_api_key:
        raise BrainError(
            "Gemini API key set nahi hai. App me Settings (⚙️) kholo, Gemini key "
            "daalo — free key aistudio.google.com se milti hai (Google account "
            "chahiye, card nahi). Ya Settings me Ollama brain chuno."
        )

    system_text, contents = _to_gemini_contents(messages)
    payload = {
        "contents": contents,
        "generationConfig": {"temperature": temperature},
    }
    if system_text:
        payload["system_instruction"] = {"parts": [{"text": system_text}]}

    url = f"{GEMINI_API_URL}/{settings.gemini_model}:generateContent"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(
                url,
                params={"key": settings.gemini_api_key},
                json=payload,
            )
    except httpx.ConnectError:
        raise BrainError(
            "Gemini API se connect nahi ho paya. Internet check karo.",
            transient=True,
        )
    except httpx.TimeoutException:
        raise BrainError(
            "Gemini API ne jawab dene me bahut der kar di (timeout).",
            transient=True,
        )
    except BrainError:
        raise
    except Exception as e:  # noqa: BLE001 — any transport/config error, cleanly
        logger.exception("Gemini transport error")
        raise BrainError(
            "Gemini API se baat karte waqt error aaya. Internet check karke "
            "dobara try karo.",
            transient=True,
        )

    if resp.status_code == 400:
        raise BrainError(
            f"Gemini ne request reject kar di (400). Ho sakta hai model id "
            f"'{settings.gemini_model}' ab free tier pe na ho — Settings (⚙️) me "
            "Gemini model badal ke gemini-3.8-flash ya gemini-3.5-flash-lite try karo."
        )
    if resp.status_code in (401, 403):
        raise BrainError(
            "Gemini key galat lag rahi hai (auth fail). Settings (⚙️) me sahi "
            "key daalo — free key aistudio.google.com se milti hai."
        )
    if resp.status_code == 429:
        raise BrainError(
            "Gemini free-tier quota khatam ho gaya (rate limit). Thodi der baad "
            "try karo, ya Settings (⚙️) me Ollama brain chuno.",
            transient=True,
        )
    if resp.status_code >= 500:
        raise BrainError(
            f"Gemini server error ({resp.status_code}). Thodi der baad dobara try karo.",
            transient=True,
        )
    if resp.status_code != 200:
        logger.warning("Gemini unexpected status %s: %s", resp.status_code, resp.text[:300])
        raise BrainError(
            f"Gemini error {resp.status_code}. Thodi der baad dobara try karo."
        )

    try:
        candidates = resp.json()["candidates"]
        return candidates[0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, ValueError):
        raise BrainError(
            "Gemini ka jawab khaali tha (shayad safety filter ne roka). "
            "Task ko dobara, thoda alag wording me try karo."
        )
