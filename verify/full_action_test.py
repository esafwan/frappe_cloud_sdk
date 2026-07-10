"""Exhaustive live test of bench/site SDK actions against an agent-owned test bench/site you
already created (see verify/create_bench.py, verify/create_site.py). Never touches any
existing production sites/benches — set FRAPPE_CLOUD_TEST_BENCH / FRAPPE_CLOUD_TEST_SITE
(or edit the fallback below) to your own agent-test-* resource names before running. Catches
every exception per-call so one failure doesn't stop the run — prints a JSON report of
{action: {ok, result_summary} | {ok: false, error_type, error_message}}. Never prints raw
credential values (SDK exceptions carry status/message only, no auth headers)."""
from __future__ import annotations

import json
import os
import sys
from _env import load_client

BENCH = os.environ.get("FRAPPE_CLOUD_TEST_BENCH", "your-agent-test-bench-name")
SITE = os.environ.get("FRAPPE_CLOUD_TEST_SITE", "your-agent-test-site.frappe.cloud")

results: dict = {}


def run(label: str, fn):
    try:
        value = fn()
        summary = value
        if isinstance(value, list):
            summary = {"type": "list", "count": len(value), "sample": value[:2]}
        results[label] = {"ok": True, "result": summary}
    except Exception as e:
        results[label] = {"ok": False, "error_type": type(e).__name__, "error_message": str(e)[:400]}


def main() -> int:
    client = load_client()

    # --- Bench: read actions ---
    run("bench.get", lambda: client.benches.get(BENCH))
    run("bench.get_config", lambda: client.benches.get_config(BENCH))
    run("bench.list_apps", lambda: client.benches.list_apps(BENCH))
    run("bench.installable_apps", lambda: client.benches.installable_apps(BENCH))
    run("bench.get_processes", lambda: client.benches.get_processes(BENCH))
    run("bench.dependencies", lambda: client.benches.dependencies(BENCH))
    run("bench.candidates", lambda: client.benches.candidates(filters={"group": BENCH}, limit_page_length=5))
    run("bench.deploy_status", lambda: client.benches.deploy_status(BENCH))
    run("bench.deploy_information", lambda: client.benches.deploy_information(BENCH))
    run("bench.exists_false_case", lambda: client.benches.exists("agent-test-this-title-should-not-exist-xyz"))

    # --- Bench: write actions (safe, on our own bench) ---
    # Valid Site/Bench Config "type" values (found live, not documented anywhere):
    # "", "String", "Password", "Number", "Boolean", "JSON" — NOT "Check".
    run("bench.update_config", lambda: client.benches.update_config(BENCH, [{"key": "keep_backups_on_delete", "value": "0", "type": "Boolean"}]))
    # update_dependencies needs the FULL active set as a JSON *list* of {"key","value"} dicts
    # (matching bench.dependencies()'s own output shape) — NOT a flat dict. A flat dict passes
    # the length check but then crashes server-side with a bare TypeError (iterating dict keys
    # as strings, then doing string["key"] indexing) — confirmed live.
    run("bench.update_dependencies", lambda: client.benches.update_dependencies(BENCH, json.dumps([
        {"key": "NVM_VERSION", "value": "0.36.0"},
        {"key": "NODE_VERSION", "value": "18.16.0"},
        {"key": "PYTHON_VERSION", "value": "3.11"},
        {"key": "WKHTMLTOPDF_VERSION", "value": "0.12.5"},
        {"key": "BENCH_VERSION", "value": "5.27.0"},
        {"key": "PIP_VERSION", "value": "25.3"},
    ])))

    # --- Site: read actions ---
    run("site.get", lambda: client.sites.get(SITE))
    run("site.get_config", lambda: client.sites.get_config(SITE))
    run("site.installed_apps", lambda: client.sites.installed_apps(SITE))
    run("site.available_apps", lambda: client.sites.available_apps(SITE))
    run("site.list_backups", lambda: client.sites.list_backups(SITE))
    run("site.domains", lambda: client.sites.domains(SITE))
    run("site.jobs", lambda: client.sites.jobs(filters={"site": SITE}, limit_page_length=5))
    run("site.running_jobs", lambda: client.sites.running_jobs(SITE))
    run("site.activities", lambda: client.sites.activities(filters={"site": SITE}, limit_page_length=5))
    run("site.check_for_updates", lambda: client.sites.check_for_updates(SITE))
    run("site.last_migrate_failed", lambda: client.sites.last_migrate_failed(SITE))
    run("site.list_logs", lambda: client.sites.list_logs(SITE))

    # --- Site: write actions (safe, on our own site) ---
    run("site.update_config", lambda: client.sites.update_config(SITE, [{"key": "pause_scheduler", "value": "0", "type": "Boolean"}]))
    run("site.clear_cache", lambda: client.sites.clear_cache(SITE))
    run("site.migrate", lambda: client.sites.migrate(SITE))
    run("site.backup", lambda: client.sites.backup(SITE, with_files=False))
    run("site.get_log", lambda: client.sites.get_log(SITE, "scheduler.log"))
    run("error.add_domain_fake", lambda: client.sites.add_domain(SITE, "agent-test-verification.example-nonexistent-domain.test"))
    run("error.get_backup_link_probe", lambda: client.sites.get_backup_link(SITE, "nonexistent-backup", "database"))

    # --- Error-handling probes: deliberately invalid inputs, expect clean typed exceptions ---
    run("error.site_get_nonexistent", lambda: client.sites.get("this-site-does-not-exist-xyz.frappe.cloud"))
    run("error.bench_get_nonexistent", lambda: client.benches.get("bench-does-not-exist-xyz"))
    run("error.site_install_bad_app", lambda: client.sites.install_app(SITE, "this_app_does_not_exist_xyz"))
    run("error.bench_add_bad_app", lambda: client.benches.add_app(BENCH, "SRC-does-not-exist", "nonexistent_app"))

    print(json.dumps(results, indent=2, default=str))
    failures = {k: v for k, v in results.items() if not v["ok"] and not k.startswith("error.")}
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
