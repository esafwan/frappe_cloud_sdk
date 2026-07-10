import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from frappe_cloud import FrappeCloudClient
from frappe_cloud.core.auth import ApiKeyAuth, AuthStrategy


def test_default_api_key_auth_sets_authorization_header():
    client = FrappeCloudClient(api_key="k", api_secret="s")
    assert client.session.headers["Authorization"] == "token k:s"


def test_missing_credentials_and_no_auth_raises():
    with pytest.raises(ValueError):
        FrappeCloudClient()


def test_explicit_api_key_auth_strategy_works():
    client = FrappeCloudClient(auth=ApiKeyAuth("k2", "s2"))
    assert client.session.headers["Authorization"] == "token k2:s2"


class FakeAuth(AuthStrategy):
    def apply(self, session):
        session.headers["X-Fake-Auth"] = "yes"


def test_custom_auth_strategy_is_applied():
    client = FrappeCloudClient(auth=FakeAuth())
    assert client.session.headers["X-Fake-Auth"] == "yes"
