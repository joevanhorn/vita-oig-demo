# Prompt: Create OAuth Application

Use this prompt to generate OAuth/OIDC application configurations.

---

## Step 1: Provide Context

Paste these context files:

```
[Paste: ai-assisted/context/terraform_examples.md]
[Paste: ai-assisted/context/okta_resource_guide.md]
```

---

## Step 2: Use This Prompt Template

```
I need to create an OAuth/OIDC application in Okta using Terraform.

ENVIRONMENT: myorg
FILE: environments/myorg/terraform/apps.tf

APPLICATION DETAILS:
- Name: [Application name]
- Type: [web | browser | native | service]
- Description: [What this app does]
- Redirect URIs: [List of callback URLs]
- Grant Types: [authorization_code, refresh_token, client_credentials, etc.]
- PKCE Required: [yes/no]
- Client Authentication: [client_secret_post, client_secret_basic, none]

GROUP ASSIGNMENTS (optional):
- [List groups that should have access]

EXAMPLE:
Name: Customer Portal
Type: web
Description: Customer-facing web application
Redirect URIs: https://portal.example.com/callback
Grant Types: authorization_code, refresh_token
PKCE Required: yes
Assign to: Customers group

OUTPUT REQUIREMENTS:
1. Generate okta_app_oauth resource
2. Include okta_app_group_assignment if groups specified
3. Follow repository patterns exactly
4. Use proper escaping for user_name_template
5. Include descriptive comments
6. Set appropriate security settings

Please generate the Terraform configuration for this application.
```

---

## Application Type Guide

### Web Application (type = "web")
**Use for:** Traditional web apps with server-side code
**Grant Types:** authorization_code, refresh_token
**PKCE:** Recommended (yes)
**Client Auth:** client_secret_post or client_secret_basic

### Single Page Application (type = "browser")
**Use for:** React, Vue, Angular apps without backend
**Grant Types:** authorization_code only
**PKCE:** Required (yes)
**Client Auth:** none (public client)

### Native/Mobile App (type = "native")
**Use for:** iOS, Android, desktop applications
**Grant Types:** authorization_code, refresh_token
**PKCE:** Required (yes)
**Client Auth:** none (public client)

### Service/M2M App (type = "service")
**Use for:** Backend services, APIs, machine-to-machine
**Grant Types:** client_credentials
**PKCE:** Not applicable
**Client Auth:** client_secret_post or client_secret_basic

---

## Example Prompts and Outputs

### Example 1: React SPA

**Prompt:**
```
Create a Single Page Application for our React-based admin dashboard.

Name: Admin Dashboard
Type: browser (SPA)
Description: Internal admin dashboard built with React
Redirect URIs: http://localhost:3000/callback, https://admin.example.com/callback
Post Logout URIs: http://localhost:3000, https://admin.example.com
Grant Types: authorization_code
PKCE: yes (required for SPA)
Client Auth: none
Assign to: Administrators group

Generate okta_app_oauth resource and group assignment.
```

**Generated Code:**
```hcl
# Admin Dashboard - React SPA
resource "okta_app_oauth" "admin_dashboard" {
  label                      = "Admin Dashboard"
  type                       = "browser"
  grant_types                = ["authorization_code"]
  redirect_uris              = [
    "http://localhost:3000/callback",
    "https://admin.example.com/callback"
  ]
  post_logout_redirect_uris  = [
    "http://localhost:3000",
    "https://admin.example.com"
  ]
  response_types             = ["code"]

  # PKCE required for SPAs (public clients)
  pkce_required              = true

  # SPAs are public clients (no client secret)
  token_endpoint_auth_method = "none"

  # Application URLs
  client_uri                 = "https://admin.example.com"

  # Login settings
  login_mode                 = "DISABLED"

  # Hide from end user dashboard
  hide_ios                   = true
  hide_web                   = true

  # User name template
  user_name_template         = "$${source.login}"
  user_name_template_type    = "BUILT_IN"
}

# Assign to Administrators group
resource "okta_app_group_assignment" "admin_dashboard_admins" {
  app_id   = okta_app_oauth.admin_dashboard.id
  group_id = okta_group.administrators.id
}
```

### Example 2: Microservice API

