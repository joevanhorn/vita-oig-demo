# Complete Terraformer Testing Workflow

Step-by-step guide for testing Terraformer import with example resources.

## 🎯 Overview

This workflow will:
1. Create test resources in your Okta org
2. Import them using Terraformer
3. Clean up and refactor the imported code
4. Verify everything works
5. Clean up test resources

**Total time:** ~20 minutes

---

## 📋 Prerequisites

### Required Tools
```bash
# Terraform
terraform version  # Should be >= 1.9.0

# Terraformer
terraformer version  # Should be >= 0.8.24

# jq (for JSON processing)
jq --version

# curl (usually pre-installed)
curl --version
```

### Environment Setup
```bash
# Set your Okta credentials
export OKTA_API_TOKEN="your-api-token-here"
export OKTA_ORG_NAME="dev-12345678"
export OKTA_BASE_URL="okta.com"  # or oktapreview.com
```

---

## 🚀 Step-by-Step Workflow

### Step 1: Create Test Resources (5 minutes)

```bash
# Make script executable
chmod +x build_test_org.sh

# Run the build script
./build_test_org.sh
```

**What gets created:**
- ✅ 3 users (john.doe@example.com, jane.smith@example.com, bob.johnson@example.com)
- ✅ 4 groups (Engineering Team, Sales Team, Security Team, All Employees)
- ✅ 2 OAuth apps (Internal CRM, Project Management)
- ✅ Group memberships and app assignments
- ✅ 1 network zone (Corporate Network)

**Expected output:**
```
============================================
✅ Test org build complete!
============================================

📊 Created Resources:
[... resource IDs listed ...]
```

### Step 2: Verify Resources in Okta Console (2 minutes)

Login to your Okta admin console and verify:

1. **Directory → People** - See 3 test users
2. **Directory → Groups** - See 4 test groups
3. **Applications** - See 2 test applications
4. **Security → Networks** - See Corporate Network zone

### Step 3: Create Terraform Provider Config (1 minute)

```bash
# Create provider configuration
cat > okta.tf <<EOF
terraform {
  required_providers {
    okta = {
      source  = "okta/okta"
      version = "~> 6.1.0"
    }
  }
}

provider "okta" {
  org_name  = "${OKTA_ORG_NAME}"
  base_url  = "${OKTA_BASE_URL}"
  api_token = "${OKTA_API_TOKEN}"
}
EOF

# Initialize Terraform
terraform init
```

### Step 4: Import with Terraformer (3 minutes)

```bash
# Import all test resources
terraformer import okta \
  --resources=okta_user,okta_group,okta_app_oauth,okta_network_zone

# Check what was generated
tree generated/
```

**Expected structure:**
```
generated/
└── okta/
    ├── okta_user/
    │   ├── provider.tf
    │   ├── user.tf
    │   ├── outputs.tf
    │   └── terraform.tfstate
    ├── okta_group/
    │   ├── provider.tf
    │   ├── group.tf
    │   └── terraform.tfstate
    ├── okta_app_oauth/
    │   ├── provider.tf
    │   ├── app_oauth.tf
    │   └── terraform.tfstate
    └── okta_network_zone/
        ├── provider.tf
        ├── zone.tf
        └── terraform.tfstate
```

### Step 5: Review Generated Code (3 minutes)

```bash
# Look at generated user resources
cat generated/okta/okta_user/user.tf

# Check the state file
cat generated/okta/okta_user/terraform.tfstate | jq '.resources[0]'

# Count imported resources
echo "Users: $(cat generated/okta/okta_user/terraform.tfstate | jq '.resources | length')"
echo "Groups: $(cat generated/okta/okta_group/terraform.tfstate | jq '.resources | length')"
echo "Apps: $(cat generated/okta/okta_app_oauth/terraform.tfstate | jq '.resources | length')"
```

**What to notice:**
- Resource names have `tfer--` prefix
- IDs match your Okta resource IDs
- All attributes are populated
- State file is complete

### Step 6: Clean Up Generated Code (2 minutes)

```bash
# Run the cleanup script
python3 scripts/cleanup_terraform.py \
  --input generated/okta \
  --output cleaned

# Review cleaned structure
tree cleaned/
```

**What the cleanup does:**
- Removes `tfer--` prefixes
- Removes null values
- Removes computed attributes
- Organizes by resource type
- Extracts variables

### Step 7: Test Cleaned Configuration (2 minutes)

```bash
cd cleaned

# Initialize
terraform init

# Validate
terraform validate

# Plan (should show no changes if state was preserved)
terraform plan
```

**Expected result:**
```
No changes. Your infrastructure matches the configuration.
```

### Step 8: Compare Examples with Generated (2 minutes)

```bash
# Compare generated state with example state
cd ..

# Generated user state
cat generated/okta/okta_user/terraform.tfstate | jq '.resources[0].instances[0].attributes' > generated_user.json

# Example user state (from artifacts)
cat example_state_users.json | jq '.resources[0].instances[0].attributes' > example_user.json

# Compare structure (they should match)
diff -u example_user.json generated_user.json || echo "Structures match!"
```

---

## ✅ Validation Checklist

After completing the workflow, verify:

- [ ] All test resources created successfully
- [ ] Terraformer import completed without errors
- [ ] Generated files have correct structure
- [ ] State files contain all resource data
- [ ] Cleanup script removed prefixes and null values
- [ ] Terraform plan shows no changes
- [ ] Generated state matches example structure

---

## 🧪 Advanced Testing Scenarios

### Scenario 1: Selective Import

Import only specific resources:

```bash
# Import only users from Engineering department
terraformer import okta \
  --resources=okta_user \
  --filter="okta_user=department=Engineering"

# Import specific groups by ID
terraformer import okta \
  --resources=okta_group \
  --filter="okta_group=00g1a2b3c4d5e6f7g8h9:00g2b3c4d5e6f7g8h9i0"
```

### Scenario 2: Import and Modify

1. Import resources
2. Modify the Terraform code
3. Apply changes back

```bash
# Import
terraformer import okta --resources=okta_group

# Edit generated code
cd generated/okta/okta_group
vim group.tf  # Change group description

# Plan changes
terraform init
terraform plan

# Apply (changes the actual Okta resource!)
terraform apply
```

### Scenario 3: Drift Detection

1. Import resources
2. Manually change something in Okta console
3. Run terraform plan to detect drift

```bash
# Import
terraformer import okta --resources=okta_user

# Manually change a user in Okta console
# (Change John Doe's title to "Lead Engineer")

# Detect drift
cd generated/okta/okta_user
terraform init
terraform plan
# Should show: user title changed from "Senior Software Engineer" to "Lead Engineer"
```

---

## 🧹 Cleanup (2 minutes)

When you're done testing:

```bash
# Clean up generated files
rm -rf generated/ cleaned/

# Clean up test resources from Okta
chmod +x cleanup_test_org.sh
./cleanup_test_org.sh
```

**The cleanup script will:**
- Delete all test applications
- Delete all test users (@example.com)
- Delete all test groups
- Delete test network zones

---

## 📊 Testing Results Template

Document your testing:

```markdown
# Terraformer Testing Results

**Date:** YYYY-MM-DD
**Tester:** [Your Name]
**Okta Org:** ${OKTA_ORG_NAME}

## Resources Created
- Users: 3
- Groups: 4
- Apps: 2
- Network Zones: 1

## Import Results
- Users imported: 3/3 ✅
- Groups imported: 4/4 ✅
- Apps imported: 2/2 ✅
- Network zones: 1/1 ✅

## Cleanup Results
- Prefixes removed: ✅
- Null values cleaned: ✅
- Variables extracted: ✅
- Files organized: ✅

## Validation
- Terraform validate: ✅ Passed
- Terraform plan: ✅ No changes
- State integrity: ✅ Valid

## Issues Found
[None / List any issues]

## Notes
[Any additional observations]
```

---

## 🐛 Troubleshooting

### Issue: "Resource not found"

**Problem:** Terraformer can't find resources

**Solution:**
```bash
# Verify resources exist
curl -s "https://${OKTA_ORG_NAME}.${OKTA_BASE_URL}/api/v1/users" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}" | jq '.[] | .profile.email'

# Check API token permissions
echo "Token: ${OKTA_API_TOKEN:0:10}..."
```

### Issue: "Rate limit exceeded"

**Problem:** Too many API calls

**Solution:**
```bash
# Import in smaller batches
terraformer import okta --resources=okta_user
sleep 30
terraformer import okta --resources=okta_group
sleep 30
terraformer import okta --resources=okta_app_oauth
```

### Issue: "Invalid credentials"

**Problem:** Environment variables not set

**Solution:**
```bash
# Verify environment
echo "Org: ${OKTA_ORG_NAME}"
echo "Base: ${OKTA_BASE_URL}"
echo "Token: ${OKTA_API_TOKEN:0:10}..."

# Re-export if needed
export OKTA_API_TOKEN="your-token"
export OKTA_ORG_NAME="your-org"
export OKTA_BASE_URL="okta.com"
```

### Issue: State file conflicts

**Problem:** Terraform detects changes after import

**Solution:**
```bash
# Refresh state
terraform refresh

# Check for attribute differences
terraform show

# May need to adjust imported config to match actual state
```

---

## 📚 Next Steps

After successfully testing Terraformer:

1. **Apply to Production Org**
   - Use the same process on your real Okta org
   - Import existing resources
   - Integrate with OIG configuration

2. **Set Up CI/CD**
   - Configure GitHub Actions
   - Enable weekly drift detection
   - Automate imports

3. **Add OIG Configuration**
   - Create access reviews
   - Configure approval workflows
   - Set up catalog entries

4. **Document Your Process**
   - Create runbooks
   - Train team members
   - Establish governance policies

---

## 🎉 Success Criteria

You've successfully tested Terraformer when:

✅ Test resources created in Okta  
✅ All resources imported by Terraformer  
✅ Generated code is valid Terraform  
✅ State files are complete and accurate  
✅ Cleanup script produces clean code  
✅ Terraform plan shows no unexpected changes  
✅ Test resources cleaned up from Okta  

**Congratulations!** You're ready to use Terraformer for real Okta imports! 🚀
