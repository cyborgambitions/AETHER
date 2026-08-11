"""
AETHER xAI Grok Client
Async proxy to xAI chat completions endpoint.
Sends a minimal OpenAI-compatible payload: model + cleaned messages only.
"""

import os
import re
import time
import httpx
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

XAI_BASE_URL = "https://api.x.ai/v1"

# Prefer grok-4.5; fall back if a key cannot access a given id
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "grok-4.5")

MODEL_FALLBACKS: List[str] = [
    "grok-4.5",
    "grok-4.3",
    "grok-4.20-0309-non-reasoning",
    "grok-4.20-0309-reasoning",
]

# Values that look like keys but are docs / templates — never send these
_PLACEHOLDER_KEY_RE = re.compile(
    r"(replace|your[_-]?key|paste|example|xxxx|sk_live_or_test|dummy|changeme|todo)",
    re.IGNORECASE,
)


def sanitize_api_key(raw: Optional[str]) -> str:
    """Strip quotes, Bearer prefix, and whitespace from a pasted/env key."""
    if not raw:
        return ""
    key = str(raw).strip()
    # BOM / zero-width / newlines from Windows paste / Out-File
    key = key.lstrip("\ufeff").strip()
    key = key.replace("\r", "").replace("\n", "").strip()
    if (key.startswith('"') and key.endswith('"')) or (
        key.startswith("'") and key.endswith("'")
    ):
        key = key[1:-1].strip()
    if key.lower().startswith("bearer "):
        key = key[7:].strip()
    return key


def _looks_like_placeholder_key(key: str) -> bool:
    if not key:
        return True
    if _PLACEHOLDER_KEY_RE.search(key):
        return True
    # Real console keys are longer than short templates like xai-your-key-here
    if key.startswith("xai-") and len(key) < 20:
        return True
    return False


def _extract_error_message(resp: httpx.Response) -> str:
    """Pull a human-readable error from xAI / OpenAI-style error JSON."""
    try:
        data = resp.json()
    except Exception:
        text = (resp.text or "").strip()
        return text[:500] if text else f"HTTP {resp.status_code}"

    # xAI format: {"code":"invalid-argument","error":"Model not found: ..."}
    err = data.get("error")
    code = data.get("code")
    if isinstance(err, dict):
        msg = err.get("message") or err.get("error") or str(err)
        code = err.get("code") or err.get("type") or code
        return f"{msg}" + (f" ({code})" if code else "")
    if isinstance(err, str):
        return f"{err}" + (f" ({code})" if code else "")
    if data.get("message"):
        return str(data["message"]) + (f" ({code})" if code else "")
    return str(data)[:500]


def _is_credits_error(status: int, message: str) -> bool:
    """True when the key is valid but the team is out of credits / spend limit."""
    lower = (message or "").lower()
    credit_tokens = (
        "used all available credits",
        "available credits",
        "spending limit",
        "monthly spending",
        "purchase more credits",
        "raise your spending limit",
        "insufficient credits",
        "out of credits",
        "quota exceeded",
        "billing",
        "payment required",
    )
    if any(t in lower for t in credit_tokens):
        return True
    # Some gateways use 402 Payment Required
    if status == 402:
        return True
    return False


def _is_auth_error(status: int, message: str) -> bool:
    """True when xAI rejected the API key itself (not credits)."""
    if _is_credits_error(status, message or ""):
        return False
    if status in (401,):
        return True
    lower = (message or "").lower()
    # 403 is often credits or permission — only treat as bad key when wording says so
    auth_tokens = (
        "incorrect api key",
        "invalid api key",
        "invalid_api_key",
        "api key provided",
        "unauthorized",
        "authentication",
        "not authorized",
        "invalid or unauthorized",
    )
    if any(t in lower for t in auth_tokens):
        return True
    if status == 403 and "permission-denied" in lower and not _is_credits_error(403, lower):
        # Generic 403 without credit language still often means key/team access
        if "api key" in lower or "unauthorized" in lower:
            return True
    return False


def _is_model_error(status: int, message: str) -> bool:
    """True when the request failed because of the model id (not auth/credits)."""
    if status != 400:
        return False
    if _is_auth_error(status, message) or _is_credits_error(status, message):
        return False
    lower = message.lower()
    # Avoid bare "invalid" — xAI uses code "invalid-argument" for many errors,
    # including bad API keys, which must not trigger model fallbacks.
    return any(
        token in lower
        for token in (
            "model not found",
            "model_not_found",
            "does not exist",
            "unknown model",
            "unsupported model",
            "invalid model",
            "no such model",
        )
    )


def _auth_error_message(detail: str = "") -> str:
    base = (
        "Invalid or unauthorized xAI API key. "
        "Get a real key at https://console.x.ai (must start with 'xai-'), "
        "then either: (1) click Connect Key in AETHER and paste it, or "
        "(2) set XAI_API_KEY on Render / in backend/.env and redeploy/restart. "
        "Do not use placeholders like xai-REPLACE_... or sk_ keys. "
        "Free grok.com chat accounts do not work for the API."
    )
    if detail:
        return f"{base} Details: {detail}"
    return base


