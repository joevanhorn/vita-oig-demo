# Prompt: Create Demo Environment

Use this prompt template to have an AI assistant generate a complete demo environment.

---

## Step 1: Provide Context

Copy and paste the following context files to your AI assistant:

**Repository Structure:**
```
[Paste contents of: ai-assisted/context/repository_structure.md]
```

**Terraform Examples:**
```
[Paste contents of: ai-assisted/context/terraform_examples.md]
```

**Resource Guide:**
```
[Paste contents of: ai-assisted/context/okta_resource_guide.md]
```

---

## Step 2: Use This Prompt Template

Copy this template and fill in your specific requirements:

```
I need to create a complete Okta demo environment using Terraform. Please generate
valid Terraform configuration files following the examples and patterns provided in
the context above.

ENVIRONMENT DETAILS:
- Target environment: myorg
- Files should go in: environments/myorg/terraform/

DEMO SCENARIO:
[Describe your demo scenario here]
Example: "SaaS company with engineering and marketing departments, integrated with
Salesforce and Google Workspace"

USERS TO CREATE:
[List users with details]
Example:
- Engineering Manager: Jane Smith (jane.smith@example.com, Engineering dept)
- 3 Engineers: [names and emails]
- Marketing Manager: Bob Jones (bob.jones@example.com, Marketing dept)
- 2 Marketing team members: [names and emails]

GROUPS TO CREATE:
[List groups]
Example:
- Engineering Team (all engineering users)
- Marketing Team (all marketing users)
- Managers (Jane and Bob)

APPLICATIONS TO CREATE:
[List applications with configuration details]
Example:
- Salesforce (OAuth web app, assign to Marketing Team)
- Internal Engineering Portal (OAuth SPA, assign to Engineering Team)
- API Gateway (service app for backend services)

OIG FEATURES (if applicable):
[List OIG features needed]
Example:
- Marketing Tools Bundle (includes Salesforce access)
- Quarterly Access Review campaign

OUTPUT REQUIREMENTS:
1. Generate separate .tf files for each resource type:
   - users.tf (all user resources)
   - groups.tf (all group resources)
   - group_memberships.tf (user-to-group assignments)
   - apps.tf (all application resources)
   - app_assignments.tf (group-to-app assignments)
   - [if OIG] oig_entitlements.tf (entitlement bundles)

2. Follow these rules:
   - Use exact naming patterns from examples
   - Escape template strings with $$ (e.g., "$${source.login}")
   - Include descriptive comments
   - Set status = "ACTIVE" for all resources
   - Use depends_on where appropriate
   - Generate realistic but fictitious data

3. Ensure all resources are properly connected:
   - Users → Group Memberships → Groups → App Assignments → Apps

4. Add a header comment to each file explaining its purpose

Please generate complete, ready-to-use Terraform code.
```

---

## Step 3: Review and Validate

After the AI generates the code:

1. **Copy the generated files** to your environment:
   ```bash
   cd environments/myorg/terraform
   # Paste generated code into appropriate files
   ```

2. **Validate syntax:**
   ```bash
   terraform fmt
   terraform validate
   ```

3. **Review for security:**
   - No hardcoded secrets
   - No real email addresses (use example.com)
   - Template strings properly escaped

4. **Test plan:**
   ```bash
   terraform plan
   ```

5. **Review the plan** before applying:
   - Check resource counts
   - Verify resource names
   - Confirm no unexpected changes

6. **Apply when ready:**
   ```bash
   terraform apply
   ```

---

## Example Filled Template

Here's an example of how you might fill out the template:

```
I need to create a complete Okta demo environment using Terraform.

ENVIRONMENT DETAILS:
- Target environment: myorg
- Files should go in: environments/myorg/terraform/

DEMO SCENARIO:
Mid-sized SaaS company demonstrating role-based access control and OIG features

USERS TO CREATE:
- CEO: Alice Williams (alice.williams@example.com)
- Engineering Manager: Jane Smith (jane.smith@example.com, Engineering dept)
- Engineers:
  * Dev Lead: Tom Brown (tom.brown@example.com, Engineering)
  * Senior Dev: Sarah Lee (sarah.lee@example.com, Engineering)
  * Junior Dev: Mike Chen (mike.chen@example.com, Engineering)
- Marketing Manager: Bob Jones (bob.jones@example.com, Marketing dept)
- Marketing Team:
  * Marketing Ops: Lisa Garcia (lisa.garcia@example.com, Marketing)
  * Content Manager: David Kim (david.kim@example.com, Marketing)

GROUPS TO CREATE:
- Engineering Team
- Marketing Team
- Leadership Team (Alice, Jane, Bob)
- All Employees

APPLICATIONS TO CREATE:
- Salesforce (OAuth web app, Marketing Team access)
- GitHub Enterprise (OAuth web app, Engineering Team access)
- Slack (OAuth web app, All Employees access)
- Internal Admin Portal (OAuth SPA, Leadership Team only)

OIG FEATURES:
- Create "Marketing Tools" entitlement bundle
- Create "Engineering Tools" entitlement bundle
- Create "Quarterly Access Review - Q1 2025" campaign

OUTPUT: Generate complete Terraform files following the requirements above.
```

---

## Tips for Best Results

1. **Be specific:** The more detail you provide, the better the output
2. **Use realistic names:** Makes demos more believable
3. **Think about dependencies:** Mention which groups should access which apps
4. **Start simple:** Generate basic setup first, then add complexity
5. **Iterate:** Generate code, test it, then ask AI to refine
6. **Verify examples:** Make sure context files are pasted correctly

---

## Common Follow-Up Prompts

After generating initial code, you might want to:

**Add more users:**
```
"Please add 3 more engineering users to the existing users.tf file,
following the same pattern. Names: Alex Rodriguez, Emma Watson, Chris Evans"
```

**Modify an app:**
```
"Update the Salesforce app configuration to include post_logout_redirect_uris
and change the redirect_uri to https://login.salesforce.com/callback"
```

**Add OIG features:**
```
"Create an entitlement bundle called 'Sales Tools' that I can manually
assign Salesforce and LinkedIn Sales Navigator to"
```

**Fix validation errors:**
```
"I got this Terraform validation error: [paste error].
Please fix the code to resolve this issue."
```

---

## Next Steps

After successfully generating your demo environment:

1. Commit your code to git
2. Document what the demo shows
3. Create a teardown plan (`terraform destroy`)
4. Consider creating variants for different demo scenarios
5. Share successful prompts with your team

For more advanced scenarios, see:
- `prompts/add_users.md` - Add users to existing environment
- `prompts/create_app.md` - Create specific applications
- `prompts/oig_setup.md` - Focus on OIG features
