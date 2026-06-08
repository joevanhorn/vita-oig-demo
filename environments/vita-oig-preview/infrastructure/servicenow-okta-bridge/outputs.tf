output "bridge_base_url" {
  description = "Base URL for ServiceNow to call the bridge"
  value       = module.servicenow_okta_bridge.bridge_base_url
}

output "secret_name" {
  description = "Populate with {okta_token, sn_base_url, sn_user, sn_pass, inbound_secret}"
  value       = module.servicenow_okta_bridge.secret_name
}

output "lambda_function_name" {
  value = module.servicenow_okta_bridge.lambda_function_name
}
