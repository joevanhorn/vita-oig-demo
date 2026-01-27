# Archived Investigation Scripts

⚠️ **DEPRECATED - FOR REFERENCE ONLY** ⚠️

These scripts are **no longer maintained or used** in normal operations. They are kept purely for historical reference and to document the investigation process that led to the current implementation.

**Do not use these scripts!** Use the production scripts in the parent `scripts/` directory instead.

---

## Purpose

This directory contains scripts that were used during the investigation and development of the label management features. They documented the process of discovering the correct API endpoints and patterns.

## Scripts

### test_apply_labels_endpoint.py
**Purpose:** Investigation script to find the correct endpoint for applying labels to resources

**Background:** During development, we encountered 405 Method Not Allowed errors when trying to apply labels. This script tested various endpoint patterns and HTTP methods to discover the correct API endpoint.

**Finding:** The correct endpoint is `POST /governance/api/v1/resource-labels/assign` with a payload containing `resourceOrns` and `labelValueIds` arrays (max 10 items each).

**Status:** Investigation complete. Functionality implemented in `apply_admin_labels.py`

### test_label_resources_endpoints.py
**Purpose:** Investigation script to test different endpoint patterns for listing resources with labels

**Background:** Initial attempts to query resources by label used incorrect endpoint patterns. This script tested various possibilities.

**Finding:** The correct endpoint is `GET /governance/api/v1/resource-labels` with a `filter` parameter using SCIM syntax: `labelValueId eq "{labelValueId}"`

**Status:** Investigation complete. Functionality implemented in `validate_labels_api.py` and `okta_api_manager.py`

## Investigation Findings

A complete write-up of the investigation was documented in `/tmp/investigation_findings.md` during development. Key findings:

1. **Label Structure:**
   - Each label has a `labelId` (e.g., `lbc11keklyNa6KhMi1d7`)
   - Each label has `values` array with `labelValueId` (e.g., `lbl11keklzHO41LJ11d7`)
   - The `name` field is just for display

2. **Querying Resources:**
   - Use `/resource-labels` endpoint
   - Filter by `labelValueId` not by `name`
   - Supports pagination with `limit` parameter

3. **Applying Labels:**
   - Use `/resource-labels/assign` endpoint
   - Batch in groups of 10 (API limit)
   - Use `labelValueIds` array, not `labelId`

## Related Files

- Production scripts: `scripts/apply_admin_labels.py`, `scripts/sync_label_mappings.py`
- Validation: `scripts/validate_labels_api.py`
- API management: `scripts/okta_api_manager.py`
- Documentation: `docs/LABELS_API_VALIDATION.md`
