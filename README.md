# Frappe Cloud Python SDK (WIP)

> ⚠️ **Unofficial**: Frappe Cloud has no published public API docs. This SDK is built by
> reading the open-source [`frappe/press`](https://github.com/frappe/press) backend (the code
> that actually implements `press.api.*`) and by live-testing calls against a real account —
> not by guessing. Every method below is marked with its verification status (see the API
> Reference section).

A Python client for automating Frappe Cloud: bench provisioning, site lifecycle, app
management, config, backups, domains, and dev-tool inspection.

## Status

Core CRUD for benches and sites is implemented and **live-verified** against a real paid
Frappe Cloud account (not just unit-tested against mocks): listing, creating, deploying,
configuring, and inspecting benches and sites all work. Exception handling is solid — every
deliberately-broken live call raised the correctly-typed exception. See
[Known limitations](#known-limitations) before relying on this for anything beyond exploration.

## Installation

```bash
pip install -r requirements.txt        # runtime: requests
pip install -r requirements-dev.txt    # dev/testing: pytest, playwright, python-dotenv
```

No PyPI package yet — use as a local import (`sys.path.insert(0, ".../frappe_cloud_sdk")` or
install in editable mode from this directory).

## Quickstart

### Auth: API key (recommended when available)

```python
from frappe_cloud import FrappeCloudClient

client = FrappeCloudClient(api_key="your_api_key", api_secret="your_api_secret")
```

Generate a key pair: Frappe Cloud Dashboard → Settings → Developer → API Access. **Both**
`api_key` and `api_secret` must be captured at generation time — Frappe only shows the secret
once.

### Auth: browser session (fallback, no API key needed)

```python
from frappe_cloud import FrappeCloudClient
from frappe_cloud.core.auth import BrowserSessionAuth

auth = BrowserSessionAuth(email="you@example.com", password="...")
client = FrappeCloudClient(auth=auth)
```

Requires Playwright (`pip install playwright && playwright install chromium`). Logs in with a
real headless browser and reuses the resulting session cookies + CSRF token. Useful when no API
key is available, or as a fallback if the API-key path gets rate-limited. **Not yet
live-verified end-to-end** — the login flow was written and unit-structure-tested, but real
verification so far used an already-authenticated browser tab directly, calling `press.api.*`
via in-page `fetch()`, which is the actual proven fallback technique so far (same idea as
`BrowserSessionAuth`, just driven manually rather than through this class).

### First calls

```python
# List everything
client.benches.list()
client.sites.list()
client.servers.list()

# Inspect one
client.benches.get("bench-xxxxx")
client.sites.get("mysite.frappe.cloud")
```

## API Reference

Organized by namespace (`client.<namespace>.<method>`). ✅ = live-verified against a real
account this project's session on 2026-07-10. 🟡 = implemented, unit-tested against mocks only,
not yet exercised live.

### `client.benches` (`frappe_cloud/services/benches.py`)

| Method | Verified | Notes |
|---|---|---|
| `list(server=None, bench_filter=None)` | ✅ | |
| `get(name)` | ✅ | |
| `options()` | ✅ | Returns `{versions, clusters}`; `versions[i].apps[j].source.name` is where to find real `AppSource` ids for `create()` |
| `exists(title)` | 🟡 | |
| `create(title, version, cluster, apps, server=None, saas_app="")` | ✅ | `apps` items need key `"name"`, not `"app"` — found via a live 500 error |
| `get_config(name)` / `update_config(name, config)` | ✅ | `config[i]["type"]` must be one of `"", "String", "Password", "Number", "Boolean", "JSON"` |
| `list_apps(name)` / `installable_apps(name)` | ✅ | |
| `add_app(name, source, app)` / `add_apps(name, apps)` | 🟡 (error path ✅) | Success path not yet exercised — would need a real bench rebuild |
| `remove_app(name, app)` | 🟡 | **Destructive** — agent-owned benches only |
| `deploy(name, apps)` | ✅ | Real build, returns a Job ID — poll with `client.tracking.wait_for_bench_deploy()` |
| `deploy_status(name)` / `deploy_information(name)` | ✅ | |
| `get_processes(name)` | ❌ blocked | `AuthenticationError: Not Permitted` even for the owning account — needs elevated/support access |
| `dependencies(name)` / `update_dependencies(name, dependencies)` | ✅ | `dependencies` must be a JSON **list** of `{"key","value"}` dicts covering every dependency — a flat dict crashes server-side with a bare `TypeError` |
| `candidates(...)` / `candidate(name)` | ✅ | Deploy/build history |

### `client.sites` (`frappe_cloud/services/sites.py`)

| Method | Verified | Notes |
|---|---|---|
| `list(site_filter=None)` / `get(name)` | ✅ | |
| `is_subdomain_available(subdomain, domain="frappe.cloud")` | ✅ (raw API level) | Real semantics: underlying endpoint returns `True` if the name is TAKEN — this method inverts that for you |
| `new_site_options(group=None)` | 🟡 | |
| `create(name, apps, version=..., plan=..., provider=..., cluster=..., domain=..., group=None, **kwargs)` | ✅ | **Subdomain limit: 32 chars**, undocumented, found via a live 417. Plan choice controls routing: a `private_bench_support`-enabled plan ignores your `group` and may provision a *different* bench; pick a plan with `private_bench_support: 0` (e.g. `"USD 5"`) to target a specific bench |
| `installed_apps(name)` / `available_apps(name)` | ✅ | |
| `install_app(name, app, plan=None)` / `uninstall_app(name, app)` | 🟡 (error path ✅) | |
| `deactivate(name)` / `activate(name)` | 🟡 | Maintenance mode |
| `clear_cache(name)` | ✅ | |
| `migrate(name, skip_failing_patches=False)` | ✅ | |
| `backup(name, with_files=False)` / `list_backups(name)` / `get_backup_link(name, backup, file)` | ✅ trigger+list; error path ✅ for get_backup_link | |
| `validate_restoration_space(name, files)` / `restore(name, files, skip_failing_patches=False)` | 🟡 not exercised | **Destructive** — real restores untested this session, recommended as next verification step |
| `change_server(name, server, ...)` | 🟡 | **Destructive** |
| `jobs(...)` / `job(job)` / `running_jobs(name)` / `activities(...)` | ✅ | |
| `check_for_updates(name)` / `last_migrate_failed(name)` | ✅ | |
| `list_logs(name)` / `get_log(name, log_name)` | ✅ | |
| `domains(name)` / `add_domain(name, domain)` / `remove_domain(name, domain)` | ✅ list; add tested against a fake domain (result inconclusive — see gotcha below) | |
| `reinstall(name)` | 🟡 | **Destructive** |
| `archive(name, force=False)` | 🟡 | **Destructive** |
| `schedule_update(...)` | 🟡 | |

### `client.servers` (`frappe_cloud/services/servers.py`)
`list(filters=None)` ✅ (returned empty — this account has no dedicated servers, a valid
result), `get(name)` 🟡, `usage(name)` 🟡 — the latter two untested because no server exists on
the test account to call them against.

### `client.devtools` (`frappe_cloud/services/devtools.py`)
`get_log(log_type, doc_name, log_name)` 🟡 — real signature confirmed against
`research/press/press/api/log_browser.py`, not yet exercised live. **No listing endpoint
exists** in the real API — source log names from `sites.list_logs()` instead.

### `client.tracking` (`frappe_cloud/services/tracking.py`) — async operation polling
- `wait_for_job(job_name, ...)` ✅ — polls an Agent Job by name (app installs, migrations, etc.)
- `wait_for_bench_deploy(bench_name, ...)` ✅ — polls a bench until `Active`/`Broken`/`Archived`
- `wait_for_site_active(site_name, ...)` ✅ — polls a site until `Active`/`Broken`/`Archived`/`Suspended`
- `wait_for_deploy(deploy_name, ...)` 🟡 — polls the older `Site Group Deploy` doctype used by
  `Sites.create()`'s original one-shot new-bench-and-site flow; not exercised this session since
  bench and site were created as two separate steps instead

### `client.database` (`frappe_cloud/services/database.py`)
`create_user(site_name, username, label="readonly")` 🟡, `archive_user(db_user_name)` 🟡 —
neither exercised.

### Core client (`frappe_cloud/core/client.py`)
- `FrappeCloudClient(api_key=None, api_secret=None, base_url=..., auth=None, manifest_path=None)`
- `.post(path, json=None)` / `.get(path, params=None)` — raw RPC calls, if you need an endpoint
  not yet wrapped
- `.get_doc(doctype, name)` / `.run_doc_method(dt, dn, method, args=None)` — generic Frappe
  document access via `press.api.client.*`
- `.manifest` — `None` unless `manifest_path` is passed at construction; see below

### Exceptions (`frappe_cloud/core/exceptions.py`)
`FrappeCloudError` (base) → `APIError` → `AuthenticationError` (HTTP 401/403),
`ValidationError` (HTTP 400/417). Every exception carries `.args[0]` (message, including the
real Frappe server message), `.status_code`, `.raw_response`. **Live-verified solid**: every
deliberately-broken call in this session's test pass raised the correctly-typed exception.

### Safety infrastructure (`frappe_cloud/core/manifest.py`) — optional, off by default
Implements the project's Agent Resource Safety Rules: pass `manifest_path="..."` to
`FrappeCloudClient(...)` to get `client.manifest`, a `ResourceManifest` that:
- generates run IDs (`generate_run_id()` → `agent-test-YYYYMMDD-HHMMSS-<short-id>`)
- only tracks resources whose name carries the `agent-test-` prefix (`register()` raises
  `ValueError` otherwise)
- fails closed on ownership checks (`verify_ownership()` raises `OwnershipError` for anything
  not explicitly registered — naming alone never implies ownership)
- keeps an audit log (`record_operation()`)
- supports one-way "adopted" promotion (`mark_adopted()` — once set, permanently un-ownable)

This is opt-in scaffolding for building safe automation on top of the SDK, not required for
basic use.

## Testing

```bash
# Unit tests (mocked HTTP, no live calls, no credentials needed)
pytest tests/ --ignore=tests/test_capture.py   # test_capture.py needs playwright installed

# Live verification (real account, real credentials via .env — see .env.example)
python verify/read_only.py           # list benches/sites/servers — safe, no writes
python verify/full_action_test.py    # exhaustive read+write+error-probe pass against
                                      # agent-owned test resources only
```

`.env` (gitignored) needs either `FRAPPE_CLOUD_API_KEY`+`FRAPPE_CLOUD_API_SECRET` or
`FRAPPE_CLOUD_EMAIL`+`FRAPPE_CLOUD_PASSWORD` (aliases `FRAPPE_API_KEY`/`FRAPPE_API_SECRET` etc.
also accepted).

## Known limitations

- **No app-install success path verified.** All live app-install testing hit deliberately
  invalid app names (to test error handling) — installing a *real* app onto a *real* site has
  not been exercised, because it requires adding that app to a bench and triggering a real
  rebuild.
- **Restore is unverified.** `sites.restore()` exists and is implemented but has never been
  called against real data.
- **Custom GitHub app sources are not implemented** — `bench.new`'s multi-step `App`/`AppSource`
  creation flow (needed before you can list a custom app as installable) isn't wrapped yet.
- **Console/SSH access is not implemented** — no dedicated `press.api` endpoint was found for
  it after checking `press.api.access`; it may not exist as a simple RPC call at all.
- **Concurrency**: triggering multiple mutating calls on the same site in quick succession (e.g.
  `migrate` then `backup` then `add_domain`) can produce a misleading
  `ValidationError: "Site is in pending state"` even while `site.status` reads `Active` —
  apparently caused by an in-flight Agent Job blocking new actions. Callers should serialize
  mutating calls per-site rather than firing them concurrently.

## Error Handling

The client uses standard exception bubbling via `FrappeCloudError`. Specifically, look out for
`AuthenticationError` (invalid API keys, lacking team access, or — confirmed live — calling an
endpoint your account doesn't have permission for even on your own resources) and
`ValidationError` (bad input: invalid config type, malformed payload, business-rule violations
like "site is busy"). Both carry the real Frappe server message.
