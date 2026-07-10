import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unittest.mock import MagicMock
from frappe_cloud import FrappeCloudClient


def make_client():
    return FrappeCloudClient(api_key="k", api_secret="s")


def test_devtools_get_log_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": [{"line": "log contents here"}]})
    result = client.devtools.get_log("bench", "site-1", "bench.log")
    assert result == [{"line": "log contents here"}]
    client.post.assert_called_once_with(
        "press.api.log_browser.get_log",
        {"log_type": "bench", "doc_name": "site-1", "log_name": "bench.log"},
    )


def test_devtools_get_log_returns_none_when_missing():
    client = make_client()
    client.post = MagicMock(return_value={})
    result = client.devtools.get_log("worker", "site-2", "worker.log")
    assert result is None
