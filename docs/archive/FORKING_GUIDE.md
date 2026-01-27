# Forking Guide: Using This Repository

This guide helps you fork this repository and use it with your own Okta tenant, whether you want to:
1. Use the existing resources as-is (for learning/testing)
2. Import your own existing Okta infrastructure
3. Start fresh with new resources

---

## Prerequisites

Before you begin, ensure you have:

- [ ] **Okta Organization** (any tier - Preview, Production, or Developer)
- [ ] **Okta API Token** with appropriate permissions
- [ ] **Terraform** >= 1.9.0 installed
- [ ] **Git** installed
- [ ] **(Optional) Terraformer** >= 0.8.24 if importing existing resources

### Installing Terraform

```bash
# macOS
brew install terraform

# Windows (with Chocolatey)
choco install terraform

# Linux
# Download from https://www.terraform.io/downloads
```

### Installing Terraformer (Optional)

```bash
# macOS
brew install terraformer

# Linux/Windows
# Download from https://github.com/GoogleCloudPlatform/terraformer/releases
```

---

## Option 1: Use as Learning/Testing (Quickest)

**Use Case:** You want to test the configuration without importing your existing Okta resources.

### Step 1: Fork the Repository

1. Go to the GitHub repository
2. Click "Fork" in the top right
3. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/okta-terraform-complete-demo.git
   cd okta-terraform-complete-demo/environments/myorg/terraform
   ```

### Step 2: Configure Credentials

```bash
# Copy the example file
cp terraform.tfvars.example terraform.tfvars

# Edit with your Okta details
nano terraform.tfvars
```

Add your Okta credentials:
```hcl
okta_org_name  = "your-org-name"        # e.g., "dev-12345678"
okta_base_url  = "okta.com"             # or "oktapreview.com" or "okta-emea.com"
okta_api_token = "your-api-token-here"
```

### Step 3: Secure Your Credentials

**IMPORTANT:** Never commit secrets to git!

```bash
# Add to .gitignore (should already be there, but verify)
echo "terraform.tfvars" >> .gitignore
echo "*.tfstate*" >> .gitignore
echo ".terraform/" >> .gitignore
```

### Step 4: Initialize and Review

```bash
# Initialize Terraform
terraform init

# Review what will be created
terraform plan
```

**Expected Output:**
- **IF** the resources don't exist in your Okta: Plan will show ~21 resources to create
- **IF** some resources exist: Plan will show a mix of creates and imports needed

### Step 5: Apply (Optional)

⚠️ **Warning:** This will create real resources in your Okta tenant!

```bash
# Create the resources
terraform apply

# Type 'yes' when prompted
```

### Step 6: Clean Up (When Done)

```bash
# Remove all created resources
terraform destroy

# Type 'yes' when prompted
```

---

## Option 2: Import Your Existing Okta Resources

**Use Case:** You have an existing Okta tenant and want to manage it with Terraform.

### Step 1: Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/okta-terraform-complete-demo.git
cd okta-terraform-complete-demo
```

### Step 2: Set Up Terraformer Credentials

```bash
# Export your Okta credentials for Terraformer
export OKTA_ORG_NAME="your-org-name"
export OKTA_BASE_URL="oktapreview.com"  # or okta.com
export OKTA_API_TOKEN="your-api-token"
```

### Step 3: Run Terraformer Import

```bash
# Create a new directory for your import
mkdir my-okta-import
cd my-okta-import

# Import specific resource types
terraformer import okta \
  --resources=user,group,app_oauth,auth_server,policy \
  --organizations=$OKTA_ORG_NAME \
  --okta-base-url=$OKTA_BASE_URL \
  --okta-api-token=$OKTA_API_TOKEN
```

This creates:
```
my-okta-import/
├── users/
│   ├── user.tf
│   ├── provider.tf
│   └── terraform.tfstate
├── groups/
├── apps/
├── auth_servers/
└── policies/
```

### Step 4: Consolidate Resources

```bash
# Move resource files to root
mv users/*.tf .
mv groups/*.tf .
mv apps/*.tf .
mv auth_servers/*.tf .
mv policies/*.tf .

# Remove duplicate providers (keep only root provider.tf)
rm */provider.tf

# Fix template strings
sed -i 's/\${source\.login}/$${source.login}/g' *.tf
```

### Step 5: Create Import Script