**Prompt:**
```
Create a service application for our backend microservice.

Name: Payment Processing Service
Type: service
Description: Backend service for processing customer payments
Grant Types: client_credentials
Client Auth: client_secret_post
Scopes: process:payments, read:customer_data
No redirect URIs needed (service-to-service)

Generate okta_app_oauth resource.
```

**Generated Code:**
```hcl
# Payment Processing Service - Backend API
resource "okta_app_oauth" "payment_service" {
  label       = "Payment Processing Service"
  type        = "service"
  grant_types = ["client_credentials"]

  # Service apps use client credentials flow
  token_endpoint_auth_method = "client_secret_post"

  # No redirect URIs for service apps
  response_types = []

  # Application metadata
  client_uri  = "https://api.example.com/payments"

  # Login settings
  login_mode  = "DISABLED"

  # Hide from dashboards (backend service)
  hide_ios    = true
  hide_web    = true
}
```

### Example 3: Salesforce Integration

**Prompt:**
```
Create a Salesforce OAuth integration for our marketing team.

Name: Salesforce - Marketing
Type: web
Description: Salesforce CRM integration for marketing department
Redirect URIs: https://login.salesforce.com/services/oauth2/callback
Grant Types: authorization_code, refresh_token
PKCE: yes
Client Auth: client_secret_post
Assign to: Marketing Team group

Generate complete configuration including group assignment.
```

**Generated Code:**
```hcl
# Salesforce - Marketing Team Integration
resource "okta_app_oauth" "salesforce_marketing" {
  label                      = "Salesforce - Marketing"
  type                       = "web"
  grant_types                = ["authorization_code", "refresh_token"]
  redirect_uris              = ["https://login.salesforce.com/services/oauth2/callback"]
  response_types             = ["code"]

  # Security settings
  pkce_required              = true
  token_endpoint_auth_method = "client_secret_post"

  # Application URLs
  client_uri                 = "https://salesforce.com"

  # Login settings
  login_mode                 = "DISABLED"

  # Visibility settings
  hide_ios                   = true
  hide_web                   = true

  # User name template
  user_name_template         = "$${source.login}"
  user_name_template_type    = "BUILT_IN"
}

# Assign to Marketing Team
resource "okta_app_group_assignment" "salesforce_marketing_team" {
  app_id   = okta_app_oauth.salesforce_marketing.id
  group_id = okta_group.marketing_team.id
}
```

---

## Security Best Practices

When generating app configurations, ensure:

1. **PKCE Enabled:** Always use PKCE for web and browser apps
2. **Minimal Grant Types:** Only include necessary grant types
3. **HTTPS Redirect URIs:** Use HTTPS in production (http://localhost OK for dev)
4. **Hide from Dashboards:** Set hide_ios and hide_web to true for internal apps
5. **Template Escaping:** Always use `$$` in user_name_template

---

## Common Follow-Up Prompts

**Add scopes to authorization server:**
```
"I need to add custom scopes to this app for my authorization server.
Add scopes: read:data, write:data, admin:all"
```

**Update redirect URIs:**
```
"Add these additional redirect URIs to the Salesforce app:
- https://test.salesforce.com/services/oauth2/callback
- https://login.salesforce.com/services/oauth2/success"
```

**Change client authentication:**
```
"Update the app to use client_secret_basic instead of client_secret_post
for the token endpoint authentication method"
```

---

## Validation Steps

After generating app configuration:

1. **Validate syntax:**
   ```bash
   terraform fmt
   terraform validate
   ```

2. **Preview changes:**
   ```bash
   terraform plan
   ```

3. **Apply configuration:**
   ```bash
   terraform apply
   ```

4. **Get client credentials:**
   ```bash
   terraform show | grep -A 10 "okta_app_oauth.your_app_name"
   ```
   Note: Client secret in terraform.tfstate (handle securely!)

5. **Test in Okta Admin Console:**
   - Navigate to Applications
   - Find your app
   - Verify configuration
   - Test sign-in flow

---

## Related Documentation

- **OAuth Guide:** https://developer.okta.com/docs/guides/implement-grant-type/authcode/main/
- **OIDC Overview:** https://developer.okta.com/docs/concepts/oauth-openid/
- **App Types:** `docs/TERRAFORM_RESOURCES.md` (Applications section)
