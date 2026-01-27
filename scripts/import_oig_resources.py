#!/usr/bin/env python3
"""
import_oig_resources.py

Automatically import existing OIG resources from Okta into Terraform.

This script:
1. Queries Okta API for existing OIG resources (entitlements, reviews, etc.)
2. Generates Terraform configuration files (.tf)
3. Generates terraform import commands

Usage:
    python3 scripts/import_oig_resources.py --output-dir imported_oig

Environment variables required:
    OKTA_ORG_NAME - Your Okta org name
    OKTA_API_TOKEN - API token with governance scopes
    OKTA_BASE_URL - Base URL (default: okta.com)
"""

import argparse
import json
import os
import sys
import requests
from typing import List, Dict, Optional
import re


class OIGImporter:
    """Import existing OIG resources from Okta"""

    def __init__(self, org_name: str, base_url: str, api_token: str):
        self.org_name = org_name
        self.base_url = f"https://{org_name}.{base_url}"
        self.headers = {
            "Authorization": f"SSWS {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make API request with error handling"""
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise

    def _sanitize_name(self, name: str) -> str:
        """Convert name to valid Terraform resource name"""
        # Remove special characters, convert to lowercase, replace spaces with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = f"resource_{sanitized}"
        return sanitized or "unnamed"

    def fetch_entitlements(self) -> List[Dict]:
        """Fetch all entitlement bundles from Okta"""
        print("Fetching entitlement bundles...")
        try:
            # Use the correct entitlement-bundles endpoint with full entitlements included
            url = f"{self.base_url}/governance/api/v1/entitlement-bundles"
            params = {
                "limit": 200,
                "include": "full_entitlements"  # Include entitlement details in response
            }
            response = self._make_request("GET", url, params=params)

            # Handle both dict and list responses
            data = response.json()
            if isinstance(data, list):
                bundles = data
            elif isinstance(data, dict):
                bundles = data.get("data", data.get("entitlements", []))
            else:
                bundles = []

            print(f"  Found {len(bundles)} entitlement bundles")
            return bundles
        except Exception as e:
            print(f"  ⚠️  Could not fetch entitlement bundles: {e}")
            return []

    def validate_bundle_readable(self, bundle_id: str) -> bool:
        """Test if a bundle can be individually retrieved (not all listed bundles are readable)"""
        try:
            # Correct endpoint: entitlement-bundles (not entitlements)
            url = f"{self.base_url}/governance/api/v1/entitlement-bundles/{bundle_id}"
            response = self._make_request("GET", url)
            return response.status_code == 200
        except Exception:
            return False

    def fetch_entitlements_for_resource(self, resource_id: str, resource_type: str = "APPLICATION") -> List[Dict]:
        """Fetch individual entitlements for a specific resource (app/group/etc)"""
        try:
            url = f"{self.base_url}/governance/api/v1/entitlements"
            # Build filter: parent.externalId eq "resourceId" AND parent.type eq "resourceType"
            filter_expr = f'parent.externalId eq "{resource_id}" AND parent.type eq "{resource_type}"'
            params = {
                "filter": filter_expr,
                "limit": 200
            }
            response = self._make_request("GET", url, params=params)
            entitlements = response.json().get("data", [])
            return entitlements
        except Exception as e:
            print(f"  ⚠️  Could not fetch entitlements for resource {resource_id}: {e}")
            return []

    def fetch_reviews(self) -> List[Dict]:
        """Fetch all access review campaigns"""
        print("Fetching access review campaigns...")
        try:
            url = f"{self.base_url}/governance/api/v1/reviews"
            params = {"limit": 200}
            response = self._make_request("GET", url, params=params)
            reviews = response.json().get("data", [])
            print(f"  Found {len(reviews)} review campaigns")
            return reviews
        except Exception as e:
            print(f"  ⚠️  Could not fetch reviews: {e}")
            return []

    def fetch_request_sequences(self, entitlement_bundles: List[Dict]) -> List[Dict]:
        """
        Fetch all approval workflows (request sequences).

        Note: API v2 requires request sequences to be fetched per-resource.
        We iterate through entitlement bundles and collect unique sequences.

        API: GET /governance/api/v2/resources/{resourceId}/request-sequences
        """
        print("Fetching approval workflows (request sequences)...")
        all_sequences = {}  # Use dict to deduplicate by ID

        if not entitlement_bundles:
            print("  ℹ️  No entitlement bundles to query for sequences")
            return []

        # Sample a few bundles to find sequences (most bundles share sequences)
        sample_size = min(5, len(entitlement_bundles))
        print(f"  Sampling {sample_size} of {len(entitlement_bundles)} bundles for sequences...")

        for bundle in entitlement_bundles[:sample_size]:
            bundle_id = bundle.get("id") or bundle.get("bundleId")
            if not bundle_id:
                continue

            try:
                # v2 API endpoint with resourceId
                url = f"{self.base_url}/governance/api/v2/resources/{bundle_id}/request-sequences"
                params = {"limit": 200}
                response = self._make_request("GET", url, params=params)
                sequences = response.json().get("data", [])

                # Add to dict to deduplicate
                for seq in sequences:
                    seq_id = seq.get("id")
                    if seq_id and seq_id not in all_sequences:
                        all_sequences[seq_id] = seq

            except Exception as e:
                # Expected for bundles without sequences - continue silently
                continue

        sequences_list = list(all_sequences.values())
        print(f"  Found {len(sequences_list)} unique approval workflows")
        return sequences_list

    def fetch_catalog_entries(self) -> List[Dict]:
        """
        Fetch all catalog entries.

        Note: This endpoint is not currently used for imports.
        Catalog entries are managed through request conditions in v2 API.
        Keeping for backwards compatibility but returning empty list.
        """
        print("Fetching catalog entries...")
        print("  ℹ️  Catalog entries import not currently supported")
        print("  ℹ️  Use request conditions API instead (v2)")
        return []

    def fetch_request_settings(self) -> Optional[Dict]:
        """
        Fetch organization-level request settings.

        API: GET /governance/api/v2/request-settings (org-level)
        """
        print("Fetching organization request settings...")
        try:
            # v2 API endpoint (org-level)
            url = f"{self.base_url}/governance/api/v2/request-settings"
            response = self._make_request("GET", url)
            settings = response.json()
            print(f"  ✅ Found organization request settings")
            return settings
        except Exception as e:
            print(f"  ⚠️  Could not fetch request settings: {e}")
            print(f"  ℹ️  This may be expected if request settings are not configured")
            return None

    def generate_entitlement_tf(self, bundles: List[Dict]) -> tuple[str, List[str]]:
        """Generate Terraform config and import commands for entitlement bundles"""
        if not bundles:
            return "", []

        tf_config = []
        import_commands = []

        tf_config.append("# =============================================================================")
        tf_config.append("# OKTA IDENTITY GOVERNANCE - ENTITLEMENT BUNDLES")
        tf_config.append("# =============================================================================")
        tf_config.append("# Entitlement bundles define collections of access rights that can be assigned")
        tf_config.append("# to users and groups. These bundles are managed via Terraform.")
        tf_config.append("#")
        tf_config.append("# IMPORTANT:")
        tf_config.append("# - Entitlement BUNDLES (definitions) are managed here in Terraform")
        tf_config.append("# - Entitlement ASSIGNMENTS (which users/groups have bundles) should be")
        tf_config.append("#   managed in Okta Admin UI or via direct API calls, NOT in Terraform")
        tf_config.append("#")
        tf_config.append("# Resource: okta_entitlement_bundle")
        tf_config.append("# Documentation: https://registry.terraform.io/providers/okta/okta/latest/docs/resources/entitlement_bundle")
        tf_config.append("# =============================================================================")
        tf_config.append("")

        for bundle in bundles:
            bundle_id = bundle.get("id") or bundle.get("bundleId")
            name = bundle.get("name", "unnamed")
            description = bundle.get("description", "")
            orn = bundle.get("orn", "")
            bundle_type = bundle.get("bundleType", "MANUAL")

            # Skip app-managed bundles if they shouldn't be in Terraform
            if ":apps:" in orn and bundle_type != "MANUAL":
                print(f"  Skipping app-managed bundle: {name}")
                continue

            # Validate bundle can be individually retrieved
            # Some bundles are listed but return 404 when accessed individually
            if not self.validate_bundle_readable(bundle_id):
                print(f"  ⚠️  Skipping unreadable bundle (404): {name} (ID: {bundle_id})")
                continue

            safe_name = self._sanitize_name(name)

            # Extract bundle properties
            target = bundle.get("target", {})
            target_id = target.get("externalId", "")
            target_type = target.get("type", "")
            target_name = target.get("name", "")
            status = bundle.get("status", "ACTIVE")
            entitlements = bundle.get("entitlements", [])

            print(f"  Generating resource for bundle: {name}")

            # Add comment header
            tf_config.append(f'# {"-" * 77}')
            tf_config.append(f'# {name}')
            if description:
                tf_config.append(f'# {description}')
            tf_config.append(f'# {"-" * 77}')
            tf_config.append(f'')

            # Generate okta_entitlement_bundle resource
            tf_config.append(f'resource "okta_entitlement_bundle" "{safe_name}" {{')
            tf_config.append(f'  name = "{name}"')

            if description:
                # Escape quotes in description
                escaped_desc = description.replace('"', '\\"')
                tf_config.append(f'  description = "{escaped_desc}"')

            if orn:
                tf_config.append(f'  target_resource_orn = "{orn}"')

            if status:
                tf_config.append(f'  status = "{status}"')

            tf_config.append(f'')

            # Add target block
            if target_id and target_type:
                tf_config.append(f'  target {{')
                tf_config.append(f'    external_id = "{target_id}"')
                tf_config.append(f'    type        = "{target_type}"')
                if target_name:
                    tf_config.append(f'    # Resource name: {target_name}')
                tf_config.append(f'  }}')
                tf_config.append(f'')

            # Add entitlements blocks
            if entitlements:
                for entitlement in entitlements:
                    ent_id = entitlement.get("id") or entitlement.get("externalId")
                    ent_values = entitlement.get("values", [])

                    if ent_id:
                        tf_config.append(f'  entitlements {{')
                        tf_config.append(f'    id = "{ent_id}"')

                        if ent_values:
                            for value in ent_values:
                                value_id = value.get("id") or value.get("externalId")
                                if value_id:
                                    tf_config.append(f'    values {{')
                                    tf_config.append(f'      id = "{value_id}"')
                                    tf_config.append(f'    }}')

                        tf_config.append(f'  }}')
                        tf_config.append(f'')

            tf_config.append(f'  # Bundle Type: {bundle_type}')
            tf_config.append(f'  # ORN: {orn}')
            tf_config.append(f'}}')
            tf_config.append('')

            # Generate import command
            import_commands.append(f'# Import bundle: {name}')
            import_commands.append(f'terraform import okta_entitlement_bundle.{safe_name} {bundle_id}')
            import_commands.append('')

        return "\n".join(tf_config), import_commands

    def generate_reviews_tf(self, reviews: List[Dict]) -> tuple[str, List[str]]:
        """Generate Terraform config and import commands for access reviews"""
        if not reviews:
            return "", []

        tf_config = []
        import_commands = []

        tf_config.append("# Access Review Campaigns\n")

        for idx, review in enumerate(reviews, 1):
            review_id = review.get("id")
            name = review.get("name")
            description = review.get("description", "")

            # Use name if available, otherwise use ID or index for uniqueness
            if name:
                safe_name = self._sanitize_name(name)
            else:
                # Use last 8 chars of ID or index to create unique name
                id_suffix = review_id[-8:] if review_id else f"{idx:03d}"
                safe_name = f"review_{id_suffix}"
                name = f"Review {id_suffix}"  # Placeholder display name

            tf_config.append(f'resource "okta_reviews" "{safe_name}" {{')
            tf_config.append(f'  # ID: {review_id}')
            tf_config.append(f'  name        = "{name}"')
            if description:
                tf_config.append(f'  description = "{description}"')
            tf_config.append(f'')
            tf_config.append(f'  # REQUIRED: Add schedule, scope, and reviewer configuration')
            tf_config.append(f'  # This access review campaign will not run until you configure these required fields.')
            tf_config.append(f'  #')
            tf_config.append(f'  # Example schedule configuration:')
            tf_config.append(f'  # schedule {{')
            tf_config.append(f'  #   frequency   = "QUARTERLY"    # Options: WEEKLY, MONTHLY, QUARTERLY')
            tf_config.append(f'  #   day_of_week = "MONDAY"       # For WEEKLY: MONDAY-SUNDAY')
            tf_config.append(f'  #   day_of_month = 1             # For MONTHLY: 1-31')
            tf_config.append(f'  #   hour        = 9              # 24-hour format: 0-23')
            tf_config.append(f'  #   timezone    = "America/Los_Angeles"')
            tf_config.append(f'  # }}')
            tf_config.append(f'  #')
            tf_config.append(f'  # Example scope configuration (what to review):')
            tf_config.append(f'  # scope {{')
            tf_config.append(f'  #   resource_type = "ENTITLEMENT_BUNDLE"  # or "APPLICATION", "GROUP"')
            tf_config.append(f'  #   resource_ids  = [okta_entitlement_bundle.example.id]')
            tf_config.append(f'  # }}')
            tf_config.append(f'  #')
            tf_config.append(f'  # Example reviewer configuration:')
            tf_config.append(f'  # reviewer {{')
            tf_config.append(f'  #   type = "MANAGER"      # or "RESOURCE_OWNER", "SPECIFIC_USER"')
            tf_config.append(f'  #   fallback_user_id = okta_user.reviewer.id  # If manager not found')
            tf_config.append(f'  # }}')
            tf_config.append(f'  #')
            tf_config.append(f'  # See: https://registry.terraform.io/providers/okta/okta/latest/docs/resources/reviews')
            tf_config.append(f'}}')
            tf_config.append('')

            import_commands.append(f'terraform import okta_reviews.{safe_name} {review_id}')

        return "\n".join(tf_config), import_commands

    def generate_request_sequences_tf(self, sequences: List[Dict]) -> tuple[str, List[str]]:
        """Generate Terraform config and import commands for approval workflows"""
        if not sequences:
            return "", []

        tf_config = []
        import_commands = []

        tf_config.append("# Approval Workflows (Request Sequences)\n")

        for seq in sequences:
            seq_id = seq.get("id")
            name = seq.get("name", "unnamed")
            description = seq.get("description", "")
            safe_name = self._sanitize_name(name)

            tf_config.append(f'resource "okta_request_sequences" "{safe_name}" {{')
            tf_config.append(f'  # ID: {seq_id}')
            tf_config.append(f'  name        = "{name}"')
            if description:
                tf_config.append(f'  description = "{description}"')
            tf_config.append(f'')
            tf_config.append(f'  # REQUIRED: Add approval stages configuration')
            tf_config.append(f'  # Approval workflows require at least one approval stage to function.')
            tf_config.append(f'  #')
            tf_config.append(f'  # Example single-stage approval:')
            tf_config.append(f'  # stage {{')
            tf_config.append(f'  #   name          = "Manager Approval"')
            tf_config.append(f'  #   type          = "MANAGER"         # or "SPECIFIC_USER", "RESOURCE_OWNER"')
            tf_config.append(f'  #   approvers     = []                # Leave empty for MANAGER type')
            tf_config.append(f'  #   timeout_hours = 48                # Hours before escalation')
            tf_config.append(f'  # }}')
            tf_config.append(f'  #')
            tf_config.append(f'  # Example two-stage approval (manager → security team):')
            tf_config.append(f'  # stage {{')
            tf_config.append(f'  #   name          = "Manager Approval"')
            tf_config.append(f'  #   type          = "MANAGER"')
            tf_config.append(f'  #   approvers     = []')
            tf_config.append(f'  #   timeout_hours = 48')
            tf_config.append(f'  # }}')
            tf_config.append(f'  # stage {{')
            tf_config.append(f'  #   name          = "Security Team Approval"')
            tf_config.append(f'  #   type          = "SPECIFIC_USER"')
            tf_config.append(f'  #   approvers     = [okta_user.security_lead.id, okta_user.security_admin.id]')
            tf_config.append(f'  #   timeout_hours = 72')
            tf_config.append(f'  # }}')
            tf_config.append(f'  #')
            tf_config.append(f'  # See: https://registry.terraform.io/providers/okta/okta/latest/docs/resources/request_sequences')
            tf_config.append(f'}}')
            tf_config.append('')

            import_commands.append(f'terraform import okta_request_sequences.{safe_name} {seq_id}')

        return "\n".join(tf_config), import_commands

    def generate_catalog_entries_tf(self, entries: List[Dict]) -> tuple[str, List[str]]:
        """Generate Terraform config and import commands for catalog entries"""
        if not entries:
            return "", []

        tf_config = []
        import_commands = []

        tf_config.append("# Catalog Entries\n")

        for entry in entries:
            entry_id = entry.get("id")
            app_id = entry.get("appId")
            name = entry.get("name", "unnamed")
            safe_name = self._sanitize_name(name)

            tf_config.append(f'resource "okta_catalog_entry_default" "{safe_name}" {{')
            tf_config.append(f'  # ID: {entry_id}')
            tf_config.append(f'  app_id = "{app_id}"')
            tf_config.append(f'')
            tf_config.append(f'  # OPTIONAL: Review and add catalog configuration')
            tf_config.append(f'  # Catalog entries control how resources appear in the access request catalog.')
            tf_config.append(f'  # Default configuration is usually sufficient, but you can customize:')
            tf_config.append(f'  #')
            tf_config.append(f'  # Example customization:')
            tf_config.append(f'  # visibility           = "EVERYONE"       # or "SPECIFIC_GROUPS"')
            tf_config.append(f'  # visible_to_groups    = [okta_group.marketing.id]')
            tf_config.append(f'  # auto_grant           = false            # Require approval (default)')
            tf_config.append(f'  # approval_workflow_id = okta_request_sequences.manager_approval.id')
            tf_config.append(f'  # request_form_fields {{')
            tf_config.append(f'  #   name     = "Business Justification"')
            tf_config.append(f'  #   required = true')
            tf_config.append(f'  #   type     = "TEXT"')
            tf_config.append(f'  # }}')
            tf_config.append(f'  #')
            tf_config.append(f'  # See: https://registry.terraform.io/providers/okta/okta/latest/docs/resources/catalog_entry_default')
            tf_config.append(f'}}')
            tf_config.append('')

            import_commands.append(f'terraform import okta_catalog_entry_default.{safe_name} {entry_id}')

        return "\n".join(tf_config), import_commands

    def generate_request_settings_tf(self, settings: Optional[Dict]) -> tuple[str, List[str]]:
        """Generate Terraform config and import commands for request settings"""
        if not settings:
            return "", []

        tf_config = []
        import_commands = []

        tf_config.append("# Global Request Settings\n")
        tf_config.append('resource "okta_request_settings" "settings" {')
        tf_config.append('  # Global settings for access requests')
        tf_config.append('')
        tf_config.append('  # OPTIONAL: Add request settings configuration')
        tf_config.append('  # Global settings that apply to all access requests in your org.')
        tf_config.append('  # If not specified, Okta defaults will be used.')
        tf_config.append('  #')
        tf_config.append('  # Example configuration:')
        tf_config.append('  # default_approval_workflow_id = okta_request_sequences.default.id')
        tf_config.append('  # require_justification        = true')
        tf_config.append('  # notification_settings {{')
        tf_config.append('  #   notify_requester  = true  # Email requester on status changes')
        tf_config.append('  #   notify_approver   = true  # Email approver when action needed')
        tf_config.append('  #   notify_on_grant   = true  # Email when access granted')
        tf_config.append('  #   notify_on_revoke  = true  # Email when access revoked')
        tf_config.append('  # }}')
        tf_config.append('  # request_expiry_days         = 90   # Auto-expire requests after 90 days')
        tf_config.append('  #')
        tf_config.append('  # See: https://registry.terraform.io/providers/okta/okta/latest/docs/resources/request_settings')
        tf_config.append('}')
        tf_config.append('')

        import_commands.append('terraform import okta_request_settings.settings default')

        return "\n".join(tf_config), import_commands

    def export_json(self, output_file: str, data: Dict):
        """Export raw API data to JSON for reference"""
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  Exported JSON to: {output_file}")

    def generate_import_files(self, output_dir: str):
        """Generate all Terraform files and import commands"""
        print(f"\n{'='*60}")
        print(f"Importing OIG Resources from Okta")
        print(f"{'='*60}\n")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Fetch all resources
        entitlements = self.fetch_entitlements()
        # Skip reviews - they should be managed in Okta Admin UI
        # Reviews are individual access review decisions, not campaign definitions
        # For campaign management, use the Okta Admin Console
        reviews = []  # self.fetch_reviews() - disabled by default
        sequences = self.fetch_request_sequences(entitlements)  # Pass bundles for v2 API
        catalog_entries = self.fetch_catalog_entries()
        request_settings = self.fetch_request_settings()

        print(f"\n{'='*60}")
        print(f"Generating Terraform Configurations")
        print(f"{'='*60}\n")

        all_import_commands = []

        # Generate entitlements
        if entitlements:
            print("Generating entitlements configuration...")
            tf_content, imports = self.generate_entitlement_tf(entitlements)
            if tf_content:
                tf_file = os.path.join(output_dir, "entitlements.tf")
                with open(tf_file, 'w') as f:
                    f.write(tf_content)
                print(f"  Created: {tf_file}")
                all_import_commands.extend(imports)

            # Export raw JSON for reference
            json_file = os.path.join(output_dir, "entitlements.json")
            self.export_json(json_file, {"entitlements": entitlements})

        # Generate reviews
        if reviews:
            print("Generating access reviews configuration...")
            tf_content, imports = self.generate_reviews_tf(reviews)
            if tf_content:
                tf_file = os.path.join(output_dir, "reviews.tf")
                with open(tf_file, 'w') as f:
                    f.write(tf_content)
                print(f"  Created: {tf_file}")
                all_import_commands.extend(imports)

            json_file = os.path.join(output_dir, "reviews.json")
            self.export_json(json_file, {"reviews": reviews})

        # Generate request sequences
        if sequences:
            print("Generating approval workflows configuration...")
            tf_content, imports = self.generate_request_sequences_tf(sequences)
            if tf_content:
                tf_file = os.path.join(output_dir, "request_sequences.tf")
                with open(tf_file, 'w') as f:
                    f.write(tf_content)
                print(f"  Created: {tf_file}")
                all_import_commands.extend(imports)

            json_file = os.path.join(output_dir, "request_sequences.json")
            self.export_json(json_file, {"sequences": sequences})

        # Generate catalog entries
        if catalog_entries:
            print("Generating catalog entries configuration...")
            tf_content, imports = self.generate_catalog_entries_tf(catalog_entries)
            if tf_content:
                tf_file = os.path.join(output_dir, "catalog_entries.tf")
                with open(tf_file, 'w') as f:
                    f.write(tf_content)
                print(f"  Created: {tf_file}")
                all_import_commands.extend(imports)

            json_file = os.path.join(output_dir, "catalog_entries.json")
            self.export_json(json_file, {"catalog_entries": catalog_entries})

        # Generate request settings
        if request_settings:
            print("Generating request settings configuration...")
            tf_content, imports = self.generate_request_settings_tf(request_settings)
            if tf_content:
                tf_file = os.path.join(output_dir, "request_settings.tf")
                with open(tf_file, 'w') as f:
                    f.write(tf_content)
                print(f"  Created: {tf_file}")
                all_import_commands.extend(imports)

            json_file = os.path.join(output_dir, "request_settings.json")
            self.export_json(json_file, {"request_settings": request_settings})

        # Generate import script
        if all_import_commands:
            print("\nGenerating import script...")
            import_script = os.path.join(output_dir, "import.sh")
            with open(import_script, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("# Terraform import commands for OIG resources\n")
                f.write("# Review the generated .tf files and complete TODO items before running\n\n")
                f.write("set -e\n\n")
                for cmd in all_import_commands:
                    f.write(f"{cmd}\n")

            os.chmod(import_script, 0o755)
            print(f"  Created: {import_script}")

        print(f"\n{'='*60}")
        print(f"Import Generation Complete!")
        print(f"{'='*60}\n")
        print(f"Generated files in: {output_dir}/")
        print(f"")
        print(f"Next steps:")
        print(f"1. Review the generated .tf files in {output_dir}/")
        print(f"2. Complete TODO items in each file")
        print(f"3. Copy files to your Terraform directory")
        print(f"4. Run: cd {output_dir} && terraform init")
        print(f"5. Run: ./import.sh")
        print(f"6. Verify: terraform plan (should show no changes)")
        print(f"")
        print(f"Note: .json files contain raw API data for reference")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Import existing OIG resources from Okta into Terraform"
    )
    parser.add_argument(
        "--output-dir",
        default="imported_oig",
        help="Output directory for generated Terraform files"
    )
    parser.add_argument(
        "--org-name",
        help="Okta organization name (or set OKTA_ORG_NAME env var)"
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Okta base URL (default: okta.com, or OKTA_BASE_URL env var)"
    )
    parser.add_argument(
        "--api-token",
        help="Okta API token (or set OKTA_API_TOKEN env var)"
    )

    args = parser.parse_args()

    # Get credentials
    org_name = args.org_name or os.environ.get("OKTA_ORG_NAME")
    api_token = args.api_token or os.environ.get("OKTA_API_TOKEN")
    base_url = args.base_url or os.environ.get("OKTA_BASE_URL", "okta.com")

    if not org_name or not api_token:
        print("Error: Okta org name and API token required")
        print("Set via --org-name and --api-token or OKTA_ORG_NAME and OKTA_API_TOKEN env vars")
        sys.exit(1)

    # Run import
    importer = OIGImporter(org_name, base_url, api_token)
    importer.generate_import_files(args.output_dir)


if __name__ == "__main__":
    main()
