from typing import Any, Dict, List, Optional


class Bench:
    """Namespace for Frappe Cloud Bench operations (provisioning, apps, config, deploys)."""

    def __init__(self, client):
        self.client = client

    def list(self, server: Optional[str] = None, bench_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List benches, optionally filtered by server or a bench filter."""
        res = self.client.post(
            "press.api.bench.all",
            {"server": server, "bench_filter": bench_filter}
        )
        return res.get("message", [])

    def get(self, name: str) -> Dict[str, Any]:
        """Fetch details for a specific bench."""
        res = self.client.post("press.api.bench.get", {"name": name})
        return res.get("message", {})

    def options(self) -> Dict[str, Any]:
        """Fetch bench creation options."""
        res = self.client.post("press.api.bench.options", {})
        return res.get("message", {})

    def exists(self, title: str) -> bool:
        """Check if a bench with the given title already exists."""
        res = self.client.post("press.api.bench.exists", {"title": title})
        return bool(res.get("message"))

    def create(
        self,
        title: str,
        version: str,
        cluster: str,
        apps: List[Dict[str, str]],
        server: Optional[str] = None,
        saas_app: str = "",
    ) -> str:
        """
        Provision a new bench (Release Group).

        `apps` must be a list of `{"name": <app_name>, "source": <app_source_name>}` dicts.
        NOTE: the key is `"name"`, not `"app"` — confirmed by a live 500 KeyError against the
        real API (`research/press/press/api/bench.py:54`'s `new()` does
        `app["name"]`/`app["source"]`, not `app["app"]`; the static source reading initially
        got this wrong). `title` must not already exist — check with `exists(title)` first.

        `source` must be a real `AppSource` document name (e.g. `"SRC-frappe-049"`) for the
        chosen `version` — fetch these from `options()["versions"][i]["apps"][j]["source"]["name"]`,
        not guessed.

        Returns the created bench's name (Release Group name).
        """
        bench = {
            "title": title,
            "version": version,
            "cluster": cluster,
            "apps": apps,
            "server": server,
            "saas_app": saas_app,
        }
        res = self.client.post("press.api.bench.new", {"bench": bench})
        return res.get("message")

    def get_config(self, name: str) -> List[Dict[str, Any]]:
        """Retrieve the current custom bench_config configurations."""
        res = self.client.post("press.api.bench.bench_config", {"name": name})
        return res.get("message", [])

    def update_config(self, name: str, config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update the bench_config settings.

        `config` format: `[{"key": "...", "value": "...", "type": "..."}]`. `type` must be one
        of `"", "String", "Password", "Number", "Boolean", "JSON"` — confirmed live 2026-07-10
        (a value like `"Check"` fails with `ValidationError: Type cannot be "Check"`).
        """
        return self.client.post("press.api.bench.update_config", {"name": name, "config": config})

    def list_apps(self, name: str) -> List[Dict[str, Any]]:
        """List apps installed on the bench."""
        res = self.client.post("press.api.bench.apps", {"name": name})
        return res.get("message", [])

    def installable_apps(self, name: str) -> List[Dict[str, Any]]:
        """List apps that can be installed on the bench."""
        res = self.client.post("press.api.bench.installable_apps", {"name": name})
        return res.get("message", [])

    def add_app(self, name: str, source: str, app: str) -> Dict[str, Any]:
        """Add a single app to the bench."""
        return self.client.post("press.api.bench.add_app", {"name": name, "source": source, "app": app})

    def add_apps(self, name: str, apps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add multiple apps to the bench."""
        return self.client.post("press.api.bench.add_apps", {"name": name, "apps": apps})

    def remove_app(self, name: str, app: str) -> Dict[str, Any]:
        """
        Remove an app from the bench.

        DESTRUCTIVE: per the project's Agent Resource Safety Rules, only call this
        on agent-owned test benches.
        """
        return self.client.post("press.api.bench.remove_app", {"name": name, "app": app})

    def deploy(self, name: str, apps: List[str]) -> Optional[str]:
        """Trigger a bench deploy with the given apps. Returns the Job ID / tracker id."""
        res = self.client.post("press.api.bench.deploy", {"name": name, "apps": apps})
        return res.get("message")

    def deploy_status(self, name: str) -> Dict[str, Any]:
        """Fetch the status of the most recent deploy for the bench."""
        res = self.client.post("press.api.bench.deploy_status", {"name": name})
        return res.get("message", {})

    def deploy_information(self, name: str) -> Dict[str, Any]:
        """Fetch deploy information for the bench."""
        res = self.client.post("press.api.bench.deploy_information", {"name": name})
        return res.get("message", {})

    def get_processes(self, name: str) -> List[Dict[str, Any]]:
        """
        List running processes on the bench.

        NOTE: confirmed live 2026-07-10 to raise `AuthenticationError` ("Not Permitted") on a
        normal team account, even for a bench that account owns — this endpoint appears to
        require elevated (System Manager / support) access on Frappe Cloud's side, not just
        resource ownership. Do not treat a failure here as an SDK bug without first confirming
        the account has the necessary access level.
        """
        res = self.client.post("press.api.bench.get_processes", {"name": name})
        return res.get("message", [])

    def dependencies(self, name: str) -> List[Dict[str, Any]]:
        """List dependencies configured for the bench."""
        res = self.client.post("press.api.bench.dependencies", {"name": name})
        return res.get("message", [])

    def update_dependencies(self, name: str, dependencies: str) -> Dict[str, Any]:
        """
        Update the dependencies configured for the bench.

        `dependencies` must be a JSON-encoded **list** of `{"key": ..., "value": ...}` dicts —
        e.g. `json.dumps([{"key": "PYTHON_VERSION", "value": "3.11"}, ...])` — matching the
        shape `dependencies()` itself returns as `active_dependencies`, NOT a flat
        `{"KEY": "value"}` dict. Confirmed live 2026-07-10: a flat dict passes the server's
        length check but then crashes with a bare `TypeError` (it iterates dict keys as plain
        strings and does `key["key"]` indexing on them). You must also supply a value for
        *every* dependency the bench has — a partial update is rejected with "Please provide a
        value for every dependency before saving."
        """
        return self.client.post(
            "press.api.bench.update_dependencies",
            {"name": name, "dependencies": dependencies}
        )

    def candidates(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit_start: Optional[int] = None,
        limit_page_length: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List deploy candidates matching the given filters."""
        res = self.client.post(
            "press.api.bench.candidates",
            {
                "filters": filters,
                "order_by": order_by,
                "limit_start": limit_start,
                "limit_page_length": limit_page_length,
            }
        )
        return res.get("message", [])

    def candidate(self, name: str) -> Optional[Dict[str, Any]]:
        """Fetch details for a specific deploy candidate."""
        res = self.client.post("press.api.bench.candidate", {"name": name})
        return res.get("message")
