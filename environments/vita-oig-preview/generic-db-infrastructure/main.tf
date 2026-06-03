# ==============================================================================
# GENERIC DATABASE INFRASTRUCTURE - VITA OIG PREVIEW ("HR System")
# ==============================================================================
# Deploys a PostgreSQL RDS instance for use with the Okta Generic Database
# Connector. Backs the demo "HR System" application: user provisioning,
# deprovisioning, and entitlement management.
#
# State is intentionally isolated from the Okta (vita-oig-preview/terraform)
# state so AWS changes never reconcile against hand-built Okta objects.
# ==============================================================================

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.0"
    }
  }

  backend "s3" {
    bucket         = "okta-terraform-demo"
    key            = "Okta-GitOps/vita-oig-preview/generic-db/terraform.tfstate"
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
      Project     = "generic-db-connector"
      Purpose     = "HR System Demo"
      ManagedBy   = "terraform"
    }
  }
}

# ==============================================================================
# DATA SOURCES
# ==============================================================================

data "aws_availability_zones" "available" {
  state = "available"
}

# ==============================================================================
# LOCAL VALUES
# ==============================================================================

locals {
  name_prefix = "vita-oig-preview-use1"

  common_tags = {
    Environment = "vita-oig-preview"
    Project     = "generic-db-connector"
    ManagedBy   = "terraform"
  }
}

# ==============================================================================
# DEDICATED VPC
# ==============================================================================

resource "aws_vpc" "generic_db" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-generic-db-vpc"
  })
}

resource "aws_internet_gateway" "generic_db" {
  vpc_id = aws_vpc.generic_db.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-generic-db-igw"
  })
}

resource "aws_subnet" "generic_db_a" {
  vpc_id                  = aws_vpc.generic_db.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, 1)
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-generic-db-subnet-a"
  })
}

resource "aws_subnet" "generic_db_b" {
  vpc_id                  = aws_vpc.generic_db.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, 2)
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-generic-db-subnet-b"
  })
}

resource "aws_route_table" "generic_db" {
  vpc_id = aws_vpc.generic_db.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.generic_db.id
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-generic-db-rt"
  })
}

resource "aws_route_table_association" "generic_db_a" {
  subnet_id      = aws_subnet.generic_db_a.id
  route_table_id = aws_route_table.generic_db.id
}

resource "aws_route_table_association" "generic_db_b" {
  subnet_id      = aws_subnet.generic_db_b.id
  route_table_id = aws_route_table.generic_db.id
}

# ==============================================================================
# SECURITY GROUP
# ==============================================================================

resource "aws_security_group" "postgres" {
  name        = "${local.name_prefix}-generic-db-postgres-sg"
  description = "Security group for PostgreSQL RDS (Generic DB Connector)"
  vpc_id      = aws_vpc.generic_db.id

  # PostgreSQL from OPC agent and allowed CIDRs
  ingress {
    description = "PostgreSQL"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.db_allowed_cidrs
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-generic-db-postgres-sg"
  })
}

# ==============================================================================
# DB SUBNET GROUP
# ==============================================================================

resource "aws_db_subnet_group" "postgres" {
  name        = "${local.name_prefix}-generic-db-subnet-group"
  description = "Subnet group for PostgreSQL RDS"
  subnet_ids  = [aws_subnet.generic_db_a.id, aws_subnet.generic_db_b.id]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-generic-db-subnet-group"
  })
}

# ==============================================================================
# RANDOM PASSWORD
# ==============================================================================

resource "random_password" "postgres_admin" {
  length           = 20
  special          = true
  override_special = "!#$%^&*"
  min_lower        = 2
  min_upper        = 2
  min_numeric      = 2
  min_special      = 1
}

# ==============================================================================
# SECRETS MANAGER
# ==============================================================================

