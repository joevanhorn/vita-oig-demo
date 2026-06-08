module "servicenow_okta_bridge" {
  source = "../../../../modules/servicenow-okta-bridge"

  name                   = "${var.environment}-servicenow-okta-bridge"
  okta_org_url           = var.okta_org_url
  justification_field_id = var.justification_field_id
  sync_schedule          = var.sync_schedule
  sn_table               = "u_okta_groups" # global custom table (u_ prefix; x_ is for scoped apps)
}
