"""
AETHER Backend
FastAPI server for the First Principles Toolkit.

Features:
- Serves the 6 canonical prompts + community contributed prompts
- Generates deep reasoning via xAI Grok (with optional bring-your-own-key)
- Persists research sessions and community prompts + votes
- Lightweight SPA frontend served at /
"""

import os
import time
import uuid
from typing import Optional, List, Dict, Any
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

import stripe
from . import prompts as prompt_lib
from . import database as db
from .grok import call_grok, DEFAULT_MODEL, sanitize_api_key

# Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PRO_PRICE_ID = os.getenv("STRIPE_PRO_PRICE_ID", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8000")

# ------------- Models -------------

class GenerateRequest(BaseModel):
    prompt_id: Optional[str] = Field(None, description="ID of a core or community prompt")
    custom_prompt: Optional[str] = Field(None, description="Raw prompt text (overrides prompt_id)")
    input_text: str = Field(..., description="The user's topic/claim/question to fill into template")
    model: Optional[str] = Field(None, description="xAI model override, e.g. grok-4.5")
    api_key: Optional[str] = Field(None, description="Bring your own xAI API key (recommended for production use)")
    temperature: float = 0.7
    use_hosted: bool = Field(False, description="Use server-hosted key (Pro feature)")
    checkout_session_id: Optional[str] = Field(None, description="Stripe Checkout session proving Pro")

class GenerateResponse(BaseModel):
    output: str
    model: str
    session_id: str
    duration_ms: Optional[int] = None
    prompt_title: Optional[str] = None

class CommunityPromptCreate(BaseModel):
    title: str
    template: str
    description: Optional[str] = ""
    category: str = "community"
    placeholder_hint: str = "Enter your input"
    author: Optional[str] = None

class VoteRequest(BaseModel):
    prompt_id: str

class SessionOut(BaseModel):
    id: str
    prompt_id: Optional[str]
    prompt_title: Optional[str]
    input_text: str
    output_text: str
    model: Optional[str]
    created_at: int

# ------------- App -------------

app = FastAPI(
    title="AETHER API",
    description="Backend for the Grok First-Principles Toolkit. Built to amplify truth-seeking and discovery.",
    version="0.1.0",
)

# CORS
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins] if cors_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
static_dir = Path(__file__).parent.parent / "static"
static_dir.mkdir(exist_ok=True)

@app.on_event("startup")
def startup():
    db.init_db()
    print("AETHER backend ready. Database initialized.")

# ------------- Routes -------------

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "aether",
        "time": int(time.time()),
        "hosted_key_configured": bool(os.getenv("XAI_API_KEY")),
        "stripe_configured": bool(stripe.api_key and STRIPE_PRO_PRICE_ID),
    }

@app.get("/api/prompts")
def list_prompts(include_core: bool = True):
    """Return all prompts (core + community) sorted by popularity."""
    return {"prompts": db.list_prompts(include_core=include_core)}

@app.get("/api/prompts/{prompt_id}")
def get_prompt(prompt_id: str):
    p = db.get_prompt(prompt_id)
    if not p:
        raise HTTPException(404, "Prompt not found")
    return p

@app.post("/api/prompts")
def create_prompt(payload: CommunityPromptCreate):
    """Submit a new community prompt template."""
    if not payload.title or not payload.template:
        raise HTTPException(400, "title and template are required")
    created = db.create_community_prompt(payload.model_dump())
    return created

@app.post("/api/prompts/{prompt_id}/vote")
def vote_prompt(prompt_id: str):
    """Upvote a community prompt."""
    new_votes = db.vote_prompt(prompt_id)
    return {"prompt_id": prompt_id, "votes": new_votes}

