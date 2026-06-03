# ==============================================================================
# OPC INFRASTRUCTURE - VITA OIG PREVIEW
# ==============================================================================
# Deploys the OPC agent(s) for the Generic Database (HR System) connector.
# A single agent is sufficient for the demo; add more instances for HA.
# ==============================================================================

locals {
  name_prefix = "vita-oig-preview-use1"

  # ==============================================================================
  # OPC AGENT DEFINITIONS
  # ==============================================================================
  opc_agents = {
    "generic-db-1" = {
      connector_type  = "generic-db"
      instance_number = 1
      database_host   = try(data.terraform_remote_state.generic_db.outputs.db_endpoint, "")
      database_name   = try(data.terraform_remote_state.generic_db.outputs.db_name, "hr_system")
      jdbc_driver_url = var.postgres_jdbc_driver_url
      enabled         = true
    }
  }

  enabled_agents = {
    for k, v in local.opc_agents : k => v if v.enabled
  }

  common_tags = {
    Environment = "vita-oig-preview"
    CostCenter  = "demo-platform"
    Owner       = "joevanhorn"
  }
}

# ==============================================================================
# DATA SOURCES - REMOTE STATE (Generic DB infrastructure)
# ==============================================================================

data "terraform_remote_state" "generic_db" {
  backend = "s3"

  config = {
    bucket = "okta-terraform-demo"
    key    = "Okta-GitOps/vita-oig-preview/generic-db/terraform.tfstate"
    region = "us-east-1"
  }
}

# ==============================================================================
# SHARED SECURITY GROUP
# ==============================================================================

resource "aws_security_group" "opc_shared" {
  name        = "${local.name_prefix}-opc-shared-sg"
  description = "Shared security group for OPC agents (HR System / Generic DB)"
  vpc_id      = data.terraform_remote_state.generic_db.outputs.vpc_id

  # HTTPS to Okta (required for all agents)
  egress {
    description = "HTTPS to Okta"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # PostgreSQL (Generic DB Connector) - to the HR System DB VPC
  egress {
    description = "PostgreSQL - HR System DB"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.generic_db_vpc_cidr]
  }

  # All outbound for package updates / driver downloads
  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Internal OPC communication (for distributed deployments)
  ingress {
    description = "OPC internal"
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    self        = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-opc-shared-sg"
  })
}

# ==============================================================================
# OPC AGENT MODULES
# ==============================================================================

# Allow each agent to read the HR System DB credentials from Secrets Manager
# (so the agent can self-fetch creds — no credentials ever pass through commands).
resource "aws_iam_role_policy" "agent_read_db_secret" {
  for_each = local.enabled_agents

  name = "read-hr-db-secret"
  role = element(split("/", module.opc_agents[each.key].iam_role_arn), 1)

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = data.terraform_remote_state.generic_db.outputs.credentials_secret_arn
    }]
  })
}

module "opc_agents" {
  source   = "../../../modules/opc-agent"
  for_each = local.enabled_agents

  environment     = "vita-oig-preview"
  region_short    = "use1"
  connector_type  = each.value.connector_type
  instance_number = each.value.instance_number

  vpc_id             = data.terraform_remote_state.generic_db.outputs.vpc_id
  subnet_id          = data.terraform_remote_state.generic_db.outputs.public_subnet_ids[0]
  security_group_ids = [aws_security_group.opc_shared.id]

  database_host   = each.value.database_host
  database_name   = each.value.database_name
  jdbc_driver_url = each.value.jdbc_driver_url
  okta_org_url    = var.okta_org_url
  instance_type   = var.instance_type

  tags = local.common_tags
}
