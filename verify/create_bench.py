"""Creates exactly ONE agent-owned test bench, registered in a manifest before creation
(fail-closed: registration happens first, so the resource is trackable even if the create
call itself fails partway). Picks the first available version/cluster from bench.options()
rather than hardcoding one, since the real catalogue can change. Prints only non-secret
results: run ID, bench name, chosen version/cluster, manifest path."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from _env import load_client
from frappe_cloud.core.manifest import ResourceManifest, generate_run_id

MANIFEST_PATH = str(Path(__file__).resolve().parent / "run_manifest.json")


def main() -> int:
    client = load_client()
    run_id = generate_run_id()
    bench_title = run_id  # already carries the agent-test- prefix

    manifest = ResourceManifest(path=MANIFEST_PATH, run_id=run_id)

    options = client.benches.options()
    versions = options.get("versions") or options.get("frappe_versions") or []
    clusters = options.get("clusters") or options.get("regions") or []
    if not versions or not clusters:
        print(json.dumps({"error": "bench.options() did not return usable versions/clusters", "raw_keys": list(options.keys())}))
        return 1

    version = versions[0] if isinstance(versions[0], str) else versions[0].get("name") or versions[0].get("version")
    cluster = clusters[0] if isinstance(clusters[0], str) else clusters[0].get("name")

    if client.benches.exists(bench_title):
        print(json.dumps({"error": f"bench title {bench_title} already exists — run ID collision, abort"}))
        return 1

    manifest.register(
        name=bench_title,
        resource_type="bench",
        purpose="Real-API verification run — Phase real-api-verification, Task 3",
        destructive_cleanup_allowed=True,
        cleanup_command=f"client.benches.archive('{bench_title}')",
    )

    default_apps = [{"app": "frappe", "source": options.get("frappe_source") or ""}]
    try:
        bench_name = client.benches.create(
            title=bench_title,
            version=version,
            cluster=cluster,
            apps=default_apps,
        )
    except Exception as e:
        manifest.record_operation(bench_title, action="create", result="failed", errors=str(e))
        print(json.dumps({"error": str(e), "run_id": run_id, "bench_title": bench_title}))
        return 1

    manifest.record_operation(bench_title, action="create", result="success", operation_id=bench_name)

    print(json.dumps({
        "run_id": run_id,
        "bench_title": bench_title,
        "bench_name": bench_name,
        "version": version,
        "cluster": cluster,
        "manifest_path": MANIFEST_PATH,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
