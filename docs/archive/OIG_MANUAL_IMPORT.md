# Importing Existing OIG Configurations

## 🚨 Important Limitation

**Terraformer does NOT support OIG resources.** The new OIG resources introduced in Terraform Provider v6.1.0 must be imported manually or created fresh.

## ⚡ Automated Import (NEW!)

We now provide an **automated import script** that generates Terraform configurations and import commands for you!

### Quick Start

```bash
# Set your Okta credentials
export OKTA_ORG_NAME="your-org"
export OKTA_API_TOKEN="your-token"
export OKTA_BASE_URL="okta.com"  # or oktapreview.com

# Run the import script
python3 scripts/import_oig_resources.py --output-dir imported_oig

# Review generated files
ls imported_oig/

# Complete TODOs in generated .tf files, then:
cd imported_oig
terraform init
./import.sh
terraform plan  # Should show no changes
```

### What Gets Imported

The script automatically imports:

- ✅ **Entitlements** (`okta_principal_entitlements`) - Manual/custom entitlements only
- ✅ **Access Review Campaigns** (`okta_reviews`)
- ✅ **Approval Workflows** (`okta_request_sequences`)
- ✅ **Catalog Entries** (`okta_catalog_entry_default`)
- ✅ **Request Settings** (`okta_request_settings`)

### Generated Files

```
imported_oig/
├── entitlements.tf          # Terraform config for entitlements
├── entitlements.json        # Raw API data (reference)
├── reviews.tf               # Terraform config for access reviews
├── reviews.json             # Raw API data
├── request_sequences.tf     # Terraform config for approval workflows
├── request_sequences.json   # Raw API data
├── catalog_entries.tf       # Terraform config for catalog
├── catalog_entries.json     # Raw API data
├── request_settings.tf      # Terraform config for settings
├── request_settings.json    # Raw API data
└── import.sh                # Terraform import commands (executable)
```

### Workflow

1. **Generate configurations**
   ```bash
   python3 scripts/import_oig_resources.py --output-dir imported_oig
   ```

2. **Review and complete TODOs**
   - Open each `.tf` file
   - Complete the TODO comments with proper configuration
   - Reference the `.json` files for attribute values

3. **Import into Terraform state**
   ```bash
   cd imported_oig
   terraform init
   ./import.sh
   ```

4. **Verify**
   ```bash
   terraform plan  # Should show no changes
   ```

### Example: Completing TODOs

**Generated entitlements.tf:**
```hcl
resource "okta_principal_entitlements" "salesforce_admin" {
  # ID: ent12pva5bAyGUBBv1d7
  # Original name: Salesforce Admin Access

  # TODO: Add required configuration
  # Review the API response and add principals, resources, etc.
  # See: https://registry.terraform.io/providers/okta/okta/latest/docs/resources/principal_entitlements
}
```

**After completing TODOs (reference entitlements.json for values):**
```hcl
resource "okta_principal_entitlements" "salesforce_admin" {
  # ID: ent12pva5bAyGUBBv1d7

  principal {
    id   = "00u1234567890abcdef"
    type = "USER"
  }

  entitlement {
    id   = "ent12pva5bAyGUBBv1d7"
    name = "Salesforce Admin Access"
  }
}
```

### Smart Filtering

The import script automatically:
- **Skips app-managed entitlements** (synced from Salesforce, Workday, etc.)
- **Only imports manual entitlements** that can be managed via Terraform
- **Provides warnings** when resources can't be fetched

---

## 🎯 Recommended Approach

### Scenario 1: No Existing OIG Configuration (Most Common)

If you're just starting with OIG, you're in luck! Simply use the Terraform configurations provided:

```bash
# Use the provided OIG configuration
cd terraform
terraform init
terraform apply
```

**This is the recommended path** since OIG is a new feature and most orgs won't have existing OIG configurations.

### Scenario 2: Existing OIG Configuration (Manual Import Required)

If you've manually configured OIG features in the Okta Admin Console, you'll need to:

#### Option A: Start Fresh (Recommended)

**Pros:**
- Clean slate with Infrastructure as Code
- No complex migration
- Documented and version-controlled from day one

**Steps:**
1. Document your current OIG configuration
2. Delete manual OIG configs (or leave them if not conflicting)
3. Deploy via Terraform
4. Migrate gradually

