"""Creates exactly ONE agent-owned test site, on the bench created by create_bench.py in this
same run (reads bench_name from run_manifest.json rather than accepting an arbitrary bench
argument, so this script can never accidentally target an existing production bench)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from _env import load_client
from frappe_cloud.core.manifest import ResourceManifest

MANIFEST_PATH = str(Path(__file__).resolve().parent / "run_manifest.json")


def main() -> int:
    manifest_file = Path(MANIFEST_PATH)
    if not manifest_file.exists():
        print(json.dumps({"error": "run_manifest.json not found — run create_bench.py first"}))
        return 1

    data = json.loads(manifest_file.read_text())
    bench_resources = [r for r in data["resources"].values() if r["resource_type"] == "bench" and r["status"] == "active"]
    if not bench_resources:
        print(json.dumps({"error": "no active agent-owned bench found in manifest"}))
        return 1
    bench_entry = bench_resources[-1]
    bench_title = bench_entry["name"]
    run_id = bench_entry["run_id"]

    client = load_client()
    manifest = ResourceManifest(path=MANIFEST_PATH, run_id=run_id)

    site_name = f"{bench_title}-site"
    if not client.sites.is_subdomain_available(site_name):
        print(json.dumps({"error": f"subdomain {site_name} not available"}))
        return 1

    manifest.register(
        name=site_name,
        resource_type="site",
        run_id=run_id,
        purpose="Real-API verification run — Phase real-api-verification, Task 4",
        parent=bench_title,
        destructive_cleanup_allowed=True,
        cleanup_command=f"client.sites.archive('{site_name}', force=True)",
    )

    try:
        result = client.sites.create(
            name=site_name,
            apps=["frappe"],
            group=bench_title,
        )
    except Exception as e:
        manifest.record_operation(site_name, action="create", result="failed", errors=str(e))
        print(json.dumps({"error": str(e), "site_name": site_name}))
        return 1

    manifest.record_operation(site_name, action="create", result="success", operation_id=json.dumps(result, default=str))

    print(json.dumps({
        "run_id": run_id,
        "bench_title": bench_title,
        "site_name": site_name,
        "create_result": result,
        "manifest_path": MANIFEST_PATH,
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
