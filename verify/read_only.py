"""Read-only live verification: list benches, sites, servers; fetch bench options (which
implicitly lists available Frappe versions/regions/apps). Prints only names/counts/statuses —
never full raw API responses that might carry account-identifying secrets."""
from __future__ import annotations

import json
import sys
from _env import load_client


def summarize(label: str, items) -> dict:
    return {"label": label, "count": len(items), "sample": items[:3]}


def main() -> int:
    client = load_client()
    results = []

    try:
        benches = client.benches.list()
        results.append(summarize("benches", benches))
    except Exception as e:
        results.append({"label": "benches", "error": str(e)})

    try:
        sites = client.sites.list()
        results.append(summarize("sites", sites))
    except Exception as e:
        results.append({"label": "sites", "error": str(e)})

    try:
        servers = client.servers.list()
        results.append(summarize("servers", servers))
    except Exception as e:
        results.append({"label": "servers", "error": str(e)})

    try:
        options = client.benches.options()
        results.append({"label": "bench_options_keys", "keys": list(options.keys()) if isinstance(options, dict) else str(type(options))})
    except Exception as e:
        results.append({"label": "bench_options", "error": str(e)})

    print(json.dumps(results, indent=2, default=str))
    failures = [r for r in results if "error" in r]
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
