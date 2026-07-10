from typing import Any, Dict, List, Optional


class Server:
    """Namespace for Frappe Cloud Server operations (read-only inspection)."""

    def __init__(self, client):
        self.client = client

    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List servers, optionally filtered."""
        res = self.client.post("press.api.server.all", {"filters": filters})
        return res.get("message", [])

    def get(self, name: str) -> Dict[str, Any]:
        """Fetch details for a specific server."""
        res = self.client.post("press.api.server.get", {"name": name})
        return res.get("message", {})

    def usage(self, name: str) -> Dict[str, Any]:
        """Fetch CPU/memory/disk usage metrics for a specific server."""
        res = self.client.post("press.api.server.usage", {"name": name})
        return res.get("message", {})
