#!/usr/bin/env python3
"""
apply_resource_owners.py

Applies resource owner assignments from config/owner_mappings.json to Okta.

This script:
1. Reads owner mappings from config/owner_mappings.json
2. For each resource, assigns the specified owners
3. Supports dry-run mode to preview changes
4. Reports results

Usage:
    python3 scripts/apply_resource_owners.py
    python3 scripts/apply_resource_owners.py --dry-run
    python3 scripts/apply_resource_owners.py --config config/owner_mappings.json
"""

import os
import sys
import json
import requests
import argparse
from typing import List, Dict


class ResourceOwnerApplier:
    """Applies resource owner assignments to Okta"""

    def __init__(self, org_name: str, base_url: str, api_token: str, dry_run: bool = False):
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
        self.dry_run = dry_run

    def load_owner_mappings(self, config_file: str) -> Dict:
        """Load owner mappings from config file"""
        print("\n" + "="*80)
        print("LOADING OWNER MAPPINGS")
        print("="*80)

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)

            assignments = config.get("assignments", {})
            total_apps = len(assignments.get("apps", []))
            total_groups = len(assignments.get("groups", []))
            total_bundles = len(assignments.get("entitlement_bundles", []))

            print(f"✅ Loaded owner mappings:")
            print(f"   Apps: {total_apps}")
            print(f"   Groups: {total_groups}")
            print(f"   Entitlement bundles: {total_bundles}")

            return assignments

        except FileNotFoundError:
            print(f"❌ Config file not found: {config_file}")
            return None
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return None

    def assign_owners(self, resource_orn: str, principal_orns: List[str]) -> Dict:
        """Assign owners to a resource"""
        url = f"{self.governance_base}/resource-owners"
        payload = {
            "principalOrns": principal_orns,
            "resourceOrns": [resource_orn]
        }

        try:
            if self.dry_run:
                print(f"  [DRY RUN] Would assign {len(principal_orns)} owner(s) to {resource_orn}")
                return {"status": "dry_run", "assigned": len(principal_orns)}

            response = self.session.put(url, json=payload)
            response.raise_for_status()

            return {
                "status": "success",
                "assigned": len(principal_orns),
                "response": response.json()
            }

        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            try:
                error_detail = e.response.json()
                error_msg = error_detail.get("errorSummary", error_msg)
            except:
                pass

            return {
                "status": "error",
                "error": error_msg
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def apply_all_owners(self, assignments: Dict) -> Dict:
        """Apply all owner assignments from config"""
        print("\n" + "="*80)
        if self.dry_run:
            print("APPLYING OWNER ASSIGNMENTS (DRY RUN)")
        else:
            print("APPLYING OWNER ASSIGNMENTS")
        print("="*80)

        results = {
            "apps": [],
            "groups": [],
            "entitlement_bundles": [],
            "summary": {
                "total": 0,
                "success": 0,
                "errors": 0,
                "dry_run": self.dry_run
            }
        }

        # Process apps
        print("\n--- Applications ---")
        for app_assignment in assignments.get("apps", []):
            resource_orn = app_assignment.get("resource_orn")
            resource_name = app_assignment.get("resource_name", "Unknown")
            owners = app_assignment.get("owners", [])

            principal_orns = [owner.get("principal_orn") for owner in owners if owner.get("principal_orn")]

            if not principal_orns:
                print(f"⚠️  {resource_name}: No owners to assign")
                continue

            print(f"\n{resource_name} ({resource_orn}):")
            for owner in owners:
                print(f"  • {owner.get('principal_name', 'Unknown')} ({owner.get('principal_type', 'user')})")

            result = self.assign_owners(resource_orn, principal_orns)
            result["resource_name"] = resource_name
            result["resource_orn"] = resource_orn
            results["apps"].append(result)
            results["summary"]["total"] += 1

            if result["status"] == "success":
                print(f"✅ Assigned {len(principal_orns)} owner(s)")
                results["summary"]["success"] += 1
            elif result["status"] == "dry_run":
                results["summary"]["success"] += 1
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
                results["summary"]["errors"] += 1

        # Process groups
        print("\n--- Groups ---")
        for group_assignment in assignments.get("groups", []):
            resource_orn = group_assignment.get("resource_orn")
            resource_name = group_assignment.get("resource_name", "Unknown")
            owners = group_assignment.get("owners", [])

            principal_orns = [owner.get("principal_orn") for owner in owners if owner.get("principal_orn")]

            if not principal_orns:
                print(f"⚠️  {resource_name}: No owners to assign")
                continue

            print(f"\n{resource_name} ({resource_orn}):")
            for owner in owners:
                print(f"  • {owner.get('principal_name', 'Unknown')} ({owner.get('principal_type', 'user')})")

            result = self.assign_owners(resource_orn, principal_orns)
            result["resource_name"] = resource_name
            result["resource_orn"] = resource_orn
            results["groups"].append(result)
            results["summary"]["total"] += 1

            if result["status"] == "success":
                print(f"✅ Assigned {len(principal_orns)} owner(s)")
                results["summary"]["success"] += 1
            elif result["status"] == "dry_run":
                results["summary"]["success"] += 1
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
                results["summary"]["errors"] += 1

        # Process entitlement bundles
        print("\n--- Entitlement Bundles ---")
        for bundle_assignment in assignments.get("entitlement_bundles", []):
            resource_orn = bundle_assignment.get("resource_orn")
            resource_name = bundle_assignment.get("resource_name", "Unknown")
            owners = bundle_assignment.get("owners", [])

            principal_orns = [owner.get("principal_orn") for owner in owners if owner.get("principal_orn")]

            if not principal_orns:
                print(f"⚠️  {resource_name}: No owners to assign")
                continue

            print(f"\n{resource_name} ({resource_orn}):")
            for owner in owners:
                print(f"  • {owner.get('principal_name', 'Unknown')} ({owner.get('principal_type', 'user')})")

            result = self.assign_owners(resource_orn, principal_orns)
            result["resource_name"] = resource_name
            result["resource_orn"] = resource_orn
            results["entitlement_bundles"].append(result)
            results["summary"]["total"] += 1

            if result["status"] == "success":
                print(f"✅ Assigned {len(principal_orns)} owner(s)")
                results["summary"]["success"] += 1
            elif result["status"] == "dry_run":
                results["summary"]["success"] += 1
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
                results["summary"]["errors"] += 1

        return results

    def run(self, config_file: str):
        """Main execution"""
        print("="*80)
        if self.dry_run:
            print("RESOURCE OWNER APPLIER (DRY RUN MODE)")
        else:
            print("RESOURCE OWNER APPLIER")
        print("="*80)

        # Load config
        assignments = self.load_owner_mappings(config_file)
        if not assignments:
            return False

        # Apply owners
        results = self.apply_all_owners(assignments)

        # Print summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total resources: {results['summary']['total']}")
        print(f"Successful: {results['summary']['success']}")
        print(f"Errors: {results['summary']['errors']}")
        if self.dry_run:
            print("\n⚠️  DRY RUN MODE - No changes were made to Okta")
        print("="*80)

        return results['summary']['errors'] == 0


def main():
    parser = argparse.ArgumentParser(
        description="Apply resource owner assignments from config to Okta"
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
        "--config",
        default="config/owner_mappings.json",
        help="Owner mappings config file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )

    args = parser.parse_args()

    if not args.org_name or not args.api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN must be set")
        sys.exit(1)

    applier = ResourceOwnerApplier(
        args.org_name,
        args.base_url,
        args.api_token,
        dry_run=args.dry_run
    )

    success = applier.run(args.config)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
