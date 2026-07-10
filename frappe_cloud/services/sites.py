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
        `type` must be one of `"", "String", "Password", "Number", "Boolean", "JSON"` —
        confirmed live 2026-07-10 (same constraint as `Bench.update_config`).
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

    def list(self, site_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List sites, optionally filtered."""
        res = self.client.post("press.api.site.all", {"site_filter": site_filter})
        return res.get("message", [])

    def get(self, name: str) -> Dict[str, Any]:
        """Get full details of a single site."""
        res = self.client.post("press.api.site.get", {"name": name})
        return res.get("message", {})

    def new_site_options(self, group: Optional[str] = None) -> Dict[str, Any]:
        """Get available options (versions, apps, clusters, etc.) for creating a new site."""
        res = self.client.post("press.api.site.get_new_site_options", {"group": group})
        return res.get("message", {})

    def installed_apps(self, name: str) -> List[Dict[str, Any]]:
        """List apps currently installed on a site."""
        res = self.client.post("press.api.site.installed_apps", {"name": name})
        return res.get("message", [])

    def available_apps(self, name: str) -> List[Dict[str, Any]]:
        """List apps available to install on a site."""
        res = self.client.post("press.api.site.available_apps", {"name": name})
        return res.get("message", [])

    def install_app(self, name: str, app: str, plan: Optional[str] = None) -> Dict[str, Any]:
        """Install an app on a site."""
        return self.client.post("press.api.site.install_app", {"name": name, "app": app, "plan": plan})

    def uninstall_app(self, name: str, app: str) -> Dict[str, Any]:
        """
        Uninstall an app from a site.

        DESTRUCTIVE per Agent Resource Safety Rules — only call on agent-owned test sites.
        """
        return self.client.post("press.api.site.uninstall_app", {"name": name, "app": app})

    def deactivate(self, name: str) -> Dict[str, Any]:
        """Deactivate a site (enable maintenance mode)."""
        return self.client.post("press.api.site.deactivate", {"name": name})

    def activate(self, name: str) -> Dict[str, Any]:
        """Activate a site (disable maintenance mode)."""
        return self.client.post("press.api.site.activate", {"name": name})

    def clear_cache(self, name: str) -> Dict[str, Any]:
        """Clear the site's cache."""
        return self.client.post("press.api.site.clear_cache", {"name": name})

    def backup(self, name: str, with_files: bool = False) -> Optional[str]:
        """Trigger a backup of the site. Returns Job ID."""
        res = self.client.post("press.api.site.backup", {"name": name, "with_files": with_files})
        return res.get("message")

    def list_backups(self, name: str) -> List[Dict[str, Any]]:
        """List available backups for a site."""
        res = self.client.post("press.api.site.backups", {"name": name})
        return res.get("message", [])

    def get_backup_link(self, name: str, backup: str, file: str) -> Optional[str]:
        """Get a downloadable link for a specific backup file."""
        res = self.client.post(
            "press.api.site.get_backup_link", {"name": name, "backup": backup, "file": file}
        )
        return res.get("message")

    def validate_restoration_space(
        self, name: str, db_file_size: int, public_file_size: int = 0, private_file_size: int = 0
    ) -> Dict[str, Any]:
        """
        Pre-restore dry-run check for available disk space before a restore.

        Real signature takes three explicit byte sizes, not a `files` dict — confirmed against
        `press.api.site.validate_restoration_space_requirements` (a prior version of this SDK
        method posted `{"files": {...}}`, which raises a server-side `TypeError`; fixed
        2026-07-10 after a live 500).
        """
        return self.client.post(
            "press.api.site.validate_restoration_space_requirements",
            {
                "name": name,
                "db_file_size": db_file_size,
                "public_file_size": public_file_size,
                "private_file_size": private_file_size,
            },
        )

    def restore(
        self, name: str, files: Dict[str, Any], skip_failing_patches: bool = False
    ) -> Optional[str]:
        """
        Restore a site from backup files. Returns Job ID.

        DESTRUCTIVE — per Agent Resource Safety Rules rule 9, `name` must be a newly-created,
        empty, agent-owned test site (`agent-test-restore-<run-id>`), NEVER an existing site.
        Caller is responsible for that check; this method does not enforce it (enforcement
        belongs in the not-yet-built verification gate).
        """
        res = self.client.post(
            "press.api.site.restore",
            {"name": name, "files": files, "skip_failing_patches": skip_failing_patches},
        )
        return res.get("message")

    def change_server(
        self,
        name: str,
        server: str,
        scheduled_datetime: Optional[str] = None,
        skip_failing_patches: bool = False,
    ) -> Optional[str]:
        """
        Move a site to a different server/bench.

        DESTRUCTIVE, agent-owned sites only.
        """
        res = self.client.post(
            "press.api.site.change_server",
            {
                "name": name,
                "server": server,
                "scheduled_datetime": scheduled_datetime,
                "skip_failing_patches": skip_failing_patches,
            },
        )
        return res.get("message")

    def jobs(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit_start: Optional[int] = None,
        limit_page_length: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List Agent Jobs, optionally filtered."""
        res = self.client.post(
            "press.api.site.jobs",
            {
                "filters": filters,
                "order_by": order_by,
                "limit_start": limit_start,
                "limit_page_length": limit_page_length,
            },
        )
        return res.get("message", [])

    def job(self, job: str) -> Dict[str, Any]:
        """Get details of a single Agent Job."""
        res = self.client.post("press.api.site.job", {"job": job})
        return res.get("message", {})

    def running_jobs(self, name: str) -> List[Dict[str, Any]]:
        """List currently running jobs for a site."""
        res = self.client.post("press.api.site.running_jobs", {"name": name})
        return res.get("message", [])

    def activities(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit_start: Optional[int] = None,
        limit_page_length: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List site activity log entries."""
        res = self.client.post(
            "press.api.site.activities",
            {
                "filters": filters,
                "order_by": order_by,
                "limit_start": limit_start,
                "limit_page_length": limit_page_length,
            },
        )
        return res.get("message", [])

    def check_for_updates(self, name: str) -> Dict[str, Any]:
        """Check whether updates are available for a site's bench."""
        res = self.client.post("press.api.site.check_for_updates", {"name": name})
        return res.get("message", {})

    def last_migrate_failed(self, name: str) -> Optional[str]:
        """Check whether the site's last migration failed."""
        res = self.client.post("press.api.site.last_migrate_failed", {"name": name})
        return res.get("message")

    def domains(self, name: str) -> List[Dict[str, Any]]:
        """List domains attached to a site."""
        res = self.client.post("press.api.site.domains", {"name": name})
        return res.get("message", [])

    def add_domain(self, name: str, domain: str) -> Dict[str, Any]:
        """
        Add a custom domain to a site.

        Per Agent Resource Safety Rules rule 12, only sandbox/test domains — never real
        customer domains.
        """
        return self.client.post("press.api.site.add_domain", {"name": name, "domain": domain})

    def remove_domain(self, name: str, domain: str) -> Dict[str, Any]:
        """Remove a domain from a site."""
        return self.client.post("press.api.site.remove_domain", {"name": name, "domain": domain})
