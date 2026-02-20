# =============================================================================
# VITA OIG Preview - Agency User Groups, Group Rules, and Delegated Admin
# =============================================================================
# Creates a user group for each Virginia agency and auto-assigns users based
# on their login email domain. Resource sets are extended to include these
# groups so realm admins can manage their agency's users and groups.
# =============================================================================

# =============================================================================
# Agency User Groups
# =============================================================================
# One group per agency for general user membership.
# Users are auto-assigned via group rules (below).
# =============================================================================

resource "okta_group" "agency_users" {
  for_each = local.virginia_agencies

  name        = "${each.key} - ${each.value}"
  description = "Users belonging to ${each.value} (${each.key})"
}

# =============================================================================
# Domain-Based Group Rules
# =============================================================================
# Auto-assign users to their agency group based on login email domain.
# Users with @{abbrev}.gov logins are assigned to the corresponding group.
#
# Unlike realm assignments, group rules have no per-profile-source limit.
# =============================================================================

resource "okta_group_rule" "agency_domain_assignment" {
  for_each = local.virginia_agencies

  name              = "${each.key} Domain Auto-Assignment"
  status            = "ACTIVE"
  group_assignments = [okta_group.agency_users[each.key].id]
  expression_type   = "urn:okta:expression:1.0"
  expression_value  = "String.stringContains(user.login, \"@${lower(each.key)}.gov\")"
}

# =============================================================================
# Resource Sets (Delegated Administration)
# =============================================================================
# Each resource set scopes Department Administrator permissions to a specific
# agency's realm, users, groups, and applications. Department admins can
# manage users, group membership, and app assignments within their scope.
# =============================================================================

resource "okta_resource_set" "realm_resources" {
  for_each = local.virginia_agencies

  label       = "${each.key} Department Resources"
  description = "Resource set for ${each.value} delegated administration"
  resources = [
    "https://${var.okta_org_name}.${var.okta_base_url}/api/v1/realms/${okta_realm.virginia_agencies[each.key].id}",
    "https://${var.okta_org_name}.${var.okta_base_url}/api/v1/realms/${okta_realm.virginia_agencies[each.key].id}/users",
    "https://${var.okta_org_name}.${var.okta_base_url}/api/v1/groups/${okta_group.agency_users[each.key].id}",
    "https://${var.okta_org_name}.${var.okta_base_url}/api/v1/groups/${okta_group.realm_admins[each.key].id}",
    "https://${var.okta_org_name}.${var.okta_base_url}/api/v1/apps"
  ]
}

# =============================================================================
# Outputs
# =============================================================================

output "agency_group_ids" {
  description = "Map of agency abbreviations to their user group IDs"
  value = {
    for abbrev, group in okta_group.agency_users : abbrev => group.id
  }
}

output "agency_group_rule_ids" {
  description = "Map of agency abbreviations to their group rule IDs"
  value = {
    for abbrev, rule in okta_group_rule.agency_domain_assignment : abbrev => rule.id
  }
}

output "realm_resource_set_ids" {
  description = "Map of agency abbreviations to their resource set IDs"
  value = {
    for abbrev, rs in okta_resource_set.realm_resources : abbrev => rs.id
  }
}
