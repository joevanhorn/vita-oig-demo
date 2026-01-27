# GitHub Actions Workflows

This document describes all GitHub Actions workflows in this repository.

## Active Production Workflows

### Apply Admin Labels (Environment-Agnostic)
**File:** `.github/workflows/apply-admin-labels.yml`

**Purpose:** Automatically finds and labels admin entitlements with the "Privileged" label

**Trigger:** Manual (`workflow_dispatch`)

**Parameters:**
- `environment` - Target environment (myorg, production, etc.) **REQUIRED**
- `dry_run` - Set to `true` to preview changes without applying (default: `true`)

**What It Does:**
1. Queries all entitlement bundles from Okta
2. Filters for bundles with "admin" in name or description
3. Applies "Privileged" label to matching resources
4. Supports batching for API limits (10 resources per request)

**Usage:**
```bash
# Dry run
gh workflow run apply-admin-labels.yml -f environment=myorg -f dry_run=true

# Apply labels
gh workflow run apply-admin-labels.yml -f environment=myorg -f dry_run=false
```

**Results:** Creates 16 admin entitlements labeled as Privileged

---

### Validate Labels API (Environment-Agnostic)
**File:** `.github/workflows/validate-labels.yml`

**Purpose:** Validates the Labels API integration and verifies label assignments

**Trigger:** Manual (`workflow_dispatch`)

**Parameters:**
- `environment` - Target environment (myorg, production, etc.) **REQUIRED**

**What It Does:**
1. Tests API connection
2. Lists all labels with their IDs
3. Retrieves individual label details
4. Queries resources assigned to each label
5. Validates data structure
6. Compares with exported data

**Usage:**
```bash
gh workflow run validate-labels.yml -f environment=myorg
```

**Validation Checks:**
- ✅ API connectivity
- ✅ Label enumeration
- ✅ Label detail retrieval
- ✅ Resource-label queries
- ✅ Data structure validation

---

### Export OIG Resources (Environment-Agnostic)
**File:** `.github/workflows/export-oig.yml`

**Purpose:** Exports OIG API-only resources (Labels and Resource Owners) to JSON

**Trigger:** Manual (`workflow_dispatch`)

**Parameters:**
- `environment` - Target environment (myorg, production, etc.) **REQUIRED**
- `export_labels` - Export governance labels (default: `true`)
- `export_owners` - Export resource owners (default: `false`)
- `resource_orns` - Space-separated list of resource ORNs for owner export (optional)

**What It Does:**
1. Exports current labels and their assignments
2. Optionally exports resource owner assignments for specified resources
3. Saves to `oig-exports/{environment}/latest.json`
4. Creates timestamped backup
5. Commits to repository

**Usage:**
```bash
# Export labels only (default)
gh workflow run export-oig.yml -f environment=myorg

# Export labels only (explicit)
gh workflow run export-oig.yml -f environment=myorg -f export_labels=true -f export_owners=false

# Export both labels and owners (requires resource ORNs)
gh workflow run export-oig.yml \
  -f environment=myorg \
  -f export_labels=true \
  -f export_owners=true \
  -f resource_orns="orn:okta:idp:org:apps:oauth2:0oa123 orn:okta:directory:org:groups:00g456"

# Export owners only for specific resources
gh workflow run export-oig.yml \
  -f environment=myorg \
  -f export_labels=false \
  -f export_owners=true \
  -f resource_orns="orn:okta:governance:org:entitlement-bundles:enb789"
```

**Output:** JSON file in `oig-exports/myorg/`

**Note:** Resource owners export requires specific resource ORNs to be provided via the `resource_orns` parameter.

---

### Apply Resource Owners (Environment-Agnostic)
**File:** `.github/workflows/apply-owners.yml`

**Purpose:** Applies resource owner assignments from `config/owner_mappings.json` to Okta

**Trigger:** Manual (`workflow_dispatch`)

**Parameters:**
- `environment` - Target environment (myorg, production, etc.) **REQUIRED**
- `dry_run` - Preview changes without applying (default: `true`)

**What It Does:**
1. Loads owner assignments from `environments/{environment}/config/owner_mappings.json`
2. Assigns owners to apps, groups, and entitlement bundles
3. Reports success/failure for each resource
4. Supports dry-run mode for safe previewing

**Usage:**
```bash
# Dry run (preview changes)
gh workflow run apply-owners.yml -f environment=myorg -f dry_run=true

# Apply owners
gh workflow run apply-owners.yml -f environment=myorg -f dry_run=false
```

**Prerequisites:**
- `config/owner_mappings.json` must exist (run sync workflow or create manually)
- Owner mappings should follow the structure defined in the config template

**Results:** Creates artifact with full log and owner assignment results

---

### Import All Resources (Environment-Agnostic)
**File:** `.github/workflows/import-all-resources.yml`

**Purpose:** Complete import of Okta resources including base resources and OIG resources

**Trigger:** Manual (`workflow_dispatch`)

