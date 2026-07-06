"""
AETHER Database Layer
Simple SQLite persistence for:
- Community prompts (user contributed templates)
- Research sessions (history of generations)
- Votes / popularity
"""

import sqlite3
import os
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

# Support DATABASE_PATH env var (used on Render with persistent disk)
_db_env = os.getenv("DATABASE_PATH")
DB_PATH_DEFAULT = Path(_db_env) if _db_env else (Path(__file__).parent.parent / "data" / "aether.db")

@contextmanager
def get_conn(db_path: Optional[Path] = None):
    path = db_path or DB_PATH_DEFAULT
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db(db_path: Optional[Path] = None):
    with get_conn(db_path) as conn:
        cur = conn.cursor()
        # Community / custom prompts
        cur.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                template TEXT NOT NULL,
                placeholder_hint TEXT,
                author TEXT,
                votes INTEGER DEFAULT 0,
                uses INTEGER DEFAULT 0,
                created_at INTEGER NOT NULL,
                is_core INTEGER DEFAULT 0
            )
        """)
        # Research / generation sessions
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                prompt_id TEXT,
                prompt_title TEXT,
                input_text TEXT NOT NULL,
                output_text TEXT NOT NULL,
                model TEXT,
                filled_prompt TEXT,
                duration_ms INTEGER,
                created_at INTEGER NOT NULL
            )
        """)
        # Simple vote log (to allow light anti-spam in future)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id TEXT NOT NULL,
                session_id TEXT,
                voter_hash TEXT,
                created_at INTEGER NOT NULL
            )
        """)
        conn.commit()

def _gen_id(prefix: str = "p") -> str:
    return f"{prefix}_{int(time.time()*1000)}_{hex(hash(str(time.time())))[2:8]}"

# ---- Prompts ----

def list_prompts(db_path: Optional[Path] = None, include_core: bool = True) -> List[Dict[str, Any]]:
    init_db(db_path)
    prompts = []
    if include_core:
        from .prompts import get_all_core_prompt_dicts
        for p in get_all_core_prompt_dicts():
            p = p.copy()
            p["uses"] = 0   # will be incremented via sessions
            p["votes"] = 0
            prompts.append(p)

    with get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM prompts ORDER BY votes DESC, created_at DESC"
        ).fetchall()
        for r in rows:
            d = dict(r)
            d["is_core"] = bool(d.get("is_core", 0))
            prompts.append(d)
    return prompts

def get_prompt(prompt_id: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    init_db(db_path)
    # First check core
    from .prompts import get_prompt_by_id
    core = get_prompt_by_id(prompt_id)
    if core:
        d = core.model_dump()
        d["votes"] = 0
        d["uses"] = 0
        return d

    with get_conn(db_path) as conn:
        row = conn.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,)).fetchone()
        if row:
            d = dict(row)
            d["is_core"] = bool(d.get("is_core", 0))
            return d
    return None

def create_community_prompt(data: Dict[str, Any], db_path: Optional[Path] = None) -> Dict[str, Any]:
    init_db(db_path)
    pid = data.get("id") or _gen_id("community")
    now = int(time.time())
    with get_conn(db_path) as conn:
        conn.execute("""
            INSERT INTO prompts (id, title, category, description, template, placeholder_hint, author, votes, uses, created_at, is_core)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?, 0)
        """, (
            pid,
            data["title"],
            data.get("category", "community"),
            data.get("description", ""),
            data["template"],
            data.get("placeholder_hint", "Enter input"),
            data.get("author"),
            now,
        ))
        conn.commit()
    return get_prompt(pid, db_path)  # type: ignore

def increment_prompt_uses(prompt_id: str, db_path: Optional[Path] = None):
    init_db(db_path)
    with get_conn(db_path) as conn:
        conn.execute("UPDATE prompts SET uses = uses + 1 WHERE id = ?", (prompt_id,))
        conn.commit()

def vote_prompt(prompt_id: str, voter_hash: Optional[str] = None, db_path: Optional[Path] = None) -> int:
    init_db(db_path)
    now = int(time.time())
    with get_conn(db_path) as conn:
        # Only increment votes for community prompts (core stay inspirational)
        conn.execute("UPDATE prompts SET votes = votes + 1 WHERE id = ?", (prompt_id,))
        conn.execute(
            "INSERT INTO votes (prompt_id, voter_hash, created_at) VALUES (?, ?, ?)",
            (prompt_id, voter_hash or "anon", now)
        )
        conn.commit()
        row = conn.execute("SELECT votes FROM prompts WHERE id = ?", (prompt_id,)).fetchone()
        return row["votes"] if row else 0

# ---- Sessions ----

def save_session(data: Dict[str, Any], db_path: Optional[Path] = None) -> Dict[str, Any]:
    init_db(db_path)
    sid = data.get("id") or _gen_id("sess")
    now = int(time.time())
    with get_conn(db_path) as conn:
        conn.execute("""
            INSERT INTO sessions (id, prompt_id, prompt_title, input_text, output_text, model, filled_prompt, duration_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sid,
            data.get("prompt_id"),
            data.get("prompt_title"),
            data.get("input_text", ""),
            data.get("output_text", ""),
            data.get("model"),
            data.get("filled_prompt"),
            data.get("duration_ms"),
            now,
        ))
        conn.commit()
    return get_session(sid, db_path)

def get_session(sid: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    init_db(db_path)
    with get_conn(db_path) as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (sid,)).fetchone()
        return dict(row) if row else None

def list_sessions(limit: int = 50, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    init_db(db_path)
    with get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]