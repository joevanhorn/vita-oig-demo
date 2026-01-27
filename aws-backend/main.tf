# AWS Backend Infrastructure for Okta Terraform Demo
# This creates the S3 bucket and DynamoDB table for Terraform state management

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Okta-GitOps"
      ManagedBy   = "Terraform"
      Repository  = "okta-terraform-complete-demo"
      Environment = "Infrastructure"
    }
  }
}

# S3 Bucket for Terraform State
resource "aws_s3_bucket" "terraform_state" {
  bucket = var.state_bucket_name

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name        = "Terraform State Bucket"
    Description = "Stores Terraform state files for all Okta environments"
  }
}

# Enable versioning for state files
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable bucket logging (optional, but recommended)
resource "aws_s3_bucket" "terraform_state_logs" {
  bucket = "${var.state_bucket_name}-logs"

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name        = "Terraform State Logs"
    Description = "Access logs for Terraform state bucket"
  }
}

resource "aws_s3_bucket_logging" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  target_bucket = aws_s3_bucket.terraform_state_logs.id
  target_prefix = "state-access-logs/"
}

# DynamoDB Table for State Locking
resource "aws_dynamodb_table" "terraform_state_lock" {
  name         = var.dynamodb_table_name
  billing_mode = "PAY_PER_REQUEST" # On-demand pricing
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name        = "Terraform State Lock"
    Description = "State locking for all Okta environments"
  }
}

# IAM Policy for Terraform State Access
resource "aws_iam_policy" "terraform_state_access" {
  name        = "TerraformStateAccess"
  description = "Policy for accessing Terraform state in S3 and DynamoDB"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3StateAccess"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketVersioning"
        ]
        Resource = aws_s3_bucket.terraform_state.arn
      },
      {
        Sid    = "S3StateObjectAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.terraform_state.arn}/*"
      },
      {
        Sid    = "DynamoDBStateLock"
        Effect = "Allow"
        Action = [
          "dynamodb:DescribeTable",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem"
        ]
        Resource = aws_dynamodb_table.terraform_state_lock.arn
      }
    ]
  })

  tags = {
    Name = "Terraform State Access Policy"
  }
}

# GitHub Actions OIDC Provider
resource "aws_iam_openid_connect_provider" "github_actions" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
  ]

  tags = {
    Name        = "GitHub Actions OIDC Provider"
    Description = "OIDC provider for GitHub Actions authentication"
  }
}

# IAM Role for GitHub Actions
resource "aws_iam_role" "github_actions" {
  name               = var.github_actions_role_name
  description        = "Role assumed by GitHub Actions for Terraform deployments"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role.json

  tags = {
    Name        = "GitHub Actions Terraform Role"
    Description = "Allows GitHub Actions to manage Terraform state"
  }
}

# Assume role policy for GitHub Actions OIDC
data "aws_iam_policy_document" "github_actions_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github_actions.arn]
    }

    actions = ["sts:AssumeRoleWithWebIdentity"]

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repository}:*"]
    }
  }
}

# Attach Terraform state access policy to GitHub Actions role
resource "aws_iam_role_policy_attachment" "github_actions_terraform_state" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.terraform_state_access.arn
}

# Optional: Attach ReadOnlyAccess for debugging (remove in production)
# resource "aws_iam_role_policy_attachment" "github_actions_readonly" {
#   role       = aws_iam_role.github_actions.name
#   policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
# }
