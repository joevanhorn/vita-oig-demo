# ServiceNow <-> Okta bridge: Lambda + API Gateway HTTP API + EventBridge schedule.
# See app/handler.py. Reuses the okta-docusign-poc/oracle-scim-proxy IaC pattern.

locals {
  secret_name = coalesce(var.bridge_secret_name, "${var.name}-creds")
}

data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/app"
  output_path = "${path.module}/build/${var.name}.zip"
  excludes    = ["__pycache__", "*.pyc"]
}

resource "aws_iam_role" "lambda" {
  name = "${var.name}-role"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Secret: { okta_token, sn_base_url, sn_user, sn_pass, inbound_secret }.
# Created empty; populated out-of-band (deploy workflow) so secret material never lands in state.
resource "aws_secretsmanager_secret" "bridge" {
  name        = local.secret_name
  description = "ServiceNow<->Okta bridge: Okta token + ServiceNow creds + inbound shared secret"
  tags        = var.tags
  lifecycle {
    ignore_changes = [tags, tags_all] # demo acct SCP denies secretsmanager:UntagResource
  }
}

resource "aws_iam_role_policy" "read_secret" {
  name = "${var.name}-read-secret"
  role = aws_iam_role.lambda.id
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "secretsmanager:GetSecretValue", Resource = aws_secretsmanager_secret.bridge.arn }]
  })
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.name}"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

resource "aws_lambda_function" "bridge" {
  function_name    = var.name
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  timeout          = 300 # scheduled group-sync can iterate many groups (EventBridge path, not API GW)
  memory_size      = 256

  environment {
    variables = {
      OKTA_ORG_URL           = var.okta_org_url
      BRIDGE_SECRET_NAME     = aws_secretsmanager_secret.bridge.name
      SN_TABLE               = var.sn_table
      GROUP_SYNC_FILTER      = var.group_sync_filter
      JUSTIFICATION_FIELD_ID = var.justification_field_id
    }
  }
  depends_on = [aws_cloudwatch_log_group.lambda]
  tags       = var.tags
}

# ---- API Gateway HTTP API (ServiceNow -> bridge) ----
resource "aws_apigatewayv2_api" "bridge" {
  name          = var.name
  protocol_type = "HTTP"
  tags          = var.tags
}

resource "aws_apigatewayv2_integration" "bridge" {
  api_id                 = aws_apigatewayv2_api.bridge.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.bridge.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
  timeout_milliseconds   = 30000
}

resource "aws_apigatewayv2_route" "any" {
  api_id    = aws_apigatewayv2_api.bridge.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.bridge.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.bridge.id
  name        = "$default"
  auto_deploy = true
  tags        = var.tags
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bridge.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.bridge.execution_arn}/*/*"
}

# ---- EventBridge schedule (Flow 3: periodic group sync) ----
resource "aws_cloudwatch_event_rule" "sync" {
  count               = var.enable_schedule ? 1 : 0
  name                = "${var.name}-group-sync"
  description         = "Periodic Okta->ServiceNow group sync"
  schedule_expression = var.sync_schedule
  # No tags: the CI role lacks events:TagResource (PutRule without tags is allowed).
}

resource "aws_cloudwatch_event_target" "sync" {
  count     = var.enable_schedule ? 1 : 0
  rule      = aws_cloudwatch_event_rule.sync[0].name
  target_id = "bridge-sync"
  arn       = aws_lambda_function.bridge.arn
  input     = jsonencode({ scheduled = true })
}

resource "aws_lambda_permission" "events" {
  count         = var.enable_schedule ? 1 : 0
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bridge.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.sync[0].arn
}
