# Outputs for AWS Backend Infrastructure

output "s3_bucket_name" {
  description = "Name of the S3 bucket for Terraform state"
  value       = aws_s3_bucket.terraform_state.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.terraform_state.arn
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for state locking"
  value       = aws_dynamodb_table.terraform_state_lock.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  value       = aws_dynamodb_table.terraform_state_lock.arn
}

output "github_actions_role_arn" {
  description = "ARN of the IAM role for GitHub Actions (use this in workflows)"
  value       = aws_iam_role.github_actions.arn
}

output "github_actions_role_name" {
  description = "Name of the IAM role for GitHub Actions"
  value       = aws_iam_role.github_actions.name
}

output "oidc_provider_arn" {
  description = "ARN of the GitHub Actions OIDC provider"
  value       = aws_iam_openid_connect_provider.github_actions.arn
}

output "backend_configuration" {
  description = "Backend configuration to use in Terraform"
  value = <<-EOT

  Add this to your terraform block:

  backend "s3" {
    bucket         = "${aws_s3_bucket.terraform_state.id}"
    key            = "Okta-GitOps/<environment>/terraform.tfstate"
    region         = "${var.aws_region}"
    encrypt        = true
    dynamodb_table = "${aws_dynamodb_table.terraform_state_lock.name}"
  }

  Replace <environment> with: lowerdecklabs, production, staging, etc.
  EOT
}

output "github_secret_instructions" {
  description = "Instructions for setting up GitHub secrets"
  value = <<-EOT

  Add this secret to your GitHub repository:

  Secret Name: AWS_ROLE_ARN
  Secret Value: ${aws_iam_role.github_actions.arn}

  Then update your GitHub Actions workflows to include:

  permissions:
    id-token: write
    contents: read

  - name: Configure AWS Credentials
    uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
      role-session-name: GitHubActions-Terraform
      aws-region: ${var.aws_region}
  EOT
}
