#!/usr/bin/env python3
"""
find_admin_resources.py

Scans Terraform configurations to find resources with "admin" in their name
and generates label assignment recommendations.

Usage:
    python3 scripts/find_admin_resources.py --config-dir production-ready
    python3 scripts/find_admin_resources.py --config-dir production-ready --apply-labels
"""

import os
import re
import json
import argparse
from typing import List, Dict, Tuple
from pathlib import Path


class AdminResourceFinder:
    """Find and categorize admin-related resources in Terraform configs"""

    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.admin_pattern = re.compile(r'.*admin.*', re.IGNORECASE)
        self.super_admin_pattern = re.compile(r'.*super.*admin.*', re.IGNORECASE)

    def scan_terraform_files(self) -> List[Dict]:
        """Scan all .tf files for resources with 'admin' in name"""
        admin_resources = []

        for tf_file in self.config_dir.glob('*.tf'):
            with open(tf_file, 'r') as f:
                content = f.read()

            # Find resource blocks
            resource_pattern = re.compile(
                r'resource\s+"([^"]+)"\s+"([^"]+)"\s*{',
                re.MULTILINE
            )

            for match in resource_pattern.finditer(content):
                resource_type = match.group(1)
                resource_name = match.group(2)

                # Check if name contains "admin"
                if self.admin_pattern.match(resource_name):
                    # Determine severity
                    if self.super_admin_pattern.match(resource_name):
                        labels = ["Privileged", "Compliance-Required"]
                        severity = "CRITICAL"
                    else:
                        labels = ["Privileged"]
                        severity = "HIGH"

                    admin_resources.append({
                        "file": tf_file.name,
                        "resource_type": resource_type,
                        "resource_name": resource_name,
                        "recommended_labels": labels,
                        "severity": severity,
                        "terraform_address": f"{resource_type}.{resource_name}"
                    })

        return admin_resources

    def generate_label_config(self, admin_resources: List[Dict]) -> Dict:
        """Generate label configuration for admin resources"""
        config = {
            "labels": {
                "assignments": {
                    "entitlements": {},
                    "apps": {},
                    "groups": {}
                }
            }
        }

        for resource in admin_resources:
            resource_type = resource["resource_type"]
            resource_name = resource["resource_name"]
            labels = resource["recommended_labels"]

            # Map to config structure
            if resource_type == "okta_principal_entitlements":
                # Use terraform resource name as key (will need to map to actual ID)
                config["labels"]["assignments"]["entitlements"][resource_name] = labels
            elif resource_type.startswith("okta_app_"):
                config["labels"]["assignments"]["apps"][resource_name] = labels
            elif resource_type == "okta_group":
                config["labels"]["assignments"]["groups"][resource_name] = labels

        return config

    def print_summary(self, admin_resources: List[Dict]):
        """Print summary of admin resources found"""
        print("=" * 80)
        print("ADMIN RESOURCE SCAN RESULTS")
        print("=" * 80)
        print(f"\nTotal admin resources found: {len(admin_resources)}\n")

        if not admin_resources:
            print("No resources with 'admin' in the name were found.")
            return

        # Group by severity
        by_severity = {}
        for resource in admin_resources:
            severity = resource["severity"]
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(resource)

        for severity in ["CRITICAL", "HIGH"]:
            if severity not in by_severity:
                continue

            print(f"\n{severity} PRIORITY:")
            print("-" * 80)

            for resource in by_severity[severity]:
                print(f"  📋 {resource['terraform_address']}")
                print(f"     File: {resource['file']}")
                print(f"     Recommended Labels: {', '.join(resource['recommended_labels'])}")
                print()

        print("=" * 80)
        print("RECOMMENDED ACTIONS:")
        print("=" * 80)
        print("1. Review the admin resources listed above")
        print("2. Update config/api_config.json with label assignments")
        print("3. Apply labels using: python3 scripts/okta_api_manager.py --action apply --config config/api_config.json")
        print("4. Verify in Okta Admin Console under Identity Governance")
        print("=" * 80)

    def update_api_config(self, admin_resources: List[Dict], config_path: str):
        """Update api_config.json with admin resource labels"""
        config_file = Path(config_path)

        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            config = {
                "labels": {
                    "assignments": {
                        "entitlements": {},
                        "apps": {},
                        "groups": {}
                    }
                }
            }

        # Add admin resources to config
        for resource in admin_resources:
            resource_type = resource["resource_type"]
            resource_name = resource["resource_name"]
            labels = resource["recommended_labels"]

            if resource_type == "okta_principal_entitlements":
                config["labels"]["assignments"]["entitlements"][resource_name] = labels
            elif resource_type.startswith("okta_app_"):
                config["labels"]["assignments"]["apps"][resource_name] = labels
            elif resource_type == "okta_group":
                config["labels"]["assignments"]["groups"][resource_name] = labels

        # Write updated config
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"\n✅ Updated {config_path} with admin resource labels")


def main():
    parser = argparse.ArgumentParser(
        description="Find admin resources in Terraform configs and recommend labels"
    )
    parser.add_argument(
        "--config-dir",
        default="production-ready",
        help="Directory containing Terraform configurations"
    )
    parser.add_argument(
        "--api-config",
        default="config/api_config.json",
        help="Path to api_config.json file"
    )
    parser.add_argument(
        "--apply-labels",
        action="store_true",
        help="Update api_config.json with recommended labels"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    # Find admin resources
    finder = AdminResourceFinder(args.config_dir)
    admin_resources = finder.scan_terraform_files()

    if args.json:
        print(json.dumps(admin_resources, indent=2))
    else:
        finder.print_summary(admin_resources)

    # Optionally update api_config.json
    if args.apply_labels:
        finder.update_api_config(admin_resources, args.api_config)


if __name__ == "__main__":
    main()
