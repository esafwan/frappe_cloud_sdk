from typing import Any, Dict, List

class Backups:
    """Namespace for Frappe Cloud Backup & Restore operations."""
    
    def __init__(self, client):
        self.client = client

    def list(self, site_name: str) -> List[Dict[str, Any]]:
        """List available local and offsite backups for the site."""
        res = self.client.post("press.api.site.backups", {"name": site_name})
        return res.get("message", [])

    def trigger(self, site_name: str, with_files: bool = True) -> Dict[str, Any]:
        """Manually trigger a logical backup for the site. Will queue an agent job."""
        return self.client.post(
            "press.api.site.backup", 
            {"name": site_name, "with_files": with_files}
        )

    def restore(self, target_site: str, backup_record: Dict[str, Any], skip_failing_patches: bool = False) -> Dict[str, Any]:
        """
        Restore a site from a specific Frappe Cloud backup record.
        
        Args:
            target_site: The name of the site to overwrite (DANGEROUS).
            backup_record: A record retrieved from the `list()` method.
            skip_failing_patches: Skip patches that fail upon restoration.
        """
        files = {
            "database": backup_record.get("remote_database_file"),
            "public": backup_record.get("remote_public_file"),
            "private": backup_record.get("remote_private_file"),
            "config": backup_record.get("remote_config_file"),
        }
        
        # Filter out missing files (only attempt to restore what was actually backed up)
        files = {k: v for k, v in files.items() if v}
        
        if not files:
            raise ValueError("No restorable remote files found in the provided backup record object")

        return self.client.post(
            "press.api.site.restore",
            {
                "name": target_site,
                "files": files,
                "skip_failing_patches": skip_failing_patches
            }
        )
