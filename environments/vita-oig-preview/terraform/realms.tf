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

  name       = "${each.key} - ${each.value}"
  realm_type = "PARTNER"
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
