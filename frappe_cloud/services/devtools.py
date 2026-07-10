from typing import Any, List, Optional


class DevTools:
    """Namespace for Frappe Cloud dev-tool inspection endpoints (log browser). Read-only —
    does not execute arbitrary SQL/commands against production data.

    NOTE: `press.api.log_browser` has no listing endpoint (confirmed against
    `research/press/press/api/log_browser.py`) — log names/types must come from
    `Sites.list_logs()` / `Bench.get_processes()` etc. `get_log()` below matches the real
    confirmed signature `press.api.log_browser.get_log(log_type, doc_name, log_name)`.
    """

    def __init__(self, client):
        self.client = client

    def get_log(self, log_type: str, doc_name: str, log_name: str) -> Optional[List[Any]]:
        """Fetch formatted log entries for a bench/site log file.

        `log_type` is `"site"` or `"bench"` — which owning-document type `doc_name` refers to
        (NOT a log-format/filename key, as an earlier version of this docstring claimed).
        `doc_name` is the owning Site/Bench document name; `log_name` is a specific log filename
        (e.g. `"database.log"`, `"scheduler.log"`) sourced from `Sites.list_logs()`. Confirmed
        live 2026-07-10 with `log_type="site"` against a real site's `database.log` (117 entries
        returned).
        """
        res = self.client.post(
            "press.api.log_browser.get_log",
            {"log_type": log_type, "doc_name": doc_name, "log_name": log_name},
        )
        return res.get("message")
