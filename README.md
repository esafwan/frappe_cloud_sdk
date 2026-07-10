# Frappe Cloud Python SDK

A Python client for automating Frappe Cloud: bench provisioning, site lifecycle, app
management, configuration, backups, domains, async-job tracking, and dev-tool inspection.

Frappe Cloud ships no published public API, so this SDK is built from first principles: by
reading the open-source [`frappe/press`](https://github.com/frappe/press) backend (the code that
actually implements `press.api.*`) and by exercising every call against a real paid Frappe Cloud
account. Anything listed under [Supported functionality](#supported-functionality) below has been
confirmed to work against live infrastructure — not mocked.

The client talks to the same `press.api.*` RPC endpoints the Frappe Cloud dashboard uses, over
plain HTTPS with `requests`.

## Installation

```bash
pip install -r requirements.txt        # runtime: requests
pip install -r requirements-dev.txt    # dev/testing: pytest, playwright, python-dotenv
```

Use it as a local import (`sys.path.insert(0, ".../frappe_cloud_sdk")`) or install this directory
in editable mode. No PyPI package is published yet.

## Quickstart

### Authenticate with an API key (recommended)

```python
from frappe_cloud import FrappeCloudClient

client = FrappeCloudClient(api_key="your_api_key", api_secret="your_api_secret")
```

Generate a key pair under **Frappe Cloud Dashboard → Settings → Developer → API Access**. Capture
**both** values at generation time — Frappe only shows the secret once. API-key auth is the
primary, fully supported path.

### Authenticate with a browser session (alternative)

When no API key is available, the SDK can log in with a headless browser and reuse the resulting
session cookies and CSRF token:

```python
from frappe_cloud import FrappeCloudClient
from frappe_cloud.core.auth import BrowserSessionAuth

auth = BrowserSessionAuth(email="you@example.com", password="...")
client = FrappeCloudClient(auth=auth)
```

Requires Playwright (`pip install playwright && playwright install chromium`). This is a
documented, supported alternative; the API-key path above is the recommended default.

### First calls

```python
client.benches.list()
client.sites.list()
client.servers.list()

client.benches.get("bench-xxxxx")
client.sites.get("mysite.frappe.cloud")
```

## Supported functionality

Everything below is live-verified against a real Frappe Cloud account. Capabilities that are
broken, blocked by the platform, or never exercised are intentionally not listed.

### Benches — `client.benches`

- List and inspect benches: `list()`, `get(name)`.
- Creation inputs: `options()` (versions, clusters, and the real `AppSource` IDs needed by
  `create()`), and `exists(title)` to check whether a bench title is already taken (keyed on the
  bench **title**, not its generated `bench-xxxxx` name).
- Provision: `create(title, version, cluster, apps, ...)` — `apps` entries use the key `"name"`
  (plus `"source"`), not `"app"`.
- Config: `get_config(name)` / `update_config(name, config)`, where each row's `type` is one of
  `""`, `"String"`, `"Password"`, `"Number"`, `"Boolean"`, `"JSON"`.
- Apps: `list_apps(name)`, `installable_apps(name)`.
- Deploys: `deploy(name, apps)` (returns a job ID — poll it with
  `client.tracking.wait_for_bench_deploy()`), plus `deploy_status(name)` and
  `deploy_information(name)`.
- Dependencies: `dependencies(name)` / `update_dependencies(name, dependencies)` — pass a JSON
  **list** of `{"key", "value"}` dicts covering every dependency (a flat dict crashes server-side).
- Build/deploy history: `candidates(...)`, `candidate(name)`.

### Sites — `client.sites`

- List and inspect: `list()`, `get(name)`, and `is_subdomain_available(subdomain, domain)` (the SDK
  inverts the underlying endpoint, which returns `True` when a name is *taken*).
- Creation inputs: `new_site_options(group=None)` (versions, apps, clusters, plans).
- Provision: `create(name, apps, ...)` — subdomain is capped at 32 characters; to target a specific
  bench, pick a plan with `private_bench_support: 0` (e.g. `"USD 5"`), otherwise routing may ignore
  your `group`.
- Apps: `installed_apps(name)`, `available_apps(name)`.
- Lifecycle: `clear_cache(name)`, `migrate(name, skip_failing_patches=False)`.
- Backups: `backup(name, with_files=False)` (returns a job ID), `list_backups(name)`, and
  `validate_restoration_space(name, db_file_size, public_file_size=0, private_file_size=0)` — a
  non-destructive pre-restore disk-space check (byte sizes come from `list_backups()`'s output).
- Async state: `jobs(...)`, `job(job)`, `running_jobs(name)`, `activities(...)`.
- Update health: `check_for_updates(name)`, `last_migrate_failed(name)`.
- Logs: `list_logs(name)` and `get_log(name, log_name)` (plain filenames such as
  `"scheduler.log"`).
- Domains: `domains(name)`.

### Servers — `client.servers`

- `list(filters=None)` — returns the dedicated servers on the account (an empty list is a valid
  result for accounts without dedicated servers).

### Async tracking — `client.tracking`

Long-running operations (deploys, installs, migrations, backups) return a job/resource ID; poll it
to completion:

- `wait_for_job(job_name, ...)` — poll an Agent Job by name.
- `wait_for_bench_deploy(bench_name, ...)` — until `Active` / `Broken` / `Archived`.
- `wait_for_site_active(site_name, ...)` — until `Active` / `Broken` / `Archived` / `Suspended`.

### Dev tools — `client.devtools`

- `get_log(log_type, doc_name, log_name)` — formatted log entries from the log browser. `log_type`
  is `"site"` or `"bench"`, `doc_name` is the owning Site/Bench, and `log_name` is a filename
  sourced from `client.sites.list_logs()` (the log browser has no listing endpoint of its own).

### Low-level and safety

- Raw access: `client.post(path, json)` / `client.get(path, params)` for endpoints not yet wrapped,
  plus generic `get_doc(doctype, name)` and `run_doc_method(dt, dn, method, args)`.
- Typed exceptions (`frappe_cloud.core.exceptions`): `FrappeCloudError` → `APIError` →
  `AuthenticationError` (HTTP 401/403), `ValidationError` (HTTP 400/417). Each carries the real
  server message, `.status_code`, and `.raw_response`.
- Optional resource-safety manifest: pass `manifest_path="..."` to `FrappeCloudClient(...)` to get
  `client.manifest`, a `ResourceManifest` that generates run IDs, tracks only `agent-test-`-prefixed
  resources, fails closed on ownership checks, keeps an audit log, and supports one-way "adopted"
  promotion. Opt-in scaffolding for safe automation; not required for basic use.

## Known limitations

A short list of caveats worth knowing before you build on this:

- **No console/SSH access.** There is no `press.api` endpoint for console or SSH access, so it is
  not exposed by the SDK.
- **`benches.get_processes()` is permission-blocked** on normal team accounts — it raises
  `AuthenticationError` even for benches the account owns, and appears to require elevated/support
  access on Frappe Cloud's side.
- **Some reads need resources the account may not have.** `servers.get()`/`servers.usage()` require
  a dedicated server, and `sites.get_backup_link()` only succeeds for backups that have been pushed
  offsite (onsite-only backups carry no remote file to link to).
- **Restore itself is unverified and destructive.** The pre-check (`validate_restoration_space()`)
  is live-verified, but `sites.restore()` has not been exercised against real data — treat it as
  destructive regardless.
- **Serialize mutations per site.** Firing several mutating calls on one site in quick succession
  can surface a misleading `ValidationError: "Site is in pending state"` while `site.status` still
  reads `Active` — an in-flight Agent Job blocks new actions. Serialize mutating calls per site
  rather than running them concurrently.

## Error handling

Errors bubble up as typed `FrappeCloudError` subclasses. Watch for `AuthenticationError` (bad
keys, missing team access, or calling an endpoint your account tier cannot use even on its own
resources) and `ValidationError` (bad input: an invalid config type, a malformed payload, or a
business-rule violation such as a busy site). Both carry the real Frappe server message.

## Testing

```bash
# Unit tests (mocked HTTP, no live calls, no credentials needed)
pytest tests/ --ignore=tests/test_capture.py   # test_capture.py needs playwright installed

# Live verification (real account, real credentials via .env — see .env.example)
python verify/read_only.py           # list benches/sites/servers — safe, no writes
python verify/full_action_test.py    # read/write/error-probe pass against agent-owned resources
python verify/extra_live_tests.py    # read-only checks for the remaining unverified methods
```

`.env` (gitignored) needs either `FRAPPE_CLOUD_API_KEY` + `FRAPPE_CLOUD_API_SECRET` or
`FRAPPE_CLOUD_EMAIL` + `FRAPPE_CLOUD_PASSWORD` (the shorter aliases `FRAPPE_API_KEY`,
`FRAPPE_API_SECRET`, etc. are also accepted).
