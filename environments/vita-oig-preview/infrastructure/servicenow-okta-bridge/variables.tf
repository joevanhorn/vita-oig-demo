variable "aws_region" {
  description = "Region for the bridge Lambda + API Gateway"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (naming/tags)"
  type        = string
  default     = "vita-oig-preview"
}

variable "okta_org_url" {
  description = "Okta org URL (no trailing slash)"
  type        = string
  default     = "https://demo-vita-oig.oktapreview.com"
}

variable "justification_field_id" {
  description = "Optional OIG request-field id for Flow 1 justification mapping"
  type        = string
  default     = ""
}

variable "sync_schedule" {
  description = "EventBridge schedule for the Flow 3 group sync"
  type        = string
  default     = "rate(1 day)"
}
