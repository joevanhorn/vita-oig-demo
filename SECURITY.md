# Security Best Practices

This document outlines security best practices for managing Okta with Terraform and GitOps.

---

## 🚨 Critical: Environment Secrets vs Repository Secrets

**This is the #1 security misconfiguration!**

### ⚠️ The Problem

Using **Repository secrets** instead of **Environment secrets** can cause:
- Resources created in wrong Okta organization
- Production credentials used in development
- Accidental cross-environment data leakage
- Difficult-to-debug authentication issues

### ✅ Correct Setup: Environment Secrets

Each environment should have its own isolated secrets:

```
Settings → Environments → Production → Secrets
  OKTA_API_TOKEN    = prod-token-xxx
  OKTA_ORG_NAME     = your-company
  OKTA_BASE_URL     = okta.com

Settings → Environments → Staging → Secrets
  OKTA_API_TOKEN    = staging-token-xxx
  OKTA_ORG_NAME     = your-company-staging
  OKTA_BASE_URL     = oktapreview.com
```

### ❌ Wrong Setup: Repository Secrets

**DON'T DO THIS:**

```
Settings → Secrets and variables → Actions → Repository secrets
  OKTA_API_TOKEN    = ❌ Applies to ALL environments!
  OKTA_ORG_NAME     = ❌ Wrong org might be used!
```

### Verify Your Setup

```bash
# Check repository secrets (should ONLY be AWS_ROLE_ARN)
gh secret list

# Expected output:
# AWS_ROLE_ARN  Updated YYYY-MM-DD

# Check environment secrets (should be Okta credentials)
gh secret list -e Production

# Expected output:
# OKTA_API_TOKEN   Updated YYYY-MM-DD
# OKTA_ORG_NAME    Updated YYYY-MM-DD
# OKTA_BASE_URL    Updated YYYY-MM-DD
```

---

## 🔑 Okta API Token Security

### Token Permissions (Least Privilege)

Use separate tokens with minimal required scopes:

| Use Case | Required Scopes | Notes |
|----------|----------------|-------|
| **Read-only (import)** | `okta.*.read` | Safest, for sync/drift detection |
| **Full management** | `okta.*.manage` | Required for terraform apply |
| **Governance only** | `okta.governance.*` | Labels and resource owners |

**Best Practice:** Use read-only token for scheduled imports, full-access token only for apply operations.

### Token Rotation Schedule

| Environment | Rotation Frequency | When to Rotate Immediately |
|-------------|-------------------|---------------------------|
| **Production** | Every 90 days | Token exposed, team member leaves |
| **Staging** | Every 180 days | Token exposed, suspicious activity |
| **Development** | Every 180 days | Token exposed |

### Creating Tokens with Correct Permissions

1. Log into Okta Admin Console
2. Go to **Security → API → Tokens**
3. Click **Create Token**
4. Name descriptively: `Terraform-Production-RW` or `Terraform-Staging-RO`
5. **Document creation date** in GitHub Environment description
6. Copy token immediately (shown only once!)

### Token Storage Checklist

- [ ] Stored in GitHub **Environment** secrets (not repository secrets!)
- [ ] Separate token per environment
- [ ] Token name indicates purpose (prod/staging/read-only/read-write)
- [ ] Creation date documented
- [ ] Never committed to git
- [ ] Not shared between team members
- [ ] Not reused across multiple projects

### Revoking Compromised Tokens

**If a token is exposed:**

1. **Immediately revoke** in Okta Admin Console:
   - Security → API → Tokens → [Find token] → Revoke

2. **Generate new token** with same scopes

3. **Update GitHub Environment secret**:
   ```bash
   gh secret set OKTA_API_TOKEN -e Production --body "new-token-here"
   ```

4. **Review Okta System Log** for unauthorized activity:
   - Filter by Actor: Previous token
   - Time range: Last 7 days
   - Look for unexpected changes

5. **Document incident** and update procedures

---

## 🔐 State File Security

### What's in State Files?

