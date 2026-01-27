# Example AI Session: Gemini

This is a real example of using Google Gemini to generate Okta Terraform code.

**Date:** 2025-01-07
**AI:** Google Gemini 1.5 Pro
**Task:** Generate a complete demo environment for a SaaS company

---

## Session Transcript

### User (Initial Context)

```
I'm going to paste you some context files about an Okta Terraform repository.
Please read and understand the patterns, then I'll ask you to generate some code.

[Pasted: ai-assisted/context/repository_structure.md]
[Pasted: ai-assisted/context/terraform_examples.md]
[Pasted: ai-assisted/context/okta_resource_guide.md]
```

### Gemini

```
I've reviewed the context files. I understand:

1. Repository Structure:
   - Environment-based organization (environments/myorg/terraform/)
   - Separate files for each resource type (users.tf, groups.tf, apps.tf, etc.)
   - Naming conventions using snake_case
   - Template string escaping with $$

2. Terraform Patterns:
   - User resources with email, first_name, last_name, login, status
   - Group resources with name and description
   - OAuth app resources with proper configuration
   - Group memberships and app assignments

3. Best Practices:
   - status = "ACTIVE" for production resources
   - user_name_template = "$${source.login}" (with $$ escaping)
   - PKCE required for security
   - Descriptive comments

I'm ready to generate Terraform code following these patterns. What would you like me to create?
```

### User (Main Request)

```
Perfect! I need to create a complete demo environment for a SaaS company demonstration.

ENVIRONMENT: myorg
TARGET PATH: environments/myorg/terraform/

DEMO SCENARIO:
Mid-sized SaaS company with engineering and marketing departments. Show RBAC and app integrations.

USERS TO CREATE:
- CEO: Alice Chen (alice.chen@example.com)
- Engineering Manager: David Kim (david.kim@example.com, Engineering dept, Senior Engineering Manager)
- Engineers:
  * Sarah Johnson (sarah.johnson@example.com, Engineering, Senior Software Engineer)
  * Mike Rodriguez (mike.rodriguez@example.com, Engineering, Software Engineer)
  * Emma Davis (emma.davis@example.com, Engineering, Junior Software Engineer)
- Marketing Manager: Lisa Wang (lisa.wang@example.com, Marketing dept, VP Marketing)
- Marketing Team:
  * Tom Brown (tom.brown@example.com, Marketing, Marketing Manager)
  * Jennifer Lee (jennifer.lee@example.com, Marketing, Content Strategist)

GROUPS TO CREATE:
- Engineering Team (all engineering users)
- Marketing Team (all marketing users)
- Leadership Team (Alice, David, Lisa)
- All Employees (everyone)

APPLICATIONS TO CREATE:
- GitHub Enterprise (OAuth web app, Engineering Team only)
  * Redirect URI: https://github.example.com/auth/callback
  * Grant types: authorization_code, refresh_token
  * PKCE: yes

- Salesforce (OAuth web app, Marketing Team only)
  * Redirect URI: https://login.salesforce.com/services/oauth2/callback
  * Grant types: authorization_code, refresh_token
  * PKCE: yes

- Slack (OAuth web app, All Employees)
  * Redirect URI: https://slack.example.com/oauth/callback
  * Grant types: authorization_code, refresh_token
  * PKCE: yes

OUTPUT: Generate separate .tf files for users, groups, group_memberships, apps, and app_assignments.
Please include descriptive comments and follow all the patterns from the context.
```

### Gemini (Generated Code)

```
I'll generate the complete Terraform configuration for your demo environment. Here are the files:

---
**File: environments/myorg/terraform/users.tf**

```hcl
# Demo Users for SaaS Company Demo Environment
# Last Updated: 2025-01-07

# CEO
resource "okta_user" "alice_chen" {
  email      = "alice.chen@example.com"
  first_name = "Alice"
  last_name  = "Chen"
  login      = "alice.chen@example.com"
  title      = "Chief Executive Officer"
  status     = "ACTIVE"
}

# Engineering Manager
resource "okta_user" "david_kim" {
  email      = "david.kim@example.com"
  first_name = "David"
  last_name  = "Kim"
  login      = "david.kim@example.com"
  department = "Engineering"
  title      = "Senior Engineering Manager"
  status     = "ACTIVE"
}