@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """
    Core endpoint. Fills a prompt template (or uses custom) then calls Grok.
    Returns the reasoning + stores a session.
    """
    start = time.time()

    filled = None
    prompt_title = None
    prompt_id = req.prompt_id

    # Determine which key to use
    effective_api_key = sanitize_api_key(req.api_key)
    if req.use_hosted:
        if stripe.api_key and STRIPE_PRO_PRICE_ID:
            if not _checkout_is_pro(req.checkout_session_id):
                raise HTTPException(402, "Hosted Pro requires an active AETHER subscription.")
        server_key = sanitize_api_key(os.getenv("XAI_API_KEY"))
        if server_key:
            effective_api_key = server_key
            prompt_title = (prompt_title or "Hosted Pro") + " (Server)"
        else:
            raise HTTPException(402, "Hosted mode requires server configuration. Use your own key or upgrade.")

    if req.custom_prompt:
        filled = req.custom_prompt
        if "{input}" in filled:
            filled = filled.replace("{input}", req.input_text)
        prompt_title = prompt_title or "Custom Prompt"
    elif req.prompt_id:
        p = db.get_prompt(req.prompt_id)
        if not p:
            raise HTTPException(404, f"Prompt {req.prompt_id} not found")
        template = p.get("template") or p.get("text", "")
        filled = prompt_lib.fill_template(template, req.input_text)
        prompt_title = prompt_title or p.get("title")
        # increment uses for community prompts
        if not p.get("is_core"):
            db.increment_prompt_uses(req.prompt_id)
    else:
        raise HTTPException(400, "Either prompt_id or custom_prompt must be provided")

    if not filled or not str(filled).strip():
        raise HTTPException(400, "Resolved prompt is empty. Provide input text and a mode.")

    # Prefer client key, then server env; sanitize whitespace / quotes / Bearer prefix
    if not effective_api_key:
        effective_api_key = sanitize_api_key(os.getenv("XAI_API_KEY")) or None

    try:
        result = await call_grok(
            prompt=filled,
            model=req.model,
            api_key=effective_api_key,
            temperature=req.temperature or 0.7,
        )
    except ValueError as e:
        # Auth / config / model issues — show clean message to UI
        raise HTTPException(502, str(e))
    except Exception as e:
        raise HTTPException(502, f"Grok call failed: {str(e)}")

    duration_ms = result.get("duration_ms") or int((time.time() - start) * 1000)

    # Persist session
    session = db.save_session({
        "prompt_id": prompt_id,
        "prompt_title": prompt_title,
        "input_text": req.input_text,
        "output_text": result["output"],
        "model": result["model"],
        "filled_prompt": filled,
        "duration_ms": duration_ms,
    })

    return GenerateResponse(
        output=result["output"],
        model=result["model"],
        session_id=session["id"],
        duration_ms=duration_ms,
        prompt_title=prompt_title,
    )

@app.get("/api/sessions", response_model=List[SessionOut])
def list_sessions(limit: int = Query(30, le=200)):
    rows = db.list_sessions(limit=limit)
    return [
        SessionOut(
            id=r["id"],
            prompt_id=r.get("prompt_id"),
            prompt_title=r.get("prompt_title"),
            input_text=r["input_text"],
            output_text=r["output_text"],
            model=r.get("model"),
            created_at=r["created_at"],
        )
        for r in rows
    ]

@app.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    s = db.get_session(session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    return s

# ------------- Monetization (Stripe) + Quotas -------------

class CheckoutRequest(BaseModel):
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


def _checkout_is_pro(session_id: Optional[str]) -> bool:
    if not session_id or not stripe.api_key:
        return False
    try:
        sess = stripe.checkout.Session.retrieve(session_id)
    except Exception:
        return False
    paid = sess.get("payment_status") in ("paid", "no_payment_required")
    complete = sess.get("status") == "complete"
    return bool(paid or complete)


@app.post("/api/create-checkout-session")
async def create_checkout_session(req: CheckoutRequest):
    """Create a Stripe Checkout session for AETHER Pro."""
    if not stripe.api_key or not STRIPE_PRO_PRICE_ID:
        raise HTTPException(503, "Stripe is not configured. Set STRIPE_SECRET_KEY and STRIPE_PRO_PRICE_ID on the server.")

    origin = (FRONTEND_URL or "").rstrip("/")
    success_url = req.success_url or f"{origin}/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = req.cancel_url or f"{origin}/#pricing"
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": STRIPE_PRO_PRICE_ID,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"product": "aether-pro"},
            allow_promotion_codes=True,
        )
        return {"url": session.url, "id": session.id, "configured": True}
    except Exception as e:
        raise HTTPException(400, f"Stripe error: {str(e)}")


