# =============================================================================
# VITA OIG Preview - Virginia Commonwealth Agency Realms
# =============================================================================
# This file defines Okta Realms for all Virginia state agencies.
# Each realm represents an isolated identity domain for the agency.
#
# Total Agencies: 60
# Naming Convention: "ABBREV - Full Agency Name"
# =============================================================================

locals {
  # Virginia Commonwealth Agencies
  # Key = abbreviation (used for resource naming)
  # Value = full agency name
  virginia_agencies = {
    "BOA"    = "Board of Accountancy"
    "CASC"   = "Commonwealth Attorneys Services Council"
    "CB"     = "State Compensation Board"
    "CSA"    = "Office of Children's Services"
    "DARS"   = "Department for Aging and Rehabilitative Services"
    "DBHDS"  = "Department of Behavioral Health and Developmental Services"
    "DBVI"   = "Dept. for the Blind and Vision Impaired"
    "DCJS"   = "Department of Criminal Justice Services"
    "DCR"    = "Department of Conservation and Recreation"
    "DEQ"    = "Department of Environmental Quality"
    "DFP"    = "Department of Fire Programs"
    "DFS"    = "Department of Forensic Science"
    "DGS"    = "Department of General Services"
    "DHCD"   = "Department of Housing and Community Development"
    "DHP"    = "Department of Health Professions"
    "DHR"    = "Department of Historic Resources"
    "DHRM"   = "Department of Human Resource Management"
    "DJJ"    = "Department of Juvenile Justice"
    "DMA"    = "Department of Military Affairs"
    "DMAS"   = "Department of Medical Assistance Services"
    "DMV"    = "Department of Motor Vehicles"
    "DOA"    = "Department of Accounts"
    "DOAV"   = "Department of Aviation"
    "DOC"    = "Department of Corrections"
    "DOE"    = "Department of Education"
    "DOF"    = "Department of Forestry"
    "DOLI"   = "Department of Labor and Industry"
    "DPB"    = "Department of Planning and Budget"
    "DPOR"   = "Department of Professional and Occupational Regulation"
    "DRPT"   = "Department of Rail and Public Transportation"
    "DSBSD"  = "Department of Small Business and Supplier Diversity"
    "DSS"    = "Department of Social Services"
    "DVS"    = "Department of Veterans Services"
    "DWR"    = "Department of Wildlife Resources"
    "ELECT"  = "State Board of Elections"
    "ENERGY" = "Virginia Energy"
    "GOV"    = "Office of the Governor (Includes Lt. Gov and Secretariats)"
    "LVA"    = "Library of Virginia"
    "MRC"    = "Marine Resources Commission"
    "MVDB"   = "Motor Vehicle Dealer Board"
    "ODGA"   = "Office of Data Governance and Analytics"
    "OSIG"   = "Office of the State Inspector General"
    "SCHEV"  = "State Council of Higher Education for Virginia"
    "TAX"    = "Department of Taxation"
    "TRS"    = "Department of the Treasury"
    "VASAP"  = "Virginia Alcohol Safety Action Program"
    "VBPD"   = "Virginia Board for People with Disabilities"
    "VCA"    = "Virginia Commission for the Arts"
    "VCCS"   = "Virginia Community College System"
    "VDACS"  = "Department of Agriculture and Consumer Services"
    "VDDHH"  = "Department for the Deaf and Hard of Hearing"
    "VDEM"   = "Department of Emergency Management"
    "VDH"    = "Virginia Department of Health"
    "VDOT"   = "Virginia Department of Transportation"
    "VEC"    = "Virginia Employment Commission"
    "VIPC"   = "Virginia Innovation Partnership Corporation"
    "VITA"   = "Virginia Information Technologies Agency"
    "VOF"    = "Virginia Outdoors Foundation"
    "VRC"    = "Virginia Racing Commission"
    "VSP"    = "Virginia Department of State Police"
  }
}

# =============================================================================
# Okta Realms for Virginia Agencies
# =============================================================================
# Each realm creates an isolated identity domain within the Okta organization.
# Users and groups can be assigned to realms for multi-tenant management.
#
# Documentation: https://registry.terraform.io/providers/okta/okta/latest/docs/resources/realm
# =============================================================================

resource "okta_realm" "virginia_agencies" {
  for_each = local.virginia_agencies

  name       = each.key
  realm_type = "PARTNER"
}