# Senior Software Engineer
resource "okta_user" "sarah_johnson" {
  email      = "sarah.johnson@example.com"
  first_name = "Sarah"
  last_name  = "Johnson"
  login      = "sarah.johnson@example.com"
  department = "Engineering"
  title      = "Senior Software Engineer"
  manager_id = okta_user.david_kim.id
  status     = "ACTIVE"
}

# Software Engineer
resource "okta_user" "mike_rodriguez" {
  email      = "mike.rodriguez@example.com"
  first_name = "Mike"
  last_name  = "Rodriguez"
  login      = "mike.rodriguez@example.com"
  department = "Engineering"
  title      = "Software Engineer"
  manager_id = okta_user.david_kim.id
  status     = "ACTIVE"
}

# Junior Software Engineer
resource "okta_user" "emma_davis" {
  email      = "emma.davis@example.com"
  first_name = "Emma"
  last_name  = "Davis"
  login      = "emma.davis@example.com"
  department = "Engineering"
  title      = "Junior Software Engineer"
  manager_id = okta_user.david_kim.id
  status     = "ACTIVE"
}

# VP Marketing
resource "okta_user" "lisa_wang" {
  email      = "lisa.wang@example.com"
  first_name = "Lisa"
  last_name  = "Wang"
  login      = "lisa.wang@example.com"
  department = "Marketing"
  title      = "VP Marketing"
  status     = "ACTIVE"
}

# Marketing Manager
resource "okta_user" "tom_brown" {
  email      = "tom.brown@example.com"
  first_name = "Tom"
  last_name  = "Brown"
  login      = "tom.brown@example.com"
  department = "Marketing"
  title      = "Marketing Manager"
  manager_id = okta_user.lisa_wang.id
  status     = "ACTIVE"
}

# Content Strategist
resource "okta_user" "jennifer_lee" {
  email      = "jennifer.lee@example.com"
  first_name = "Jennifer"
  last_name  = "Lee"
  login      = "jennifer.lee@example.com"
  department = "Marketing"
  title      = "Content Strategist"
  manager_id = okta_user.lisa_wang.id
  status     = "ACTIVE"
}
```

---
**File: environments/myorg/terraform/groups.tf**

```hcl
# Demo Groups for SaaS Company Demo Environment
# Last Updated: 2025-01-07

# Engineering Team
resource "okta_group" "engineering_team" {
  name        = "Engineering Team"
  description = "All engineering department members including developers and engineering managers"
}

# Marketing Team
resource "okta_group" "marketing_team" {
  name        = "Marketing Team"
  description = "All marketing department members including marketing managers and content team"
}

# Leadership Team
resource "okta_group" "leadership_team" {
  name        = "Leadership Team"
  description = "Executive leadership and department heads"
}

# All Employees
resource "okta_group" "all_employees" {
  name        = "All Employees"
  description = "All company employees across all departments"
}
```

---
**File: environments/myorg/terraform/group_memberships.tf**

```hcl
# Group Membership Assignments for Demo Environment
# Last Updated: 2025-01-07

# Engineering Team Members
resource "okta_group_memberships" "engineering_team_members" {
  group_id = okta_group.engineering_team.id
  users = [
    okta_user.david_kim.id,
    okta_user.sarah_johnson.id,
    okta_user.mike_rodriguez.id,
    okta_user.emma_davis.id,
  ]

  depends_on = [
    okta_user.david_kim,
    okta_user.sarah_johnson,
    okta_user.mike_rodriguez,
    okta_user.emma_davis,
  ]
}

# Marketing Team Members
resource "okta_group_memberships" "marketing_team_members" {
  group_id = okta_group.marketing_team.id
  users = [
    okta_user.lisa_wang.id,
    okta_user.tom_brown.id,
    okta_user.jennifer_lee.id,
  ]

  depends_on = [
    okta_user.lisa_wang,
    okta_user.tom_brown,
    okta_user.jennifer_lee,
  ]
}

# Leadership Team Members
resource "okta_group_memberships" "leadership_team_members" {
  group_id = okta_group.leadership_team.id
  users = [
    okta_user.alice_chen.id,
    okta_user.david_kim.id,
    okta_user.lisa_wang.id,
  ]

  depends_on = [
    okta_user.alice_chen,
    okta_user.david_kim,
    okta_user.lisa_wang,
  ]
}

