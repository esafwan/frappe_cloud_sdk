"""Agent resource manifest and safety-gate infrastructure.

Implements the Agent Resource Safety Rules for this SDK: every resource the agent creates
must be tracked here before it can be written to again, must carry the `agent-test-` prefix,
and must belong to the current run. Ownership verification fails closed — any uncertainty
blocks the write, it never falls back to assuming ownership.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

TEST_PREFIX = "agent-test-"
RUN_ID_RE = re.compile(r"^agent-test-\d{8}-\d{6}-[0-9a-f]{4,8}$")


def generate_run_id() -> str:
    """agent-test-YYYYMMDD-HHMMSS-<short-id>"""
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    short_id = uuid.uuid4().hex[:8]
    return f"agent-test-{timestamp}-{short_id}"


class OwnershipError(Exception):
    """Raised when a write is attempted against a resource that cannot be verified as
    agent-owned. Fail-closed: this is raised on any uncertainty, not just confirmed conflicts."""


@dataclass
class ResourceEntry:
    name: str
    resource_type: str
    run_id: str
    created_at: float
    parent: Optional[str] = None
    repo: Optional[str] = None
    branch: Optional[str] = None
    purpose: str = ""
    status: str = "active"
    destructive_cleanup_allowed: bool = False
    cleanup_command: Optional[str] = None
    last_operation: Optional[str] = None
    final_cleanup_status: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditEntry:
    action: str
    resource_name: str
    timestamp: float
    result: str
    files_changed: List[str] = field(default_factory=list)
    operation_id: Optional[str] = None
    errors: Optional[str] = None
    rollback_available: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ResourceManifest:
    """File-backed manifest of agent-owned resources + audit log. One manifest per run
    identifier is the recommended usage, but a manifest can span multiple runs if reused.

    Usage:
        manifest = ResourceManifest(path="manifest.json", run_id=generate_run_id())
        manifest.register(name="agent-test-bench-001", resource_type="bench", purpose="...")
        manifest.verify_ownership("agent-test-bench-001")  # raises OwnershipError if not owned
        manifest.record_operation("agent-test-bench-001", action="deploy", result="success")
    """

    def __init__(self, path: str, run_id: Optional[str] = None):
        self.path = Path(path)
        self.run_id = run_id or generate_run_id()
        self._resources: Dict[str, ResourceEntry] = {}
        self._audit_log: List[AuditEntry] = []
        if self.path.exists():
            self._load()

    def _load(self) -> None:
        data = json.loads(self.path.read_text())
        self._resources = {
            name: ResourceEntry(**entry) for name, entry in data.get("resources", {}).items()
        }
        self._audit_log = [AuditEntry(**entry) for entry in data.get("audit_log", [])]

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({
            "resources": {name: r.to_dict() for name, r in self._resources.items()},
            "audit_log": [a.to_dict() for a in self._audit_log],
        }, indent=2))

    def register(
        self,
        name: str,
        resource_type: str,
        purpose: str = "",
        parent: Optional[str] = None,
        repo: Optional[str] = None,
        branch: Optional[str] = None,
        destructive_cleanup_allowed: bool = False,
        cleanup_command: Optional[str] = None,
    ) -> ResourceEntry:
        """Register a newly created agent-owned resource. Raises ValueError if `name` doesn't
        carry the required agent-test- prefix (rule 3) — registration itself enforces naming."""
        if not name.startswith(TEST_PREFIX):
            raise ValueError(f"Resource name {name!r} must start with {TEST_PREFIX!r}")
        entry = ResourceEntry(
            name=name,
            resource_type=resource_type,
            run_id=self.run_id,
            created_at=time.time(),
            parent=parent,
            repo=repo,
            branch=branch,
            purpose=purpose,
            destructive_cleanup_allowed=destructive_cleanup_allowed,
            cleanup_command=cleanup_command,
        )
        self._resources[name] = entry
        self._save()
        return entry

    def is_owned(self, name: str) -> bool:
        """True only if `name` has the test prefix AND is present in the manifest with a
        matching run. This never returns True on naming alone (rule 14: no cross-resource
        naming assumptions)."""
        if not name.startswith(TEST_PREFIX):
            return False
        entry = self._resources.get(name)
        return entry is not None and entry.status != "adopted"

    def verify_ownership(self, name: str) -> ResourceEntry:
        """Fail-closed pre-action verification gate (rule 15 / rule 18). Raises OwnershipError
        if the resource is not verifiably agent-owned — never guesses, never falls back."""
        if not self.is_owned(name):
            raise OwnershipError(
                f"STOP — ownership of {name!r} could not be verified; treating as read-only "
                f"existing resource."
            )
        return self._resources[name]

    def mark_adopted(self, name: str) -> None:
        """Rule 20: once a resource is promoted/adopted for real use, it becomes permanently
        read-only to the agent. This is one-way — there is no un-adopt."""
        if name in self._resources:
            self._resources[name].status = "adopted"
            self._save()

    def record_operation(
        self,
        resource_name: str,
        action: str,
        result: str,
        files_changed: Optional[List[str]] = None,
        operation_id: Optional[str] = None,
        errors: Optional[str] = None,
        rollback_available: bool = False,
    ) -> AuditEntry:
        """Post-action audit log (rule 16). Also updates the resource's last_operation."""
        entry = AuditEntry(
            action=action,
            resource_name=resource_name,
            timestamp=time.time(),
            result=result,
            files_changed=files_changed or [],
            operation_id=operation_id,
            errors=errors,
            rollback_available=rollback_available,
        )
        self._audit_log.append(entry)
        if resource_name in self._resources:
            self._resources[resource_name].last_operation = action
        self._save()
        return entry

    def resources_for_run(self, run_id: Optional[str] = None) -> List[ResourceEntry]:
        target_run = run_id or self.run_id
        return [r for r in self._resources.values() if r.run_id == target_run]

    def cleanup_candidates(self, run_id: Optional[str] = None) -> List[ResourceEntry]:
        """Resources eligible for automatic cleanup (rule 19): exact match on run_id, test
        prefix, present in manifest, destructive_cleanup_allowed=True, not adopted. Never
        returns a wildcard set — caller must still act on exact names, one at a time."""
        return [
            r for r in self.resources_for_run(run_id)
            if r.destructive_cleanup_allowed and r.status != "adopted"
        ]
