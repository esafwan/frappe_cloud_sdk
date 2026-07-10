import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unittest.mock import MagicMock
from frappe_cloud import FrappeCloudClient


def make_client():
    return FrappeCloudClient(api_key="k", api_secret="s")


def test_sites_list_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": [{"name": "site-1"}]})
    result = client.sites.list()
    client.post.assert_called_once_with("press.api.site.all", {"site_filter": None})
    assert result == [{"name": "site-1"}]


def test_sites_get_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": {"name": "site-1"}})
    result = client.sites.get("site-1")
    client.post.assert_called_once_with("press.api.site.get", {"name": "site-1"})
    assert result == {"name": "site-1"}


def test_sites_installed_apps_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": [{"app": "frappe"}]})
    result = client.sites.installed_apps("site-1")
    client.post.assert_called_once_with("press.api.site.installed_apps", {"name": "site-1"})
    assert result == [{"app": "frappe"}]


def test_sites_available_apps_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": [{"app": "erpnext"}]})
    result = client.sites.available_apps("site-1")
    client.post.assert_called_once_with("press.api.site.available_apps", {"name": "site-1"})
    assert result == [{"app": "erpnext"}]


def test_sites_install_app_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": "queued"})
    result = client.sites.install_app("site-1", "erpnext", plan="Plan A")
    client.post.assert_called_once_with(
        "press.api.site.install_app", {"name": "site-1", "app": "erpnext", "plan": "Plan A"}
    )
    assert result == {"message": "queued"}


def test_sites_uninstall_app_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": "queued"})
    result = client.sites.uninstall_app("site-1", "erpnext")
    client.post.assert_called_once_with(
        "press.api.site.uninstall_app", {"name": "site-1", "app": "erpnext"}
    )
    assert result == {"message": "queued"}


def test_sites_backup_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": "job-123"})
    result = client.sites.backup("site-1", with_files=True)
    client.post.assert_called_once_with(
        "press.api.site.backup", {"name": "site-1", "with_files": True}
    )
    assert result == "job-123"


def test_sites_list_backups_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": [{"backup": "b1"}]})
    result = client.sites.list_backups("site-1")
    client.post.assert_called_once_with("press.api.site.backups", {"name": "site-1"})
    assert result == [{"backup": "b1"}]


def test_sites_restore_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": "job-456"})
    files = {"database": "db.sql.gz"}
    result = client.sites.restore("agent-test-restore-1", files, skip_failing_patches=True)
    client.post.assert_called_once_with(
        "press.api.site.restore",
        {"name": "agent-test-restore-1", "files": files, "skip_failing_patches": True},
    )
    assert result == "job-456"


def test_sites_domains_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": [{"domain": "example.com"}]})
    result = client.sites.domains("site-1")
    client.post.assert_called_once_with("press.api.site.domains", {"name": "site-1"})
    assert result == [{"domain": "example.com"}]


def test_sites_add_domain_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": "ok"})
    result = client.sites.add_domain("site-1", "sandbox.example.com")
    client.post.assert_called_once_with(
        "press.api.site.add_domain", {"name": "site-1", "domain": "sandbox.example.com"}
    )
    assert result == {"message": "ok"}


def test_sites_jobs_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": [{"job": "j1"}]})
    result = client.sites.jobs(filters={"site": "site-1"}, order_by="creation desc", limit_start=0, limit_page_length=20)
    client.post.assert_called_once_with(
        "press.api.site.jobs",
        {
            "filters": {"site": "site-1"},
            "order_by": "creation desc",
            "limit_start": 0,
            "limit_page_length": 20,
        },
    )
    assert result == [{"job": "j1"}]


def test_sites_activities_calls_correct_endpoint():
    client = make_client()
    client.post = MagicMock(return_value={"message": [{"activity": "created"}]})
    result = client.sites.activities()
    client.post.assert_called_once_with(
        "press.api.site.activities",
        {
            "filters": None,
            "order_by": None,
            "limit_start": None,
            "limit_page_length": None,
        },
    )
    assert result == [{"activity": "created"}]