# All Employees Members
resource "okta_group_memberships" "all_employees_members" {
  group_id = okta_group.all_employees.id
  users = [
    okta_user.alice_chen.id,
    okta_user.david_kim.id,
    okta_user.sarah_johnson.id,
    okta_user.mike_rodriguez.id,
    okta_user.emma_davis.id,
    okta_user.lisa_wang.id,
    okta_user.tom_brown.id,
    okta_user.jennifer_lee.id,
  ]

  depends_on = [
    okta_user.alice_chen,
    okta_user.david_kim,
    okta_user.sarah_johnson,
    okta_user.mike_rodriguez,
    okta_user.emma_davis,
    okta_user.lisa_wang,
    okta_user.tom_brown,
    okta_user.jennifer_lee,
  ]
}
```

---
**File: environments/myorg/terraform/apps.tf**

```hcl
# OAuth Applications for Demo Environment
# Last Updated: 2025-01-07

# GitHub Enterprise - Engineering Team
resource "okta_app_oauth" "github_enterprise" {
  label                      = "GitHub Enterprise"
  type                       = "web"
  grant_types                = ["authorization_code", "refresh_token"]
  redirect_uris              = ["https://github.example.com/auth/callback"]
  response_types             = ["code"]

  # Security settings
  pkce_required              = true
  token_endpoint_auth_method = "client_secret_post"

  # Application URLs
  client_uri                 = "https://github.example.com"
  logo_uri                   = "https://github.example.com/logo.png"

  # Login settings
  login_mode                 = "DISABLED"

  # Hide from end user dashboard
  hide_ios                   = true
  hide_web                   = true

  # User name template (IMPORTANT: escaped with $$)
  user_name_template         = "$${source.login}"
  user_name_template_type    = "BUILT_IN"
}

# Salesforce - Marketing Team
resource "okta_app_oauth" "salesforce" {
  label                      = "Salesforce"
  type                       = "web"
  grant_types                = ["authorization_code", "refresh_token"]
  redirect_uris              = ["https://login.salesforce.com/services/oauth2/callback"]
  response_types             = ["code"]

  # Security settings
  pkce_required              = true
  token_endpoint_auth_method = "client_secret_post"

  # Application URLs
  client_uri                 = "https://salesforce.com"
  logo_uri                   = "https://salesforce.com/logo.png"

  # Login settings
  login_mode                 = "DISABLED"

  # Hide from end user dashboard
  hide_ios                   = true
  hide_web                   = true

  # User name template (IMPORTANT: escaped with $$)
  user_name_template         = "$${source.login}"
  user_name_template_type    = "BUILT_IN"
}

# Slack - All Employees
resource "okta_app_oauth" "slack" {
  label                      = "Slack"
  type                       = "web"
  grant_types                = ["authorization_code", "refresh_token"]
  redirect_uris              = ["https://slack.example.com/oauth/callback"]
  response_types             = ["code"]

  # Security settings
  pkce_required              = true
  token_endpoint_auth_method = "client_secret_post"

  # Application URLs
  client_uri                 = "https://slack.example.com"
  logo_uri                   = "https://slack.example.com/logo.png"

  # Login settings
  login_mode                 = "DISABLED"

  # Hide from end user dashboard
  hide_ios                   = true
  hide_web                   = true

  # User name template (IMPORTANT: escaped with $$)
  user_name_template         = "$${source.login}"
  user_name_template_type    = "BUILT_IN"
}
```

---
**File: environments/myorg/terraform/app_assignments.tf**

```hcl
# Application Group Assignments for Demo Environment
# Last Updated: 2025-01-07

# GitHub Enterprise → Engineering Team
resource "okta_app_group_assignment" "github_engineering" {
  app_id   = okta_app_oauth.github_enterprise.id
  group_id = okta_group.engineering_team.id
}

# Salesforce → Marketing Team
resource "okta_app_group_assignment" "salesforce_marketing" {
  app_id   = okta_app_oauth.salesforce.id
  group_id = okta_group.marketing_team.id
}