def _credits_error_message(detail: str = "") -> str:
    base = (
        "xAI API key is valid, but your team is out of credits or hit its spending limit. "
        "Open https://console.x.ai → Billing / Credits, purchase more credits or raise the monthly limit, "
        "then try again. (This is not a bug in AETHER.)"
    )
    if detail:
        return f"{base} Details: {detail}"
    return base


def clean_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Keep only valid chat turns:
      - role present
      - content is a non-empty string
    """
    cleaned: List[Dict[str, str]] = []
    for m in messages or []:
        if not m or not isinstance(m, dict):
            continue
        role = m.get("role")
        content = m.get("content")
        if not role or not isinstance(content, str):
            continue
        text = content.strip()
        if not text:
            continue
        cleaned.append({"role": str(role), "content": text})
    return cleaned


def _messages_from_prompt(prompt: str) -> List[Dict[str, str]]:
    text = (prompt or "").strip()
    if not text:
        return []
    return [{"role": "user", "content": text}]


async def call_grok(
    prompt: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    messages: Optional[List[Dict[str, Any]]] = None,
    # Kept for API compatibility with main.py / UI — not sent to xAI
    max_tokens: int = 2048,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """
    Call xAI Grok with a minimal payload:
      { "model": "...", "messages": [ { role, content }, ... ] }

    No max_tokens / temperature / stream — some Grok 4 endpoints 400 on extras.
    """
    key = sanitize_api_key(api_key or os.getenv("XAI_API_KEY") or "")
    if not key:
        raise ValueError(
            "No xAI API key provided. Pass api_key or set XAI_API_KEY in environment. "
            "Get a key at https://console.x.ai"
        )
    if _looks_like_placeholder_key(key):
        raise ValueError(
            "XAI_API_KEY looks like a placeholder (e.g. xai-REPLACE_...), not a real console key. "
            "Create a key at https://console.x.ai and set it on Render (Environment → XAI_API_KEY) "
            "or paste it via Connect Key in the app."
        )
    if not key.startswith("xai-"):
        raise ValueError(
            "xAI API keys must start with 'xai-'. "
            "OpenAI/Stripe keys (sk-...) will not work. Get a key at https://console.x.ai"
        )

    if messages is not None:
        clean = clean_messages(messages)
    else:
        clean = _messages_from_prompt(prompt or "")

    if not clean:
        raise ValueError(
            "No valid messages to send. Each message needs a role and non-empty string content."
        )

    requested = (model or DEFAULT_MODEL or "grok-4.5").strip()
    candidates: List[str] = []
    for m in [requested] + MODEL_FALLBACKS:
        if m and m not in candidates:
            candidates.append(m)

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    start = time.time()
    last_error = "Unknown error"
    used_model = requested
    data: Dict[str, Any] = {}

    async with httpx.AsyncClient(timeout=120.0) as client:
        for idx, candidate in enumerate(candidates):
            # Minimal payload only — matches known-good client pattern
            payload = {
                "model": candidate,
                "messages": clean,
            }

            resp = await client.post(
                f"{XAI_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )

            if resp.status_code == 429:
                raise ValueError(
                    "xAI rate limit hit (429). Wait a moment and try again, or check your credits at console.x.ai."
                )

            if resp.is_success:
                data = resp.json()
                used_model = candidate
                break

            message = _extract_error_message(resp)
            last_error = f"HTTP {resp.status_code}: {message}"

            # Credits / spend limit: stop immediately (key is fine)
            if _is_credits_error(resp.status_code, message):
                raise ValueError(_credits_error_message(last_error))

            # Bad key: stop immediately (do not cycle models)
            if _is_auth_error(resp.status_code, message):
                raise ValueError(_auth_error_message(last_error))

            # Only retry other model ids on genuine model-name failures
            if _is_model_error(resp.status_code, message) and idx < len(candidates) - 1:
                continue

            raise ValueError(
                f"Grok API error — {last_error}. "
                f"Tried model '{candidate}'. "
                "If this is a model name issue, set DEFAULT_MODEL to one of: "
                + ", ".join(MODEL_FALLBACKS[:3])
            )
        else:
            raise ValueError(
                f"Grok API error — {last_error}. "
                f"No working model found. Available fallbacks: {', '.join(MODEL_FALLBACKS)}"
            )

    duration = int((time.time() - start) * 1000)

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        content = None

    if content is None:
        try:
            msg = data["choices"][0]["message"]
            content = msg.get("reasoning_content") or msg.get("refusal") or str(msg)
        except Exception:
            content = str(data)

    return {
        "output": content if isinstance(content, str) else str(content),
        "model": used_model,
        "usage": data.get("usage"),
        "duration_ms": duration,
        "raw": data,
    }
