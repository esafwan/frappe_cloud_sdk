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
