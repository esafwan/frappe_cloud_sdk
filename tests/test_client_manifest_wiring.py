import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from frappe_cloud import FrappeCloudClient
from frappe_cloud.core.manifest import OwnershipError


def test_manifest_is_none_by_default():
    client = FrappeCloudClient(api_key="k", api_secret="s")
    assert client.manifest is None


def test_manifest_path_constructs_a_usable_manifest(tmp_path):
    client = FrappeCloudClient(api_key="k", api_secret="s", manifest_path=str(tmp_path / "manifest.json"))
    assert client.manifest is not None
    client.manifest.register(name="agent-test-bench-001", resource_type="bench")
    assert client.manifest.is_owned("agent-test-bench-001") is True


def test_manifest_blocks_writes_to_unowned_resources(tmp_path):
    client = FrappeCloudClient(api_key="k", api_secret="s", manifest_path=str(tmp_path / "manifest.json"))
    with pytest.raises(OwnershipError):
        client.manifest.verify_ownership("someone-elses-production-site.frappe.cloud")
