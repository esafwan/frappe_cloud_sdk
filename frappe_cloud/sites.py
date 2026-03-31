from typing import Any, Dict, List, Optional
import copy

class Sites:
    """Namespace for Frappe Cloud Site operations (provisioning, lifecycle, config)."""
    
    def __init__(self, client):
        self.client = client

    def is_subdomain_available(self, subdomain: str, domain: str = "frappe.cloud") -> bool:
        """Check if a given subdomain is available under a specific root domain."""
        res = self.client.post(
            "press.api.site.exists", 
            {"subdomain": subdomain, "domain": domain}
        )
        return bool(res.get("message"))

    def create(self, name: str, apps: List[str], version: str = "Version 16", plan: str = "USD 5 - Hetzner", 
               provider: str = "Hetzner", cluster: str = "Falkenstein", domain: str = "frappe.cloud", 
               group: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Provision a new Frappe Cloud site.
        
        Returns the deployment response containing the Tracking ID (`site_group_deploy`)
        or the active `site`.
        """
        site_config = {
            "name": name,
            "apps": apps,
            "version": version,
            "plan": plan,
            "provider": provider,
            "cluster": cluster,
            "domain": domain,
        }
        if group:
            site_config["group"] = group
            
        site_config.update(kwargs)
        
        res = self.client.post("press.api.site.new", {"site": site_config})
        return res.get("message", {})

    def migrate(self, name: str, skip_failing_patches: bool = False) -> Dict[str, Any]:
        """Trigger a site migration / minor update."""
        return self.client.post(
            "press.api.site.migrate", 
            {"name": name, "skip_failing_patches": skip_failing_patches}
        )

    def schedule_update(self, name: str, skip_failing_patches: bool = False, skip_backups: bool = False) -> Dict[str, Any]:
        """Schedule a site update (similar to migrate, but runs in background queues)."""
        return self.client.post(
            "press.api.site.update", 
            {
                "name": name, 
                "skip_failing_patches": skip_failing_patches, 
                "skip_backups": skip_backups
            }
        )

    def reinstall(self, name: str) -> Optional[str]:
        """Reset the site to a clean database state. Destructive! Returns Job ID."""
        res = self.client.post("press.api.site.reinstall", {"name": name})
        return res.get("message")

    def archive(self, name: str, force: bool = False) -> Dict[str, Any]:
        """Drop/Archive the site permanently."""
        return self.client.post("press.api.site.archive", {"name": name, "force": force})

    def get_config(self, name: str) -> List[Dict[str, Any]]:
        """Retrieve the current custom site_config configurations."""
        res = self.client.post("press.api.site.site_config", {"name": name})
        return res.get("message", [])

    def update_config(self, name: str, config_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update the site_config settings.
        `config_rows` format: [{"key": "redis_cache", "value": "redis://...", "type": "String"}]
        Note: The Frappe Cloud UI deliberately blocks `developer_mode` via this API path.
        """
        return self.client.post("press.api.site.update_config", {"name": name, "config": config_rows})

    def list_logs(self, name: str) -> List[Dict[str, Any]]:
        """List available server log files for this site."""
        res = self.client.post("press.api.site.logs", {"name": name})
        return res.get("message", [])

    def get_log(self, name: str, log_name: str) -> Optional[str]:
        """Fetch the contents of a specific site log file."""
        res = self.client.post("press.api.site.log", {"name": name, "log": log_name})
        return res.get("message")
