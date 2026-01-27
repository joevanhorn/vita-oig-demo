#!/usr/bin/env python3
"""
apply_labels_from_config.py

Generic label management tool that applies labels based on label_mappings.json configuration.

This is the "apply" counterpart to sync_label_mappings.py:
- sync_label_mappings.py: Okta → label_mappings.json (import/sync)
- apply_labels_from_config.py: label_mappings.json → Okta (apply/deploy)

Features:
- Creates labels with multiple values if they don't exist
- Supports both single-value and multi-value labels
- Applies specific label values to resources (apps, groups, entitlement bundles)
- Supports dry-run mode
- GitOps workflow: label_mappings.json is source of truth

Hierarchical Label Structure:
- Label (key): Top-level category with labelId (e.g., "Compliance")
- Label Values: Individual entries with labelValueId (e.g., "SOX", "GDPR", "PII")
- Assignments: Assign specific VALUES (not labels) to resources

Okta Label Constraints:
- Max 10 custom label keys per org
- Each key supports up to 10 values (max 100 total labels)
- Each resource can have up to 10 labels assigned
- Predefined labels: Crown Jewel, Privileged

Usage:
    python3 scripts/apply_labels_from_config.py --config environments/lowerdecklabs/config/label_mappings.json
    python3 scripts/apply_labels_from_config.py --config config/label_mappings.json --dry-run
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.okta_api_manager import OktaAPIManager


class LabelApplier:
    """Applies labels from config file to Okta resources"""

    def __init__(self, manager: OktaAPIManager, dry_run: bool = False):
        self.manager = manager
        self.dry_run = dry_run
        self.stats = {
            "labels_created": 0,
            "labels_skipped": 0,
            "label_values_created": 0,
            "assignments_applied": 0,
            "assignments_skipped": 0,
            "errors": []
        }
        # Cache to store labelValueId mappings: {"Label:Value": "labelValueId"}
        self.label_value_cache = {}

    def load_config(self, config_file: str) -> Dict:
        """Load label configuration from JSON file"""
        print(f"Loading configuration from {config_file}...")
        with open(config_file, 'r') as f:
            config = json.load(f)

        labels_count = len(config.get("labels", {}))
        print(f"  ✅ Loaded {labels_count} label definitions")
        return config

    def ensure_label_exists(self, label_name: str, label_config: Dict) -> bool:
        """
        Ensure label exists in Okta with all its values.

        For hierarchical labels (multi-value), this creates the label with all values
        in a single API call using create_label_with_values().

        Returns: True if successful, False if error
        """
        print(f"\n📌 Processing label: {label_name}")

        # Check if label already exists
        existing_label = self.manager.get_label(label_name)

        if existing_label:
            label_id = existing_label.get("labelId")
            print(f"  ✅ Label already exists (labelId: {label_id})")

            # Cache existing label value IDs
            for value in existing_label.get("values", []):
                value_name = value.get("name")
                value_id = value.get("labelValueId")
                cache_key = f"{label_name}:{value_name}"
                self.label_value_cache[cache_key] = value_id
                print(f"     - {value_name}: {value_id}")

            self.stats["labels_skipped"] += 1
            return True

        # Create new label with all values
        values_config = label_config.get("values", {})

        if self.dry_run:
            print(f"  🔍 DRY RUN: Would create label '{label_name}'")
            print(f"     Description: {label_config.get('description', 'N/A')}")
            print(f"     Type: {label_config.get('type', 'N/A')}")
            print(f"     Values ({len(values_config)}):")
            for value_name, value_data in values_config.items():
                print(f"       - {value_name}: {value_data.get('description', 'N/A')}")
                # Cache dummy IDs for dry run
                cache_key = f"{label_name}:{value_name}"
                self.label_value_cache[cache_key] = f"dry-run-value-{value_name}"

            self.stats["labels_created"] += 1
            self.stats["label_values_created"] += len(values_config)
            return True

        # Build values array for API call
        values_array = []
        for value_name, value_data in values_config.items():
            value_entry = {
                "name": value_name
            }
            # Add description if provided
            if "description" in value_data:
                value_entry["description"] = value_data["description"]
            # Add metadata if provided
            if "metadata" in value_data:
                value_entry["metadata"] = value_data["metadata"]
            values_array.append(value_entry)

        try:
            description = label_config.get("description", f"{label_name} label")
            result = self.manager.create_label_with_values(
                name=label_name,
                description=description,
                values=values_array
            )

            if result and not result.get("exists"):
                label_id = result.get("labelId")
                print(f"  ✅ Created label successfully (labelId: {label_id})")

                # Cache the label value IDs
                for value in result.get("values", []):
                    value_name = value.get("name")
                    value_id = value.get("labelValueId")
                    cache_key = f"{label_name}:{value_name}"
                    self.label_value_cache[cache_key] = value_id
                    print(f"     - {value_name}: {value_id}")

                self.stats["labels_created"] += 1
                self.stats["label_values_created"] += len(values_array)
                return True
            else:
                # Label exists but wasn't in our initial check (race condition)
                existing_label = self.manager.get_label(label_name)
                if existing_label:
                    # Cache existing values
                    for value in existing_label.get("values", []):
                        value_name = value.get("name")
                        value_id = value.get("labelValueId")
                        cache_key = f"{label_name}:{value_name}"
                        self.label_value_cache[cache_key] = value_id
                    self.stats["labels_skipped"] += 1
                    return True

        except Exception as e:
            print(f"  ❌ Error creating label: {e}")
            self.stats["errors"].append(f"Failed to create label '{label_name}': {e}")
            return False

    def apply_assignments(self, assignment_key: str, resource_orns: List[str]) -> int:
        """
        Apply a label value to a list of resources.

        Args:
            assignment_key: Either "LabelName" or "LabelName:ValueName"
            resource_orns: List of resource ORNs

        Returns: Number of resources successfully labeled
        """
        if not resource_orns:
            return 0

        # Parse assignment key
        if ":" in assignment_key:
            # Multi-value format: "Compliance:SOX"
            label_name, value_name = assignment_key.split(":", 1)
            display_name = f"{label_name}:{value_name}"
        else:
            # Single-value format: "Privileged"
            label_name = assignment_key
            value_name = assignment_key
            display_name = label_name

        # Get labelValueId from cache
        cache_key = f"{label_name}:{value_name}"
        label_value_id = self.label_value_cache.get(cache_key)

        if not label_value_id:
            print(f"  ⚠️  Label value ID not found for '{assignment_key}'")
            self.stats["errors"].append(f"Label value ID not found for '{assignment_key}'")
            return 0

        if self.dry_run:
            print(f"  🔍 DRY RUN: Would assign '{display_name}' to {len(resource_orns)} resources")
            for orn in resource_orns[:5]:  # Show first 5
                print(f"     - {orn}")
            if len(resource_orns) > 5:
                print(f"     ... and {len(resource_orns) - 5} more")
            self.stats["assignments_applied"] += len(resource_orns)
            return len(resource_orns)

        try:
            print(f"  📦 Assigning '{display_name}' to {len(resource_orns)} resources...")
            print(f"     Label value ID: {label_value_id}")
            print(f"     Resource ORNs:")
            for orn in resource_orns:
                print(f"       - {orn}")

            self.manager.assign_label_values_to_resources(
                label_value_ids=[label_value_id],
                resource_orns=resource_orns
            )
            self.stats["assignments_applied"] += len(resource_orns)
            return len(resource_orns)
        except Exception as e:
            print(f"  ❌ Error assigning '{display_name}': {e}")
            print(f"     Label value ID used: {label_value_id}")
            print(f"     Number of resource ORNs: {len(resource_orns)}")
            print(f"     Resource ORNs:")
            for orn in resource_orns:
                print(f"       - {orn}")

            # Print response details if available
            if hasattr(e, 'response') and e.response is not None:
                print(f"     HTTP Status: {e.response.status_code}")
                try:
                    error_body = e.response.json()
                    print(f"     Error body: {json.dumps(error_body, indent=6)}")
                except:
                    print(f"     Response text: {e.response.text}")

            self.stats["errors"].append(f"Failed to assign '{display_name}': {e}")
            return 0

    def apply_all_labels(self, config: Dict) -> bool:
        """Process all labels and their assignments from config"""
        print("\n" + "="*80)
        print("APPLYING LABELS FROM CONFIGURATION")
        print("="*80)

        if self.dry_run:
            print("\n🔍 DRY RUN MODE - No changes will be made to Okta")

        labels_config = config.get("labels", {})
        assignments_config = config.get("assignments", {})

        # Step 1: Ensure all labels exist with their values
        print("\n" + "="*80)
        print("STEP 1: ENSURE LABELS EXIST")
        print("="*80)

        for label_name, label_info in labels_config.items():
            success = self.ensure_label_exists(label_name, label_info)
            if not success:
                print(f"  ⚠️  Skipping assignments for '{label_name}' due to creation error")

        # Step 2: Apply assignments
        print("\n" + "="*80)
        print("STEP 2: APPLY ASSIGNMENTS")
        print("="*80)

        total_assignments = 0
        for resource_type in ["apps", "groups", "entitlement_bundles", "other"]:
            type_assignments = assignments_config.get(resource_type, {})

            if not type_assignments:
                continue

            print(f"\n📂 Processing {resource_type}:")

            for assignment_key, orns in type_assignments.items():
                if orns:
                    count = self.apply_assignments(assignment_key, orns)
                    total_assignments += count
                else:
                    print(f"  ℹ️  No resources configured for '{assignment_key}'")

        if total_assignments == 0:
            print(f"\n  ℹ️  No assignments were configured")

        return True

    def print_summary(self):
        """Print summary of operations"""
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)

        if self.dry_run:
            print("Mode: 🔍 DRY RUN (no changes made)")
        else:
            print("Mode: ✅ APPLY (changes applied to Okta)")

        print(f"\nLabels:")
        print(f"  Created: {self.stats['labels_created']}")
        print(f"  Already existed: {self.stats['labels_skipped']}")
        print(f"  Total values created: {self.stats['label_values_created']}")

        print(f"\nAssignments:")
        print(f"  Applied: {self.stats['assignments_applied']}")

        if self.stats['errors']:
            print(f"\nErrors ({len(self.stats['errors'])}):")
            for error in self.stats['errors']:
                print(f"  ❌ {error}")

        print("="*80)


def main():
    parser = argparse.ArgumentParser(
        description="Apply labels to Okta resources from label_mappings.json"
    )
    parser.add_argument(
        "--config",
        default="environments/lowerdecklabs/config/label_mappings.json",
        help="Path to label_mappings.json config file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--org-name",
        default=os.environ.get("OKTA_ORG_NAME"),
        help="Okta organization name (default: from OKTA_ORG_NAME env)"
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OKTA_BASE_URL", "okta.com"),
        help="Okta base URL (default: from OKTA_BASE_URL env or okta.com)"
    )
    parser.add_argument(
        "--api-token",
        default=os.environ.get("OKTA_API_TOKEN"),
        help="Okta API token (default: from OKTA_API_TOKEN env)"
    )

    args = parser.parse_args()

    # Validate required arguments
    if not args.org_name or not args.api_token:
        print("❌ Error: OKTA_ORG_NAME and OKTA_API_TOKEN must be set")
        print("   Either set environment variables or use --org-name and --api-token")
        sys.exit(1)

    if not os.path.exists(args.config):
        print(f"❌ Error: Config file not found: {args.config}")
        sys.exit(1)

    # Initialize manager
    manager = OktaAPIManager(
        org_name=args.org_name,
        base_url=args.base_url,
        api_token=args.api_token
    )

    # Run label application
    applier = LabelApplier(manager, dry_run=args.dry_run)

    try:
        config = applier.load_config(args.config)
        success = applier.apply_all_labels(config)
        applier.print_summary()

        # Save results to JSON for workflow consumption
        results = {
            "dry_run": args.dry_run,
            "config_file": args.config,
            **applier.stats
        }

        with open("label_application_results.json", 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\nResults saved to: label_application_results.json")

        sys.exit(0 if success and not applier.stats['errors'] else 1)

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
