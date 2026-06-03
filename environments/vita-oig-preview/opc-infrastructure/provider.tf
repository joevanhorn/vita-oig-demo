# ==============================================================================
# OPC INFRASTRUCTURE - PROVIDER CONFIGURATION (VITA OIG PREVIEW)
# ==============================================================================
# Deploys the Okta On-Prem Connector (OPC) agent EC2 host(s) that bridge Okta
# to the HR System PostgreSQL database. State is isolated from both the Okta
# state and the generic-db state.
# ==============================================================================

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }

  backend "s3" {
    bucket         = "okta-terraform-demo"
    key            = "Okta-GitOps/vita-oig-preview/opc-infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "okta-terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = "vita-oig-preview"
      ManagedBy   = "terraform"
      Project     = "opc-infrastructure"
      Purpose     = "HR System Demo"
    }
  }
}
