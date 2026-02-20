# =============================================================================
# VITA OIG Preview - Demo Users
# =============================================================================
# Creates demo users from CSV. Each user's login domain (@{abbrev}.gov)
# triggers the group rules in agency_groups.tf for automatic agency group
# assignment. No manual group membership needed.
#
# To add users: edit vita_users.csv and re-apply.
# =============================================================================

locals {
  csv_users = csvdecode(file("${path.module}/vita_users.csv"))
  users_map = { for user in local.csv_users : user.key => user }
}

resource "okta_user" "demo_users" {
  for_each = local.users_map

  first_name = each.value.first_name
  last_name  = each.value.last_name
  login      = each.value.login
  email      = each.value.login
  department = each.value.department
  title      = each.value.title

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
