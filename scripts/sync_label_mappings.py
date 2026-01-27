#!/usr/bin/env python3
"""
sync_label_mappings.py

Syncs label mappings from Okta OIG to the local config/label_mappings.json file.
This keeps the repository's label configuration up-to-date with the Okta environment.

Now supports hierarchical label structure:
- Labels with multiple values (e.g., Compliance: SOX, GDPR, PII)
- Labels with single values (e.g., Privileged, Crown Jewel)
- Assignment tracking by label value, not just label

Usage:
    python3 scripts/sync_label_mappings.py
    python3 scripts/sync_label_mappings.py --output config/label_mappings.json
"""

import os
import sys
import json
import requests
import argparse
from typing import Dict, List
from datetime import datetime


class LabelMappingSync:
    """Syncs label mappings from Okta to local config"""

    def __init__(self, org_name: str, base_url: str, api_token: str):
        self.org_name = org_name
        self.base_url = f"https://{org_name}.{base_url}"
        self.governance_base = f"{self.base_url}/governance/api/v1"
        self.headers = {
            "Authorization": f"SSWS {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_all_labels(self) -> List[Dict]:
        """Query all labels from Okta"""
        print("Querying labels from Okta...")
        url = f"{self.governance_base}/labels"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            labels = data.get("data", [])
            print(f"  ✅ Found {len(labels)} labels")
            return labels
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return []

    def get_all_resource_labels(self) -> List[Dict]:
        """Query all resource-label assignments from Okta"""
        print("Querying resource-label assignments...")
        url = f"{self.governance_base}/resource-labels"
        params = {"limit": 200}

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            assignments = data.get("data", [])
            print(f"  ✅ Found {len(assignments)} assignments")
            return assignments
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return []

    def build_mappings(self, labels: List[Dict], assignments: List[Dict]) -> Dict:
        """Build the hierarchical label mappings structure"""
        print("\nBuilding label mappings...")

        # Build hierarchical label metadata
        label_metadata = {}
        label_value_to_label = {}  # Map labelValueId -> (labelName, valueName)

        for label in labels:
            name = label.get("name")
            label_id = label.get("labelId")
            values = label.get("values", [])

            # Determine if this is a single-value or multi-value label
            label_type = "single_value" if len(values) == 1 and values[0].get("name") == name else "multi_value"

            # Build values structure
            values_dict = {}
            for value in values:
                value_name = value.get("name")
                value_id = value.get("labelValueId")
                description = value.get("description", f"{value_name} label value")

                # Store mapping for later assignment processing
                label_value_to_label[value_id] = (name, value_name)

                # Extract color from metadata
                color = None
                bg_color = None
                metadata = value.get("metadata", {})
                additional_props = metadata.get("additionalProperties", {})
                bg_color = additional_props.get("backgroundColor")

                # Map background color to simple color name
                color_map = {
                    "red": "red",
                    "green": "green",
                    "blue": "blue",
                    "orange": "orange",
                    "yellow": "yellow",
                    "purple": "purple"
                }
                color = color_map.get(bg_color, bg_color)

                values_dict[value_name] = {
                    "labelValueId": value_id,
                    "description": description,
                    "color": color,
                    "metadata": {
                        "backgroundColor": bg_color
                    } if bg_color else {}
                }

            label_metadata[name] = {
                "labelId": label_id,
                "description": label.get("description", f"{name} label"),
                "type": label_type,
                "values": values_dict
            }

            print(f"  • {name} ({label_type}): {label_id}")
            for value_name in values_dict.keys():
                print(f"      - {value_name}: {values_dict[value_name]['labelValueId']}")

        # Build assignments by label value and resource type
        # Format: assignments[resource_type][Label:Value] = [ORN1, ORN2, ...]
        assignments_by_type = {
            "apps": {},
            "groups": {},
            "entitlement_bundles": {},
            "other": {}
        }

        for assignment in assignments:
            resource = assignment.get("resource", {})
            resource_orn = resource.get("orn", "")

            # Determine resource category
            if "entitlement-bundles" in resource_orn:
                category = "entitlement_bundles"
            elif ":apps:" in resource_orn:
                category = "apps"
            elif ":groups:" in resource_orn:
                category = "groups"
            else:
                category = "other"

            # Get label values for this resource
            for label_value in assignment.get("labels", []):
                label_value_id = label_value.get("labelValueId")

                # Look up which label and value this belongs to
                if label_value_id in label_value_to_label:
                    label_name, value_name = label_value_to_label[label_value_id]

                    # Determine assignment key format
                    label_info = label_metadata.get(label_name, {})
                    if label_info.get("type") == "single_value":
                        # Single-value labels use simple name
                        assignment_key = label_name
                    else:
                        # Multi-value labels use "Label:Value" format
                        assignment_key = f"{label_name}:{value_name}"

                    # Add to assignments
                    if assignment_key not in assignments_by_type[category]:
                        assignments_by_type[category][assignment_key] = []

                    if resource_orn and resource_orn not in assignments_by_type[category][assignment_key]:
                        assignments_by_type[category][assignment_key].append(resource_orn)

        print(f"  ✅ Built assignments structure")

        # Build final structure
        mappings = {
            "description": "Label ID mappings synced from Okta OIG",
            "last_synced": datetime.utcnow().isoformat() + "Z",
            "labels": label_metadata,
            "assignments": {
                category: {key: sorted(orns) for key, orns in assignments_by_type[category].items()}
                for category in ["apps", "groups", "entitlement_bundles", "other"]
            },
            "notes": [
                "This file is the source of truth for label assignments",
                "",
                "Label Structure:",
                "  - Each label can have multiple values (hierarchical structure)",
                "  - Single-value labels (Privileged, Crown Jewel) have one value matching the label name",
                "  - Multi-value labels (Compliance) have multiple distinct values (SOX, GDPR, PII)",
                "",
                "To add a new label:",
                "  1. Add label definition to 'labels' section with its values",
                "  2. labelId/labelValueId can be empty - will be created during apply",
                "  3. Add resource ORNs to appropriate assignment arrays using 'Label:Value' format",
                "  4. Submit PR with changes",
                "  5. Run 'Apply Labels from Config' workflow with dry_run=true to preview",
                "  6. Merge PR and run workflow with dry_run=false to apply",
                "",
                "To sync this file FROM Okta:",
                "  - Run: python3 scripts/sync_label_mappings.py --output environments/lowerdecklabs/config/label_mappings.json",
                "",
                "To apply labels TO Okta:",
                "  - Run: python3 scripts/apply_labels_from_config.py --config environments/lowerdecklabs/config/label_mappings.json --dry-run",
                "  - Or use GitHub Actions workflow: 'LowerDeckLabs - Apply Labels from Config'",
                "",
                "ORN Format:",
                "  - Apps: orn:okta:application:{orgId}:apps:{appId}",
                "  - Groups: orn:okta:directory:{orgId}:groups:{groupId}",
                "  - Entitlement Bundles: orn:okta:governance:{orgId}:entitlement-bundles:{bundleId}",
                "",
                "Assignment Format:",
                "  - For single-value labels: use label name (e.g., 'Privileged')",
                "  - For multi-value labels: use 'Label:Value' format (e.g., 'Compliance:SOX', 'Compliance:GDPR')"
            ]
        }

        return mappings

    def save_mappings(self, mappings: Dict, output_file: str):
        """Save mappings to file"""
        print(f"\nSaving mappings to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(mappings, f, indent=2)
        print(f"  ✅ Saved successfully")

    def sync(self, output_file: str) -> bool:
        """Run the complete sync process"""
        print("="*80)
        print("SYNC LABEL MAPPINGS FROM OKTA")
        print("="*80)
        print()

        # Get labels
        labels = self.get_all_labels()
        if not labels:
            print("\n❌ No labels found - cannot sync")
            return False

        # Get assignments
        assignments = self.get_all_resource_labels()

        # Build mappings
        mappings = self.build_mappings(labels, assignments)

        # Save to file
        self.save_mappings(mappings, output_file)

        # Summary
        print("\n" + "="*80)
        print("SYNC SUMMARY")
        print("="*80)
        print(f"  Labels synced: {len(mappings['labels'])}")

        total_assignments = sum(
            len(orns)
            for category in mappings['assignments'].values()
            for orns in category.values()
        )
        print(f"  Total assignments: {total_assignments}")

        for category in ["apps", "groups", "entitlement_bundles", "other"]:
            count = sum(len(orns) for orns in mappings['assignments'][category].values())
            if count > 0:
                print(f"    - {category}: {count}")

        print(f"  Output file: {output_file}")
        print("="*80)

        return True


def main():
    parser = argparse.ArgumentParser(
        description="Sync label mappings from Okta to local config"
    )
    parser.add_argument(
        "--org-name",
        default=os.environ.get("OKTA_ORG_NAME"),
        help="Okta organization name"
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OKTA_BASE_URL", "okta.com"),
        help="Okta base URL"
    )
    parser.add_argument(
        "--api-token",
        default=os.environ.get("OKTA_API_TOKEN"),
        help="Okta API token"
    )
    parser.add_argument(
        "--output",
        default="config/label_mappings.json",
        help="Output file path"
    )

    args = parser.parse_args()

    if not args.org_name or not args.api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN must be set")
        sys.exit(1)

    syncer = LabelMappingSync(args.org_name, args.base_url, args.api_token)
    success = syncer.sync(args.output)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