Terraform state files contain:
- ✅ Resource IDs (not sensitive alone)
- ⚠️ Resource configurations
- ⚠️ ORNs (Okta Resource Names)
- ⚠️ Potentially secrets (if you put them in Terraform - **DON'T!**)

### State Protection Measures

**AWS S3 Backend:**
- [ ] Encryption at rest enabled (AES256)
- [ ] Versioning enabled (for recovery)
- [ ] Bucket access restricted via IAM
- [ ] Bucket policy blocks public access
- [ ] DynamoDB locking enabled
- [ ] CloudTrail logging enabled (audit)

**Terraform Cloud:**
- [ ] Workspace access restricted
- [ ] Team permissions configured
- [ ] State access logged
- [ ] Encryption at rest (automatic)

**Local State (Testing Only):**
- [ ] Never used for production
- [ ] State file not committed to git
- [ ] Regular manual backups
- [ ] Encrypted disk storage

### State File Best Practices

**DO:**
- ✅ Use remote backend (S3 or Terraform Cloud)
- ✅ Enable encryption
- ✅ Enable versioning for rollback
- ✅ Restrict access via IAM/RBAC
- ✅ Regular backups
- ✅ Audit access logs

**DON'T:**
- ❌ Commit state files to git
- ❌ Store secrets in Terraform variables (use environment variables)
- ❌ Share state between environments
- ❌ Use local state for production
- ❌ Give wide IAM/bucket access

### Verify State Security

```bash
# Check .gitignore includes state files
grep -E "\.tfstate|\.tfstate\.backup" .gitignore

# Should return:
# *.tfstate
# *.tfstate.*

# Verify no state files committed
git log --all --full-history -- "*.tfstate*"

# Should return: nothing (no results = good)

# Check S3 bucket encryption (if using S3)
aws s3api get-bucket-encryption --bucket okta-terraform-demo

# Should show AES256 or aws:kms encryption
```

---

## 🛡️ GitHub Actions Security

### Workflow Security

**Authentication:**
- ✅ Use Environment secrets (not repository secrets)
- ✅ Use AWS OIDC (no long-lived AWS keys)
- ✅ Okta tokens scoped to minimum permissions
- ✅ Workflow approvals for production

**Workflow Files:**
```yaml
jobs:
  job-name:
    # ALWAYS specify environment for Okta credentials
    environment: ${{ inputs.environment }}  # Good!
    # environment: Production              # Also good!
    # [no environment]                     # BAD!

    permissions:
      id-token: write  # Required for AWS OIDC
      contents: read   # Minimum needed
```

### Preventing Secret Exposure

**In workflows:**
```yaml
- name: Terraform Apply
  env:
    TF_VAR_okta_api_token: ${{ secrets.OKTA_API_TOKEN }}
  run: |
    # Secrets automatically masked in logs
    terraform apply -auto-approve
```

**Never do this:**
```yaml
- name: Debug  # ❌ BAD!
  run: |
    echo "Token: ${{ secrets.OKTA_API_TOKEN }}"  # ❌ Exposes secret!
```

### Workflow Security Checklist

- [ ] All production workflows require environment
- [ ] Environment protection rules configured
- [ ] Required reviewers set for production
- [ ] Wait timer configured (5-10 min for production)
- [ ] Branch protection rules enabled
- [ ] Status checks required before merge
- [ ] Secrets never echoed to logs
- [ ] Workflow runs logged and reviewed regularly

---

## 🔒 Git Security

### Never Commit These Files

**Add to `.gitignore`:**
```gitignore
# Terraform
*.tfstate
*.tfstate.*
*.tfvars
.terraform/
.terraform.lock.hcl

# Secrets
.env
*.key
*.pem
credentials.json
secrets.yaml

# Logs (may contain tokens)
*.log
*_output.txt
*_results.json

# Temporary
complete-import-*/
```

### Pre-Commit Checks

**Scan for secrets before committing:**

```bash
# Check for potential secrets
git diff --cached | grep -iE "api.token|secret|password|key.*=|token.*="

# Use git-secrets (install once)
brew install git-secrets
git secrets --install
git secrets --register-aws

# Scan repository
git secrets --scan
```

### Removing Accidentally Committed Secrets

**If you committed a secret:**

1. **Revoke the secret immediately** (Okta token, AWS key, etc.)

2. **Remove from git history:**
   ```bash
   # Use BFG Repo Cleaner (safest)
   brew install bfg
   bfg --replace-text passwords.txt  # File with secrets to remove
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   ```

3. **Force push** (⚠️ coordinate with team):
   ```bash
   git push --force-with-lease
   ```

4. **Generate new secret** and update GitHub

5. **Audit Okta System Log** for unauthorized use

---

## 🔍 Security Audit Checklist

Run this monthly:

### 1. Secret Management Audit

```bash
# Verify only AWS role in repository secrets
gh secret list | wc -l
# Expected: 1 (AWS_ROLE_ARN)

# Verify each environment has required secrets
for env in Production Staging Development; do
  echo "Checking $env..."
  gh secret list -e $env | grep -E "OKTA_API_TOKEN|OKTA_ORG_NAME|OKTA_BASE_URL"
done
# Each should show 3 secrets
```

### 2. Token Rotation Check

```bash
# Check token ages in GitHub Environment descriptions
# Rotate any > 90 days old (production)
# Rotate any > 180 days old (staging/development)
```

### 3. Git History Scan

```bash
# Scan for accidentally committed secrets
git log -p | grep -iE "api.token|okta.*token|password|secret.*=" || echo "Clean!"

# Check no state files committed
git log --all --full-history -- "*.tfstate*" || echo "Clean!"

# Check no .env files committed
git log --all --full-history -- ".env" || echo "Clean!"
```

### 4. State File Security

```bash
# Verify .gitignore coverage
git check-ignore -v *.tfstate .env *.key

# Check S3 bucket security (if using S3)
aws s3api get-bucket-acl --bucket okta-terraform-demo
# Should show owner-only access

aws s3api get-bucket-encryption --bucket okta-terraform-demo
# Should show encryption enabled

aws s3api get-bucket-versioning --bucket okta-terraform-demo
# Should show versioning enabled
```

### 5. Okta System Log Review

1. Log into Okta Admin Console
2. Go to **Reports → System Log**
3. Filter by:
   - **Actor:** Terraform API tokens
   - **Time range:** Last 30 days
4. Look for:
   - Unexpected changes
   - Failed authentication
   - Unusual activity patterns
5. Investigate anomalies

### 6. IAM Permission Audit (if using AWS)

```bash
# Review IAM role permissions
aws iam get-role-policy \
  --role-name GitHubActions-OktaTerraform \
  --policy-name terraform-state-access

# Verify least privilege:
# - S3: GetObject, PutObject on specific bucket only
# - DynamoDB: GetItem, PutItem on specific table only
# - No admin or wildcard permissions
```

---

## 🚦 Environment Protection Rules

### Production Environment

**Required settings:**

1. **Deployment protection rules:**
   - ✅ Required reviewers: 2+
   - ✅ Wait timer: 5-10 minutes
   - ✅ Deployment branches: main only

2. **Branch protection (main):**
   - ✅ Require PR before merging
   - ✅ Require approvals: 1+
   - ✅ Require status checks to pass
   - ✅ Require branches be up to date
   - ✅ Include administrators

3. **Secrets access:**
   - ✅ Environment-specific secrets only
   - ✅ No repository secrets with Okta credentials
   - ✅ AWS role has minimal permissions

### Staging Environment

**Recommended settings:**

1. **Deployment protection rules:**
   - ✅ Required reviewers: 1
   - ⚠️ Wait timer: optional (2-5 minutes)
   - ✅ Deployment branches: main, staging

2. **Branch protection:**
   - ✅ Require PR before merging
   - ✅ Require status checks to pass
   - ⚠️ Approvals: optional

### Development Environment

**Minimal settings:**

1. **Deployment protection rules:**
   - ⚠️ Required reviewers: optional
   - ❌ Wait timer: none
   - ✅ Deployment branches: any

2. **Branch protection:**
   - ✅ Require status checks to pass
   - ⚠️ All other rules optional

---

## 🔐 Secrets in Terraform

### What NOT to Store

**Never put these in Terraform code:**
- ❌ API tokens
- ❌ Passwords
- ❌ Private keys
- ❌ OAuth client secrets
- ❌ Any credentials

### How to Handle Secrets

**Use environment variables:**

```hcl
# BAD - hardcoded secret
resource "okta_app_oauth" "bad" {
  client_secret = "hardcoded-secret-123"  # ❌ DON'T!
}

# GOOD - from environment variable
variable "client_secret" {
  sensitive = true
}

resource "okta_app_oauth" "good" {
  client_secret = var.client_secret  # ✅ Good!
}
```

**Pass via workflow:**
```yaml
- name: Terraform Apply
  env:
    TF_VAR_client_secret: ${{ secrets.CLIENT_SECRET }}
  run: terraform apply
```

### Marking Variables as Sensitive

```hcl
variable "okta_api_token" {
  type      = string
  sensitive = true  # ← Masks value in terraform output
}
```

---

## 📋 Security Incident Response

### If Token is Exposed

**Immediate actions (within 5 minutes):**

1. ✅ Revoke token in Okta Admin Console
2. ✅ Generate new token
3. ✅ Update GitHub Environment secret
4. ✅ Notify team

**Investigation (within 1 hour):**

5. ✅ Review Okta System Log for unauthorized activity
6. ✅ Check GitHub Actions workflow runs
7. ✅ Review recent Terraform state changes
8. ✅ Identify blast radius (what could have been accessed)

**Recovery (within 24 hours):**

9. ✅ Document incident
10. ✅ Update procedures to prevent recurrence
11. ✅ Review all recent changes for malicious activity
12. ✅ Consider rotating other credentials

### If State File is Exposed

**Immediate actions:**

1. ✅ Assess what data was in state file
2. ✅ Determine if any secrets were stored (they shouldn't be!)
3. ✅ Rotate any credentials that might be inferred
4. ✅ Review access logs (S3 CloudTrail, GitHub Actions)

**Mitigation:**

5. ✅ Consider resource IDs as potentially leaked
6. ✅ Review recent Okta activity for unusual patterns
7. ✅ Document incident
8. ✅ Improve state file security

### If Wrong Org Modified

**Immediate actions:**

1. ✅ Identify what was changed (Okta System Log)
2. ✅ Document all affected resources
3. ✅ Stop any running workflows

**Recovery:**

4. ✅ Revert changes in wrong org:
   - Delete mistakenly created resources
   - Restore previous configurations
5. ✅ Apply correct changes to correct org
6. ✅ Verify environment secret configuration
7. ✅ Add validation to prevent recurrence

---

## 📚 Security Resources

### Okta Security

- [Okta API Token Best Practices](https://developer.okta.com/docs/guides/create-an-api-token/)
- [Okta Security](https://help.okta.com/en/prod/Content/Topics/Security/Security.htm)
- [Okta System Log](https://help.okta.com/en/prod/Content/Topics/Reports/Reports_SysLog.htm)

### GitHub Security

- [GitHub Secrets Best Practices](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [GitHub OIDC with AWS](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [GitHub Environment Protection Rules](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment#environment-protection-rules)

### Terraform Security

- [Terraform State Security](https://www.terraform.io/docs/language/state/sensitive-data.html)
- [Terraform Sensitive Variables](https://www.terraform.io/docs/language/values/variables.html#suppressing-values-in-cli-output)
- [Terraform S3 Backend](https://www.terraform.io/docs/language/settings/backends/s3.html)

### General Security

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)
- [12 Factor App](https://12factor.net/) (Config section)

---

## 📝 Security Checklist for New Environments

When setting up a new environment:

- [ ] Create GitHub Environment (not repository secrets)
- [ ] Add required secrets (OKTA_API_TOKEN, OKTA_ORG_NAME, OKTA_BASE_URL)
- [ ] Configure environment protection rules
- [ ] Set up branch protection for main branch
- [ ] Create Okta API token with least privilege
- [ ] Document token creation date
- [ ] Set up remote backend (S3 or Terraform Cloud)
- [ ] Verify .gitignore includes state files
- [ ] Test with dry-run first
- [ ] Document environment in repository

---

## 🆘 Questions?

**Security concern or incident?**
[Create a private security advisory](https://github.com/joevanhorn/okta-terraform-demo-template/security/advisories/new)

**General security questions?**
[GitHub Discussions - Security category](https://github.com/joevanhorn/okta-terraform-demo-template/discussions/categories/security)

**Review security documentation:**
- [05-TROUBLESHOOTING.md](./docs/05-TROUBLESHOOTING.md)
- [AWS_BACKEND_SETUP.md](./docs/AWS_BACKEND_SETUP.md)
- [ROLLBACK_GUIDE.md](./docs/ROLLBACK_GUIDE.md)
