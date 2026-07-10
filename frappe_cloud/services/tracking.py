import time
from typing import Any, Dict

class Tracking:
    """Namespace for polling asynchronous job and deployment statuses."""
    
    def __init__(self, client):
        self.client = client

    def wait_for_deploy(self, deploy_name: str, timeout_sec: int = 1800, poll_sec: int = 10) -> Dict[str, Any]:
        """
        Polls a `Site Group Deploy` object until it reaches a terminal success or failure state.
        Typical workflow for a new site: Pending -> Deploying Bench -> Creating Site -> Site Created.
        """
        final_ok = {"Site Created"}
        final_fail = {"Site Creation Failed", "Bench Deploy Failed"}
        started = time.time()

        while time.time() - started < timeout_sec:
            # We use the generic document getter attached to the client
            res = self.client.get_doc("Site Group Deploy", deploy_name)
            doc = res.get("message", {})
            status = doc.get("status")

            if status in final_ok:
                return doc
            if status in final_fail:
                raise RuntimeError(f"Provisioning failed with status: {status}. Details: {doc}")

            time.sleep(poll_sec)

        raise TimeoutError(f"Timed out waiting for Site Group Deploy {deploy_name} after {timeout_sec}s")

    def wait_for_job(self, job_name: str, timeout_sec: int = 3600, poll_sec: int = 10) -> str:
        """
        Polls a Frappe Cloud `Agent Job` until completion.
        Useful for app installations, updates, migrations, and reinstallations.

        Live-verified 2026-07-10 against a real completed job (`press.api.site.get_job_status`
        confirmed to exist and match this exact param/return shape in `research/press`).
        """
        started = time.time()

        while time.time() - started < timeout_sec:
            res = self.client.post("press.api.site.get_job_status", {"job_name": job_name})
            status = (res.get("message") or {}).get("status")

            if status in {"Success", "Failure", "Error"}:
                if status != "Success":
                    raise RuntimeError(f"Agent Job {job_name} failed. Status: {status}")
                return status

            time.sleep(poll_sec)

        raise TimeoutError(f"Timed out waiting for Agent Job {job_name} after {timeout_sec}s")

    def wait_for_bench_deploy(self, bench_name: str, timeout_sec: int = 1800, poll_sec: int = 15) -> Dict[str, Any]:
        """
        Polls a Bench (Release Group's deployed Bench) until it reaches `Active` or a known
        failure status. This matches the actual `Bench.create()` -> `Bench.deploy()` -> poll
        flow used to provision a bench in this SDK (as opposed to `wait_for_deploy()`, which
        tracks the older combined `Site Group Deploy` object used by `Sites.create()`'s
        one-shot new-bench-and-site flow).

        Live-verified 2026-07-10: a real bench went `Awaiting Deploy` -> `Active` in ~6 minutes
        under this exact polling shape (`client.benches.get(name).status`).
        """
        final_ok = {"Active"}
        final_fail = {"Broken", "Archived"}
        started = time.time()

        while time.time() - started < timeout_sec:
            bench = self.client.benches.get(bench_name)
            status = bench.get("status")

            if status in final_ok:
                return bench
            if status in final_fail:
                raise RuntimeError(f"Bench {bench_name} deploy failed with status: {status}. Details: {bench}")

            time.sleep(poll_sec)

        raise TimeoutError(f"Timed out waiting for bench {bench_name} to become Active after {timeout_sec}s")

    def wait_for_site_active(self, site_name: str, timeout_sec: int = 1800, poll_sec: int = 15) -> Dict[str, Any]:
        """
        Polls a Site until it reaches `Active` or a known failure status. Matches the
        `Sites.create()` -> poll flow used to provision a site on an already-deployed bench in
        this SDK.

        Live-verified 2026-07-10: a real site went straight to `Active` (fast — the bench was
        already deployed) under this exact polling shape (`client.sites.get(name).status`).
        """
        final_ok = {"Active"}
        final_fail = {"Broken", "Archived", "Suspended"}
        started = time.time()

        while time.time() - started < timeout_sec:
            site = self.client.sites.get(site_name)
            status = site.get("status")

            if status in final_ok:
                return site
            if status in final_fail:
                raise RuntimeError(f"Site {site_name} provisioning failed with status: {status}. Details: {site}")

            time.sleep(poll_sec)

        raise TimeoutError(f"Timed out waiting for site {site_name} to become Active after {timeout_sec}s")
