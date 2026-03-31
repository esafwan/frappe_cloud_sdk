# Frappe Cloud Python SDK (WIP)

> ⚠️ **Work in Progress**: This SDK is currently in early development. The official Frappe Cloud API documentation has been removed/no longer exists for unknown reasons. This SDK is generated via experimental reverse-engineering of the dashboard API (the internal `press.api`). Features may change unexpectedly.

A Python interface for automating site provisioning, app installations, backups, and domains on Frappe Cloud.

## Installation

You can install dependencies using pip:
```bash
pip install -r requirements.txt
```
*(PyPI package coming soon)*

## Getting an API Key

To use this SDK, you need developer credentials for your Frappe Cloud team.
1. Log in to your [Frappe Cloud Dashboard](https://frappecloud.com/dashboard).
2. Go to **Settings** -> **Developer**.
3. Generate a new API Key. You will be given an **API Key** and **API Secret**. Save the secret somewhere secure, as it will only be shown once.

## Usage

Because it relies on standard REST patterns, the SDK is segmented into specific object namespaces (like `sites`, `apps`, `backups`).

```python
from frappe_cloud import FrappeCloudClient

# Initialize the client
client = FrappeCloudClient(
    api_key="your_api_key",
    api_secret="your_api_secret"
)

# 1. Provision a New Site
if client.sites.is_subdomain_available("my-new-erp", "frappe.cloud"):
    print("Subdomain available, deploying...")
    
    deploy_info = client.sites.create(
        name="my-new-erp",
        apps=["frappe", "erpnext"],
        version="Version 16"
    )
    
    # 2. Wait for deployment to finish (blocking polling)
    tracker_id = deploy_info.get("site_group_deploy")
    client.tracking.wait_for_deploy(tracker_id)
    print("Site created successfully!")

# 3. Add a matching custom domain
client.domains.add("my-new-erp.frappe.cloud", "erp.mycompany.com")

# 4. Trigger logical backup
client.backups.trigger("my-new-erp.frappe.cloud")
```

## Modules Available

- `client.sites` - Provision sites, check domains, handle updates/resets/archives.
- `client.apps` - List available/installed apps, install, and uninstall apps.
- `client.domains` - Verify DNS, manage domains.
- `client.backups` - Trigger logic/file backups and list backup records for restoration.
- `client.tracking` - Utility pollers for Agent Jobs and Deployments.
- `client.database` - Provision and archive remote Database users.

### Error Handling

The client uses standard exception bubbling via `FrappeCloudError`. 
Specifically, look out for `AuthenticationError` (e.g. invalid API keys or lacking team access) and `ValidationError` (e.g., DNS missing during domain validation, duplicate subdomain).
