"""Captures browser network traffic + console logs while driving the Frappe Cloud
dashboard with Playwright, for API discovery and fixture generation."""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.sync_api import Page, Request, Response, sync_playwright

PRESS_API_PATH_RE = re.compile(r"/api/method/(press\.api\.[a-zA-Z0-9_.]+)")

REDACT_HEADER_KEYS = {"authorization", "cookie", "x-frappe-csrf-token"}


@dataclass
class CapturedCall:
    method_path: str
    http_method: str
    request_payload: Optional[Dict[str, Any]]
    status: int
    response_body: Any
    timestamp: float = field(default_factory=time.time)

    def redacted(self) -> Dict[str, Any]:
        return {
            "method_path": self.method_path,
            "http_method": self.http_method,
            "request_payload": self.request_payload,
            "status": self.status,
            "response_body": self.response_body,
        }


class NetworkCapture:
    """Usage:

        with NetworkCapture(base_url="https://cloud.frappe.io") as capture:
            capture.login(email, password)
            capture.page.goto(f"{capture.base_url}/dashboard/sites")
            capture.page.wait_for_selector("text=New Site")
        capture.save("discovery/captures/sites_list.json")
    """

    def __init__(self, base_url: str = "https://cloud.frappe.io", headless: bool = True):
        self.base_url = base_url.rstrip("/")
        self.headless = headless
        self.calls: List[CapturedCall] = []
        self.console_errors: List[str] = []
        self._playwright = None
        self._browser = None
        self._context = None
        self.page: Optional[Page] = None

    def __enter__(self) -> "NetworkCapture":
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context()
        self.page = self._context.new_page()
        self.page.on("response", self._on_response)
        self.page.on("console", self._on_console)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def _on_console(self, msg) -> None:
        if msg.type == "error":
            self.console_errors.append(msg.text)

    def _on_response(self, response: Response) -> None:
        request: Request = response.request
        match = PRESS_API_PATH_RE.search(request.url)
        if not match:
            return
        method_path = match.group(1)
        try:
            payload = request.post_data_json
        except Exception:
            payload = None
        try:
            body = response.json()
        except Exception:
            body = None
        self.calls.append(
            CapturedCall(
                method_path=method_path,
                http_method=request.method,
                request_payload=payload,
                status=response.status,
                response_body=body,
            )
        )

    def login(self, email: str, password: str) -> None:
        assert self.page is not None
        self.page.goto(f"{self.base_url}/dashboard/login")
        self.page.click("text=Continue with password")
        self.page.fill('input[type="email"]', email)
        self.page.fill('input[type="password"]', password)
        self.page.click('button:has-text("Log In")')
        self.page.wait_for_selector("text=Sites", timeout=15000)

    def save(self, path: str) -> None:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(
                {
                    "calls": [c.redacted() for c in self.calls],
                    "console_errors": self.console_errors,
                },
                indent=2,
                default=str,
            )
        )
