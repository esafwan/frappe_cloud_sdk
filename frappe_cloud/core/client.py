import logging
from typing import Any, Dict, Optional, TYPE_CHECKING
import requests

from .exceptions import APIError, AuthenticationError, ValidationError

if TYPE_CHECKING:
    from .auth import AuthStrategy

logger = logging.getLogger(__name__)

class FrappeCloudClient:
    """Core client for interacting with Frappe Cloud APIs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: str = "https://cloud.frappe.io",
        auth: Optional["AuthStrategy"] = None,
        manifest_path: Optional[str] = None,
    ):
        from .auth import ApiKeyAuth

        if auth is None:
            if not api_key or not api_secret:
                raise ValueError("Either (api_key and api_secret) or an explicit `auth` strategy must be provided")
            auth = ApiKeyAuth(api_key, api_secret)

        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.auth = auth

        # Configure a standard HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        self.auth.apply(self.session)

        # Agent resource manifest / safety-gate (Agent Resource Safety Rules). Optional: only
        # constructed when a manifest_path is given, so existing callers are unaffected.
        self.manifest = None
        if manifest_path:
            from .manifest import ResourceManifest
            self.manifest = ResourceManifest(path=manifest_path)

        # Attach feature namespaces. App/backup/domain operations live only on `sites` —
        # the original Apps/Backups/Domains services duplicated this and were removed
        # (pre-1.0, no back-compat needed): `sites.*` is the version that was live-verified.
        from ..services.sites import Sites
        from ..services.tracking import Tracking
        from ..services.database import Database
        from ..services.benches import Bench
        from ..services.servers import Server
        from ..services.devtools import DevTools

        self.sites = Sites(self)
        self.tracking = Tracking(self)
        self.database = Database(self)
        self.benches = Bench(self)
        self.servers = Server(self)
        self.devtools = DevTools(self)
        
    def _handle_error(self, response: requests.Response):
        """Standardized error handling logic mapping HTTP status codes to custom exceptions."""
        try:
            data = response.json()
        except ValueError:
            data = {"message": response.text}
            
        status = response.status_code
        message = data.get("exc_type") or data.get("message") or f"API Error HTTP {status}"
        
        # Surface internal Frappe server unhandled messages for debugging
        server_messages = data.get("_server_messages")
        if server_messages:
            message = f"{message} | Server Logs: {server_messages}"
            
        # Map specific codes to SDK exception types
        if status in (401, 403):
            raise AuthenticationError(message, status, data)
        elif status in (400, 417):
            raise ValidationError(message, status, data)
        else:
            raise APIError(message, status, data)

    def request(self, method: str, path: str, json: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Core raw HTTP request method for the Frappe Cloud SDK."""
        url = f"{self.base_url}/api/method/{path}"
        logger.debug(f"FrappeCloud API call: {method} {url}")
        
        response = self.session.request(method, url, json=json, params=params)
        
        if not response.ok:
            self._handle_error(response)
            
        return response.json()

    def post(self, path: str, json: Optional[Dict] = None) -> Dict[str, Any]:
        """Convenience wrapper for POST method, the primary HTTP verb used by Frappe Cloud's RPC API."""
        return self.request("POST", path, json=json)
        
    def get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Convenience wrapper for GET requests."""
        return self.request("GET", path, params=params)

    # Core Generic Frappe Cloud Wrappers
    def get_doc(self, doctype: str, name: str) -> Dict[str, Any]:
        """Fetch a specific generic document from Frappe Cloud."""
        return self.post("press.api.client.get", {"doctype": doctype, "name": name})

    def run_doc_method(self, dt: str, dn: str, method: str, args: Optional[Dict] = None) -> Dict[str, Any]:
        """Run a whitelisted dashboard method on a specific Frappe Cloud document."""
        return self.post(
            "press.api.client.run_doc_method",
            {"dt": dt, "dn": dn, "method": method, "args": args}
        )
