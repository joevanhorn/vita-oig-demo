# Okta Terraform Provider - Complete Resource Guide

This comprehensive guide provides both a complete catalog of all Okta Terraform resources and detailed attribute documentation for key resources.

**Provider Version:** v6.1.0+
**Last Updated:** 2025-11-07

---

## 📊 Document Overview

This guide is organized into four main sections:

1. **[Resource Catalog](#part-1-complete-resource-catalog-116-resources)** - Complete list of all 116 Terraform resources
2. **[Data Source Catalog](#part-2-complete-data-source-catalog-63-data-sources)** - Complete list of all 63 data sources
3. **[Detailed Attribute Guides](#part-3-detailed-attribute-guides)** - In-depth documentation for key resources
4. **[Management Best Practices](#part-4-management--best-practices)** - Implementation patterns and workflows

**Quick Stats:**
- 116 Terraform Resources
- 63 Data Sources  
- ~90 Resources importable via Terraformer
- 2+ API-only resources (no Terraform support)

---
## 📊 Quick Summary

| Management Method | Resource Count | Use Case |
|-------------------|----------------|----------|
| **Terraformer Import** | ~90 resources | Existing infrastructure import (automated) |
| **Manual Terraform** | 116 resources | New resources & complete infrastructure |
| **API-Only (Python)** | 2+ resources | Labels, Resource Owners (no Terraform support yet) |
| **Data Sources** | 63 data sources | Read-only queries for existing resources |

**Total Resources Available:** 116
**Total Data Sources Available:** 63

---

## 📖 Table of Contents

### Resources (116 Total)
- [👥 Users & User Management (10)](#-users--user-management-10-resources)
- [👪 Groups & Group Management (6)](#-groups--group-management-5-resources)
- [📱 Applications (24)](#-applications-24-resources)
- [🔐 Authorization Servers & OAuth (7)](#-authorization-servers--oauth-7-resources)
- [🔒 Policies (20)](#-policies-20-resources)
- [🌐 Identity Providers & Social Auth (4)](#-identity-providers--social-auth-4-resources)
- [🛡️ Security & Network (4)](#️-security--network-4-resources)
- [🎨 Brands, Themes & Customization (9)](#-brands-themes--customization-9-resources)
- [🌍 Domains & Certificates (3)](#-domains--certificates-3-resources)
- [🔗 Hooks & Event Handlers (3)](#-hooks--event-handlers-3-resources)
- [👔 OIG - Identity Governance (11)](#-okta-identity-governance-oig---v610-11-resources)
- [👨‍💼 Admin Roles & Permissions (5)](#-admin-roles--permissions-5-resources)
- [⚙️ Org Settings & Configuration (6)](#️-org-settings--configuration-6-resources)
- [🔗 Linking & Associations (3)](#-linking--associations-3-resources)
- [📊 Logging & Monitoring (1)](#-logging--monitoring-1-resource)
- [🌐 Realms (2)](#-realms-beta-2-resources)

### Data Sources (63 Total)
- [👥 User Data Sources (5)](#-user-data-sources-5)
- [👪 Group Data Sources (4)](#-group-data-sources-4)
- [📱 Application Data Sources (8)](#-application-data-sources-8)
- [🔐 Authorization Server Data Sources (5)](#-authorization-server-data-sources-5)
- [🔒 Policy Data Sources (3)](#-policy-data-sources-2)
- [🛡️ Security Data Sources (5)](#️-security-data-sources-4)
- [🌐 Identity Provider Data Sources (4)](#-identity-provider-data-sources-4)
- [🎨 Branding Data Sources (7)](#-branding-data-sources-6)
- [📧 Email Data Sources (4)](#-email-data-sources-4)
- [👔 OIG Data Sources (12)](#-oig-data-sources-7)
- [⚙️ Organization Data Sources (6)](#️-organization-data-sources-5)

### Part 3: Detailed Attribute Guides
- [okta_user](#okta_user) - User account management with all attributes
- [okta_group](#okta_group) - Group management
- [okta_app_oauth](#okta_app_oauth) - OAuth/OIDC application configuration
- [okta_auth_server_default](#okta_auth_server_default) - Default authorization server
- [okta_policy_mfa_default](#okta_policy_mfa_default) - Default MFA policy

### Part 4: Management & Best Practices
- [🎯 Resource Management Best Practices](#-resource-management-best-practices)
  - [Use Case 1: Import Existing Infrastructure](#use-case-1-import-existing-infrastructure)
  - [Use Case 2: Create New Resources](#use-case-2-create-new-resources)
  - [Use Case 3: OIG Governance via API](#use-case-3-oig-governance-via-api)
- [📖 Additional Resources](#-additional-resources)
- [🔄 Version History](#-version-history)

---

# PART 1: Complete Resource Catalog (116 Resources)

---

## 📋 Complete Resource Reference (116 Resources)

### 👥 USERS & USER MANAGEMENT (10 resources)

| Resource | Terraformer | Notes |
|----------|-------------|-------|
| `okta_user` | ✅ | User accounts |
| `okta_user_type` | ✅ | User types/categories |
| `okta_user_base_schema_property` | ✅ | Base schema attributes |
| `okta_user_schema_property` | ✅ | Custom user attributes |
| `okta_user_admin_roles` | - | Admin role assignments |
| `okta_user_group_memberships` | - | User's group memberships |
| `okta_user_factor_question` | - | Security question setup |
| `okta_factor` | ✅ | MFA factors (legacy) |
| `okta_factor_totp` | - | TOTP authenticator |
| `okta_security_notification_emails` | - | Security notification settings |

---

### 👪 GROUPS & GROUP MANAGEMENT (5 resources)

| Resource | Terraformer | Notes |
|----------|-------------|-------|
| `okta_group` | ✅ | User groups |
| `okta_group_schema_property` | ✅ | Custom group attributes |
| `okta_group_rule` | ✅ | Dynamic membership rules |
| `okta_group_memberships` | - | Bulk membership management |
| `okta_group_owner` | - | Group ownership assignments |
| `okta_group_role` | - | Group role assignments |

---

### 📱 APPLICATIONS (24 resources)

| Resource | Terraformer | Notes |
|----------|-------------|-------|
| `okta_app_oauth` | ✅ | OAuth/OIDC applications |
| `okta_app_saml` | ✅ | SAML 2.0 applications |
| `okta_app_basic_auth` | ✅ | Basic auth applications |
| `okta_app_bookmark` | ✅ | Bookmark applications |
| `okta_app_secure_password_store` | ✅ | SWA applications (legacy) |
| `okta_app_swa` | ✅ | Secure Web Authentication apps |
| `okta_app_shared_credentials` | - | Shared credentials apps |
| `okta_app_three_field` | ✅ | Three-field SWA apps |
| `okta_app_auto_login` | ✅ | Auto-login applications |
| `okta_app_user` | - | App user assignments |
| `okta_app_user_base_schema_property` | - | Base app user schema |
| `okta_app_user_schema_property` | - | Custom app user attributes |
| `okta_app_group_assignment` | - | Single group assignment |
| `okta_app_group_assignments` | - | Bulk group assignments |
| `okta_app_oauth_api_scope` | - | OAuth API scope grants |
| `okta_app_oauth_redirect_uri` | - | OAuth redirect URIs |
| `okta_app_oauth_post_logout_redirect_uri` | - | Post-logout redirect URIs |
| `okta_app_oauth_role_assignment` | - | OAuth role assignments |
| `okta_app_saml_app_settings` | - | SAML app-specific settings |
| `okta_app_signon_policy` | - | App sign-on policies |
| `okta_app_signon_policy_rule` | - | App sign-on policy rules |
| `okta_app_access_policy_assignment` | - | Access policy assignments |
| `okta_customized_signin_page` | - | Custom sign-in page per app |
| `okta_preview_signin_page` | - | Preview sign-in page |

---

### 🔐 AUTHORIZATION SERVERS & OAUTH (7 resources)

| Resource | Terraformer | Notes |
|----------|-------------|-------|
| `okta_auth_server` | ✅ | Custom authorization servers |
| `okta_auth_server_default` | ✅ | Default authorization server |
| `okta_auth_server_policy` | ✅ | Auth server policies |
| `okta_auth_server_policy_rule` | ✅ | Auth server policy rules |
| `okta_auth_server_claim` | ✅ | Custom claims |
| `okta_auth_server_claim_default` | - | Default claims configuration |
| `okta_auth_server_scope` | ✅ | Custom OAuth scopes |

---

### 🔒 POLICIES (20 resources)

| Resource | Terraformer | Notes |
|----------|-------------|-------|
| `okta_policy_mfa` | ✅ | MFA policies |
| `okta_policy_mfa_default` | - | Default MFA policy |
| `okta_policy_rule_mfa` | ✅ | MFA policy rules |
| `okta_policy_password` | ✅ | Password policies |
| `okta_policy_password_default` | - | Default password policy |
| `okta_policy_rule_password` | ✅ | Password policy rules |
| `okta_policy_signon` | ✅ | Sign-on policies |
| `okta_policy_rule_signon` | ✅ | Sign-on policy rules |
| `okta_policy_profile_enrollment` | - | Profile enrollment policies |
| `okta_policy_profile_enrollment_apps` | - | Enrollment policy apps |
| `okta_policy_rule_profile_enrollment` | - | Enrollment policy rules |
| `okta_policy_rule_idp_discovery` | - | IdP discovery rules |
| `okta_policy_device_assurance_windows` | - | Windows device assurance |
| `okta_policy_device_assurance_macos` | - | macOS device assurance |
| `okta_policy_device_assurance_android` | - | Android device assurance |
| `okta_policy_device_assurance_ios` | - | iOS device assurance |
| `okta_policy_device_assurance_chromeos` | - | ChromeOS device assurance |
| `okta_rate_limiting` | - | API rate limiting |
| `okta_threat_insight_settings` | - | Threat insight configuration |
| `okta_authenticator` | - | Authenticator configuration |

---

### 🌐 IDENTITY PROVIDERS & SOCIAL AUTH (4 resources)

| Resource | Terraformer | Notes |
|----------|-------------|-------|
| `okta_idp_saml` | ✅ | SAML identity providers |
| `okta_idp_saml_key` | - | SAML signing keys |
| `okta_idp_oidc` | ✅ | OIDC identity providers |
| `okta_idp_social` | ✅ | Social identity providers |

---

### 🛡️ SECURITY & NETWORK (4 resources)

| Resource | Terraformer | Notes |
|----------|-------------|-------|
| `okta_network_zone` | ✅ | Network zones (IP allowlists) |
| `okta_trusted_origin` | ✅ | CORS trusted origins |
| `okta_trusted_server` | - | Trusted servers |
| `okta_behavior` | - | Anomaly detection behaviors |

---

### 🎨 BRANDS, THEMES & CUSTOMIZATION (9 resources)

| Resource | Terraformer | Notes |
|----------|-------------|-------|
| `okta_brand` | - | Organization brands |
| `okta_theme` | - | Custom themes |
| `okta_email_customization` | - | Email template customizations |
| `okta_email_template_settings` | - | Email template settings |
| `okta_email_domain` | - | Custom email domains |
| `okta_email_domain_verification` | - | Email domain verification |
| `okta_email_sender` | - | Email sender configuration |
| `okta_email_sender_verification` | - | Sender verification |
| `okta_email_smtp_server` | - | Custom SMTP server |

---

### 🌍 DOMAINS & CERTIFICATES (3 resources)

| Resource | Terraformer | Notes |
|----------|-------------|-------|
| `okta_domain` | - | Custom domains |
| `okta_domain_certificate` | - | SSL certificates for domains |
| `okta_domain_verification` | - | Domain ownership verification |

---

### 🔗 HOOKS & EVENT HANDLERS (3 resources)

| Resource | Terraformer | Notes |
|----------|-------------|-------|
| `okta_inline_hook` | ✅ | Inline hooks (sync) |
| `okta_event_hook` | ✅ | Event hooks (async) |
| `okta_event_hook_verification` | - | Event hook verification |

---

### 👔 OKTA IDENTITY GOVERNANCE (OIG) - v6.1.0+ (11 resources)

#### Terraform-Managed (11 resources)

| Resource | Terraformer | Notes |
|----------|-------------|-------|
| `okta_campaign` | ❌ | Access certification campaigns (renamed from okta_reviews) |
| `okta_review` | ❌ | Individual access reviews |
| `okta_entitlement` | ❌ | Manual/custom entitlements only |
| `okta_request_condition` | ❌ | Access request conditions |
| `okta_request_sequence` | ❌ | Multi-stage approval workflows |
| `okta_request_setting_organization` | ❌ | Org-level request settings |
| `okta_request_setting_resource` | ❌ | Resource-level request settings |
| `okta_request_v2` | ❌ | Programmatic access requests |
| `okta_catalog_entry_default` | ❌ | Data source only (read-only) |
| `okta_catalog_entry_user_access_request_fields` | ❌ | Data source only (read-only) |
| `okta_end_user_my_requests` | ❌ | Data source only (read-only) |

**IMPORTANT:**
- `okta_campaign` is the new name for access review campaigns (formerly `okta_reviews`)
- `okta_entitlement` can ONLY manage **manual/custom entitlements**
- App-managed entitlements (Salesforce, Workday, etc.) are read-only
- Principal assignments (grants) should be managed in Okta Admin UI, not Terraform

#### API-Only (No Terraform Support)

| Resource | Management Method | API Endpoint |
|----------|-------------------|--------------|
| **Entitlement Bundles** | ❌ Terraform ✅ API | `/api/v1/governance/entitlement-bundles` |
| **Governance Labels** | ❌ Terraform ✅ API | `/api/v1/governance/labels` |
| **Resource Owners** | ❌ Terraform ✅ API | `/api/v1/governance/resource-owners` |

---

### 👨‍💼 ADMIN ROLES & PERMISSIONS (5 resources)

| Resource | Terraformer | Notes |
|----------|-------------|-------|
| `okta_admin_role_custom` | - | Custom administrator roles |
| `okta_admin_role_custom_assignments` | - | Custom role assignments |
| `okta_admin_role_targets` | - | Role target restrictions |
| `okta_resource_set` | - | Resource sets for role assignments |
| `okta_role_subscription` | - | Role subscription management |

---

### ⚙️ ORG SETTINGS & CONFIGURATION (6 resources)

| Resource | Terraformer | Notes |
|----------|-------------|-------|
| `okta_org_configuration` | - | Organization-level settings |
| `okta_org_support` | - | Support access settings |
| `okta_feature` | - | Feature flags/toggles |
| `okta_captcha` | - | CAPTCHA configuration |
| `okta_captcha_org_wide_settings` | - | Org-wide CAPTCHA settings |
| `okta_template_sms` | ✅ | SMS message templates |

---

### 🔗 LINKING & ASSOCIATIONS (3 resources)

| Resource | Terraformer | Notes |
|----------|-------------|-------|
| `okta_link_definition` | - | Link type definitions |
| `okta_link_value` | - | Link values between resources |
| `okta_profile_mapping` | - | Attribute mapping between sources |

---

### 📊 LOGGING & MONITORING (1 resource)

| Resource | Terraformer | Notes |
|----------|-------------|-------|
| `okta_log_stream` | - | Log streaming to SIEM |

---

### 🌐 REALMS (BETA) (2 resources)

| Resource | Terraformer | Notes |
|----------|-------------|-------|
| `okta_realm` | - | Workforce Identity Realms |
| `okta_realm_assignment` | - | Realm user/group assignments |

---

# PART 2: Complete Data Source Catalog (63 Data Sources)

---

## 📚 Complete Data Source Reference (63 Data Sources)

Data sources allow you to query existing resources without managing them in Terraform.

### 👥 User Data Sources (5)

| Data Source | Purpose |
|-------------|---------|
| `okta_user` | Query single user |
| `okta_users` | Query multiple users |
| `okta_user_type` | Query user types |
| `okta_user_profile_mapping_source` | Query profile mapping sources |
| `okta_user_security_questions` | Query available security questions |

---

### 👪 Group Data Sources (4)

| Data Source | Purpose |
|-------------|---------|
| `okta_group` | Query single group |
| `okta_groups` | Query multiple groups |
| `okta_everyone_group` | Query the Everyone group |
| `okta_group_rule` | Query group rules |

---

### 📱 Application Data Sources (8)

| Data Source | Purpose |
|-------------|---------|
| `okta_app` | Query single app (generic) |
| `okta_apps` | Query multiple apps |
| `okta_app_oauth` | Query OAuth app |
| `okta_app_saml` | Query SAML app |
| `okta_app_metadata_saml` | Query SAML metadata |
| `okta_app_signon_policy` | Query app sign-on policy |
| `okta_app_group_assignments` | Query app's group assignments |
| `okta_app_user_assignments` | Query app's user assignments |

---

### 🔐 Authorization Server Data Sources (5)

| Data Source | Purpose |
|-------------|---------|
| `okta_auth_server` | Query custom auth server |
| `okta_auth_server_policy` | Query auth server policy |
| `okta_auth_server_claim` | Query custom claims |
| `okta_auth_server_claims` | Query all claims |
| `okta_auth_server_scopes` | Query all scopes |

---

### 🔒 Policy Data Sources (2)

| Data Source | Purpose |
|-------------|---------|
| `okta_policy` | Query policies by type |
| `okta_default_policy` | Query default policies |
| `okta_device_assurance_policy` | Query device assurance policies |

---

### 🛡️ Security Data Sources (4)

| Data Source | Purpose |
|-------------|---------|
| `okta_authenticator` | Query authenticator config |
| `okta_behavior` | Query single behavior |
| `okta_behaviors` | Query all behaviors |
| `okta_network_zone` | Query network zones |
| `okta_trusted_origins` | Query trusted origins |

---

### 🌐 Identity Provider Data Sources (4)

| Data Source | Purpose |
|-------------|---------|
| `okta_idp_oidc` | Query OIDC IdP |
| `okta_idp_saml` | Query SAML IdP |
| `okta_idp_social` | Query social IdP |
| `okta_idp_metadata_saml` | Query SAML IdP metadata |

---

### 🎨 Branding Data Sources (6)

| Data Source | Purpose |
|-------------|---------|
| `okta_brand` | Query single brand |
| `okta_brands` | Query all brands |
| `okta_theme` | Query single theme |
| `okta_themes` | Query all themes |
| `okta_email_customization` | Query email customization |
| `okta_email_customizations` | Query all email customizations |
| `okta_default_signin_page` | Query default sign-in page |

---

### 📧 Email Data Sources (4)

| Data Source | Purpose |
|-------------|---------|
| `okta_email_template` | Query single email template |
| `okta_email_templates` | Query all email templates |
| `okta_email_smtp_server` | Query SMTP configuration |
| `okta_domain` | Query custom domains |

---

### 👔 OIG Data Sources (7)

| Data Source | Purpose |
|-------------|---------|
| `okta_campaign` | Query access review campaign |
| `okta_review` | Query individual review |
| `okta_entitlement` | Query entitlements |
| `okta_principal_entitlements` | Query principal's entitlements |
| `okta_catalog_entry_default` | Query catalog entries |
| `okta_catalog_entry_user_access_request_fields` | Query request fields |
| `okta_end_user_my_requests` | Query user's access requests |
| `okta_request_condition` | Query request conditions |
| `okta_request_sequence` | Query approval sequences |
| `okta_request_setting_organization` | Query org request settings |
| `okta_request_setting_resource` | Query resource request settings |
| `okta_request_v2` | Query access requests |

---

### ⚙️ Organization Data Sources (5)

| Data Source | Purpose |
|-------------|---------|
| `okta_org_metadata` | Query org metadata |
| `okta_features` | Query enabled features |
| `okta_role_subscription` | Query role subscriptions |
| `okta_log_stream` | Query log streams |
| `okta_realm` | Query realms |
| `okta_realm_assignment` | Query realm assignments |

---

# PART 4: Management & Best Practices

---

## 🎯 Resource Management Best Practices

### Use Case 1: Import Existing Infrastructure

**Tool:** Terraformer
**Supported:** ~90 resources (basic Okta resources)
**Workflow:** `import-all-resources.yml`

```bash
# Import from existing tenant
gh workflow run import-all-resources.yml \
  -f tenant_environment=MyOrg \
  -f update_terraform=true \
  -f commit_changes=true

# Resources imported:
# - Users, Groups, Apps, Policies
# - Authorization Servers
# - Identity Providers
# - Network Zones, Hooks, etc.
```

---

### Use Case 2: Create New Resources

**Tool:** Manual Terraform
**Supported:** All 116 resources
**Location:** `environments/<env>/terraform/`

```hcl
# Create any resource type
resource "okta_user" "new_user" {
  email      = "user@example.com"
  first_name = "John"
  last_name  = "Doe"
  login      = "user@example.com"
}

resource "okta_campaign" "quarterly_review" {
  name = "Q1 2025 Access Review"
  # Campaign configuration...
}
```

---

### Use Case 3: OIG Governance via API

**Tool:** Python API Scripts
**Supported:** Entitlement Bundles, Labels, Resource Owners
**Workflow:** API scripts in `scripts/`

```bash
# Import entitlement bundles (read-only documentation)
python3 scripts/import_oig_resources.py \
  --output-dir environments/myorg/imports

# Sync resource owners
python3 scripts/sync_owner_mappings.py \
  --output environments/myorg/config/owner_mappings.json

# Apply resource owners
python3 scripts/apply_resource_owners.py \
  --config environments/myorg/config/owner_mappings.json
```

---

## 📖 Additional Resources

- **Official Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs
- **Provider Repo:** https://github.com/okta/terraform-provider-okta
- **Resource Examples:** `environments/myorg/terraform/RESOURCE_EXAMPLES.tf`
- **API Scripts:** `scripts/` directory

---

## 🔄 Version History

| Date | Version | Provider Version | Changes |
|------|---------|------------------|---------|
| 2025-11-07 | 2.0 | v6.1.0+ | Complete resource matrix - all 116 resources + 63 data sources |
| 2025-11-07 | 1.0 | v6.1.0+ | Initial comprehensive resource matrix |

---

**Questions?** Refer to the [Terraform Registry](https://registry.terraform.io/providers/okta/okta/latest/docs) for detailed resource documentation.

---
---

# PART 3: Detailed Attribute Guides

The following sections provide comprehensive attribute-level documentation for the most commonly used Okta Terraform resources. Each section includes detailed explanations of all attributes, valid values, examples, and best practices.

---

## okta_user

Manages Okta user accounts.

### Basic Attributes

#### `email` (Required)
- **Type:** String
- **Description:** Primary email address of the user
- **Example:** `"john.doe@example.com"`
- **Notes:** Must be unique across the Okta organization

#### `first_name` (Required)
- **Type:** String
- **Description:** User's first/given name
- **Example:** `"John"`
- **Notes:** Displayed in Okta dashboard and user profile

#### `last_name` (Required)
- **Type:** String
- **Description:** User's last/family name
- **Example:** `"Doe"`
- **Notes:** Displayed in Okta dashboard and user profile

#### `login` (Required)
- **Type:** String
- **Description:** Unique identifier for the user to log in
- **Example:** `"john.doe@example.com"`
- **Notes:**
  - Must be unique across the organization
  - Often the same as email but can be different
  - Cannot be changed after creation

### Profile Attributes

#### `city` (Optional)
- **Type:** String
- **Description:** City where the user is located
- **Example:** `"San Francisco"`
- **Notes:** Part of the user's profile, used for reporting

#### `country_code` (Optional)
- **Type:** String
- **Description:** Two-letter country code (ISO 3166-1 alpha-2)
- **Example:** `"US"`
- **Valid Values:** Any valid ISO country code
- **Notes:** Used for localization and compliance

#### `department` (Optional)
- **Type:** String
- **Description:** Department or team the user belongs to
- **Example:** `"Engineering"`
- **Notes:** Useful for grouping and reporting

#### `state` (Optional)
- **Type:** String
- **Description:** State/province where the user is located
- **Example:** `"CA"` or `"California"`
- **Notes:** Can be abbreviation or full name

#### `title` (Optional)
- **Type:** String
- **Description:** User's job title
- **Example:** `"Senior Software Engineer"`
- **Notes:** Displayed in user profile

#### `mobile_phone` (Optional)
- **Type:** String
- **Description:** User's mobile phone number in E.164 format
- **Example:** `"+14155551234"`
- **Format:** Must start with `+` followed by country code
- **Notes:** Used for SMS-based MFA

#### `custom_profile_attributes` (Optional)
- **Type:** String (JSON)
- **Description:** Custom profile attributes as JSON string
- **Example:** `"{\"customField1\": \"value1\"}"`
- **Default:** `"{}"`
- **Notes:** For custom schema attributes defined in your Okta org

### Status and Behavior

#### `status` (Optional)
- **Type:** String
- **Description:** Lifecycle status of the user
- **Valid Values:**
  - `"ACTIVE"` - User is active and can log in
  - `"PROVISIONED"` - User created but not yet activated
  - `"STAGED"` - User account created but email not sent
  - `"DEPROVISIONED"` - User account deactivated
  - `"SUSPENDED"` - User account temporarily suspended
- **Default:** `"ACTIVE"`
- **Example:** `"ACTIVE"`
- **Notes:**
  - Setting to `"ACTIVE"` sends activation email
  - Changing between states follows Okta's lifecycle rules

#### `expire_password_on_create` (Optional)
- **Type:** Boolean
- **Description:** Force user to change password on first login
- **Default:** `false`
- **Example:** `false`
- **Notes:** Security best practice for new accounts

#### `skip_roles` (Optional)
- **Type:** Boolean
- **Description:** Skip processing of assigned roles during user creation
- **Default:** `false`
- **Notes:** Internal Terraform optimization flag

### Computed Attributes (Read-Only)

#### `id`
- **Type:** String
- **Description:** Unique identifier assigned by Okta
- **Example:** `"00u1234567890abcdef"`
- **Notes:** Generated automatically, used for imports and references

#### `raw_status`
- **Type:** String
- **Description:** The raw status value from Okta API
- **Notes:** May differ from `status` during transitions

### Example

```hcl
resource "okta_user" "john_doe" {
  # Required fields
  email      = "john.doe@example.com"
  first_name = "John"
  last_name  = "Doe"
  login      = "john.doe@example.com"

  # Profile fields
  city         = "San Francisco"
  country_code = "US"
  department   = "Engineering"
  mobile_phone = "+14155551234"
  state        = "CA"
  title        = "Senior Software Engineer"

  # Custom attributes
  custom_profile_attributes = jsonencode({
    employeeNumber = "EMP001"
    startDate      = "2024-01-15"
  })

  # Status
  status                    = "ACTIVE"
  expire_password_on_create = false
}
```

---

## okta_group

Manages Okta groups for organizing users.

### Attributes

#### `name` (Required)
- **Type:** String
- **Description:** Display name of the group
- **Example:** `"Engineering Team"`
- **Notes:** Must be unique within the organization

#### `description` (Optional)
- **Type:** String
- **Description:** Human-readable description of the group's purpose
- **Example:** `"Engineering team members with access to development resources"`
- **Notes:** Helps document the group's intended use

#### `custom_profile_attributes` (Optional)
- **Type:** String (JSON)
- **Description:** Custom attributes for the group as JSON string
- **Example:** `"{}"`
- **Default:** `"{}"`
- **Notes:** For custom schema attributes on group objects

### Computed Attributes

#### `id`
- **Type:** String
- **Description:** Unique identifier assigned by Okta
- **Example:** `"00g1234567890abcdef"`

### Example

```hcl
resource "okta_group" "engineering" {
  name                      = "Engineering Team"
  description               = "Engineering team members with access to development resources"
  custom_profile_attributes = "{}"
}
```

### Group Membership

Group membership is typically managed separately using `okta_group_memberships` or `okta_user_group_memberships` resources (not shown in this configuration).

---

## okta_app_oauth

Manages OAuth 2.0 / OIDC applications in Okta.

### Basic Configuration

#### `label` (Required)
- **Type:** String
- **Description:** Display name of the application
- **Example:** `"Internal CRM System"`
- **Notes:** Shown in Okta Admin Console and user dashboard

#### `type` (Required)
- **Type:** String
- **Description:** OAuth application type
- **Valid Values:**
  - `"web"` - Web application (server-side)
  - `"native"` - Native/mobile application
  - `"browser"` - Single-page application
  - `"service"` - Service/machine-to-machine app
- **Example:** `"web"`
- **Notes:** Determines available grant types and security settings

### OAuth 2.0 Configuration

#### `grant_types` (Required for most types)
- **Type:** List of strings
- **Description:** OAuth 2.0 grant types supported by the application
- **Valid Values:**
  - `"authorization_code"` - Authorization Code flow
  - `"implicit"` - Implicit flow (deprecated)
  - `"password"` - Resource Owner Password flow
  - `"client_credentials"` - Client Credentials flow
  - `"refresh_token"` - Refresh token support
  - `"urn:ietf:params:oauth:grant-type:saml2-bearer"` - SAML 2.0 bearer
  - `"urn:ietf:params:oauth:grant-type:jwt-bearer"` - JWT bearer
- **Example:** `["authorization_code", "refresh_token"]`
- **Notes:**
  - Choose based on your application architecture
  - `authorization_code` is most secure for web apps

#### `response_types` (Required for most types)
- **Type:** List of strings
- **Description:** OAuth response types the app expects
- **Valid Values:**
  - `"code"` - Authorization code
  - `"token"` - Access token (implicit flow)
  - `"id_token"` - ID token (OpenID Connect)
- **Example:** `["code"]`
- **Notes:** Should match your grant types

#### `redirect_uris` (Required for web/native/browser)
- **Type:** List of strings
- **Description:** Valid OAuth redirect/callback URIs
- **Example:** `["https://myapp.example.com/callback"]`
- **Notes:**
  - Must use HTTPS in production (except localhost)
  - Wildcards not allowed (use exact matches)
  - Must be whitelisted for security

#### `post_logout_redirect_uris` (Optional)
- **Type:** List of strings
- **Description:** Valid URIs to redirect to after logout
- **Example:** `["https://myapp.example.com/logout"]`
- **Notes:** OIDC logout endpoint redirect destinations

### Client Authentication

#### `token_endpoint_auth_method` (Required)
- **Type:** String
- **Description:** How the client authenticates with the token endpoint
- **Valid Values:**
  - `"client_secret_basic"` - HTTP Basic with client ID/secret
  - `"client_secret_post"` - Client secret in POST body
  - `"client_secret_jwt"` - Client secret as JWT
  - `"private_key_jwt"` - Private key JWT (most secure)
  - `"none"` - No authentication (public clients)
- **Example:** `"client_secret_post"`
- **Notes:**
  - `private_key_jwt` most secure, requires JWKS
  - `none` only for browser-based apps with PKCE

#### `pkce_required` (Optional)
- **Type:** Boolean or String
- **Description:** Whether PKCE (Proof Key for Code Exchange) is required
- **Valid Values:** `true`, `false`, or `"true"`, `"false"` (string)
- **Default:** `false`
- **Example:** `true`
- **Notes:**
  - **Highly recommended** for mobile and SPA apps
  - Security best practice even for confidential clients
  - Prevents authorization code interception

### Key Configuration (for private_key_jwt)

#### `jwks` (Optional, Required for private_key_jwt)
- **Type:** Block
- **Description:** JSON Web Key Set for client authentication
- **Example:**
  ```hcl
  jwks {
    kty = "RSA"
    e   = "AQAB"
    n   = "lKl3Wk7VzPgARVBQ..."
    kid = "my-key-id"
  }
  ```
- **Attributes:**
  - `kty` - Key type (usually "RSA")
  - `e` - RSA public exponent
  - `n` - RSA modulus
  - `kid` - Key ID for identification

### Application Settings

#### `client_uri` (Optional)
- **Type:** String
- **Description:** URL of the application's home page
- **Example:** `"https://myapp.example.com"`
- **Notes:** Shown in consent screens

#### `consent_method` (Optional)
- **Type:** String
- **Description:** How user consent is handled
- **Valid Values:**
  - `"REQUIRED"` - User must consent
  - `"TRUSTED"` - Auto-consent for trusted apps
- **Default:** `"TRUSTED"`
- **Example:** `"REQUIRED"`
- **Notes:** Third-party apps should use `"REQUIRED"`

#### `auto_key_rotation` (Optional)
- **Type:** Boolean or String
- **Description:** Whether Okta automatically rotates client secrets
- **Default:** `true`
- **Example:** `true`
- **Notes:** Security best practice to enable

#### `refresh_token_rotation` (Optional)
- **Type:** String
- **Description:** Refresh token rotation policy
- **Valid Values:**
  - `"STATIC"` - Refresh tokens don't rotate
  - `"ROTATE_ON_USE"` - New token issued on each use (requires additional config)
- **Default:** `"STATIC"`
- **Example:** `"STATIC"`
- **Notes:** Based on testing, `"STATIC"` has better compatibility

#### `refresh_token_leeway` (Optional)
- **Type:** Number
- **Description:** Grace period (in seconds) for refresh token rotation
- **Default:** `0`
- **Example:** `0`

### Visibility and Access

#### `hide_ios` (Optional)
- **Type:** Boolean or String
- **Description:** Hide app from Okta Mobile (iOS)
- **Default:** `false`
- **Example:** `true`
- **Notes:** Set to `true` for backend/API apps

#### `hide_web` (Optional)
- **Type:** Boolean or String
- **Description:** Hide app from Okta Web Dashboard
- **Default:** `false`
- **Example:** `true`
- **Notes:** Set to `true` for backend/API apps

#### `login_mode` (Optional)
- **Type:** String
- **Description:** Application login/initiation mode
- **Valid Values:**
  - `"DISABLED"` - No IdP-initiated login
  - `"SPEC"` - Application-specific login page
  - `"OKTA"` - Okta-hosted login
- **Default:** `"DISABLED"`
- **Example:** `"DISABLED"`
- **Important Constraint:**
  - Cannot be `"DISABLED"` if `hide_ios = false` OR `hide_web = false`
  - If using `"SPEC"`, must also provide `login_uri`

#### `login_uri` (Conditional)
- **Type:** String
- **Description:** Application-specific login initiation URL
- **Required:** When `login_mode = "SPEC"`
- **Example:** `"https://myapp.example.com/login"`

### User Management

#### `user_name_template` (Optional)
- **Type:** String
- **Description:** Template for username in the application
- **Example:** `"${source.login}"`
- **Default:** `"${source.login}"`
- **Important:** Must escape with `$$` in Terraform:
  ```hcl
  user_name_template = "$${source.login}"
  ```
- **Available Variables:**
  - `${source.login}` - User's Okta login
  - `${source.email}` - User's email
  - `${source.firstName}` - User's first name
  - `${source.lastName}` - User's last name

#### `user_name_template_type` (Optional)
- **Type:** String
- **Description:** Type of username template
- **Valid Values:**
  - `"BUILT_IN"` - Okta built-in template
  - `"CUSTOM"` - Custom template
- **Default:** `"BUILT_IN"`
- **Example:** `"BUILT_IN"`

#### `user_name_template_suffix` (Optional)
- **Type:** String
- **Description:** Suffix to append to usernames
- **Example:** `"@myapp.com"`

#### `user_name_template_push_status` (Optional)
- **Type:** String
- **Description:** Status of username template push to app
- **Notes:** Typically managed by Okta

### Advanced Settings

#### `implicit_assignment` (Optional)
- **Type:** Boolean or String
- **Description:** Automatically assign all users to the app
- **Default:** `false`
- **Example:** `false`
- **Notes:**
  - Security risk - explicitly assign users instead
  - Useful for internal apps everyone should access

#### `accessibility_self_service` (Optional)
- **Type:** Boolean or String
- **Description:** Allow users to request access via self-service
- **Default:** `false`
- **Example:** `false`

#### `auto_submit_toolbar` (Optional)
- **Type:** Boolean or String
- **Description:** Auto-submit credentials from Okta browser extension
- **Default:** `false`
- **Example:** `false`

#### `issuer_mode` (Optional)
- **Type:** String
- **Description:** How the issuer identifier is formatted
- **Valid Values:**
  - `"ORG_URL"` - Use organization URL as issuer
  - `"CUSTOM_URL"` - Use custom authorization server
  - `"DYNAMIC"` - Dynamic based on request
- **Default:** `"ORG_URL"`
- **Example:** `"ORG_URL"`

#### `wildcard_redirect` (Optional)
- **Type:** String
- **Description:** Allow wildcard in redirect URIs
- **Valid Values:**
  - `"DISABLED"` - No wildcards allowed (recommended)
  - `"SUBDOMAIN"` - Subdomain wildcards allowed
- **Default:** `"DISABLED"`
- **Example:** `"DISABLED"`
- **Notes:** **Security risk** - avoid in production

#### `status` (Optional)
- **Type:** String
- **Description:** Application status
- **Valid Values:**
  - `"ACTIVE"` - Application is active
  - `"INACTIVE"` - Application is deactivated
- **Default:** `"ACTIVE"`
- **Example:** `"ACTIVE"`

### JSON Settings

#### `app_links_json` (Optional)
- **Type:** String (JSON)
- **Description:** Application links configuration as JSON
- **Example:** `"{\"oidc_client_link\":true}"`
- **Notes:** Controls which links appear in user dashboard

#### `app_settings_json` (Optional)
- **Type:** String (JSON)
- **Description:** Application-specific settings as JSON
- **Example:** `"{}"`
- **Notes:** App-specific configuration

### Authentication Policy

#### `authentication_policy` (Optional)
- **Type:** String
- **Description:** ID of the authentication policy to use
- **Example:** `"rstrf0wlwjAEOO9IS1d7"`
- **Notes:** Controls sign-on requirements (MFA, etc.)

### Computed Attributes

#### `id`
- **Type:** String
- **Description:** Application ID
- **Example:** `"0oa1234567890abcdef"`

#### `client_id` (For OAuth apps)
- **Type:** String
- **Description:** OAuth client ID
- **Example:** `"0oarfddbqbmYn6AvT1d7"`
- **Notes:** Used in OAuth flows

#### `client_secret` (Sensitive)
- **Type:** String
- **Description:** OAuth client secret
- **Notes:**
  - **Sensitive** - not shown in logs
  - Store securely (vault, secrets manager)

#### `name`
- **Type:** String
- **Description:** Internal Okta name for the app
- **Example:** `"oidc_client"`

#### `sign_on_mode`
- **Type:** String
- **Description:** Sign-on mode (computed from type)
- **Example:** `"OPENID_CONNECT"`

#### `logo_url`
- **Type:** String
- **Description:** URL of the application logo
- **Example:** `"https://example.com/logo.png"`

### Example: Web Application

```hcl
resource "okta_app_oauth" "my_web_app" {
  # Basic config
  label = "My Web Application"
  type  = "web"

  # OAuth configuration
  grant_types    = ["authorization_code", "refresh_token"]
  response_types = ["code"]
  redirect_uris  = ["https://myapp.example.com/callback"]
  post_logout_redirect_uris = ["https://myapp.example.com/logout"]

  # Security
  pkce_required              = true
  token_endpoint_auth_method = "client_secret_post"
  consent_method             = "REQUIRED"

  # Application settings
  client_uri                 = "https://myapp.example.com"
  auto_key_rotation          = true
  refresh_token_rotation     = "STATIC"

  # Visibility
  hide_ios   = true
  hide_web   = true
  login_mode = "DISABLED"

  # User mapping
  user_name_template      = "$${source.login}"
  user_name_template_type = "BUILT_IN"

  # Advanced
  implicit_assignment = false
  wildcard_redirect   = "DISABLED"
  status              = "ACTIVE"

  # JSON settings
  app_links_json    = jsonencode({ oidc_client_link = true })
  app_settings_json = jsonencode({})
}
```

### Example: Service Application (M2M)

```hcl
resource "okta_app_oauth" "api_service" {
  label = "Backend API Service"
  type  = "service"

  grant_types    = ["client_credentials"]
  response_types = ["token"]

  token_endpoint_auth_method = "private_key_jwt"

  jwks {
    kty = "RSA"
    e   = "AQAB"
    n   = "your-rsa-modulus-here"
    kid = "service-key-1"
  }

  hide_ios   = true
  hide_web   = true
  login_mode = "DISABLED"

  user_name_template      = "$${source.login}"
  user_name_template_type = "BUILT_IN"
}
```

---

## okta_auth_server_default

Manages the default Okta authorization server.

### Attributes

#### `id` (Computed)
- **Type:** String
- **Description:** Authorization server ID
- **Value:** `"default"`
- **Notes:** The default auth server always has ID "default"

### Notes

The default authorization server is automatically created by Okta and has limited configuration options via Terraform. Most settings are managed through:
- Scopes (via `okta_auth_server_scope`)
- Claims (via `okta_auth_server_claim`)
- Policies (via `okta_auth_server_policy`)

### Example

```hcl
resource "okta_auth_server_default" "default" {
  # No configuration needed - just declares management
}
```

---

## okta_policy_mfa_default

Manages the default Multi-Factor Authentication (MFA) policy.

### Attributes

#### `id` (Computed)
- **Type:** String
- **Description:** Policy ID
- **Example:** `"00p1234567890abcdef"`
- **Notes:** Auto-assigned by Okta

### Notes

The default MFA policy is automatically created by Okta. Configuration typically includes:
- Which MFA factors are enabled
- Factor enrollment requirements
- Policy rules

These are typically managed via:
- `okta_policy_rule_mfa` for specific rules
- Okta Admin Console for factor settings

### Example

```hcl
resource "okta_policy_mfa_default" "default" {
  # No configuration needed - just declares management
}
```

---

## Common Patterns

### Template String Escaping

**Problem:** Okta uses `${variable}` for templates, Terraform uses `${}` for interpolation

**Solution:** Escape with double `$$`:

```hcl
# ❌ WRONG - Terraform tries to interpolate
user_name_template = "${source.login}"

# ✅ CORRECT - Literal string passed to Okta
user_name_template = "$${source.login}"
```

### Boolean vs String Booleans

Some attributes accept both `true` (boolean) and `"true"` (string):

```hcl
# Both valid
hide_ios = true
hide_ios = "true"

# Recommended: Use boolean for clarity
hide_ios = true
```

### JSON-Encoded Settings

Use `jsonencode()` for complex settings:

```hcl
app_settings_json = jsonencode({
  setting1 = "value1"
  setting2 = 123
  nested = {
    key = "value"
  }
})
```

### Secure Credential Management

**Never hardcode secrets:**

```hcl
# ❌ BAD
variable "api_token" {
  default = "00H_actual_token_here"
}

# ✅ GOOD - Use environment variables
variable "api_token" {
  type      = string
  sensitive = true
}

# ✅ GOOD - Use external secret managers
data "aws_secretsmanager_secret_version" "okta_token" {
  secret_id = "okta/api-token"
}
```

---

## Additional Resources

- [Okta Terraform Provider Documentation](https://registry.terraform.io/providers/okta/okta/latest/docs)
- [Okta API Reference](https://developer.okta.com/docs/reference/)
- [OAuth 2.0 Specification](https://oauth.net/2/)
- [OpenID Connect Specification](https://openid.net/connect/)
- [PKCE Specification](https://oauth.net/2/pkce/)

---

## Version Information

This reference is based on:
- **Okta Terraform Provider:** v6.1.0
- **Terraform:** >= 1.9.0

Some attributes may differ in other versions. Always check the official provider documentation for your specific version.

---

## Contributing

Found an error or missing attribute? Please submit a pull request or open an issue!

Last updated: 2025-11-04