```bash
# Deploy new OIG configuration
cd terraform
terraform apply

# Old manual configs will remain but won't be managed by Terraform
```

#### Option B: Manual Import (Advanced)

For each OIG resource, you'll need to:

**Step 1: Find Resource IDs**

```bash
# Use Okta API to get IDs
curl -X GET "https://${OKTA_ORG_NAME}.okta.com/governance/api/v1/catalog/entries" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}"
```

**Step 2: Create Terraform Configuration**

```hcl
# Manually create resource blocks matching your existing config
resource "okta_catalog_entry_default" "existing_entry" {
  app_id      = "0oa1234567890abcdef"  # Your existing app ID
  name        = "Existing Catalog Entry"
  description = "Manually created entry"
  # ... match all existing settings
}
```

**Step 3: Import State**

```bash
# Import each resource individually
terraform import okta_catalog_entry_default.existing_entry <entry-id>
terraform import okta_request_sequences.existing_workflow <workflow-id>
terraform import okta_reviews.existing_review <review-id>
```

**Step 4: Verify**

```bash
terraform plan  # Should show no changes if import was successful
```

## 📋 OIG Import Checklist

### 1. Catalog Entries

```bash
# List all catalog entries
curl -X GET "https://${OKTA_ORG_NAME}.okta.com/governance/api/v1/catalog/entries" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}" | jq '.data[] | {id, name, appId}'

# For each entry:
# 1. Create resource block in Terraform
# 2. Import: terraform import okta_catalog_entry_default.name <id>
```

### 2. Approval Workflows (Request Sequences)

```bash
# List workflows via API
curl -X GET "https://${OKTA_ORG_NAME}.okta.com/governance/api/v1/request-sequences" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}"

# Import each workflow
terraform import okta_request_sequences.workflow_name <workflow-id>
```

### 3. Access Reviews

```bash
# List review campaigns
curl -X GET "https://${OKTA_ORG_NAME}.okta.com/governance/api/v1/reviews" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}"

# Import each review
terraform import okta_reviews.review_name <review-id>
```

### 4. Request Settings

```bash
# Get request settings
curl -X GET "https://${OKTA_ORG_NAME}.okta.com/governance/api/v1/request-settings" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}"

# Import settings (only one per org)
terraform import okta_request_settings.settings default
```

### 5. Entitlements

```bash
# List entitlements
curl -X GET "https://${OKTA_ORG_NAME}.okta.com/governance/api/v1/entitlements" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}"

# Import each entitlement
terraform import okta_principal_entitlements.name <entitlement-id>
```

## 🔧 Helper Script: Generate Import Commands

Create a script to help generate import commands:

```python
#!/usr/bin/env python3
"""
generate_oig_imports.py
Generate Terraform import commands for existing OIG resources
"""

import requests
import os

okta_org = os.environ['OKTA_ORG_NAME']
api_token = os.environ['OKTA_API_TOKEN']
base_url = f"https://{okta_org}.okta.com"

headers = {
    "Authorization": f"SSWS {api_token}",
    "Accept": "application/json"
}

def generate_imports():
    print("#!/bin/bash")
    print("# Generated OIG import commands\n")
    
    # Catalog Entries
    print("# Catalog Entries")
    response = requests.get(
        f"{base_url}/governance/api/v1/catalog/entries",
        headers=headers
    )
    for entry in response.json().get('data', []):
        safe_name = entry['name'].lower().replace(' ', '_').replace('-', '_')
        print(f"terraform import okta_catalog_entry_default.{safe_name} {entry['id']}")
    
    print()
    
    # Review Campaigns
    print("# Access Review Campaigns")
    response = requests.get(
        f"{base_url}/governance/api/v1/reviews",
        headers=headers
    )
    for review in response.json().get('data', []):
        safe_name = review['name'].lower().replace(' ', '_').replace('-', '_')
        print(f"terraform import okta_reviews.{safe_name} {review['id']}")
    
    print()
    
    # Request Sequences
    print("# Approval Workflows")
    response = requests.get(
        f"{base_url}/governance/api/v1/request-sequences",
        headers=headers
    )
    for sequence in response.json().get('data', []):
        safe_name = sequence['name'].lower().replace(' ', '_').replace('-', '_')
        print(f"terraform import okta_request_sequences.{safe_name} {sequence['id']}")

if __name__ == '__main__':
    generate_imports()
```