resource "aws_secretsmanager_secret" "postgres_credentials" {
  name        = "${local.name_prefix}-generic-db-credentials"
  description = "PostgreSQL credentials for Generic Database Connector (HR System)"

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "postgres_credentials" {
  secret_id = aws_secretsmanager_secret.postgres_credentials.id
  secret_string = jsonencode({
    host     = aws_db_instance.postgres.address
    port     = aws_db_instance.postgres.port
    database = var.db_name
    username = var.db_username
    password = random_password.postgres_admin.result
    jdbc_url = "jdbc:postgresql://${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${var.db_name}"
  })
}

# ==============================================================================
# RDS POSTGRESQL INSTANCE
# ==============================================================================

resource "aws_db_instance" "postgres" {
  identifier = "${local.name_prefix}-generic-db"

  # Engine
  engine         = "postgres"
  engine_version = var.postgres_version
  instance_class = var.instance_class

  # Storage
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true

  # Database
  db_name  = var.db_name
  username = var.db_username
  password = random_password.postgres_admin.result

  # Network
  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = [aws_security_group.postgres.id]
  publicly_accessible    = var.publicly_accessible
  port                   = 5432

  # Backup & Maintenance
  backup_retention_period = var.backup_retention_days
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  # Options
  multi_az            = false # Single AZ for demo
  skip_final_snapshot = true  # Demo - no final snapshot
  deletion_protection = false # Demo - allow deletion

  # Performance Insights (free tier)
  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  # Parameter group for logging
  parameter_group_name = aws_db_parameter_group.postgres.name

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-generic-db"
  })
}

resource "aws_db_parameter_group" "postgres" {
  name   = "${local.name_prefix}-generic-db-params"
  family = "postgres${split(".", var.postgres_version)[0]}"

  # Enable query logging for debugging
  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "0"
  }

  tags = local.common_tags
}

# ==============================================================================
# SSM PARAMETERS (for easy reference / OPC discovery)
# ==============================================================================

resource "aws_ssm_parameter" "db_endpoint" {
  name        = "/vita-oig-preview/generic-db/endpoint"
  description = "PostgreSQL endpoint for Generic DB Connector"
  type        = "String"
  value       = aws_db_instance.postgres.address

  tags = local.common_tags
}

resource "aws_ssm_parameter" "db_jdbc_url" {
  name        = "/vita-oig-preview/generic-db/jdbc-url"
  description = "JDBC URL for Generic DB Connector"
  type        = "String"
  value       = "jdbc:postgresql://${aws_db_instance.postgres.address}:5432/${var.db_name}"

  tags = local.common_tags
}

# ==============================================================================
# VARIABLES
# ==============================================================================

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the dedicated Generic DB VPC"
  type        = string
  default     = "10.6.0.0/16"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "hr_system"
}

variable "db_username" {
  description = "Database admin username"
  type        = string
  default     = "oktaadmin"
}

variable "postgres_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.10"
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro" # Free tier eligible
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Max storage for autoscaling in GB"
  type        = number
  default     = 100
}

variable "backup_retention_days" {
  description = "Backup retention in days"
  type        = number
  default     = 7
}

variable "publicly_accessible" {
  description = "Make RDS publicly accessible (for demo/OPC access)"
  type        = bool
  default     = true # Demo environment
}

variable "db_allowed_cidrs" {
  description = "CIDR blocks allowed to access PostgreSQL"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Open for demo - restrict in production
}

# ==============================================================================
# OUTPUTS
# ==============================================================================

output "db_endpoint" {
  description = "PostgreSQL endpoint"
  value       = aws_db_instance.postgres.address
}

output "db_port" {
  description = "PostgreSQL port"
  value       = aws_db_instance.postgres.port
}

output "db_name" {
  description = "Database name"
  value       = var.db_name
}

output "jdbc_url" {
  description = "JDBC URL for Okta Generic DB Connector"
  value       = "jdbc:postgresql://${aws_db_instance.postgres.address}:5432/${var.db_name}"
}

output "credentials_secret" {
  description = "Secrets Manager secret name for credentials"
  value       = aws_secretsmanager_secret.postgres_credentials.name
}

output "security_group_id" {
  description = "Security group ID for PostgreSQL"
  value       = aws_security_group.postgres.id
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.generic_db.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = [aws_subnet.generic_db_a.id, aws_subnet.generic_db_b.id]
}

output "connection_info" {
  description = "Connection information for Okta Generic DB Connector"
  value = {
    host        = aws_db_instance.postgres.address
    port        = aws_db_instance.postgres.port
    database    = var.db_name
    username    = var.db_username
    jdbc_url    = "jdbc:postgresql://${aws_db_instance.postgres.address}:5432/${var.db_name}"
    jdbc_driver = "org.postgresql.Driver"
    secret_name = aws_secretsmanager_secret.postgres_credentials.name
  }
}