# =============================================================================
# Realm Admin Groups
# =============================================================================
# Each realm has a corresponding admin group for delegated administration.
# Members of these groups will be granted realm admin permissions.
# =============================================================================

resource "okta_group" "realm_admins" {
  for_each = local.virginia_agencies

  name        = "${each.key}-realm-admin"
  description = "Realm administrators for ${each.value}"
}

# =============================================================================
# Custom Admin Role
# =============================================================================
# A single custom admin role used across all realms for consistent permissions.
# This role grants user and group management capabilities.
# =============================================================================

resource "okta_admin_role_custom" "realm_admin" {
  label       = "Realm Administrator"
  description = "Custom admin role for realm user and group management"
  permissions = [
    "okta.users.read",
    "okta.users.manage",
    "okta.groups.read",
    "okta.groups.manage"
  ]
}

# =============================================================================
# Resource Sets
# =============================================================================
# Each realm has a resource set that scopes admin permissions to that realm.
# Currently includes the realm and its users. Can be extended to include
# apps and groups in scope.
# =============================================================================

resource "okta_resource_set" "realm_resources" {
  for_each = local.virginia_agencies

  label       = "${each.key} Realm Resources"
  description = "Resource set for ${each.value} realm administration"
  resources   = [
    "https://${var.okta_org_name}.${var.okta_base_url}/api/v1/realms/${okta_realm.virginia_agencies[each.key].id}",
    "https://${var.okta_org_name}.${var.okta_base_url}/api/v1/realms/${okta_realm.virginia_agencies[each.key].id}/users"
  ]
}

# =============================================================================
# Admin Role Assignments
# =============================================================================
# Binds the realm admin groups to the custom role with their resource sets.
# Members of each realm admin group will have the Realm Administrator role
# scoped to their specific realm's resources.
# =============================================================================

resource "okta_admin_role_custom_assignments" "realm_admin_assignments" {
  for_each = local.virginia_agencies

  resource_set_id = okta_resource_set.realm_resources[each.key].id
  custom_role_id  = okta_admin_role_custom.realm_admin.id
  members = [
    format("https://%s.%s/api/v1/groups/%s", var.okta_org_name, var.okta_base_url, okta_group.realm_admins[each.key].id)
  ]
}

# =============================================================================
# Realm Assignment Rules
# =============================================================================
# Domain-based realm assignments automatically assign users to realms based on
# their email domain. Users with @[abbrev].gov emails are assigned to the
# corresponding realm (e.g., @boa.gov -> BOA realm).
# =============================================================================

resource "okta_realm_assignment" "domain_based" {
  for_each = local.virginia_agencies

  name                 = "${each.key} Domain Assignment"
  priority             = 1
  status               = "ACTIVE"
  condition_expression = "user.profile.login.contains(\"@${lower(each.key)}.gov\")"
  realm_id             = okta_realm.virginia_agencies[each.key].id
}

# =============================================================================
# Outputs
# =============================================================================

output "realm_ids" {
  description = "Map of agency abbreviations to their Okta Realm IDs"
  value = {
    for abbrev, realm in okta_realm.virginia_agencies : abbrev => realm.id
  }
}

output "realm_count" {
  description = "Total number of realms created"
  value       = length(okta_realm.virginia_agencies)
}

output "realm_admin_group_ids" {
  description = "Map of agency abbreviations to their realm admin group IDs"
  value = {
    for abbrev, group in okta_group.realm_admins : abbrev => group.id
  }
}

output "realm_admin_role_id" {
  description = "ID of the custom Realm Administrator role"
  value       = okta_admin_role_custom.realm_admin.id
}

output "realm_resource_set_ids" {
  description = "Map of agency abbreviations to their resource set IDs"
  value = {
    for abbrev, rs in okta_resource_set.realm_resources : abbrev => rs.id
  }
}

output "realm_admin_assignment_ids" {
  description = "Map of agency abbreviations to their admin role assignment IDs"
  value = {
    for abbrev, assignment in okta_admin_role_custom_assignments.realm_admin_assignments : abbrev => assignment.id
  }
}

output "realm_assignment_ids" {
  description = "Map of agency abbreviations to their realm assignment rule IDs"
  value = {
    for abbrev, assignment in okta_realm_assignment.domain_based : abbrev => assignment.id
  }
}
