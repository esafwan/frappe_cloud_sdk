"""Loads Frappe Cloud credentials from .env and constructs a real FrappeCloudClient.
Never prints, logs, or returns raw credential values — only presence/absence and the
constructed client object."""
from __future__ import annotations

import os
import sys
from pathlib import Path

SDK_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SDK_ROOT.parent.parent
sys.path.insert(0, str(SDK_ROOT))

# Accept both this package's documented var names and the shorter aliases a user might
# reasonably write by hand. First name found wins.
_KEY_ALIASES = {
    "FRAPPE_CLOUD_BASE_URL": ["FRAPPE_CLOUD_BASE_URL", "FRAPPE_BASE_URL"],
    "FRAPPE_CLOUD_API_KEY": ["FRAPPE_CLOUD_API_KEY", "FRAPPE_API_KEY"],
    "FRAPPE_CLOUD_API_SECRET": ["FRAPPE_CLOUD_API_SECRET", "FRAPPE_API_SECRET"],
    "FRAPPE_CLOUD_EMAIL": ["FRAPPE_CLOUD_EMAIL", "FRAPPE_EMAIL"],
    "FRAPPE_CLOUD_PASSWORD": ["FRAPPE_CLOUD_PASSWORD", "FRAPPE_PASSWORD"],
}


def _env(canonical_name: str) -> str | None:
    for alias in _KEY_ALIASES[canonical_name]:
        value = os.environ.get(alias)
        if value:
            return value
    return None


def _load_dotenv() -> None:
    from dotenv import load_dotenv
    # Check the SDK-local .env first (documented location, .env.example lives here), then
    # fall back to the repo root in case it was dropped there instead.
    candidates = [SDK_ROOT / ".env", REPO_ROOT / ".env"]
    found = next((p for p in candidates if p.exists()), None)
    if found is None:
        raise RuntimeError(
            f".env not found at any of: {[str(p) for p in candidates]}. Copy "
            f"integrations/frappe_cloud_sdk/.env.example to one of those paths and fill in "
            f"real credentials (never commit this file)."
        )
    load_dotenv(found)


def credential_report() -> dict:
    """Presence-only report — booleans and non-secret values only, safe to print."""
    _load_dotenv()
    return {
        "base_url": _env("FRAPPE_CLOUD_BASE_URL") or "https://cloud.frappe.io",
        "has_api_key_pair": bool(_env("FRAPPE_CLOUD_API_KEY")) and bool(_env("FRAPPE_CLOUD_API_SECRET")),
        "has_browser_credentials": bool(_env("FRAPPE_CLOUD_EMAIL")) and bool(_env("FRAPPE_CLOUD_PASSWORD")),
    }


def load_client():
    """Construct a real FrappeCloudClient from .env. Raises RuntimeError with a clear,
    secret-free message if neither auth path is configured."""
    _load_dotenv()
    from frappe_cloud import FrappeCloudClient

    api_key = _env("FRAPPE_CLOUD_API_KEY")
    api_secret = _env("FRAPPE_CLOUD_API_SECRET")
    base_url = _env("FRAPPE_CLOUD_BASE_URL") or "https://cloud.frappe.io"

    if api_key and api_secret:
        return FrappeCloudClient(api_key=api_key, api_secret=api_secret, base_url=base_url)

    email = _env("FRAPPE_CLOUD_EMAIL")
    password = _env("FRAPPE_CLOUD_PASSWORD")
    if email and password:
        from frappe_cloud.core.auth import BrowserSessionAuth
        auth = BrowserSessionAuth(email=email, password=password, base_url=base_url)
        return FrappeCloudClient(auth=auth, base_url=base_url)

    raise RuntimeError(
        "No usable credentials in .env — set either (FRAPPE_CLOUD_API_KEY + "
        "FRAPPE_CLOUD_API_SECRET) or (FRAPPE_CLOUD_EMAIL + FRAPPE_CLOUD_PASSWORD)."
    )
