from typing import Any, Dict

class Domains:
    """Namespace for Frappe Cloud custom domain verification and management."""
    
    def __init__(self, client):
        self.client = client

    def check_dns(self, site_name: str, domain: str) -> Dict[str, Any]:
        """Verify if DNS CNAME or A records are properly point to the Frappe site IP/CNAME."""
        return self.client.post("press.api.site.check_dns", {"name": site_name, "domain": domain})

    def add(self, site_name: str, domain: str) -> Dict[str, Any]:
        """Create and bind a custom domain record to the site (if DNS check passes)."""
        return self.client.post("press.api.site.add_domain", {"name": site_name, "domain": domain})

    def remove(self, site_name: str, domain: str) -> Dict[str, Any]:
        """Delete a custom domain binding from the site."""
        return self.client.post("press.api.site.remove_domain", {"name": site_name, "domain": domain})

    def set_primary(self, site_name: str, domain: str) -> Dict[str, Any]:
        """Set an existing bound domain as the primary `host_name` for the site."""
        return self.client.post("press.api.site.set_host_name", {"name": site_name, "domain": domain})
