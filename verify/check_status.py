"""Polls the bench deploy status and site existence for the resources created in Tasks 3-4,
using client.benches.deploy_status() / client.sites.get(). Read-only — no further resources
created. Times out after a fixed number of attempts rather than polling forever."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from _env import load_client

MANIFEST_PATH = str(Path(__file__).resolve().parent / "run_manifest.json")
MAX_ATTEMPTS = 20
SLEEP_SECONDS = 15


def main() -> int:
    data = json.loads(Path(MANIFEST_PATH).read_text())
    resources = data["resources"]
    bench = next((r for r in resources.values() if r["resource_type"] == "bench"), None)
    site = next((r for r in resources.values() if r["resource_type"] == "site"), None)
    if not bench or not site:
        print(json.dumps({"error": "manifest missing bench or site entry"}))
        return 1

    client = load_client()
    site_status = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        bench_status = client.benches.deploy_status(bench["name"])
        try:
            site_info = client.sites.get(site["name"])
            site_status = site_info.get("status")
        except Exception as e:
            site_status = f"error: {e}"

        print(json.dumps({
            "attempt": attempt,
            "bench_status": bench_status,
            "site_status": site_status,
        }, default=str))

        if site_status == "Active":
            print(json.dumps({"result": "site is Active", "bench_name": bench["name"], "site_name": site["name"]}))
            return 0

        time.sleep(SLEEP_SECONDS)

    print(json.dumps({"result": "timed out waiting for site to become Active", "last_site_status": site_status}))
    return 1


if __name__ == "__main__":
    sys.exit(main())
