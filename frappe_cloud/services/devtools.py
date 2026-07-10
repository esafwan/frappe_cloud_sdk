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

        `log_type` is one of the formatter keys press supports (e.g. "bench", "worker",
        "frappe", "database", "scheduler", "redis", "web.error", "monitor.json", "ipython").
        `doc_name` is the owning Bench/Site document name; `log_name` is the specific log file.
        """
        res = self.client.post(
            "press.api.log_browser.get_log",
            {"log_type": log_type, "doc_name": doc_name, "log_name": log_name},
        )
        return res.get("message")
