# GitOps Workflow Guide

This repository implements a complete GitOps workflow for managing Okta infrastructure as code with Terraform.

## Table of Contents

1. [Overview](#overview)
2. [Branch Protection](#branch-protection)
3. [Development Workflow](#development-workflow)
4. [Automated Workflows](#automated-workflows)
5. [Manual Workflows](#manual-workflows)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### GitOps Principles

This repository follows GitOps best practices:

- **Git as single source of truth** - All infrastructure changes are version controlled
- **Pull request workflow** - All changes require review before merging
- **Automated validation** - Terraform plan runs on every PR
- **Controlled deployments** - Manual approval required for apply
- **Audit trail** - Complete history of all infrastructure changes

### Workflow Summary

```
┌─────────────────┐
│  Create Branch  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Make Changes   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Push Branch    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Create PR      │◄─── Terraform Plan runs automatically
└────────┬────────┘     Plan results posted as PR comment
         │
         ▼
┌─────────────────┐
│  Code Review    │◄─── Required: 1 approval
└────────┬────────┘     All conversations resolved
         │              Terraform Plan must pass
         ▼
┌─────────────────┐
│  Merge to Main  │◄─── Terraform Plan runs on main
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Manual Trigger │◄─── terraform-apply-with-approval
│  (Apply)        │     Requires manual approval
└─────────────────┘     Applies changes to Okta
```

---

## Branch Protection

The `main` branch is protected with the following rules:

### Required Status Checks
- **Terraform Plan** must pass before merging
- Branch must be **up to date** with main before merging

### Pull Request Requirements
- **1 approval** required before merging
- **Stale reviews dismissed** when new commits are pushed
- **All conversations must be resolved** before merging

### Branch Restrictions
- **No force pushes** to main
- **No deletions** of main branch
- **No direct commits** to main (must use PRs)

### Configuration

Branch protection is configured via GitHub API. To view current settings:

```bash
gh api repos/joevanhorn/okta-terraform-complete-demo/branches/main/protection
```

---

## Development Workflow

### Step 1: Create a Feature Branch

Never commit directly to `main`. Always create a branch:

```bash
# Create and switch to new branch
git checkout -b feature/add-new-users

# Or for bug fixes
git checkout -b fix/update-group-rules
```

**Branch naming conventions:**
- `feature/*` - New features or additions
- `fix/*` - Bug fixes or corrections
- `docs/*` - Documentation updates
- `refactor/*` - Code refactoring without functionality changes

### Step 2: Make Your Changes

Edit Terraform files in the appropriate environment:

```bash
# Example: Add new users
vim environments/myorg/terraform/users.tf

# Example: Update applications
vim environments/myorg/terraform/apps.tf
```

**Always validate locally:**

```bash
cd environments/myorg/terraform

# Format code
terraform fmt

# Validate syntax
terraform validate

# Optional: Run local plan (requires API token)
terraform plan
```

### Step 3: Commit and Push

```bash
# Stage changes
git add environments/myorg/terraform/

# Commit with descriptive message
git commit -m "feat: Add 5 new marketing users

- Added marketing team members
- Created Marketing-Advanced group
- Updated group assignments"

# Push to GitHub
git push -u origin feature/add-new-users
```

### Step 4: Create Pull Request

```bash
# Using GitHub CLI
gh pr create \
  --title "Add marketing team users" \
  --body "Adds 5 new marketing users and Marketing-Advanced group"

# Or use GitHub web interface
open https://github.com/joevanhorn/okta-terraform-complete-demo/compare
```

### Step 5: Wait for Automated Checks

GitHub Actions will automatically:

1. Run `terraform fmt -check` to verify formatting
2. Run `terraform validate` to check syntax
3. Run `terraform plan` to show proposed changes
4. Post plan results as a PR comment

**What to look for:**

```
✅ Terraform Plan - All checks passed

Plan: 5 to add, 0 to change, 0 to destroy
```

### Step 6: Code Review

Request review from a teammate or approve yourself (if you have permissions):

1. Reviewer examines Terraform plan output
2. Reviewer checks for:
   - Unintended deletions
   - Security issues
   - Naming conventions
   - Resource organization
3. Reviewer approves or requests changes

### Step 7: Resolve Conversations

If reviewer leaves comments:

1. Address all feedback
2. Push new commits to same branch
3. Terraform Plan will run again automatically
4. Previous approvals are dismissed (due to `dismiss_stale_reviews`)
5. Request re-review

### Step 8: Merge to Main

Once all checks pass and you have approval:

```bash
# Using GitHub CLI
gh pr merge --squash

# Or use GitHub web interface
```

**What happens on merge:**

1. PR is squashed and merged to main
2. Feature branch is deleted (optional)
3. Terraform Plan runs on main branch
4. Plan results are saved as artifacts
5. Ready for apply (manual step)

---

## Automated Workflows

### Terraform Plan (On Pull Request)

**Trigger:** Opened, updated, or synchronized PR to `main`

**File:** `.github/workflows/terraform-plan.yml`

**What it does:**

1. Detects which environment changed based on file paths
2. Checks out code
3. Sets up Terraform
4. Configures variables from GitHub secrets
5. Runs `terraform init`
6. Runs `terraform validate`
7. Runs `terraform fmt -check`
8. Runs `terraform plan`
9. Posts plan results as PR comment
10. Uploads plan artifact for review

**Example PR comment:**

```markdown
## Terraform Plan Results

<details>
<summary>Show Plan</summary>

```terraform
Terraform will perform the following actions:

  # okta_user.john_doe will be created
  + resource "okta_user" "john_doe" {
      + email      = "john.doe@example.com"
      + first_name = "John"
      + last_name  = "Doe"
      + login      = "john.doe@example.com"
      + status     = "ACTIVE"
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

</details>

*Environment: myorg*
```

### Terraform Plan (On Push to Main)

**Trigger:** Push to `main` branch that modifies terraform files

**File:** `.github/workflows/terraform-plan.yml`

**What it does:**

Same as PR workflow, but:
- Runs on the committed code
- Does not post PR comment
- Saves plan artifact for later apply
- Validates that merged code still plans correctly

**Protects against:**
- Merge conflicts affecting Terraform state
- Changes to secrets between PR and merge
- Concurrent merges causing plan drift

---

## Manual Workflows

### 1. Terraform Apply (with Approval)

**When to use:** After merging PR to main, to apply changes to Okta

**File:** `.github/workflows/terraform-apply-with-approval.yml`

**Steps:**

```bash
# Option 1: Use GitHub CLI
gh workflow run terraform-apply-with-approval.yml \
  -f environment=myorg

# Option 2: Use GitHub web interface
# 1. Go to Actions tab
# 2. Click "Terraform Apply (with Approval)"
# 3. Click "Run workflow"
# 4. Select environment
# 5. Click "Run workflow" button
```

**Process:**

1. **Approval Gate** - Workflow pauses and waits for manual approval
   - GitHub sends notification to approvers
   - Approver reviews the plan
   - Approver clicks "Approve and run" or "Reject"

2. **Apply Execution** (after approval)
   - Checks out code
   - Sets up Terraform
   - Generates fresh plan
   - Displays plan for final review
   - Runs `terraform apply -auto-approve`
   - Uploads apply output as artifact
   - Commits updated state file (if local state)

**Approval configuration:**

Approvers are configured in GitHub Settings > Environments:

```
Repository Settings
  └─ Environments
      └─ myorg-approval
          └─ Required reviewers: [Add approvers here]
```

### 2. Terraform Plan (Manual)

**When to use:**
- Testing workflow changes
- Planning for specific environment
- Investigating plan issues

**File:** `.github/workflows/terraform-plan.yml`

**Steps:**

```bash
gh workflow run terraform-plan.yml \
  -f environment=myorg
```

### 3. Terraform Apply (Legacy)

**When to use:** Emergency changes (bypasses approval)

**File:** `.github/workflows/terraform-apply.yml`

**Steps:**

```bash
# Dry run (plan only, no apply)
gh workflow run terraform-apply.yml \
  -f environment=myorg \
  -f dry_run=true \
  -f auto_approve=false

# Real apply (USE WITH CAUTION)
gh workflow run terraform-apply.yml \
  -f environment=myorg \
  -f dry_run=false \
  -f auto_approve=true
```

**Warning:** This workflow bypasses the approval gate. Only use for emergencies.

---

## Best Practices

### 1. Always Use Feature Branches

**Good:**
```bash
git checkout -b feature/add-users
# make changes
git push origin feature/add-users
# create PR
```

**Bad:**
```bash
git checkout main
# make changes
git push origin main  # ❌ BLOCKED by branch protection
```

### 2. Write Descriptive PR Titles

**Good:**
- `feat: Add 5 engineering users and GitHub OAuth app`
- `fix: Update Salesforce redirect URIs`
- `refactor: Organize users by department`

**Bad:**
- `Updates`
- `Fix`
- `Changes to terraform`

### 3. Review Terraform Plans Carefully

Before approving a PR, check:

- ✅ Only expected resources are being created/modified/deleted
- ✅ No accidental deletions of critical resources
- ✅ Sensitive data is not hardcoded
- ✅ Naming conventions are followed
- ✅ Resource counts make sense

**Example - Dangerous plan:**

```terraform
Plan: 1 to add, 0 to change, 50 to destroy.  # ⚠️ INVESTIGATE!
```

### 4. Use Conventional Commits

Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Test updates
- `chore:` - Maintenance tasks

**Example:**

```
feat(users): Add marketing team members

Added 5 new users:
- Jane Smith (Marketing Manager)
- Bob Jones (Content Strategist)
- Alice Chen (Social Media Specialist)
- Mike Davis (Marketing Coordinator)
- Sarah Lee (Campaign Manager)

Created Marketing-Advanced group and assigned users.

Closes #42
```

### 5. Keep PRs Focused

**Good PR:**
- Adds 5 users
- Creates 1 group
- Assigns users to group

**Bad PR:**
- Adds 20 users
- Creates 10 groups
- Modifies 5 applications
- Updates 3 group rules
- Changes authentication policies

**Why:** Smaller PRs are easier to review and safer to merge.

### 6. Test Locally When Possible

Before pushing:

```bash
cd environments/myorg/terraform

# Format
terraform fmt

# Validate
terraform validate

# Plan (if you have API token)
export OKTA_API_TOKEN="your-token"
terraform plan
```

### 7. Resolve All Conversations

Don't merge until:
- All reviewer comments are addressed
- All conversations are marked as resolved
- All questions are answered

### 8. Monitor Apply Jobs

After triggering apply:

```bash
# Watch the workflow
gh run watch

# Or view in browser
open https://github.com/joevanhorn/okta-terraform-complete-demo/actions
```

### 9. Document Infrastructure Changes

For significant changes, update:
- `README.md` - If adding new features
- `docs/TERRAFORM_RESOURCES.md` - If using new resources
- `testing/DETAILED_DEMO_BUILD_GUIDE.md` - If affecting demo builds

---

## Troubleshooting

### PR is Blocked - "Branch is out of date"

**Cause:** Someone else merged to main after you created your branch

**Solution:**

```bash
# Update your branch
git checkout main
git pull origin main
git checkout your-feature-branch
git merge main

# Resolve any conflicts
git add .
git commit -m "Merge main into feature branch"
git push
```

### PR is Blocked - "Terraform Plan failed"

**Cause:** Syntax error, validation error, or plan error

**Solution:**

1. Click "Details" on failed check
2. Review error message
3. Fix the issue locally
4. Commit and push fix
5. Plan will run again automatically

**Common errors:**

```terraform
Error: Invalid interpolation syntax
# Fix: Check for unescaped $ characters (use $$ in Okta templates)

Error: Duplicate resource
# Fix: Resource with same name exists elsewhere

Error: Missing required argument
# Fix: Add the required attribute
```

### PR is Blocked - "Requires approving review"

**Cause:** No one has approved your PR yet

**Solution:**

1. Request review from teammate
2. Or approve yourself (if you have permissions)
3. Or ask repo admin to approve

### Apply Fails - "Error acquiring state lock"

**Cause:** Another apply is running or didn't finish cleanly

**Solution:**

```bash
# Wait 5-10 minutes for lock to expire
# Or manually unlock (use with caution)
cd environments/myorg/terraform
terraform force-unlock <lock-id>
```

### Apply Fails - "API token is invalid"

**Cause:** GitHub secret is wrong or expired

**Solution:**

```bash
# Update secret via GitHub CLI
gh secret set OKTA_API_TOKEN

# Or via web interface
# Settings > Secrets and variables > Actions > Update OKTA_API_TOKEN
```

### Branch Protection Bypass Needed

**Scenario:** Emergency hotfix needed immediately

**Solution:**

Repository admins can temporarily disable branch protection:

```bash
# Disable enforcement
gh api -X PUT /repos/joevanhorn/okta-terraform-complete-demo/branches/main/protection \
  -f enforce_admins=false

# Make emergency change

# Re-enable enforcement
gh api -X PUT /repos/joevanhorn/okta-terraform-complete-demo/branches/main/protection \
  -f enforce_admins=true
```

**Better approach:** Use environment-specific approval bypass for emergencies

---

## Workflow Files Reference

### Terraform Plan
- **File:** `.github/workflows/terraform-plan.yml`
- **Triggers:** PR to main, push to main, manual
- **Purpose:** Validate and preview infrastructure changes
- **Outputs:** Plan artifact, PR comment

### Terraform Apply (with Approval)
- **File:** `.github/workflows/terraform-apply-with-approval.yml`
- **Triggers:** Manual only
- **Purpose:** Apply infrastructure changes with approval gate
- **Requires:** Manual approval from authorized users

### Terraform Apply (Legacy)
- **File:** `.github/workflows/terraform-apply.yml`
- **Triggers:** Manual only
- **Purpose:** Emergency apply without approval
- **Warning:** Bypasses approval process

---

## Environment Configuration

### GitHub Secrets Required

All environments need these secrets:

| Secret | Description | Example |
|--------|-------------|---------|
| `OKTA_ORG_NAME` | Okta organization name | `dev-12345678` |
| `OKTA_BASE_URL` | Okta base URL | `okta.com` or `oktapreview.com` |
| `OKTA_API_TOKEN` | Okta API token | `00abc...xyz` |

### Environment-Specific Approvers

Configure in: Settings > Environments

| Environment | Approval Required | Approvers |
|-------------|-------------------|-----------|
| `myorg` | No | N/A |
| `myorg-approval` | Yes | [Configure here] |
| `production` | Yes | [Configure here] |
| `production-approval` | Yes | [Configure here] |

---

## Security Considerations

### 1. Secrets Management

- Never commit API tokens
- Use GitHub encrypted secrets
- Rotate tokens regularly
- Use least-privilege tokens

### 2. State Files

- Never commit `terraform.tfstate`
- Use remote backend (S3, Terraform Cloud) for production
- Current setup uses local state for demo purposes

### 3. Code Review

- Always require review before merge
- Focus on security implications
- Check for overly permissive permissions

### 4. Audit Trail

- All changes are tracked in Git history
- All approvals are logged in PR timeline
- All applies create workflow run artifacts

---

## Label Management GitOps Workflow

### Overview

Governance labels are managed through a dedicated GitOps workflow that provides validation, dry-runs, and manual approval before applying changes to Okta.

### Workflow Architecture

```
┌──────────────────────────────────────────────────────────┐
│              Label Management GitOps Flow                 │
└──────────────────────────────────────────────────────────┘

  Developer
     │
     ├─ Edit label_mappings.json
     │  (Add/modify label assignments)
     │
     ├─ Create Feature Branch
     │  git checkout -b feature/add-privileged-labels
     │
     ├─ Commit and Push
     │  git commit -m "feat: Label admin apps as Privileged"
     │
     ▼
┌──────────────────────────────────────────────────────────┐
│           Phase 1: Pull Request Validation               │
│                                                           │
│  Workflow: validate-label-mappings.yml                   │
│  Trigger: PR that modifies label_mappings.json           │
│  Secrets: NONE (syntax-only validation)                  │
│                                                           │
│  ✅ Validate JSON syntax                                 │
│  ✅ Check required structure (labels, assignments)       │
│  ✅ Validate ORN formats (must start with orn:)         │
│  ✅ Post validation results as PR comment                │
│                                                           │
└──────────────────────────────────────────────────────────┘
     │
     ├─ Code Review
     ├─ Approval
     ├─ Merge to Main
     │
     ▼
┌──────────────────────────────────────────────────────────┐
│          Phase 2: Automatic Dry-Run on Merge             │
│                                                           │
│  Workflow: apply-labels-from-config.yml                  │
│  Trigger: Push to main (label_mappings.json changed)     │
│  Environment: Auto-detected from file path, uses secrets │
│  Mode: DRY RUN (no changes made)                         │
│                                                           │
│  🔍 Connect to Okta API                                  │
│  🔍 Validate labels exist or show what would be created  │
│  🔍 Show assignment operations that would be performed   │
│  🔍 Upload results as workflow artifacts                 │
│                                                           │
└──────────────────────────────────────────────────────────┘
     │
     ├─ Review Dry-Run Results
     ├─ Verify no errors
     ├─ Confirm changes look correct
     │
     ▼
┌──────────────────────────────────────────────────────────┐
│            Phase 3: Manual Apply Trigger                 │
│                                                           │
│  Workflow: apply-labels-from-config.yml                  │
│  Trigger: Manual workflow dispatch                       │
│  Environment: Specified via input parameter              │
│  Mode: APPLY (makes changes to Okta)                     │
│                                                           │
│  Command:                                                 │
│  gh workflow run apply-labels-from-config.yml \          │
│    -f environment=myorg \                        │
│    -f dry_run=false                                       │
│                                                           │
│  ✅ Create labels in Okta                                │
│  ✅ Assign labels to resources                           │
│  ✅ Upload results as workflow artifacts                 │
│  ✅ Complete audit trail in Git                          │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### Key Benefits

1. **Code Review for Governance Changes**
   - All label changes go through PR review
   - Validates configuration before merging
   - Team visibility into governance changes

2. **Separation of Concerns**
   - PR validation: Syntax check (no secrets needed)
   - Deployment: API validation (uses environment secrets)
   - Respects GitHub Environment protection rules

3. **Safety Through Automation**
   - Automatic dry-run on merge shows impact
   - Manual approval required for actual changes
   - No accidental deployments to production

4. **Complete Audit Trail**
   - Git history shows who changed what and when
   - PR discussions capture rationale
   - Workflow logs provide execution details

### Step-by-Step: Adding a Label Assignment

#### 1. Create Feature Branch

```bash
git checkout -b feature/label-crm-as-privileged
```

#### 2. Edit Label Configuration

```bash
vim environments/myorg/config/label_mappings.json
```

Add the resource ORN to the appropriate label assignment:

```json
{
  "labels": {
    "Privileged": {
      "type": "single_value",
      "description": "High-privilege applications"
    }
  },
  "assignments": {
    "apps": {
      "Privileged": [
        "orn:okta:idp:myorg:apps:saml2:0oa123EXISTING",
        "orn:okta:idp:myorg:apps:oauth2:0oa456NEWAPP"
      ]
    }
  }
}
```

#### 3. Commit and Push

```bash
git add environments/myorg/config/label_mappings.json
git commit -m "feat: Label CRM app as Privileged

Adding Privileged label to CRM application for enhanced
governance and access review filtering."

git push -u origin feature/label-crm-as-privileged
```

#### 4. Create Pull Request

```bash
gh pr create \
  --title "Label CRM app as Privileged" \
  --body "Marking the CRM application as privileged to include it in quarterly admin access reviews."
```

#### 5. Automatic PR Validation

GitHub Actions automatically:
- Runs `validate-label-mappings.yml` workflow
- Validates JSON syntax
- Checks ORN formats
- Posts results as PR comment

**What to check:**
- ✅ Green checkmark on PR (validation passed)
- ✅ PR comment shows configuration summary
- ✅ No validation errors

#### 6. Code Review and Merge

- Get approval from teammate
- Ensure all conversations resolved
- Merge PR to main

#### 7. Automatic Dry-Run

On merge to main, GitHub Actions automatically:
- Runs `apply-labels-from-config.yml` in dry-run mode
- Connects to Okta API (using environment secrets)
- Shows what would be created/assigned
- Uploads results as artifacts

**What to review:**
- Workflow summary shows dry-run mode
- Labels to create count
- Assignments to apply count
- No errors in execution

#### 8. Manual Apply (After Review)

```bash
# Trigger apply workflow manually
gh workflow run apply-labels-from-config.yml \
  -f environment=myorg \
  -f dry_run=false

# Monitor execution
gh run watch

# Download artifacts for review
gh run download <RUN_ID>
```

**What happens:**
- Labels created in Okta (if they don't exist)
- Label assignments applied to resources
- Results uploaded as workflow artifacts
- Complete log available for audit

#### 9. Verify in Okta

Navigate to Okta Admin Console:
- Identity Governance → Labels
- Verify label exists and assignments are correct
- Check resources show the applied label

### Configuration File Structure

The `label_mappings.json` file has this structure:

```json
{
  "labels": {
    "LabelName": {
      "type": "single_value" | "multi_value",
      "description": "Description of the label",
      "labelId": "00l123..." (populated by sync script),
      "values": {
        "ValueName": {
          "description": "Description of the value",
          "labelValueId": "00v456..." (populated by sync script)
        }
      }
    }
  },
  "assignments": {
    "apps": {
      "LabelName": ["orn:okta:...", "orn:okta:..."],
      "LabelName:ValueName": ["orn:okta:..."]
    },
    "groups": {
      "LabelName": ["orn:okta:...", "orn:okta:..."]
    },
    "entitlements": {
      "LabelName": ["orn:okta:...", "orn:okta:..."]
    }
  }
}
```

**Key Points:**
- `labels`: Define label names, types, and values
- `assignments`: Map labels to resource ORNs
- `labelId` and `labelValueId`: Auto-populated by sync script
- Multi-value labels use `LabelName:ValueName` format in assignments

### Workflows Reference

#### Workflow 1: validate-label-mappings.yml

**Purpose:** Validate label configuration on PRs

**Triggers:**
- Pull request events (opened, synchronize, reopened)
- Only when `label_mappings.json` is modified

**Permissions:**
- `contents: read` - Read repository files
- `pull-requests: write` - Post PR comments

**Environment:** None (no secrets needed)

**What It Does:**
1. Checks out PR code
2. Sets up Python
3. Finds changed label mapping files
4. Validates JSON syntax
5. Runs `validate_label_config.py` script
6. Posts validation results as PR comment
7. Exits with error if validation fails (blocks merge)

#### Workflow 2: apply-labels-from-config.yml

**Purpose:** Apply labels to Okta (with dry-run support, environment-agnostic)

**Triggers:**
- Push to main (when `label_mappings.json` changes) - Auto dry-run
- Manual workflow dispatch - With dry_run choice

**Permissions:**
- `contents: write` - Commit if needed
- `actions: read` - Read workflow info

**Environment:** MyOrg (with Okta API secrets)

**What It Does:**
1. Checks out code
2. Sets up Python
3. Displays label configuration
4. Determines dry-run mode:
   - Push to main: Always dry-run
   - Manual dispatch: Uses input parameter
5. Runs `apply_labels_from_config.py` script
6. Parses and uploads results
7. Posts summary to workflow

**Inputs (Manual Dispatch):**
- `dry_run`: Choice of 'true' or 'false' (default: 'true')

### Environment Protection Strategy

The deployment workflow (`apply-labels-from-config.yml`) uses GitHub Environment protection:

**Why No Pull Request Trigger:**
- GitHub Environment protection applies to ALL workflow runs
- PR workflows can't access environment secrets (by design)
- Validation must happen without secrets (syntax-only)

**Solution:**
- PR validation: Separate workflow, no environment, no secrets
- Deployment: Uses environment, has secrets, only runs on main or manual

**This Prevents:**
- External contributors accessing environment secrets via PRs
- Accidental deployments from unreviewed code
- Bypassing environment protection rules

### Best Practices

1. **Small, Focused Changes**
   - One label operation per PR
   - Clear commit messages explaining why
   - Easy to review and rollback

2. **Always Review Dry-Run**
   - Never skip straight to apply
   - Verify counts match expectations
   - Check for unexpected operations

3. **Sync After Manual Changes**
   ```bash
   # If labels created manually in Okta
   python3 scripts/sync_label_mappings.py \
     --output environments/myorg/config/label_mappings.json

   git add environments/myorg/config/label_mappings.json
   git commit -m "chore: Sync label IDs from Okta"
   ```

4. **Monitor Workflow Runs**
   ```bash
   # List recent label workflow runs
   gh run list --workflow=apply-labels-from-config.yml

   # Watch a specific run
   gh run watch <RUN_ID>

   # Download artifacts for offline review
   gh run download <RUN_ID>
   ```

5. **Document Label Taxonomy**
   - Maintain documentation of label meanings
   - Document when each label should be used
   - Keep label descriptions up to date

### Troubleshooting

**Issue: PR validation workflow doesn't run**

**Cause:** File path doesn't match workflow trigger

**Solution:**
- Ensure file is at: `environments/*/config/label_mappings.json`
- Check PR includes changes to this file
- Verify workflow exists: `.github/workflows/validate-label-mappings.yml`

**Issue: Dry-run shows errors**

**Cause:** Invalid ORNs, missing labels, or API issues

**Solution:**
1. Check workflow logs for specific error
2. Validate ORNs are correct format
3. Ensure labels exist (or script will create them)
4. Verify API token has governance permissions

**Issue: Apply works but labels don't show in Okta**

**Cause:** UI cache or sync delay

**Solution:**
- Clear browser cache
- Wait 1-2 minutes for UI to sync
- Verify via API query:
  ```bash
  curl -X GET "https://myorg.oktapreview.com/governance/api/v1/labels" \
    -H "Authorization: SSWS $OKTA_API_TOKEN"
  ```

---

## Related Documentation

- **[Manual Validation Plan](../testing/MANUAL_VALIDATION_PLAN.md)** - Testing checklist (Section 5.4.3 for label workflows)
- **[Demo Build Guide](../testing/DETAILED_DEMO_BUILD_GUIDE.md)** - Step-by-step tutorials (Level 5 for OIG and labels)
- **[API Management Guide](./API_MANAGEMENT.md)** - GitOps label validation workflow details
- **[Terraform Resources](TERRAFORM_RESOURCES.md)** - Resource reference
- **[Main README](../README.md)** - Repository overview

---

**Last Updated:** 2025-11-10

**Questions?** Review the troubleshooting section or check workflow run logs in the Actions tab.
