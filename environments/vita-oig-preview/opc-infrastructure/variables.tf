# ==============================================================================
# OPC INFRASTRUCTURE VARIABLES
# ==============================================================================

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "okta_org_url" {
  description = "Okta organization URL (e.g., https://vita-oig.oktapreview.com). Passed from CI from OKTA_ORG_NAME/OKTA_BASE_URL secrets."
  type        = string
  default     = ""
}

variable "instance_type" {
  description = "EC2 instance type for OPC agents"
  type        = string
  default     = "t3.medium"
}

variable "postgres_jdbc_driver_url" {
  description = "Download URL for the PostgreSQL JDBC driver staged on the agent"
  type        = string
  default     = "https://jdbc.postgresql.org/download/postgresql-42.7.4.jar"
}

variable "generic_db_vpc_cidr" {
  description = "CIDR of the VPC hosting the HR System DB (used for the PostgreSQL egress rule). Defaults to the account default VPC CIDR."
  type        = string
  default     = "172.31.0.0/16"
}
