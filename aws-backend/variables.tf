# Variables for AWS Backend Infrastructure

variable "aws_region" {
  description = "AWS region for backend resources"
  type        = string
  default     = "us-east-1"
}

variable "state_bucket_name" {
  description = "Name of the S3 bucket for Terraform state"
  type        = string
  default     = "okta-terraform-demo"
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table for state locking"
  type        = string
  default     = "okta-terraform-state-lock"
}

variable "github_repository" {
  description = "GitHub repository in format 'owner/repo'"
  type        = string
  default     = "joevanhorn/okta-terraform-complete-demo"
}

variable "github_actions_role_name" {
  description = "Name of the IAM role for GitHub Actions"
  type        = string
  default     = "GitHubActions-OktaTerraform"
}