# Slack → All Employees
resource "okta_app_group_assignment" "slack_all_employees" {
  app_id   = okta_app_oauth.slack.id
  group_id = okta_group.all_employees.id
}
```

---

I've generated all the necessary Terraform files for your demo environment:

**Summary:**
- ✅ 8 users (1 CEO, 4 engineering, 3 marketing)
- ✅ 4 groups (Engineering, Marketing, Leadership, All Employees)
- ✅ Proper group memberships with dependencies
- ✅ 3 OAuth applications (GitHub, Salesforce, Slack)
- ✅ Correct group-to-app assignments
- ✅ All template strings properly escaped with $$
- ✅ PKCE enabled for security
- ✅ Manager relationships set correctly
- ✅ Descriptive comments throughout

**Next Steps:**
1. Copy each file to your environments/myorg/terraform/ directory
2. Run `terraform fmt` to format
3. Run `terraform validate` to check syntax
4. Run `terraform plan` to preview changes
5. Run `terraform apply` to create the resources

Let me know if you need any modifications!
```
```

### User (Follow-up)

```
This looks great! Can you also add one more engineer named Carlos Martinez
(carlos.martinez@example.com, Engineering, DevOps Engineer) and add him
to the Engineering Team?
```

### Gemini (Update)

```
Sure! Here's the updated user and group membership to add Carlos Martinez:

**Add to users.tf:**

```hcl
# DevOps Engineer
resource "okta_user" "carlos_martinez" {
  email      = "carlos.martinez@example.com"
  first_name = "Carlos"
  last_name  = "Martinez"
  login      = "carlos.martinez@example.com"
  department = "Engineering"
  title      = "DevOps Engineer"
  manager_id = okta_user.david_kim.id
  status     = "ACTIVE"
}
```

**Update in group_memberships.tf - Engineering Team Members:**

Replace the engineering_team_members resource with:

```hcl
# Engineering Team Members
resource "okta_group_memberships" "engineering_team_members" {
  group_id = okta_group.engineering_team.id
  users = [
    okta_user.david_kim.id,
    okta_user.sarah_johnson.id,
    okta_user.mike_rodriguez.id,
    okta_user.emma_davis.id,
    okta_user.carlos_martinez.id,  # Added
  ]

  depends_on = [
    okta_user.david_kim,
    okta_user.sarah_johnson,
    okta_user.mike_rodriguez,
    okta_user.emma_davis,
    okta_user.carlos_martinez,  # Added
  ]
}
```

**Also update All Employees in group_memberships.tf:**

```hcl
# All Employees Members
resource "okta_group_memberships" "all_employees_members" {
  group_id = okta_group.all_employees.id
  users = [
    okta_user.alice_chen.id,
    okta_user.david_kim.id,
    okta_user.sarah_johnson.id,
    okta_user.mike_rodriguez.id,
    okta_user.emma_davis.id,
    okta_user.carlos_martinez.id,  # Added
    okta_user.lisa_wang.id,
    okta_user.tom_brown.id,
    okta_user.jennifer_lee.id,
  ]

  depends_on = [
    okta_user.alice_chen,
    okta_user.david_kim,
    okta_user.sarah_johnson,
    okta_user.mike_rodriguez,
    okta_user.emma_davis,
    okta_user.carlos_martinez,  # Added
    okta_user.lisa_wang,
    okta_user.tom_brown,
    okta_user.jennifer_lee,
  ]
}
```

Carlos is now added to both Engineering Team and All Employees!
```
```

---

## Key Takeaways from This Session

**What Worked Well:**
1. ✅ Providing complete context upfront (all 3 context files)
2. ✅ Specific, detailed requirements
3. ✅ Gemini followed all patterns correctly ($$, PKCE, status, etc.)
4. ✅ Generated clean, well-commented code
5. ✅ Easy to make iterative updates

**Tips for Success:**
- Always paste all context files first
- Be specific about requirements (names, emails, departments)
- Mention which groups should access which apps
- Ask for separate files (easier to manage)
- Iterate: start with basics, then add complexity

**Time Saved:**
- Manual coding: ~45-60 minutes
- With AI assistance: ~5-10 minutes
- **Time savings: 85-90%**

---

## Full File Outputs

The complete generated files are production-ready and can be applied immediately with:

```bash
cd environments/myorg/terraform
terraform init
terraform plan
terraform apply
```

This demo environment includes:
- 9 users across 2 departments
- 4 groups with proper memberships
- 3 integrated applications
- Manager relationships
- Role-based access control (RBAC)

Perfect for demonstrating Okta's capabilities to prospects!
