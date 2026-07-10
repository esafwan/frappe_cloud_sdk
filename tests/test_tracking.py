import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unittest.mock import MagicMock
import pytest
from frappe_cloud import FrappeCloudClient


def make_client():
    return FrappeCloudClient(api_key="k", api_secret="s")


def test_wait_for_job_returns_success_immediately():
    client = make_client()
    client.post = MagicMock(return_value={"message": {"status": "Success"}})
    result = client.tracking.wait_for_job("job-1", timeout_sec=5, poll_sec=0)
    assert result == "Success"


def test_wait_for_job_raises_on_failure():
    client = make_client()
    client.post = MagicMock(return_value={"message": {"status": "Failure"}})
    with pytest.raises(RuntimeError):
        client.tracking.wait_for_job("job-1", timeout_sec=5, poll_sec=0)


def test_wait_for_bench_deploy_returns_bench_when_active():
    client = make_client()
    client.benches.get = MagicMock(return_value={"name": "bench-1", "status": "Active"})
    result = client.tracking.wait_for_bench_deploy("bench-1", timeout_sec=5, poll_sec=0)
    assert result == {"name": "bench-1", "status": "Active"}


def test_wait_for_bench_deploy_raises_on_broken():
    client = make_client()
    client.benches.get = MagicMock(return_value={"name": "bench-1", "status": "Broken"})
    with pytest.raises(RuntimeError):
        client.tracking.wait_for_bench_deploy("bench-1", timeout_sec=5, poll_sec=0)


def test_wait_for_site_active_returns_site_when_active():
    client = make_client()
    client.sites.get = MagicMock(return_value={"name": "site-1", "status": "Active"})
    result = client.tracking.wait_for_site_active("site-1", timeout_sec=5, poll_sec=0)
    assert result == {"name": "site-1", "status": "Active"}


def test_wait_for_site_active_raises_on_suspended():
    client = make_client()
    client.sites.get = MagicMock(return_value={"name": "site-1", "status": "Suspended"})
    with pytest.raises(RuntimeError):
        client.tracking.wait_for_site_active("site-1", timeout_sec=5, poll_sec=0)
