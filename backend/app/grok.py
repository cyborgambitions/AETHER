"""
AETHER xAI Grok Client
Async proxy to xAI chat completions endpoint.
Compatible with OpenAI client style (xAI uses OpenAI-compatible API).
"""

import os
import time
import httpx
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

XAI_BASE_URL = "https://api.x.ai/v1"
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "grok-3")

async def call_grok(
    prompt: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    max_tokens: int = 2048,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """
    Call xAI Grok. Returns dict with:
      { "output": str, "model": str, "usage": {... or None}, "raw": ... }
    """
    key = api_key or os.getenv("XAI_API_KEY")
    if not key:
        raise ValueError("No xAI API key provided. Pass api_key or set XAI_API_KEY in environment.")

    model = model or DEFAULT_MODEL
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }

    start = time.time()
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{XAI_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
        )

        if resp.status_code == 401 or resp.status_code == 403:
            raise ValueError(
                "Invalid or unauthorized xAI API key (403/401). "
                "Get a key at https://console.x.ai, then click the key icon in AETHER and paste it. "
                "Keys must start with 'xai-'. Free grok.com accounts do not work for the API."
            )

        resp.raise_for_status()
        data = resp.json()

    duration = int((time.time() - start) * 1000)

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        content = str(data)

    usage = data.get("usage")

    return {
        "output": content,
        "model": model,
        "usage": usage,
        "duration_ms": duration,
        "raw": data,  # for debugging / advanced clients
    }