"""Pluggable authentication strategies for FrappeCloudClient.

ApiKeyAuth is the default, unchanged behavior (Authorization: token key:secret header).
BrowserSessionAuth is an alternate strategy that authenticates via a browser session
(username/password login) and reuses the resulting cookies + CSRF header, as a fallback for
avoiding API rate limits or when API keys aren't available. It requires Playwright and is only
imported lazily (inside a method) so environments without Playwright installed can still use
ApiKeyAuth without an ImportError.
"""
from __future__ import annotations

from typing import Dict, Optional
import requests


class AuthStrategy:
    """Base interface: apply(session) mutates a requests.Session in place to carry auth."""

    def apply(self, session: requests.Session) -> None:
        raise NotImplementedError


class ApiKeyAuth(AuthStrategy):
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret

    def apply(self, session: requests.Session) -> None:
        session.headers.update({
            "Authorization": f"token {self.api_key}:{self.api_secret}",
        })


class BrowserSessionAuth(AuthStrategy):
    """Authenticates via a real browser login (Playwright) and reuses the resulting session
    cookies + CSRF token as an alternate transport. Does not perform the login until
    `apply()` is called, so constructing this object is always safe/side-effect-free.

    SAFETY: credentials passed here must come from environment variables or a secrets file,
    never hardcoded. This class only ever performs a login (an auth action on the account's own
    session) — it does not create, modify, or delete any Frappe Cloud resource by itself.
    Callers remain responsible for following the Agent Resource Safety Rules for any subsequent
    write calls made using the resulting session.
    """

    def __init__(self, email: str, password: str, base_url: str = "https://cloud.frappe.io", headless: bool = True):
        self.email = email
        self.password = password
        self.base_url = base_url.rstrip("/")
        self.headless = headless
        self._cookies: Optional[Dict[str, str]] = None
        self._csrf_token: Optional[str] = None

    def _login_and_extract(self) -> None:
        """Launches a real browser, logs in, extracts cookies + CSRF token. Lazy Playwright
        import so this module can be imported without Playwright installed."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context()
            page = context.new_page()
            page.goto(f"{self.base_url}/dashboard/login")
            page.click("text=Continue with password")
            page.fill('input[type="email"]', self.email)
            page.fill('input[type="password"]', self.password)
            page.click('button:has-text("Log In")')
            page.wait_for_selector("text=Sites", timeout=15000)

            cookies = context.cookies()
            self._cookies = {c["name"]: c["value"] for c in cookies}
            self._csrf_token = self._cookies.get("csrf_token")

            browser.close()

    def apply(self, session: requests.Session) -> None:
        if self._cookies is None:
            self._login_and_extract()
        assert self._cookies is not None
        session.cookies.update(self._cookies)
        if self._csrf_token:
            session.headers.update({"X-Frappe-CSRF-Token": self._csrf_token})
        session.headers.pop("Authorization", None)

    def is_authenticated(self) -> bool:
        return self._cookies is not None
