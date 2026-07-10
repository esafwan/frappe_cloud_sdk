"""Live-test the remaining safe, non-destructive, implemented-but-unverified SDK methods
against your own agent-owned bench/site (see verify/create_bench.py, verify/create_site.py).
Set FRAPPE_CLOUD_TEST_BENCH / FRAPPE_CLOUD_TEST_SITE before running.

Each call is wrapped in try/except so one failure doesn't stop the run; prints a JSON report
of {action: {ok, result} | {ok: false, error_type, error_message}}. Read-only / dry-run only —
no reinstall/archive/change_server/install_app/uninstall_app/restore/add_domain/database writes.
Never prints raw credential values (SDK exceptions carry status/message only, no auth headers).

Covers:
  1. benches.exists(BENCH)                          — true case
  2. sites.new_site_options()                       — no-arg
  3. devtools.get_log(log_type, doc_name, log_name) — real log_name from sites.list_logs()
  4. sites.validate_restoration_space(SITE, ...)    — dry-run disk check (NOT restore)
  5. sites.get_backup_link(SITE, real_backup, "database") — success path w/ real backup id
  6. servers.list()                                 — re-confirm []
"""
from __future__ import annotations

import json
import os
import sys
from _env import load_client

BENCH = os.environ.get("FRAPPE_CLOUD_TEST_BENCH", "your-agent-test-bench-name")
SITE = os.environ.get("FRAPPE_CLOUD_TEST_SITE", "your-agent-test-site.frappe.cloud")

results: dict = {}


def _safe(value):
    """Compact, JSON-safe summary that never echoes huge payloads or secrets."""
    if isinstance(value, list):
        return {"type": "list", "count": len(value), "sample": value[:2]}
    if isinstance(value, dict):
        return {"type": "dict", "keys": list(value.keys())[:30], "sample": _shallow(value)}
    return value


def _shallow(d: dict) -> dict:
    out = {}
    for k, v in list(d.items())[:12]:
        if isinstance(v, (dict, list)):
            out[k] = f"<{type(v).__name__} len={len(v)}>"
        else:
            s = str(v)
            out[k] = s[:120]
    return out


def run(label: str, fn):
    try:
        results[label] = {"ok": True, "result": _safe(fn())}
    except Exception as e:
        results[label] = {
            "ok": False,
            "error_type": type(e).__name__,
            "error_message": str(e)[:400],
        }


def _extract_log_name(logs):
    """sites.list_logs() -> agent `.../logs` payload; pull out one usable log filename."""
    if isinstance(logs, dict):
        return next(iter(logs.keys()), None)
    if isinstance(logs, list) and logs:
        first = logs[0]
        if isinstance(first, str):
            return first
        if isinstance(first, dict):
            return first.get("name") or first.get("log") or next(iter(first.values()), None)
    return None


def _completed_backups(backups):
    if not isinstance(backups, list):
        return []
    ok = []
    for b in backups:
        if not isinstance(b, dict):
            continue
        status = (b.get("status") or "").lower()
        if status in ("success", "completed", "") and b.get("name"):
            ok.append(b)
    return ok


def main() -> int:
    client = load_client()

    # 1. benches.exists — true case
    run("benches.exists_true", lambda: client.benches.exists(BENCH))

    # 2. sites.new_site_options — no-arg
    run("sites.new_site_options", lambda: client.sites.new_site_options())

    # 3. devtools.get_log — derive a REAL log_name from the site, then fetch it.
    #    press log_browser.get_log(log_type: LOG_TYPE, doc_name, log_name): LOG_TYPE is an
    #    enum whose VALUES are "site"/"bench"; @protected(["Site","Bench"]) checks doc_name.
    def _devtools_get_log():
        logs = client.sites.list_logs(SITE)
        log_name = _extract_log_name(logs) or "scheduler.log"
        entries = client.devtools.get_log(log_type="site", doc_name=SITE, log_name=log_name)
        n = len(entries) if isinstance(entries, list) else None
        return {
            "log_name_used": log_name,
            "list_logs_shape": type(logs).__name__,
            "entry_count": n,
            "sample": entries[:2] if isinstance(entries, list) else entries,
        }

    run("devtools.get_log", _devtools_get_log)

    # Shared backup discovery for steps 4 & 5.
    backups = []
    try:
        backups = client.sites.list_backups(SITE) or []
    except Exception as e:  # pragma: no cover - recorded via its own run if needed
        results["sites.list_backups(for 4&5)"] = {
            "ok": False,
            "error_type": type(e).__name__,
            "error_message": str(e)[:400],
        }

    completed = _completed_backups(backups)
    chosen = completed[0] if completed else (backups[0] if backups else None)

    # 4. validate_restoration_space — non-destructive dry-run disk check with a REAL backup.
    def _validate_space():
        if not chosen:
            return {"skipped": "no backup available to validate against"}
        db_size = int(chosen.get("database_size") or 0)
        public_size = int(chosen.get("public_size") or 0)
        private_size = int(chosen.get("private_size") or 0)
        res = client.sites.validate_restoration_space(
            SITE, db_file_size=db_size, public_file_size=public_size, private_file_size=private_size
        )
        return {
            "backup_used": chosen.get("name"),
            "sizes": {"db": db_size, "public": public_size, "private": private_size},
            "response": res,
        }

    run("sites.validate_restoration_space", _validate_space)

    # 5. get_backup_link success path with a REAL backup id.
    #    Server reads Site Backup.remote_database_file then returns its Remote File download_link,
    #    so prefer a backup that actually HAS a remote_database_file (offsite/uploaded).
    def _backup_link():
        if not backups:
            return {"skipped": "no backups returned"}
        pool = completed or [b for b in backups if isinstance(b, dict)]
        with_remote = [b for b in pool if b.get("remote_database_file")]
        cand = (with_remote or pool)[0]
        link = client.sites.get_backup_link(SITE, cand.get("name"), "database")
        return {
            "backup_used": cand.get("name"),
            "offsite": cand.get("offsite"),
            "had_remote_database_file": bool(cand.get("remote_database_file")),
            "link_type": type(link).__name__,
            "link_present": bool(link),
        }

    run("sites.get_backup_link", _backup_link)

    # 6. servers.list — re-confirm []
    run("servers.list", lambda: client.servers.list())

    print(json.dumps(results, indent=2, default=str))
    failures = [k for k, v in results.items() if not v.get("ok")]
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