Create a script to import all resources into root state. See [LESSONS_LEARNED.md](./LESSONS_LEARNED.md#3-terraform-state-organization) for details.

Example script:
```bash
#!/bin/bash
set -e

echo "Importing users..."
terraform import 'okta_user.tfer--user_00urfd91ncmFPEKoH1d7' 00urfd91ncmFPEKoH1d7
# ... repeat for all users

echo "Importing groups..."
terraform import 'okta_group.tfer--group_All-0020-Employees' 00grfdazwxD4pal2f1d7
# ... repeat for all groups

echo "Importing apps..."
terraform import 'okta_app_oauth.tfer--oarfddbqbmyn6avt1d7-oidc-client' 0oarfddbqbmYn6AvT1d7
# ... repeat for all apps

echo "All resources imported!"
```

### Step 6: Handle Okta System Apps

Remove Okta-managed system apps from your configuration:

```bash
# Identify Okta system apps (look for these labels):
# - "Okta Workflows"
# - "Okta Access Requests"
# - "Okta Identity Governance"
# - "Okta Access Certification Reviews"
# - "Okta Workflows OAuth"

# Remove from state
terraform state rm 'okta_app_oauth.tfer--oarf1km0tncsdlwh1d7-okta-iga-reviewer'
terraform state rm 'okta_app_oauth.tfer--oarf1kr5tks4wmlh1d7-okta-flow-sso'
# ... etc

# Remove from .tf files or move to .excluded file
```

### Step 7: Validate

```bash
# Check for errors
terraform validate

# Should show no changes (all resources imported)
terraform plan
```

**Expected Output:**
```
No changes. Your infrastructure matches the configuration.
```

### Step 8: Add New Resources

Now you can safely add new resources and apply changes! See [README.md](./README.md#common-tasks) for examples.

---

## Option 3: Start Fresh (Custom Configuration)

**Use Case:** You want to start with a clean slate using this repo as a template.

### Step 1: Fork and Clean

```bash
git clone https://github.com/YOUR_USERNAME/okta-terraform-complete-demo.git
cd okta-terraform-complete-demo

# Option 1: Use existing environment structure
cd environments/myorg/terraform
# Remove existing resource files (keep structure)
rm *.tf

# Option 2: Create your own environment
mkdir -p environments/mycompany/terraform
cd environments/mycompany/terraform
```

### Step 2: Copy Template Files

```bash
# If starting fresh, copy only the infrastructure files from myorg
cp ../../myorg/terraform/provider.tf .
cp ../../myorg/terraform/variables.tf .
cp ../../myorg/terraform/terraform.tfvars.example terraform.tfvars
```

### Step 3: Configure

Edit `terraform.tfvars` with your credentials.

### Step 4: Create Your Resources

Create resource files following the examples in the original repo:

**users.tf:**
```hcl
resource "okta_user" "john_doe" {
  email      = "john.doe@example.com"
  first_name = "John"
  last_name  = "Doe"
  login      = "john.doe@example.com"
  status     = "ACTIVE"
}
```

**groups.tf:**
```hcl
resource "okta_group" "engineering" {
  name        = "Engineering Team"
  description = "Engineering team members"
}
```

**apps.tf:**
```hcl
resource "okta_app_oauth" "my_app" {
  label                      = "My Application"
  type                       = "web"
  grant_types                = ["authorization_code", "refresh_token"]
  redirect_uris              = ["https://myapp.example.com/callback"]
  response_types             = ["code"]
  client_uri                 = "https://myapp.example.com"
  pkce_required              = true
  token_endpoint_auth_method = "client_secret_post"
  login_mode                 = "DISABLED"
  hide_ios                   = true
  hide_web                   = true
  user_name_template         = "$${source.login}"
  user_name_template_type    = "BUILT_IN"
}
```

### Step 5: Apply

```bash
terraform init
terraform plan
terraform apply
```

---

## Recommended Okta API Token Permissions

Create an API token with these minimum scopes:

### Read-Only (for imports/planning)
- `okta.users.read`
- `okta.groups.read`
- `okta.apps.read`
- `okta.authorizationServers.read`
- `okta.policies.read`

### Read-Write (for applying changes)
- `okta.users.manage`
- `okta.groups.manage`
- `okta.apps.manage`
- `okta.authorizationServers.manage`
- `okta.policies.manage`

### Creating an API Token

1. Log into your Okta Admin Console
2. Go to **Security** → **API** → **Tokens**
3. Click **Create Token**
4. Name it (e.g., "Terraform Management")
5. Copy the token **immediately** (you won't see it again!)
6. Store it securely (password manager, vault, etc.)

---

## Security Best Practices

### 1. Never Commit Secrets

```bash
# Verify .gitignore includes:
terraform.tfvars
*.tfstate
*.tfstate.backup
.terraform/
.terraform.lock.hcl
```

### 2. Use Environment Variables (Alternative to terraform.tfvars)

```bash
export TF_VAR_okta_org_name="your-org"
export TF_VAR_okta_base_url="okta.com"
export TF_VAR_okta_api_token="your-token"

terraform plan  # Will use environment variables
```

### 3. Use Remote State (Production)

For production usage, configure a remote backend:

```hcl
# In provider.tf
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "okta/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-lock"
  }
}
```

Or use Terraform Cloud:
```hcl
terraform {
  cloud {
    organization = "my-org"
    workspaces {
      name = "okta-production"
    }
  }
}
```

### 4. Enable State Locking

Prevents multiple people from applying changes simultaneously.

**AWS S3 + DynamoDB:**
```hcl
backend "s3" {
  bucket         = "my-state"
  key            = "okta/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "terraform-lock"  # Enables locking
}
```

### 5. Separate Environments

Create separate state files for different environments:

```
terraform/
├── development/
│   ├── main.tf
│   └── terraform.tfvars
├── staging/
│   ├── main.tf
│   └── terraform.tfvars
└── production/
    ├── main.tf
    └── terraform.tfvars
```

---

## Common Issues & Solutions

### Issue: "Provider configuration not present"

**Solution:**
```bash
terraform init
```

### Issue: "Reference to undeclared resource" with ${source.login}

**Solution:**
Escape with `$$`:
```hcl
user_name_template = "$${source.login}"
```

### Issue: "Missing required argument 'type'" on OAuth apps

**Solution:**
This happens with Okta system apps. Exclude them from management. See [LESSONS_LEARNED.md](./LESSONS_LEARNED.md#2-missing-required-type-attribute-on-okta-system-apps).

### Issue: State conflicts with multiple users

**Solution:**
1. Use remote state backend
2. Enable state locking
3. Coordinate with team before applying

### Issue: "Resource already exists" when applying

**Solution:**
Import the existing resource instead:
```bash
terraform import okta_user.john_doe 00u1234567890abcdef
```

---

## Testing Your Configuration

### 1. Syntax Validation

```bash
terraform validate
```

### 2. Formatting

```bash
terraform fmt -recursive
terraform fmt -check  # CI/CD
```

### 3. Plan Review

```bash
terraform plan -out=tfplan
# Review the plan carefully
terraform apply tfplan
```

### 4. Drift Detection

```bash
# Check if actual infrastructure matches config
terraform plan
```

Expected output if no drift:
```
No changes. Your infrastructure matches the configuration.
```

---

## Getting Help

### Documentation

- [README.md](./README.md) - Overview and quick start
- [LESSONS_LEARNED.md](./LESSONS_LEARNED.md) - Detailed issues and solutions
- [TERRAFORM_RESOURCES.md](./TERRAFORM_RESOURCES.md) - Complete resource guide (catalog + detailed attributes)
- [Okta Provider Docs](https://registry.terraform.io/providers/okta/okta/latest/docs)
- [Terraformer Docs](https://github.com/GoogleCloudPlatform/terraformer)

### Community

- Okta Developer Forums: https://devforum.okta.com/
- Terraform Okta Provider Issues: https://github.com/okta/terraform-provider-okta/issues
- Terraformer Issues: https://github.com/GoogleCloudPlatform/terraformer/issues

### Support

- Check existing GitHub issues in this repo
- Open a new issue with:
  - Your Terraform version (`terraform version`)
  - Your Okta provider version (check `.terraform.lock.hcl`)
  - Error messages (redact sensitive data!)
  - Steps to reproduce

---

## Next Steps

After successfully forking and setting up:

1. ✅ Review the [LESSONS_LEARNED.md](./LESSONS_LEARNED.md) document
2. ✅ Reference [TERRAFORM_RESOURCES.md](./TERRAFORM_RESOURCES.md) for detailed attribute explanations
3. ✅ Set up remote state backend for production
4. ✅ Configure CI/CD for automated validation
5. ✅ Set up monitoring/alerting for drift detection
6. ✅ Document your specific customizations
7. ✅ Train your team on the workflow

---

## Contributing Back

If you find issues or improvements:

1. Fork the original repo
2. Create a feature branch
3. Make your changes
4. Submit a pull request
5. Document your changes clearly

We welcome contributions! 🎉

---

## License

This repository is provided as-is for educational and demonstration purposes. Check the repository's LICENSE file for details.

---

## Acknowledgments

- Okta for the Terraform Provider
- HashiCorp for Terraform
- Google for Terraformer
- The open-source community

Happy Terraforming! 🚀
