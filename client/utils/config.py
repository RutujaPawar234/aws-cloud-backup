"""
Client-side configuration: the backend URL and (optionally) a remembered token.

The backend URL comes from, in order:
  1. the BACKEND_URL environment variable (handy after cloud deployment),
  2. a saved client_config.json next to the app,
  3. the default http://127.0.0.1:8000 for local development.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "client_config.json"


def _read() -> dict:
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def _write(data: dict) -> None:
    try:
        _CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError:
        pass  # non-fatal: app still works without a saved config


def get_backend_url() -> str:
    """Return the backend base URL (no trailing slash)."""
    url = os.getenv("BACKEND_URL") or _read().get("backend_url") or DEFAULT_BACKEND_URL
    return url.rstrip("/")


def set_backend_url(url: str) -> None:
    """Persist a chosen backend URL."""
    data = _read()
    data["backend_url"] = url.rstrip("/")
    _write(data)