@app.get("/api/billing/verify")
def verify_billing(session_id: str = Query(...)):
    """Confirm a Checkout session actually paid before unlocking Pro in the browser."""
    if not stripe.api_key:
        raise HTTPException(503, "Stripe is not configured.")
    if not _checkout_is_pro(session_id):
        return {"pro": False, "session_id": session_id}
    return {"pro": True, "session_id": session_id}


@app.get("/success", response_class=HTMLResponse)
def success():
    """Post-checkout landing. Browser verifies the session with Stripe before unlocking Pro."""
    html = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>AETHER · Access</title>
<style>
  html,body{margin:0;min-height:100%;background:#02040a;color:#e8eef4;font-family:system-ui,sans-serif;display:flex;align-items:center;justify-content:center}
  .box{max-width:28rem;padding:2.5rem;text-align:center}
  h1{font-weight:400;font-size:1.75rem;letter-spacing:-0.02em}
  p{color:rgba(255,255,255,.55);line-height:1.6}
  a{color:#8ad4ff}
</style>
</head><body>
<div class="box">
  <p style="letter-spacing:3px;font-size:12px;color:#8ad4ff">ACCESS</p>
  <h1 id="t">Confirming orbit…</h1>
  <p id="s">Checking payment with Stripe.</p>
</div>
<script>
(async function () {
  const params = new URLSearchParams(location.search);
  const sessionId = params.get('session_id');
  const t = document.getElementById('t');
  const s = document.getElementById('s');
  if (!sessionId) {
    t.textContent = 'No session.';
    s.innerHTML = '<a href="/#pricing">Return to Access</a>';
    return;
  }
  try {
    const r = await fetch('/api/billing/verify?session_id=' + encodeURIComponent(sessionId));
    const data = await r.json();
    if (data.pro) {
      localStorage.setItem('aether_pro', 'true');
      localStorage.setItem('aether_checkout_session', sessionId);
      t.textContent = 'Pro is live.';
      s.textContent = 'Hosted runs are unlocked. Returning to the deck.';
      setTimeout(function () { location.href = '/'; }, 1400);
    } else {
      t.textContent = 'Payment not confirmed.';
      s.innerHTML = '<a href="/#pricing">Try Access again</a>';
    }
  } catch (e) {
    t.textContent = 'Could not verify.';
    s.innerHTML = '<a href="/#pricing">Return to Access</a>';
  }
})();
</script>
</body></html>"""
    return html

@app.get("/api/usage")
def get_usage():
    """Simple daily usage info for frontend (demo quota)."""
    # In production you would track per user/IP
    return {"daily_limit": 50, "used": 0, "is_pro": False}  # Client overrides with localStorage pro

# ------------- Frontend (served at root) -------------

NO_CACHE = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}

@app.middleware("http")
async def disable_html_cache(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.endswith(".html"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response

@app.get("/", response_class=HTMLResponse)
def index():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return HTMLResponse(
            content=index_file.read_text(encoding="utf-8"),
            headers=NO_CACHE,
        )
    return """
    <html><head><title>AETHER</title></head><body>
    <h1>AETHER Backend is running.</h1>
    <p>Visit <a href="/static/index.html">/static/index.html</a> once the frontend is built, or POST to /api/generate.</p>
    <p>See <a href="/docs">/docs</a> for interactive API explorer.</p>
    </body></html>
    """

# Static assets (if you add extra css/js later)
# Mounted last so API + root routes have priority
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