**Parameters:**
- `tenant_environment` - Target environment (MyOrg, Production, etc.) **REQUIRED**
- `update_terraform` - Automatically update production-ready TF files (default: `false`)
- `commit_changes` - Commit imported files to repository (default: `false`)

**What It Does:**
1. Imports standard Okta resources using Terraformer
2. Imports OIG resources (entitlement bundles, reviews, sequences) via API
3. Generates Terraform configuration files (.tf)
4. Generates JSON exports with full API data
5. Creates terraform import commands
6. Optionally updates production files and commits to repo

**Usage:**
```bash
# Import and review (doesn't update or commit)
gh workflow run import-all-resources.yml -f tenant_environment=MyOrg

# Import and automatically update Terraform files
gh workflow run import-all-resources.yml \
  -f tenant_environment=MyOrg \
  -f update_terraform=true

# Import, update, and commit
gh workflow run import-all-resources.yml \
  -f tenant_environment=MyOrg \
  -f update_terraform=true \
  -f commit_changes=true
```

**Note:** This workflow replaces the following archived workflows:
- `myorg-import.yml`
- `myorg-import-oig.yml`
- `myorg-import-complete.yml`

Use `import-all-resources.yml` for all import operations going forward.

---

### Governance Setup (Environment-Agnostic)
**File:** `.github/workflows/governance-setup.yml`

**Purpose:** Initial setup of OIG governance features

**Trigger:** Manual (`workflow_dispatch`)

**Parameters:**
- `environment` - Target environment (myorg, production, etc.) **REQUIRED**

**What It Does:**
1. Creates initial OIG configuration
2. Sets up entitlements
3. Configures access reviews
4. Initializes catalog entries

**Usage:**
```bash
gh workflow run governance-setup.yml -f environment=myorg
```

---

## Investigation/Development Workflows

These workflows were used during development and are kept for reference:

### MyOrg - Investigate Labels API
**File:** `.github/workflows/myorg-investigate-labels-api.yml`

**Purpose:** Deep investigation of Labels API to troubleshoot 405 errors

**Status:** Investigation complete. Findings documented in `scripts/archive/README.md`

**Key Findings:**
- Labels API uses `labelId` not `name` in URLs
- Resource queries use `/resource-labels` with filter parameter
- Must use `labelValueId` for filtering, not `labelId`

---

### MyOrg - Test Label Endpoints
**File:** `.github/workflows/myorg-test-label-endpoints.yml`

**Purpose:** Test various endpoint patterns to find correct API syntax

**Status:** Investigation complete. Correct endpoint identified as `POST /resource-labels/assign`

---

### Apply Labels (Environment-Agnostic)
**File:** `.github/workflows/apply-labels.yml`

**Purpose:** Apply governance labels to resources

**Status:** Superseded by `apply-admin-labels.yml` and `apply-labels-from-config.yml`

---

## Workflow Dependencies

### Environment Secrets Required

All environment-specific workflows require these secrets to be configured in the corresponding GitHub environment (e.g., `MyOrg`, `Production`):

- `OKTA_API_TOKEN` - API token with governance scopes
- `OKTA_ORG_NAME` - Okta organization name
- `OKTA_BASE_URL` - Base URL (e.g., `okta.com` or `oktapreview.com`)

**Note:** Workflows now require an `environment` parameter to select which environment's secrets to use.

### Permissions

Workflows use these permissions:
- `contents: write` - For committing export files
- `actions: read` - For workflow information

## Workflow Patterns

### Standard Workflow Structure

Most workflows follow this pattern:

1. **Safety Check** - Display environment and operation details
2. **Checkout** - Get latest code
3. **Setup** - Install Python, dependencies
4. **Execute** - Run the main operation
5. **Results** - Parse and display results
6. **Artifacts** - Upload logs and outputs
7. **Summary** - Post GitHub step summary

### Error Handling

- All workflows capture full logs
- Artifacts retained for 30-90 days
- Detailed summaries posted to workflow run
- Failed steps clearly marked

## Best Practices

1. **Always dry-run first** - For workflows with dry-run mode
2. **Review artifacts** - Check uploaded logs for details
3. **Monitor summaries** - GitHub step summaries show key results
4. **Use manual triggers** - Most workflows are manual to prevent accidents
5. **Check permissions** - Ensure environment secrets are configured

## Adding New Workflows

When creating new workflows:

1. Use the `MyOrg` environment
2. Follow the standard structure pattern
3. Include comprehensive error handling
4. Upload artifacts for debugging
5. Post detailed summaries
6. Document in this file
7. Add appropriate triggers

## Troubleshooting

### Workflow Won't Run
- Check environment is configured
- Verify secrets are set
- Ensure proper permissions

### API Errors
- Verify API token has correct scopes
- Check rate limiting
- Review artifact logs for details

### Unexpected Results
- Download artifacts for full logs
- Check step summaries for errors
- Compare with expected output in documentation

## Related Documentation

- [Labels API Validation](./LABELS_API_VALIDATION.md)
- [API Management Guide](./API_MANAGEMENT.md)
- [OIG Manual Import](./OIG_MANUAL_IMPORT.md)
- [Config README](../config/README.md)
