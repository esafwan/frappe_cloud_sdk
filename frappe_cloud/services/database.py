from typing import Any, Dict

class Database:
    """Namespace for managing direct database credentials (Site Database User)."""
    
    def __init__(self, client):
        self.client = client

    def create_user(self, site_name: str, username: str, label: str = "readonly") -> str:
        """
        Provision a new remote database user profile (typically read-only).
        Returns the specific credential secret payload containing the database password.
        """
        doc = {
            "doctype": "Site Database User",
            "site": site_name,
            "label": label,
            "username": username,
            "mode": "read_only",
            "max_connections": 20,
            "use_replica_server": 0,
        }

        # 1. Create the entry in Frappe Cloud's ledger
        res_insert = self.client.post("press.api.client.insert", {"doc": doc})
        db_user_name = res_insert["message"]["name"]

        # 2. Trigger proxysql and backend propagation
        self.client.run_doc_method("Site Database User", db_user_name, "apply_changes", None)

        # 3. Fetch generating credentials payload
        res_cred = self.client.run_doc_method("Site Database User", db_user_name, "get_credential", None)
        return res_cred.get("message")

    def archive_user(self, db_user_name: str) -> None:
        """De-provision and archive an existing database user."""
        self.client.run_doc_method(
            "Site Database User", 
            db_user_name, 
            "archive", 
            {"raise_error": True, "skip_remove_db_user_step": False}
        )
