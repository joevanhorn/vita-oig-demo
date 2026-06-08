output "bridge_base_url" {
  description = "HTTPS base URL ServiceNow calls (routes: /servicenow/request, /servicenow/approved, /sync/groups, /healthz)"
  value       = aws_apigatewayv2_api.bridge.api_endpoint
}

output "secret_name" {
  description = "Populate with {okta_token, sn_base_url, sn_user, sn_pass, inbound_secret}"
  value       = aws_secretsmanager_secret.bridge.name
}

output "lambda_function_name" {
  value = aws_lambda_function.bridge.function_name
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.lambda.name
}
