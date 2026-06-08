# servicenow-okta-bridge (Terraform module)

A Python AWS Lambda behind an API Gateway HTTP API that bridges ServiceNow and Okta for the
VITA OIG demo. Plus an IAM role, a Secrets Manager secret, and an EventBridge schedule for the
periodic group sync. See `app/handler.py`.

## Flows
| Route | Flow | What it does |
| --- | --- | --- |
| `POST /servicenow/request` | 1 | SN catalog request → create an Okta **OIG access request** (`governance/api/v2/requests`); Okta runs approval + provisioning |
| `POST /servicenow/approved` | 2 | SN already approved → **add the user to the Okta group**; optionally closes the RITM |
| `POST /sync/groups` (+ EventBridge schedule) | 3 | Pull Okta groups → upsert the SN custom table `x_okta_groups` for the catalog |
| `GET /healthz` | — | unauthenticated health check |

## Auth
- ServiceNow → bridge: header **`x-bridge-secret: <inbound_secret>`**.
- bridge → Okta: SSWS token. bridge → ServiceNow: basic auth.
- All in the Secrets Manager secret: `{ okta_token, sn_base_url, sn_user, sn_pass, inbound_secret }`
  (created empty by Terraform; populate out-of-band so secret material never lands in state).

## Usage
```hcl
module "servicenow_okta_bridge" {
  source       = "../../../../modules/servicenow-okta-bridge"
  name         = "vita-oig-preview-servicenow-okta-bridge"
  okta_org_url = "https://demo-vita-oig.oktapreview.com"
}
```
After apply, populate `secret_name`, then point ServiceNow business rules / scripted REST at
`bridge_base_url`. ServiceNow-side artifacts + setup live under
`environments/vita-oig-preview/config/servicenow/` and `scripts/setup_servicenow_integration.py`.

## Key variables / outputs
- Inputs: `okta_org_url` (required), `name`, `sn_table` (`x_okta_groups`), `group_sync_filter`
  (`type eq "OKTA_GROUP"`), `justification_field_id`, `enable_schedule`, `sync_schedule` (`rate(1 day)`).
- Outputs: `bridge_base_url`, `secret_name`, `lambda_function_name`, `log_group_name`.

Pure stdlib + boto3 (Lambda-provided) — no build step.
