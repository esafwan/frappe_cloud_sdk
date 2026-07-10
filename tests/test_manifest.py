import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from frappe_cloud.core.manifest import (
    ResourceManifest,
    OwnershipError,
    generate_run_id,
    RUN_ID_RE,
)


def test_generate_run_id_matches_pattern():
    run_id = generate_run_id()
    assert RUN_ID_RE.match(run_id)


def test_register_rejects_missing_prefix(tmp_path):
    manifest = ResourceManifest(path=str(tmp_path / "manifest.json"))
    with pytest.raises(ValueError):
        manifest.register(name="prod-site-1", resource_type="site")


def test_register_valid_name_and_is_owned(tmp_path):
    manifest = ResourceManifest(path=str(tmp_path / "manifest.json"))
    manifest.register(name="agent-test-bench-001", resource_type="bench")
    assert manifest.is_owned("agent-test-bench-001") is True


def test_is_owned_false_for_unregistered_prefixed_name(tmp_path):
    manifest = ResourceManifest(path=str(tmp_path / "manifest.json"))
    assert manifest.is_owned("agent-test-never-registered") is False


def test_is_owned_false_for_name_without_prefix(tmp_path):
    manifest = ResourceManifest(path=str(tmp_path / "manifest.json"))
    manifest.register(name="agent-test-bench-001", resource_type="bench")
    assert manifest.is_owned("prod-bench-001") is False


def test_verify_ownership_raises_for_unowned(tmp_path):
    manifest = ResourceManifest(path=str(tmp_path / "manifest.json"))
    with pytest.raises(OwnershipError):
        manifest.verify_ownership("agent-test-unowned")


def test_verify_ownership_returns_entry_for_owned(tmp_path):
    manifest = ResourceManifest(path=str(tmp_path / "manifest.json"))
    manifest.register(name="agent-test-bench-001", resource_type="bench")
    entry = manifest.verify_ownership("agent-test-bench-001")
    assert entry.name == "agent-test-bench-001"


def test_record_operation_updates_audit_log_and_last_operation(tmp_path):
    manifest = ResourceManifest(path=str(tmp_path / "manifest.json"))
    manifest.register(name="agent-test-bench-001", resource_type="bench")
    manifest.record_operation(
        "agent-test-bench-001", action="deploy", result="success"
    )
    assert len(manifest._audit_log) == 1
    assert manifest._audit_log[0].action == "deploy"
    assert manifest._resources["agent-test-bench-001"].last_operation == "deploy"


def test_mark_adopted_makes_owned_fail_afterward(tmp_path):
    manifest = ResourceManifest(path=str(tmp_path / "manifest.json"))
    manifest.register(name="agent-test-bench-001", resource_type="bench")
    assert manifest.is_owned("agent-test-bench-001") is True
    manifest.mark_adopted("agent-test-bench-001")
    assert manifest.is_owned("agent-test-bench-001") is False


def test_cleanup_candidates_filters_correctly(tmp_path):
    manifest = ResourceManifest(path=str(tmp_path / "manifest.json"))
    manifest.register(
        name="agent-test-cleanup-me",
        resource_type="bench",
        destructive_cleanup_allowed=True,
    )
    manifest.register(
        name="agent-test-not-cleanup",
        resource_type="bench",
        destructive_cleanup_allowed=False,
    )
    manifest.register(
        name="agent-test-adopted",
        resource_type="bench",
        destructive_cleanup_allowed=True,
    )
    manifest.mark_adopted("agent-test-adopted")

    candidates = manifest.cleanup_candidates()
    names = {r.name for r in candidates}
    assert names == {"agent-test-cleanup-me"}


def test_manifest_persistence_across_instances(tmp_path):
    path = str(tmp_path / "manifest.json")
    manifest1 = ResourceManifest(path=path)
    manifest1.register(name="agent-test-persisted", resource_type="site")

    manifest2 = ResourceManifest(path=path)
    assert manifest2.is_owned("agent-test-persisted") is True
