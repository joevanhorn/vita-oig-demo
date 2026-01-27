# Prompt: Add Users to Existing Environment

Use this prompt to add users to an existing Terraform-managed Okta environment.

---

## Step 1: Provide Context

Paste these context files to your AI:

```
[Paste: ai-assisted/context/repository_structure.md]
[Paste: ai-assisted/context/terraform_examples.md]
```

---

## Step 2: Use This Prompt

```
I need to add new users to an existing Okta Terraform environment.

ENVIRONMENT: myorg
FILE: environments/myorg/terraform/users.tf

EXISTING USERS (for reference):
[List a few existing users if helpful for pattern matching]

NEW USERS TO ADD:
[List new users with details]
Example:
- Name: John Doe
  Email: john.doe@example.com
  Department: Engineering
  Title: Senior Engineer
  Manager: [reference to existing user if applicable]

OUTPUT REQUIREMENTS:
1. Generate only the new okta_user resources
2. Follow exact naming pattern of existing resources
3. Use status = "ACTIVE"
4. Include department and title
5. Add descriptive comments

Please generate the Terraform code for these new users.
```

---

## Step 3: Add Generated Users

1. Copy the generated `okta_user` resources
2. Append to your existing `users.tf` file
3. Run `terraform fmt` to format
4. Run `terraform plan` to preview changes
5. Run `terraform apply` to create the users

---

## Adding Users to Groups

If you also need to add these users to groups:

```
I need to update group memberships to include the new users I just added.

NEW USERS:
- john_doe (should be in Engineering group)
- jane_smith (should be in Marketing group)

EXISTING GROUP MEMBERSHIPS:
[Paste your current okta_group_memberships resources]

Please update the group_memberships resources to include the new user IDs.
```

---

## Example

**Prompt:**
```
I need to add 3 new marketing team members to my Okta environment.

ENVIRONMENT: myorg
FILE: environments/myorg/terraform/users.tf

NEW USERS:
- Sarah Johnson, sarah.johnson@example.com, Marketing, Social Media Manager
- Mike Davis, mike.davis@example.com, Marketing, Content Strategist
- Emily Chen, emily.chen@example.com, Marketing, Marketing Analyst

OUTPUT: Generate okta_user resources following the repository patterns.
```

**Result:**
```hcl
resource "okta_user" "sarah_johnson" {
  email      = "sarah.johnson@example.com"
  first_name = "Sarah"
  last_name  = "Johnson"
  login      = "sarah.johnson@example.com"
  department = "Marketing"
  title      = "Social Media Manager"
  status     = "ACTIVE"
}

resource "okta_user" "mike_davis" {
  email      = "mike.davis@example.com"
  first_name = "Mike"
  last_name  = "Davis"
  login      = "mike.davis@example.com"
  department = "Marketing"
  title      = "Content Strategist"
  status     = "ACTIVE"
}

resource "okta_user" "emily_chen" {
  email      = "emily.chen@example.com"
  first_name = "Emily"
  last_name  = "Chen"
  login      = "emily.chen@example.com"
  department = "Marketing"
  title      = "Marketing Analyst"
  status     = "ACTIVE"
}
```
