# MyOrg Environment Setup Guide

This guide walks you through setting up the **MyOrg** GitHub environment for safe, import-only operations on your primary demo tenant.

---

## 🚨 Critical Safety Notice

**MyOrg is a PRIMARY DEMO TENANT** - we use strict safeguards to prevent accidental modifications:

- ✅ **Import-only operations** by default
- ✅ **Manual approval required** for any apply operations
- ✅ **Protected workflows** that cannot modify resources without explicit approval
- ✅ **Comprehensive resource export** including OIG features (entitlements, labels, owners)

---

## Table of Contents

1. [GitHub Environment Setup](#github-environment-setup)
2. [Secrets Configuration](#secrets-configuration)
3. [Protection Rules](#protection-rules)
4. [Workflow Usage](#workflow-usage)
5. [Importing OIG Resources](#importing-oig-resources)

---

## GitHub Environment Setup

### Step 1: Create the Environment

1. **Navigate** to your GitHub repository
2. Go to **Settings** → **Environments**
3. Click **New environment**
4. Name it: `MyOrg`
5. Click **Configure environment**

### Step 2: Configure Protection Rules

**Deployment Protection Rules:**

1. ☑️ **Required reviewers**
   - Add yourself and/or team members
   - Minimum: 1 reviewer required

2. ☑️ **Wait timer** (Optional but recommended)
   - Set to: 5 minutes
   - Gives you time to cancel accidental deployments

3. ☑️ **Deployment branches** (Recommended)
   - Select: **Protected branches only**
   - Or specify: `main` branch only
   - Prevents deployments from feature branches

**Why these rules?**
- **Required reviewers**: No automated apply can run without human approval
- **Wait timer**: Buffer time to catch mistakes
- **Branch restrictions**: Only trusted branches can deploy

---

## Secrets Configuration

Add these secrets specifically to the **MyOrg** environment:

### Navigate to Secrets

1. In the **MyOrg** environment settings
2. Scroll to **Environment secrets**
3. Click **Add secret** for each:

### Required Secrets

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `OKTA_ORG_NAME` | `demo-myorg` | Your Okta org subdomain |
| `OKTA_BASE_URL` | `oktapreview.com` | Your Okta base URL |
| `OKTA_API_TOKEN` | `<your-api-token>` | API token with governance scopes |

### API Token Permissions Required

Your API token must have these scopes:

**Basic Resources:**
- `okta.users.read`
- `okta.groups.read`
- `okta.apps.read`
- `okta.authorizationServers.read`
- `okta.policies.read`
- `okta.idps.read`
- `okta.trustedOrigins.read`
- `okta.networkZones.read`

**OIG/Governance (for export):**
- `okta.governance.accessRequests.read`
- `okta.governance.accessReviews.read`
- `okta.governance.catalogs.read`

**Note:** Read-only scopes are sufficient for import/export operations. We do NOT use `manage` scopes to prevent accidental modifications.

---

## Protection Rules

### Environment Configuration

```yaml
Environment: MyOrg
├── Protection Rules:
│   ├── Required Reviewers: 1+ (YOU)
│   ├── Wait Timer: 5 minutes (optional)
│   └── Deployment Branches: main only
│
├── Secrets:
│   ├── OKTA_ORG_NAME: demo-myorg
│   ├── OKTA_BASE_URL: oktapreview.com
│   └── OKTA_API_TOKEN: <redacted>
│
└── Workflows Allowed:
    ├── myorg-import.yml (import standard resources)
    └── myorg-export-oig.yml (export OIG resources with modular approach)
```

### What Gets Protected

✅ **terraform apply** - Requires manual approval
✅ **terraform destroy** - Blocked entirely
✅ **Resource modifications** - Requires approval
❌ **terraform plan** - Allowed (read-only)
❌ **terraform import** - Allowed (read-only)
❌ **Export scripts** - Allowed (read-only)

---

## Workflow Usage

### Available Workflows

#### 1. **Import Existing Resources** (Safe - Read-only)

```bash
# Triggers: Manual or scheduled weekly
# File: .github/workflows/myorg-import.yml
```

**What it does:**
- Imports ALL existing Okta resources using Terraformer
- Filters out admin users and system apps
- Organizes resources by type
- Creates import report
- **Does NOT apply changes** - import-only

**How to run:**
1. Go to **Actions** → **MyOrg - Import Resources**
2. Click **Run workflow**
3. Select branch: `main`
4. Click **Run workflow**

**No approval needed** - this is read-only

#### 2. **Export OIG Resources** (Safe - Read-only)

```bash
# Triggers: Manual
# File: .github/workflows/myorg-export-oig.yml
```

**What it does:**
- **Modular export** of labels, entitlements, and resource owners
- Gracefully handles partial OIG availability (not every app has entitlement management enabled)
- Treats HTTP 400/404 as "not_available" instead of errors
- Creates JSON files with current state and export report
- Uploads as artifacts
- **Does NOT modify anything** - export-only

**How to run:**
1. Go to **Actions** → **MyOrg OIG Export**
2. Click **Run workflow**
3. **Approve** the deployment (required for environment protection)
4. Review the export commit in the repository

**Note:** While read-only, approval is required due to environment protection rules

**What happens:**
- Export runs and collects OIG resources
- Results are committed to `oig-exports/myorg/`
- Files created: `latest.json` and `YYYY-MM-DD.json`
- Also uploaded as artifact for backup (180 days retention)

#### 3. **Plan Changes** (Safe - Read-only)

```bash
# Triggers: Manual or on PR to main
# File: .github/workflows/myorg-plan.yml
```

**What it does:**
- Runs `terraform plan` to show what WOULD change
- Posts plan as PR comment
- **Does NOT apply** - planning only

**How to run:**
- Automatically runs on PRs
- Or manually trigger from Actions tab

**No approval needed** - this is read-only

#### 4. **Apply Changes** (DANGEROUS - Requires Approval)

```bash
# Triggers: Manual only
# File: .github/workflows/myorg-apply.yml
```

**What it does:**
- Applies Terraform changes to MyOrg
- **CAN MODIFY YOUR TENANT** - use with extreme caution

**How to run:**
1. Go to **Actions** → **MyOrg - Apply Changes**
2. Click **Run workflow**
3. **WAIT** for required reviewer approval
4. Reviewer must explicitly approve
5. Optional 5-minute wait timer
6. Then applies

**⚠️ REQUIRES APPROVAL** - protected operation

---

## Importing OIG Resources

MyOrg includes **Okta Integration Network** apps and other complex resources not supported by Terraformer. We have custom scripts for these:

### Supported OIG Imports

| Resource Type | Import Method | Output Format |
|--------------|---------------|---------------|
| **Entitlements** | API export script | JSON |
| **Resource Owners** | API export script | JSON |
| **Labels** | API export script | JSON |
| **Access Reviews** | Terraformer (if available) | `.tf` files |
| **Request Settings** | Terraformer (if available) | `.tf` files |

### Running OIG Export

**Method 1: GitHub Actions (Recommended)**

```bash
# Trigger the export workflow
Actions → MyOrg OIG Export → Run workflow
```

The workflow uses the modular `okta_api_manager.py` script with the following features:
- **Modular exports**: Labels, entitlements, and resource owners are exported independently
- **Graceful error handling**: If labels aren't available (HTTP 400/404), export continues with "not_available" status
- **Status tracking**: Each export type reports its own status (success/not_available/error)
- **Rate limiting**: Automatic handling with exponential backoff

**Method 2: Local Export**

```bash
# Set environment variables
export OKTA_ORG_NAME="demo-myorg"
export OKTA_BASE_URL="oktapreview.com"
export OKTA_API_TOKEN="<your-api-token>"

# Run modular export script
python3 scripts/okta_api_manager.py \
  --action export_oig \
  --org-name $OKTA_ORG_NAME \
  --base-url $OKTA_BASE_URL \
  --api-token $OKTA_API_TOKEN \
  --output myorg_oig_export.json \
  --export-labels \
  --export-entitlements
  # Add --export-owners --resource-orns <orns> to export resource owners
```

**Output:**

```json
{
  "export_date": "2025-11-07T01:59:19Z",
  "okta_org": "demo-myorg",
  "okta_base_url": "oktapreview.com",
  "export_status": {
    "labels": "not_available",
    "entitlements": "success"
  },
  "labels": [],
  "entitlements": [
    {
      "id": "ent123...",
      "name": "Entitlement Name",
      "description": "Description",
      "principals": [
        {
          "orn": "orn:okta:directory:demo-myorg:users:00u123",
          "email": "user@example.com"
        }
      ],
      "resources": [
        {
          "orn": "orn:okta:idp:demo-myorg:apps:oauth2:0oa456",
          "name": "App Name"
        }
      ]
    }
  ]
}
```

**Export Status Codes:**
- `success` - Export completed successfully
- `not_available` - Resource type not available (HTTP 400/404) - OIG may not be fully enabled
- `error` - Export failed with an error
- `skipped` - Export was not requested (e.g., resource owners without --resource-orns)

### Importing Exported Data

**To import the exported OIG data into a new environment:**

```bash
# View export data to understand what will be imported
cat myorg_oig_export.json | jq '.export_status'

# Import using okta_api_manager.py
# Note: This is a placeholder - full import functionality may require custom implementation
# For now, exported data can be used for documentation, drift detection, and manual recreation
python3 scripts/okta_api_manager.py \
  --action apply \
  --config myorg_oig_export.json \
  --org-name <new-org-name> \
  --api-token <new-api-token>
```

**Important:** The export is primarily designed for:
1. **Documentation** - Capturing current OIG configuration state
2. **Drift detection** - Comparing exports over time
3. **Manual recreation** - Reference for setting up OIG in new tenants
4. **Backup** - Record of entitlement assignments and labels

---

## Special Considerations for MyOrg

### Okta Integration Network Apps

**Challenge:** OIN apps have special configurations that Terraformer may not fully capture.

**Solution:**

1. **Export app settings** using custom script:
   ```bash
   python3 scripts/export_oin_apps.py \
     --org-name demo-terraform-test-example
   ```

2. **Review app configurations** manually
   - Some OIN apps require manual setup
   - Custom SAML/OIDC configurations may need adjustment
   - Provisioning settings are app-specific

3. **Document custom configurations** in separate files
   - See `docs/OIN_APPS.md` for detailed configurations
   - Include screenshots for complex setups

### Entitlement Management

**Important:** Entitlement Management must be enabled per-application:

1. **Identify apps with entitlements:**
   ```bash
   # Export will show which apps have entitlement management enabled
   python3 scripts/export_oig_resources.py --list-entitlement-apps
   ```

2. **For each app:**
   - Note current provisioning status
   - Document entitlement bundles
   - Export entitlement assignments

3. **When recreating:**
   - Disable provisioning
   - Enable entitlement management (GUI)
   - Wait 1-2 minutes
   - Re-enable provisioning

---

## Troubleshooting

### Issue: Workflow requires approval but none requested

**Solution:**
1. Check GitHub Settings → Environments → MyOrg
2. Ensure "Required reviewers" includes active users
3. Check email for approval notification

### Issue: API token errors during export

**Solution:**
1. Verify token has governance scopes:
   ```bash
   curl -H "Authorization: SSWS $OKTA_API_TOKEN" \
     https://demo-myorg.oktapreview.com/api/v1/governance/entitlements
   ```
2. Token may have expired - generate new token
3. Update GitHub secret with new token

### Issue: Labels export shows "not_available" status

**This is expected** when:
- Labels endpoint is not fully enabled in your org
- No labels exist yet
- API token lacks label management scopes

**This is NOT an error** - the export continues gracefully:
```json
{
  "export_status": {
    "labels": "not_available",
    "entitlements": "success"
  }
}
```

### Issue: Some resources not imported

**Possible causes:**
- Resource type not supported by Terraformer
- API token lacks read permissions
- Resource is Okta-managed (system apps)

**Solution:**
- Check import log for errors
- Use custom export scripts for OIG resources
- Review `docs/TERRAFORMER_OIG_FAQ.md` for limitations

---

## Workflow Files Reference

### Created for MyOrg

```
.github/workflows/
├── myorg-import.yml      # Import all resources (safe)
├── myorg-export-oig.yml  # Export OIG resources (safe)
├── myorg-plan.yml        # Plan changes (safe)
└── myorg-apply.yml       # Apply changes (PROTECTED)
```

### Scripts Used

```
scripts/
├── okta_api_manager.py           # Modular OIG export/import with graceful error handling
└── protect_admin_users.py       # Filter admin users from imports
```

**Key Script Features:**
- **Modular architecture**: Separate functions for labels, entitlements, resource owners
- **Graceful error handling**: Continues on partial OIG availability
- **Status tracking**: Reports success/not_available/error for each export type
- **Rate limiting**: Automatic retry with exponential backoff
- **CLI arguments**: `--export-labels`, `--export-entitlements`, `--export-owners`

---

## Quick Reference

### Safe Operations (No Approval Needed)

```bash
# Import all resources
Actions → MyOrg - Import Resources → Run

# Export OIG resources
Actions → MyOrg - Export OIG → Run

# Plan changes
Actions → MyOrg - Plan → Run
```

### Protected Operations (Requires Approval)

```bash
# Apply terraform changes
Actions → MyOrg - Apply → Run → WAIT FOR APPROVAL → Approves
```

### Local Operations

```bash
# Export OIG locally with modular options
python3 scripts/okta_api_manager.py \
  --action export_oig \
  --org-name demo-myorg \
  --base-url oktapreview.com \
  --api-token $OKTA_API_TOKEN \
  --output oig_export.json \
  --export-labels \
  --export-entitlements

# View current state
terraform plan  # Safe - read-only

# Apply changes (USE WITH CAUTION)
terraform apply  # Dangerous - modifies tenant
```

---

## Next Steps

1. ✅ **Create MyOrg environment** in GitHub UI (Settings → Environments)
2. ✅ **Add secrets** (OKTA_ORG_NAME, OKTA_BASE_URL, OKTA_API_TOKEN)
3. ✅ **Configure protection rules** (required reviewers, wait timer)
4. ✅ **Run initial import** to baseline current state
5. ✅ **Export OIG resources** to capture entitlements/owners/labels
6. ✅ **Review imported resources** and document customizations
7. ✅ **Test plan workflow** to verify everything works
8. ⚠️ **Never run apply** without explicit approval and review

---

## Support

**Questions or issues?**
- Check existing import logs in Actions → Workflow runs
- Review `docs/TERRAFORMER_OIG_FAQ.md` for known limitations
- See `docs/LESSONS_LEARNED.md` for common issues
- Open GitHub issue for repository-specific problems

---

Last updated: 2025-11-07
