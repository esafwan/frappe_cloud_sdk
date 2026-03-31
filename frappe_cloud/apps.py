from typing import Any, Dict, List, Optional

class Apps:
    """Namespace for Frappe Cloud App management (install, uninstall, list)."""
    
    def __init__(self, client):
        self.client = client

    def list_installed(self, site_name: str) -> List[Dict[str, Any]]:
        """List currently installed applications on the site."""
        res = self.client.post("press.api.site.installed_apps", {"name": site_name})
        return res.get("message", [])

    def list_available(self, site_name: str) -> List[Dict[str, Any]]:
        """List applications available to be installed on this site's current bench/version."""
        res = self.client.post("press.api.site.available_apps", {"name": site_name})
        return res.get("message", [])

    def install(self, site_name: str, app: str, plan: Optional[str] = None) -> Dict[str, Any]:
        """
        Install an app on the site.
        This will queue an agent job and set the site status to Pending.
        """
        payload = {"name": site_name, "app": app}
        if plan:
            payload["plan"] = plan
            
        return self.client.post("press.api.site.install_app", payload)

    def uninstall(self, site_name: str, app: str) -> Dict[str, Any]:
        """
        Uninstall an app from the site.
        This will queue an agent job and set the site status to Pending.
        """
        return self.client.post("press.api.site.uninstall_app", {"name": site_name, "app": app})
