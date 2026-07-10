import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unittest.mock import MagicMock
from frappe_cloud import FrappeCloudClient


def make_client():
    return FrappeCloudClient(api_key="k", api_secret="s")


def test_bench_list_calls_correct_endpoint_and_unwraps_message():
    client = make_client()
    client.post = MagicMock(return_value={"message": [{"name": "bench-1"}]})
    result = client.benches.list()
    client.post.assert_called_once_with("press.api.bench.all", {"server": None, "bench_filter": None})
    assert result == [{"name": "bench-1"}]


def test_bench_exists_returns_bool():
    client = make_client()
    client.post = MagicMock(return_value={"message": True})
    assert client.benches.exists("agent-test-bench-001") is True


def test_bench_deploy_returns_job_id():
    client = make_client()
    client.post = MagicMock(return_value={"message": "job-123"})
    result = client.benches.deploy("agent-test-bench-001", ["frappe", "erpnext"])
    client.post.assert_called_once_with("press.api.bench.deploy", {"name": "agent-test-bench-001", "apps": ["frappe", "erpnext"]})
    assert result == "job-123"


def test_bench_get_returns_message_dict():
    client = make_client()
    client.post = MagicMock(return_value={"message": {"name": "agent-test-bench-001", "status": "Active"}})
    result = client.benches.get("agent-test-bench-001")
    client.post.assert_called_once_with("press.api.bench.get", {"name": "agent-test-bench-001"})
    assert result == {"name": "agent-test-bench-001", "status": "Active"}


def test_bench_get_config_returns_list():
    client = make_client()
    client.post = MagicMock(return_value={"message": [{"key": "developer_mode", "value": "1"}]})
    result = client.benches.get_config("agent-test-bench-001")
    client.post.assert_called_once_with("press.api.bench.bench_config", {"name": "agent-test-bench-001"})
    assert result == [{"key": "developer_mode", "value": "1"}]


def test_bench_add_app_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": "ok"})
    result = client.benches.add_app("agent-test-bench-001", "source-1", "erpnext")
    client.post.assert_called_once_with(
        "press.api.bench.add_app",
        {"name": "agent-test-bench-001", "source": "source-1", "app": "erpnext"}
    )
    assert result == {"message": "ok"}


def test_bench_remove_app_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": "ok"})
    result = client.benches.remove_app("agent-test-bench-001", "erpnext")
    client.post.assert_called_once_with(
        "press.api.bench.remove_app",
        {"name": "agent-test-bench-001", "app": "erpnext"}
    )
    assert result == {"message": "ok"}


def test_bench_list_apps_returns_list():
    client = make_client()
    client.post = MagicMock(return_value={"message": [{"app": "frappe"}, {"app": "erpnext"}]})
    result = client.benches.list_apps("agent-test-bench-001")
    client.post.assert_called_once_with("press.api.bench.apps", {"name": "agent-test-bench-001"})
    assert result == [{"app": "frappe"}, {"app": "erpnext"}]


def test_bench_create_calls_correct_endpoint_and_returns_name():
    client = make_client()
    client.post = MagicMock(return_value={"message": "agent-test-bench-001"})
    # Regression test: press.api.bench.new's new_release_group() does
    # `app["name"]`/`app["source"]` — NOT `app["app"]`. A prior version of this test (and the
    # implementation) used "app" as the key, which passed unit tests against a mock but caused
    # a real HTTP 500 KeyError against the live API. Confirmed live 2026-07-10 against a real
    # Frappe Cloud account (bench created successfully once fixed to "name").
    apps = [{"name": "frappe", "source": "SRC-frappe-049"}]
    result = client.benches.create(
        title="agent-test-bench-001",
        version="Version 15",
        cluster="UAE",
        apps=apps,
        server="server-1",
    )
    client.post.assert_called_once_with(
        "press.api.bench.new",
        {
            "bench": {
                "title": "agent-test-bench-001",
                "version": "Version 15",
                "cluster": "UAE",
                "apps": apps,
                "server": "server-1",
                "saas_app": "",
            }
        },
    )
    assert result == "agent-test-bench-001"


def test_bench_candidates_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": [{"name": "cand-1"}]})
    result = client.benches.candidates(filters={"status": "Success"}, order_by="creation desc", limit_start=0, limit_page_length=20)
    client.post.assert_called_once_with(
        "press.api.bench.candidates",
        {
            "filters": {"status": "Success"},
            "order_by": "creation desc",
            "limit_start": 0,
            "limit_page_length": 20,
        }
    )
    assert result == [{"name": "cand-1"}]
