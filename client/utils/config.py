"""
Client-side configuration: the backend URL and (optionally) a remembered token.

The backend URL comes from, in order:
  1. the BACKEND_URL environment variable,
  2. a client_config.json next to the app (for the packaged .exe, this file
     sits beside CloudVault.exe so you can change the server without rebuilding),
  3. the default deployed backend below.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Default = the deployed EC2 backend. Change this (or client_config.json) if the
# server's address changes (e.g. after allocating an Elastic IP).
DEFAULT_BACKEND_URL = "http://16.178.22.30:8000"


def _config_path() -> Path:
    """Where client_config.json lives: next to the .exe when frozen, else client/."""
    if getattr(sys, "frozen", False):          # running as a PyInstaller .exe
        return Path(sys.executable).resolve().parent / "client_config.json"
    return Path(__file__).resolve().parent.parent / "client_config.json"


_CONFIG_PATH = _config_path()


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
