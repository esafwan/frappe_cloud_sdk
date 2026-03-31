import logging
from typing import Any, Dict, Optional
import requests

from .exceptions import APIError, AuthenticationError, ValidationError

logger = logging.getLogger(__name__)

class FrappeCloudClient:
    """Core client for interacting with Frappe Cloud APIs."""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://cloud.frappe.io"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        
        # Configure a standard HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {self.api_key}:{self.api_secret}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        # Attach feature namespaces
        from .sites import Sites
        from .apps import Apps
        from .backups import Backups
        from .domains import Domains
        from .tracking import Tracking
        from .database import Database
        
        self.sites = Sites(self)
        self.apps = Apps(self)
        self.backups = Backups(self)
        self.domains = Domains(self)
        self.tracking = Tracking(self)
        self.database = Database(self)
        
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