Usage:

```bash
python3 scripts/generate_oig_imports.py > oig_imports.sh
chmod +x oig_imports.sh

# Review the file first!
cat oig_imports.sh

# Then run it
./oig_imports.sh
```

## 🎨 Complete Workflow: Base + OIG

Recommended workflow for existing orgs:

```bash
# Step 1: Import base resources with Terraformer
./scripts/import_okta_resources.sh

# Step 2: Clean up imported base resources
python3 scripts/cleanup_terraform.py \
  --input generated/okta \
  --output cleaned

# Step 3: Add OIG configuration (new or imported)
cd terraform

# Option 3a: Create fresh OIG config (recommended)
cp ../main.tf ./main-oig.tf
terraform apply

# Option 3b: Import existing OIG manually
python3 ../scripts/generate_oig_imports.py > oig_imports.sh
# Create resource blocks to match existing OIG config
# Then run imports
./oig_imports.sh

# Step 4: Add Resource Owners and Labels via API
python3 ../scripts/okta_api_manager.py \
  --action apply \
  --config api_config.json

# Done!
```

## 📊 Migration Strategy Matrix

| Resource Type | Terraformer Support | Recommended Approach |
|---------------|---------------------|----------------------|
| Users | ✅ Yes | Import with Terraformer |
| Groups | ✅ Yes | Import with Terraformer |
| Apps (OAuth/SAML) | ✅ Yes | Import with Terraformer |
| Policies | ✅ Yes | Import with Terraformer |
| Auth Servers | ✅ Yes | Import with Terraformer |
| **Catalog Entries** | ❌ **No** | **Manual import or fresh** |
| **Approval Workflows** | ❌ **No** | **Manual import or fresh** |
| **Access Reviews** | ❌ **No** | **Manual import or fresh** |
| **Request Settings** | ❌ **No** | **Manual import or fresh** |
| **Entitlements** | ❌ **No** | **Manual import or fresh** |
| **Resource Owners** | ❌ **No** | **Python API script** |
| **Labels** | ❌ **No** | **Python API script** |

## 💡 Why "Fresh" is Often Better for OIG

1. **Clean Start** - Easier than complex imports
2. **Documentation** - Everything is version-controlled from day one
3. **Automation** - Can replicate across environments easily
4. **Best Practices** - Use our proven configuration patterns

## 🆘 Troubleshooting OIG Imports

### Issue: "Resource not found"

```bash
# Error during import
Error: Cannot import non-existent remote object

# Solution: Verify the resource exists
curl -X GET "https://${OKTA_ORG_NAME}.okta.com/governance/api/v1/catalog/entries/<id>" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}"
```

### Issue: "Configuration doesn't match state"

```bash
# After import, plan shows changes
terraform plan

# Solution: Ensure your resource block exactly matches
# Check all attributes, including optional ones
terraform show
```

### Issue: "Dependent resources missing"

```bash
# OIG resources often depend on apps, groups, etc.

# Solution: Import dependencies first
terraform import okta_app_oauth.app <app-id>
terraform import okta_group.approvers <group-id>
# Then import OIG resources
terraform import okta_catalog_entry_default.entry <entry-id>
```

## 📚 Additional Resources

- [Okta Governance API Docs](https://developer.okta.com/docs/api/iga/)
- [Terraform Import Command](https://www.terraform.io/docs/cli/import/)
- [Okta Terraform Provider - Import Examples](https://registry.terraform.io/providers/okta/okta/latest/docs)

## ✅ Recommendation Summary

**For most users:**
1. ✅ Use Terraformer for base resources (users, groups, apps, policies)
2. ✅ Create OIG configuration using our Terraform files
3. ✅ Use Python scripts for Resource Owners and Labels
4. ✅ Only manually import existing OIG configs if absolutely necessary

**The easy path:**
```bash
# Import base with Terraformer (5 minutes)
./scripts/import_okta_resources.sh

# Deploy OIG config (5 minutes)
cd terraform && terraform apply

# Configure owners/labels (2 minutes)
python3 scripts/okta_api_manager.py --action apply --config api_config.json

# Total time: ~15 minutes vs hours of manual OIG imports
```
