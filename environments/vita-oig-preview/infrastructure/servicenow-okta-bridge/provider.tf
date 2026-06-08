terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "okta-terraform-demo"
    key            = "Okta-GitOps/vita-oig-preview/infrastructure/servicenow-okta-bridge/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "okta-terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "ServiceNow-Okta-Bridge"
      ManagedBy   = "Terraform"
    }
  }
}
