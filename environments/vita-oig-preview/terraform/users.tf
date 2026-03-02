# =============================================================================
# VITA OIG Preview - Demo Users
# =============================================================================
# Creates demo users from CSV. Each user's login domain (@{abbrev}.gov)
# triggers the group rules in agency_groups.tf for automatic agency group
# assignment. No manual group membership needed.
#
# Each user is directly assigned to their agency's realm via realm_id,
# bypassing the 30 realm assignment rule limit per identity source.
# The realm is derived from the email domain: @boa.gov -> BOA realm.
#
# To add users: edit vita_users.csv and re-apply.
# =============================================================================

locals {
  csv_users = csvdecode(file("${path.module}/vita_users.csv"))
  users_map = { for user in local.csv_users : user.key => user }

  # Build a lookup from lowercase agency abbreviation to realm ID
  # e.g. "boa" -> okta_realm.virginia_agencies["BOA"].id
  agency_realm_ids = {
    for abbrev, realm in okta_realm.virginia_agencies :
    lower(abbrev) => realm.id
  }
}

resource "okta_user" "demo_users" {
  for_each = local.users_map

  first_name = each.value.first_name
  last_name  = each.value.last_name
  login      = each.value.login
  email      = each.value.login
  department = each.value.department
  title      = each.value.title
  password   = "Welcome123!"

  # Assign user to their agency's realm based on email domain
  # e.g. karen.mitchell@boa.gov -> extract "boa" -> lookup BOA realm ID
  realm_id = local.agency_realm_ids[split("@", each.value.login)[1] == "" ? "vita" : replace(split("@", each.value.login)[1], ".gov", "")]

  lifecycle {
    ignore_changes = [password, recovery_answer, recovery_question]
  }
}

# =============================================================================
# Outputs
# =============================================================================

output "demo_user_count" {
  description = "Total number of demo users created"
  value       = length(okta_user.demo_users)
}

output "demo_users_by_agency" {
  description = "Count of demo users per agency domain"
  value = {
    for abbrev, _ in local.virginia_agencies :
    abbrev => length([
      for user in local.csv_users : user.key
      if can(regex("@${lower(abbrev)}\\.gov$", user.login))
    ])
  }
}
