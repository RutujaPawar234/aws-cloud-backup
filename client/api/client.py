"""
API client: the ONLY place the desktop app talks to the backend over HTTPS.

Every method returns either parsed data or raises ApiError with a clean,
user-friendly message (no raw stack traces reach the UI).
"""
from __future__ import annotations

from typing import Any, Optional

import httpx

from client.utils.config import get_backend_url


class ApiError(Exception):
    """A friendly error with a message safe to show the user."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ApiClient:
    """Stateful client that remembers the logged-in user's token."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 60.0) -> None:
        self.base_url = (base_url or get_backend_url()).rstrip("/")
        self.timeout = timeout
        self.token: Optional[str] = None
        self.user: Optional[dict] = None

    # ---- internal helpers -------------------------------------------------
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.request(method, url, headers=self._headers(), **kwargs)
        except (httpx.ConnectError, httpx.ConnectTimeout):
            raise ApiError(
                "Cannot reach the server. Check your internet connection "
                "and that the backend is running."
            )
        except httpx.HTTPError:
            raise ApiError("Network error. Please try again.")

        if resp.status_code >= 400:
            raise ApiError(self._extract_error(resp), resp.status_code)
        return resp

    @staticmethod
    def _extract_error(resp: httpx.Response) -> str:
        try:
            detail = resp.json().get("detail")
            if isinstance(detail, list) and detail:
                return str(detail[0].get("msg", "Invalid request."))
            if detail:
                return str(detail)
        except ValueError:
            pass
        return f"Request failed ({resp.status_code})."

    # ---- health -----------------------------------------------------------
    def health(self) -> dict:
        return self._request("GET", "/health").json()

    # ---- auth -------------------------------------------------------------
    def register(self, full_name: str, email: str, password: str) -> dict:
        resp = self._request(
            "POST",
            "/auth/register",
            json={"full_name": full_name, "email": email, "password": password},
        )
        data = resp.json()
        self.token, self.user = data["access_token"], data["user"]
        return data

    def login(self, email: str, password: str) -> dict:
        resp = self._request(
            "POST", "/auth/login", json={"email": email, "password": password}
        )
        data = resp.json()
        self.token, self.user = data["access_token"], data["user"]
        return data

    def logout(self) -> None:
        self.token = None
        self.user = None

    # ---- files ------------------------------------------------------------
    def upload(self, file_path: str) -> dict:
        import os

        name = os.path.basename(file_path)
        with open(file_path, "rb") as fh:
            files = {"file": (name, fh, "application/octet-stream")}
            resp = self._request("POST", "/files/upload", files=files)
        return resp.json()

    def list_files(self) -> list[dict]:
        return self._request("GET", "/files").json()

    def download(self, file_id: str, save_path: str) -> None:
        resp = self._request("GET", f"/files/{file_id}/download")
        with open(save_path, "wb") as fh:
            fh.write(resp.content)

    def delete(self, file_id: str) -> dict:
        return self._request("DELETE", f"/files/{file_id}").json()
