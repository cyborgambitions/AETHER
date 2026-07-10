"""
AETHER xAI Grok Client
Async proxy to xAI chat completions endpoint.
Sends a minimal OpenAI-compatible payload: model + cleaned messages only.
"""

import os
import time
import httpx
from typing import Optional, Dict, Any, List, Union
from dotenv import load_dotenv

load_dotenv()

XAI_BASE_URL = "https://api.x.ai/v1"

# Prefer grok-4.5; fall back if a key cannot access it
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "grok-4.5")

MODEL_FALLBACKS: List[str] = [
    "grok-4.5",
    "grok-4.3",
    "grok-4.20-0309-non-reasoning",
    "grok-4.20-0309-reasoning",
]


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


def _is_model_error(status: int, message: str) -> bool:
    if status != 400:
        return False
    lower = message.lower()
    return any(
        token in lower
        for token in (
            "model",
            "does not exist",
            "not found",
            "invalid",
            "unsupported",
            "unknown",
        )
    )


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
    key = (api_key or os.getenv("XAI_API_KEY") or "").strip()
    if not key:
        raise ValueError(
            "No xAI API key provided. Pass api_key or set XAI_API_KEY in environment. "
            "Get a key at https://console.x.ai"
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

            if resp.status_code in (401, 403):
                raise ValueError(
                    "Invalid or unauthorized xAI API key (401/403). "
                    "Get a key at https://console.x.ai, then click the key icon in AETHER and paste it. "
                    "Keys must start with 'xai-'. Free grok.com chat accounts do not work for the API."
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
