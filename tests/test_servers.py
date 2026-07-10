import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unittest.mock import MagicMock
from frappe_cloud import FrappeCloudClient


def make_client():
    return FrappeCloudClient(api_key="k", api_secret="s")


def test_server_list_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": [{"name": "srv-1"}]})
    result = client.servers.list()
    assert result == [{"name": "srv-1"}]
    client.post.assert_called_once_with("press.api.server.all", {"filters": None})


def test_server_list_passes_filters():
    client = make_client()
    client.post = MagicMock(return_value={"message": [{"name": "srv-2"}]})
    result = client.servers.list(filters={"status": "Active"})
    assert result == [{"name": "srv-2"}]
    client.post.assert_called_once_with("press.api.server.all", {"filters": {"status": "Active"}})


def test_server_get_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": {"name": "srv-1", "status": "Active"}})
    result = client.servers.get("srv-1")
    assert result == {"name": "srv-1", "status": "Active"}
    client.post.assert_called_once_with("press.api.server.get", {"name": "srv-1"})


def test_server_usage_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": {"vcpu": 1.0, "memory": 2.0}})
    result = client.servers.usage("srv-1")
    assert result == {"vcpu": 1.0, "memory": 2.0}
    client.post.assert_called_once_with("press.api.server.usage", {"name": "srv-1"})


def test_server_get_defaults_to_empty_dict():
    client = make_client()
    client.post = MagicMock(return_value={})
    result = client.servers.get("srv-missing")
    assert result == {}
