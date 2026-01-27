# Terraformer + OIG: Frequently Asked Questions

## ❓ Will Terraformer pull in existing OIG resources?

**No.** Terraformer does **NOT** currently support the new OIG resources introduced in Terraform Provider v6.1.0.

## 📊 What's Supported?

### ✅ Terraformer CAN Import:

| Category | Resources |
|----------|-----------|
| **Identity** | Users, Groups, Group Rules, Group Memberships |
| **Applications** | OAuth/OIDC Apps, SAML Apps, SWA Apps, Bookmark Apps |
| **Authorization** | Auth Servers, Policies, Claims, Scopes |
| **Policies** | MFA, Password, Sign-On Policies and Rules |
| **Security** | Network Zones, Trusted Origins |
| **Identity Providers** | SAML, OIDC, Social IdPs |
| **Schemas** | User Schema, Group Schema |
| **Hooks** | Inline Hooks, Event Hooks |

### ❌ Terraformer CANNOT Import:

| Category | Resources | Why Not? |
|----------|-----------|----------|
| **OIG - Reviews** | `okta_reviews` | New in v6.1.0 |
| **OIG - Entitlements** | `okta_principal_entitlements` | New in v6.1.0 |
| **OIG - Conditions** | `okta_request_conditions` | New in v6.1.0 |
| **OIG - Workflows** | `okta_request_sequences` | New in v6.1.0 |
| **OIG - Settings** | `okta_request_settings` | New in v6.1.0 |
| **OIG - Requests** | `okta_request_v2` | New in v6.1.0 |
| **OIG - Catalog** | `okta_catalog_entry_*` | New in v6.1.0 |
| **OIG - Owners** | Resource Owners API | API-only, not in provider yet |
| **OIG - Labels** | Labels API | API-only, not in provider yet |

## 🤔 Why Aren't OIG Resources Supported?

1. **Terraform Provider Endpoints are New** - v6.1.0 just added OIG support (Sept 2024)
2. **Terraformer Lag** - Terraformer development lags behind provider updates
3. **Community-Driven** - Terraformer is open-source and depends on community contributions

## 💡 So How Do I Handle This?

### Recommended: Hybrid Approach

```bash
# ✅ Step 1: Use Terraformer for base resources
./scripts/import_okta_resources.sh

# ✅ Step 2: Create OIG configuration via Terraform
cd terraform
terraform apply  # Deploys new OIG resources

# ✅ Step 3: Add Resource Owners/Labels via Python API
python3 scripts/okta_api_manager.py --action apply --config api_config.json
```

**Why this works:**
- Base resources (users, groups, apps) imported easily
- OIG config starts clean and documented
- Everything is version-controlled

### If You Have Existing OIG Configuration

**Option 1: Start Fresh (Easiest)**
- Document current OIG setup
- Delete or leave existing OIG configs
- Deploy new OIG via Terraform
- Cleaner and faster than manual imports

**Option 2: Manual Import (Advanced)**
- For each OIG resource, manually create Terraform blocks
- Use `terraform import` for each resource individually
- See [OIG Manual Import Guide](./docs/OIG_MANUAL_IMPORT.md)
- Time-consuming but preserves existing configs

## 📅 Will Terraformer Support OIG Eventually?

**Possibly, but no timeline.**

Factors:
- Terraformer is community-driven
- Requires someone to contribute the code
- OIG is complex with many resource types
- May take months or longer

**Don't wait** - Use the hybrid approach now.

## 🎯 Decision Tree

```
Do you have an existing Okta org?
├─ No → Use greenfield approach (terraform apply)
└─ Yes
   ├─ Do you have existing OIG configurations?
   │  ├─ No → Use Terraformer for base + new OIG via Terraform ✅
   │  └─ Yes
   │     ├─ Are they simple/few? → Recreate via Terraform ✅
   │     └─ Are they complex/many? → Manual import (see guide) ⚠️
```

## 💻 Code Examples

### What Terraformer WILL Import

```bash
# This works - imports 50+ users, 20+ groups, 10+ apps
terraformer import okta --resources=okta_user,okta_group,okta_app_oauth,okta_app_saml

# Generated files look like:
# generated/okta/
# ├── okta_user/
# │   └── user.tf (50 okta_user resources)
# ├── okta_group/
# │   └── group.tf (20 okta_group resources)
# └── okta_app_oauth/
#     └── app_oauth.tf (10 okta_app_oauth resources)
```

### What Terraformer WILL NOT Import

```bash
# This doesn't work - OIG resources not supported
terraformer import okta --resources=okta_reviews,okta_catalog_entry_default

# Error: Resource type 'okta_reviews' is not supported by terraformer
```

### What You Need to Do Instead

```hcl
# Create OIG resources fresh in Terraform
resource "okta_reviews" "quarterly_review" {
  name        = "Quarterly Access Review"
  description = "Review all app access quarterly"
  
  schedule {
    frequency  = "QUARTERLY"
    start_date = "2025-01-01"
  }
  
  scope {
    resource_type = "APP"
    resource_ids  = [
      okta_app_oauth.imported_app_1.id,  # Reference imported app
      okta_app_oauth.imported_app_2.id,  # Reference imported app
    ]
  }
}

# Apply to create
terraform apply
```

## 🔗 Related Documentation

- [Terraformer Integration Guide](./docs/TERRAFORMER.md)
- [OIG Manual Import Guide](./docs/OIG_MANUAL_IMPORT.md)
- [API Management Guide](./docs/API_MANAGEMENT.md)
- [Complete Solution Summary](./docs/COMPLETE_SOLUTION.md)

## ✅ Quick Answer Summary

**Q: Will Terraformer import my OIG resources?**  
**A: No. Import base resources with Terraformer, create OIG with Terraform.**

**Q: What if I have existing OIG configs?**  
**A: Either recreate them (easier) or manually import each one (harder).**

**Q: What's the recommended approach?**  
**A: Hybrid - Terraformer for base resources, Terraform for OIG features.**

---

**Still have questions?** Check the [full documentation](./README.md) or open an issue.
