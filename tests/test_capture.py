import json
from pathlib import Path

from discovery.capture import CapturedCall, PRESS_API_PATH_RE


def test_press_api_path_regex_extracts_method():
    url = "https://cloud.frappe.io/api/method/press.api.site.get_list?x=1"
    match = PRESS_API_PATH_RE.search(url)
    assert match is not None
    assert match.group(1) == "press.api.site.get_list"


def test_press_api_path_regex_ignores_non_press_calls():
    url = "https://cloud.frappe.io/api/method/frappe.client.get_list"
    assert PRESS_API_PATH_RE.search(url) is None


def test_captured_call_redacted_excludes_auth_fields():
    call = CapturedCall(
        method_path="press.api.site.get_list",
        http_method="POST",
        request_payload={"filters": {}},
        status=200,
        response_body={"message": []},
    )
    redacted = call.redacted()
    assert redacted["method_path"] == "press.api.site.get_list"
    assert "authorization" not in json.dumps(redacted).lower()


def test_capture_save_writes_json(tmp_path: Path):
    from discovery.capture import NetworkCapture

    capture = NetworkCapture.__new__(NetworkCapture)  # bypass __init__, no browser needed
    capture.calls = [
        CapturedCall(
            method_path="press.api.site.get_list",
            http_method="POST",
            request_payload=None,
            status=200,
            response_body={"message": []},
        )
    ]
    capture.console_errors = []
    out_file = tmp_path / "capture.json"
    capture.save(str(out_file))

    data = json.loads(out_file.read_text())
    assert data["calls"][0]["method_path"] == "press.api.site.get_list"
    assert data["console_errors"] == []
