# Testing Documentation

This directory contains testing and validation documentation for the Okta Terraform Complete Demo project.

---

## 📋 Available Guides

### [MANUAL_VALIDATION_PLAN.md](./MANUAL_VALIDATION_PLAN.md)
Comprehensive manual validation plan covering all aspects of the Okta Terraform setup.

**Includes:**
- Pre-validation checklist (tools, access, secrets, **AWS CLI**)
- Environment validation
- Import workflow testing
- Resource management (CRUD operations)
- OIG governance validation
- **AWS Backend Infrastructure** validation
  - S3 bucket verification
  - DynamoDB state locking tests
  - GitHub Actions OIDC authentication
  - State versioning and recovery
- State management verification
- Documentation accuracy checks
- Security validation
- Cleanup procedures
- Sign-off template

**Estimated Time:** 2-3 hours for complete validation
**Required Access:** Okta Admin Console, GitHub Actions, Local Terminal, **AWS Console**

**New in v2.0:** AWS S3 backend validation section with comprehensive state management tests

### Demo Building

For building demos, please use the new simplified documentation:

- **[DEMO_GUIDE.md](../DEMO_GUIDE.md)** - Build demos with templates, AI, or manually (30-60 min)
- **[LOCAL-USAGE.md](../LOCAL-USAGE.md)** - Learn Terraform basics (15 min)
- **[TERRAFORM-BASICS.md](../TERRAFORM-BASICS.md)** - Resource reference and examples

> **Note:** The previous DETAILED_DEMO_BUILD_GUIDE.md has been archived to [docs/archive/](../docs/archive/).

---

## 🎯 When to Use

### Manual Validation Plan

Use the manual validation plan when:
- Setting up the repository for the first time
- **After deploying AWS backend infrastructure**
- After major changes to workflows or scripts
- Before deploying to production
- Troubleshooting issues
- Training new team members
- Periodic quality assurance (quarterly/biannually)
- **Validating state locking and S3 backend**

### Demo Build Guides

**Use the new simplified documentation:**

**[DEMO_GUIDE.md](../DEMO_GUIDE.md)** - The main demo guide with three approaches:
- Quick Template (5 min) - Use pre-built demo
- AI-Assisted (15 min) - Gemini Gem generates custom demos
- Manual Build (30 min) - Step-by-step for learning

**[LOCAL-USAGE.md](../LOCAL-USAGE.md)** - Start here if new to Terraform:
- Learn basics without GitHub/GitOps complexity
- 15 minutes to first success

**[TERRAFORM-BASICS.md](../TERRAFORM-BASICS.md)** - Reference:
- Resource examples (users, groups, apps, OIG)
- Common patterns and commands

---

## 🔄 Test Execution Tracking

Create a copy of the validation plan for each test run:

```bash
# Create dated copy for test run
cp MANUAL_VALIDATION_PLAN.md validation_run_$(date +%Y%m%d).md

# Fill out checklist items as you test
# Keep completed validation runs for audit trail
```

---

## 📊 Test Results Archive

Store completed validation runs in a subdirectory:

```
testing/
├── README.md
├── MANUAL_VALIDATION_PLAN.md (template)
└── results/
    ├── validation_run_20251107.md
    ├── validation_run_20251201.md
    └── ...
```

---

## 🤝 Contributing Test Plans

To add new test plans:

1. Create a new markdown file in this directory
2. Follow the format of existing plans
3. Include clear objectives and pass/fail criteria
4. Add to this README
5. Submit PR for review

---

## 📚 Related Documentation

- [Main README](../README.md) - Project overview
- [Environment README](../environments/README.md) - Environment structure
- [Resource Documentation](../docs/TERRAFORM_RESOURCES.md) - Complete resource guide
- [Workflow Documentation](../docs/PROJECT_STRUCTURE.md) - Repository structure

---

## ⚠️ Important Notes

- **Never commit sensitive data** to validation run files
- Redact API tokens, passwords, and user IDs from test results
- Use placeholders for sensitive information
- Store completed validation runs securely (not in public repo if contains sensitive data)

---

---

## 🆕 What's New in Testing Documentation

### Version 2.0 (2025-11-09) - AWS Backend Integration

**Added:**
- AWS CLI installation to prerequisites
- AWS backend infrastructure validation (Section 6.1)
- S3 state storage verification (Section 6.2)
- DynamoDB state locking tests (Section 6.3)
- GitHub Actions OIDC authentication validation (Section 6.5)
- State backup and recovery procedures (Section 6.6)
- AWS backend setup in Demo Build Guide (Section 7.5)

**Updated:**
- Pre-validation checklist includes AWS CLI
- Secrets validation includes `AWS_ROLE_ARN`
- State management section completely rewritten
- Demo build guide updated with AWS setup steps
- Estimated times updated for AWS setup

### Key Changes

**Before:** Local state files, manual state management
**After:** S3 backend with DynamoDB locking, automated state management

**Impact:**
- Enhanced team collaboration capabilities
- Production-ready state management
- GitHub Actions integration for CI/CD
- State versioning and recovery options

---

Last updated: 2025-11-09
