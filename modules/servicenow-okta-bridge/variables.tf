variable "name" {
  description = "Name prefix for the Lambda, API, role, log group, secret, schedule"
  type        = string
  default     = "servicenow-okta-bridge"
}

variable "okta_org_url" {
  description = "Okta org URL (no trailing slash), e.g. https://demo-vita-oig.oktapreview.com"
  type        = string
}

variable "bridge_secret_name" {
  description = "Secrets Manager secret name holding {okta_token, sn_base_url, sn_user, sn_pass, inbound_secret}. Defaults to <name>-creds."
  type        = string
  default     = ""
}

variable "sn_table" {
  description = "ServiceNow custom table for the group sync (Flow 3)"
  type        = string
  default     = "x_okta_groups"
}

variable "group_sync_filter" {
  description = "Okta /api/v1/groups filter for which groups to sync"
  type        = string
  default     = "type eq \"OKTA_GROUP\""
}

variable "justification_field_id" {
  description = "Optional OIG request-field id to map a SN justification into (Flow 1). Empty = rely on requester_field_values in the SN payload."
  type        = string
  default     = ""
}

variable "enable_schedule" {
  description = "Create the EventBridge schedule that runs the Flow 3 group sync"
  type        = bool
  default     = true
}

variable "sync_schedule" {
  description = "EventBridge schedule expression for the group sync"
  type        = string
  default     = "rate(1 day)"
}

variable "log_retention_days" {
  description = "CloudWatch log retention"
  type        = number
  default     = 30
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
