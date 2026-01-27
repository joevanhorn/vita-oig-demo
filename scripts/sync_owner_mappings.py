#!/usr/bin/env python3
"""
sync_owner_mappings.py

Syncs resource owner mappings from Okta OIG to the local config/owner_mappings.json file.
This keeps the repository's owner configuration up-to-date with the Okta environment.

Usage:
    python3 scripts/sync_owner_mappings.py
    python3 scripts/sync_owner_mappings.py --output config/owner_mappings.json
    python3 scripts/sync_owner_mappings.py --resource-orns <orn1> <orn2> <orn3>
"""

import os
import sys
import json
import time
import requests
import argparse
from typing import Dict, List
from datetime import datetime


class OwnerMappingSync:
    """Syncs resource owner mappings from Okta to local config"""

    def __init__(self, org_name: str, base_url: str, api_token: str):
        self.org_name = org_name
        self.base_url = f"https://{org_name}.{base_url}"
        self.governance_base = f"{self.base_url}/governance/api/v1"
        self.api_base = f"{self.base_url}/api/v1"
        self.headers = {
            "Authorization": f"SSWS {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_resource_owners(self, resource_orn: str) -> List[Dict]:
        """
        Query owners for a specific resource with retry logic and rate limiting.

        Implements exponential backoff for 429 (rate limit) errors and
        adds a small delay between requests to prevent hitting rate limits.
        """
        url = f"{self.governance_base}/resource-owners"
        filter_expr = f'parentResourceOrn eq "{resource_orn}"'
        params = {
            "filter": filter_expr,
            "limit": 200
        }

        max_retries = 3
        base_delay = 1  # Start with 1 second delay

        for attempt in range(max_retries):
            try:
                # Add small delay before each request to avoid rate limits
                if attempt > 0:
                    # Exponential backoff: 1s, 2s, 4s
                    delay = base_delay * (2 ** attempt)
                    print(f"  ⏳ Retry {attempt}/{max_retries} after {delay}s delay...")
                    time.sleep(delay)
                else:
                    # Small delay even on first attempt to space out requests
                    time.sleep(0.1)

                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    # Resource owners not available or resource not found
                    return []
                elif e.response.status_code == 429:
                    # Rate limit hit - retry with backoff
                    if attempt < max_retries - 1:
                        retry_after = e.response.headers.get('Retry-After', base_delay * (2 ** attempt))
                        try:
                            retry_after = int(retry_after)
                        except ValueError:
                            retry_after = base_delay * (2 ** attempt)
                        print(f"  ⚠️  Rate limit hit for {resource_orn}, retrying after {retry_after}s...")
                        time.sleep(retry_after)
                        continue
                    else:
                        print(f"  ❌ Rate limit persists for {resource_orn} after {max_retries} retries")
                        return []
                elif e.response.status_code == 400:
                    # Bad request - likely invalid filter or resource doesn't support owners
                    return []
                else:
                    print(f"  ⚠️  Error querying owners for {resource_orn}: {e}")
                    return []

            except requests.exceptions.Timeout:
                print(f"  ⚠️  Timeout querying owners for {resource_orn}")
                if attempt < max_retries - 1:
                    continue
                return []

            except Exception as e:
                print(f"  ⚠️  Error: {e}")
                return []

        return []

    def get_all_apps(self) -> List[Dict]:
        """Query all applications from Okta"""
        print("Querying applications...")
        url = f"{self.api_base}/apps"
        params = {"limit": 200}

        all_apps = []
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            apps = response.json()
            all_apps.extend(apps)
            print(f"  ✅ Found {len(apps)} apps")
            return all_apps
        except Exception as e:
            print(f"  ⚠️  Error querying apps: {e}")
            return []

    def get_all_groups(self) -> List[Dict]:
        """Query all groups from Okta"""
        print("Querying groups...")
        url = f"{self.api_base}/groups"
        params = {"limit": 200}

        all_groups = []
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            groups = response.json()
            all_groups.extend(groups)
            print(f"  ✅ Found {len(groups)} groups")
            return all_groups
        except Exception as e:
            print(f"  ⚠️  Error querying groups: {e}")
            return []

    def get_all_entitlement_bundles(self) -> List[Dict]:
        """Query all entitlement bundles from Okta"""
        print("Querying entitlement bundles...")
        url = f"{self.governance_base}/entitlement-bundles"
        params = {"limit": 200}

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            bundles = data.get("data", [])
            print(f"  ✅ Found {len(bundles)} entitlement bundles")
            return bundles
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"  ℹ️  Entitlement bundles not available (OIG may not be enabled)")
                return []
            print(f"  ⚠️  Error querying entitlement bundles: {e}")
            return []
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            return []

    def build_orn(self, resource_id: str, resource_type: str, app_type: str = None) -> str:
        """Build Okta Resource Name (ORN)"""
        if resource_type == "app":
            if not app_type:
                app_type = "oauth2"  # default
            return f"orn:okta:idp:{self.org_name}:apps:{app_type}:{resource_id}"
        elif resource_type == "group":
            return f"orn:okta:directory:{self.org_name}:groups:{resource_id}"
        elif resource_type == "entitlement_bundle":
            return f"orn:okta:governance:{self.org_name}:entitlement-bundles:{resource_id}"
        elif resource_type == "user":
            return f"orn:okta:directory:{self.org_name}:users:{resource_id}"
        else:
            return resource_id

    def sync_resource_owners(self, resource_orns: List[str] = None) -> Dict:
        """Sync resource owners from Okta"""
        print("="*80)
        print("SYNC RESOURCE OWNER MAPPINGS FROM OKTA")
        print("="*80)
        print()

        assignments = {
            "apps": [],
            "groups": [],
            "entitlement_bundles": []
        }

        if resource_orns:
            # Sync specific resources provided by user
            print(f"Syncing owners for {len(resource_orns)} specified resources...")
            for orn in resource_orns:
                self._sync_single_resource(orn, assignments)
        else:
            # Sync all resources
            print("Syncing owners for all resources (apps, groups, entitlement bundles)...")

            # Sync apps
            apps = self.get_all_apps()
            for app in apps:
                app_id = app.get("id")
                app_name = app.get("label", app.get("name", "Unknown"))
                app_sign_on_mode = app.get("signOnMode", "oauth2")

                # Map signOnMode to app type for ORN
                app_type_map = {
                    "SAML_2_0": "saml2",
                    "OPENID_CONNECT": "oauth2",
                    "AUTO_LOGIN": "swa",
                    "BROWSER_PLUGIN": "swa"
                }
                app_type = app_type_map.get(app_sign_on_mode, "oauth2")

                orn = self.build_orn(app_id, "app", app_type)
                self._sync_single_resource(orn, assignments, resource_name=app_name, resource_type_override="apps", app_type=app_type)

            # Sync groups
            groups = self.get_all_groups()
            for group in groups:
                group_id = group.get("id")
                group_name = group.get("profile", {}).get("name", "Unknown")
                orn = self.build_orn(group_id, "group")
                self._sync_single_resource(orn, assignments, resource_name=group_name, resource_type_override="groups")

            # Sync entitlement bundles
            bundles = self.get_all_entitlement_bundles()
            for bundle in bundles:
                bundle_id = bundle.get("bundleId")
                bundle_name = bundle.get("name", "Unknown")
                orn = self.build_orn(bundle_id, "entitlement_bundle")
                self._sync_single_resource(orn, assignments, resource_name=bundle_name, resource_type_override="entitlement_bundles")

        return assignments

    def _sync_single_resource(self, resource_orn: str, assignments: Dict, resource_name: str = None, resource_type_override: str = None, app_type: str = None):
        """Sync owners for a single resource"""
        owners_data = self.get_resource_owners(resource_orn)

        if not owners_data:
            return

        # Determine resource type from ORN
        if resource_type_override:
            resource_type = resource_type_override
        elif ":apps:" in resource_orn:
            resource_type = "apps"
        elif ":groups:" in resource_orn:
            resource_type = "groups"
        elif ":entitlement-bundles:" in resource_orn:
            resource_type = "entitlement_bundles"
        else:
            return

        # Extract owner information
        owners = []
        for owner_data in owners_data:
            principals = owner_data.get("principals", [])
            for principal in principals:
                principal_orn = principal.get("principalOrn", "")
                principal_type = principal.get("principalType", "user").lower()

                # Get principal name/email
                principal_name = principal.get("principalName", "")
                if not principal_name:
                    # Try to extract from principalOrn
                    if ":users:" in principal_orn:
                        principal_name = principal_orn.split(":")[-1]
                    elif ":groups:" in principal_orn:
                        principal_name = principal_orn.split(":")[-1]

                owners.append({
                    "principal_orn": principal_orn,
                    "principal_type": principal_type,
                    "principal_name": principal_name
                })

        if owners:
            resource_entry = {
                "resource_orn": resource_orn,
                "resource_name": resource_name or "Unknown",
                "owners": owners
            }

            if resource_type == "apps":
                resource_entry["resource_type"] = app_type or "oauth2"

            assignments[resource_type].append(resource_entry)
            print(f"  ✅ {resource_name or resource_orn}: {len(owners)} owner(s)")

    def save_mappings(self, assignments: Dict, output_file: str):
        """Save owner mappings to file"""
        print(f"\nSaving owner mappings to {output_file}...")

        mappings = {
            "description": "Resource Owner mappings synced from Okta OIG",
            "last_synced": datetime.utcnow().isoformat() + "Z",
            "version": "1.0",
            "assignments": assignments,
            "notes": [
                "This file is the source of truth for resource owner assignments",
                "To add a new owner assignment, submit a PR adding the owner to the appropriate resource",
                "Run 'python3 scripts/apply_resource_owners.py' or the GitHub Actions workflow to apply changes to Okta",
                "Run 'python3 scripts/sync_owner_mappings.py' to sync this file from Okta",
                "Owner types:",
                "  - user: Individual user ownership (orn:okta:directory:<org>:users:<id>)",
                "  - group: Delegated group ownership (orn:okta:directory:<org>:groups:<id>)",
                "Resource types:",
                "  - apps: Applications (oauth2, saml2, etc.)",
                "  - groups: Okta groups",
                "  - entitlement_bundles: OIG entitlement bundles"
            ]
        }

        with open(output_file, 'w') as f:
            json.dump(mappings, f, indent=2)
        print(f"  ✅ Saved successfully")

        return mappings

    def sync(self, output_file: str, resource_orns: List[str] = None) -> bool:
        """Run the complete sync process"""
        # Sync owners
        assignments = self.sync_resource_owners(resource_orns)

        # Save to file
        mappings = self.save_mappings(assignments, output_file)

        # Summary
        total_apps = len(assignments["apps"])
        total_groups = len(assignments["groups"])
        total_bundles = len(assignments["entitlement_bundles"])
        total_resources = total_apps + total_groups + total_bundles

        print("\n" + "="*80)
        print("SYNC SUMMARY")
        print("="*80)
        print(f"  Apps with owners: {total_apps}")
        print(f"  Groups with owners: {total_groups}")
        print(f"  Entitlement bundles with owners: {total_bundles}")
        print(f"  Total resources with owners: {total_resources}")
        print(f"  Output file: {output_file}")
        print("="*80)

        return True


def main():
    parser = argparse.ArgumentParser(
        description="Sync resource owner mappings from Okta to local config"
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
        default="config/owner_mappings.json",
        help="Output file path"
    )
    parser.add_argument(
        "--resource-orns",
        nargs="+",
        help="Specific resource ORNs to sync (optional, syncs all if not provided)"
    )

    args = parser.parse_args()

    if not args.org_name or not args.api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN must be set")
        sys.exit(1)

    syncer = OwnerMappingSync(args.org_name, args.base_url, args.api_token)
    success = syncer.sync(args.output, args.resource_orns)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
