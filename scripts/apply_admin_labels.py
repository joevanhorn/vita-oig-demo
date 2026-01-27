#!/usr/bin/env python3
"""
apply_admin_labels.py

Queries Okta for entitlements containing "admin" in their names and applies
the "Privileged" label to them.

This script:
1. Queries all entitlements from Okta IGA
2. Filters for entitlements with "admin" in the name (case-insensitive)
3. Applies the "Privileged" label to matching entitlements
4. Reports results

Usage:
    python3 scripts/apply_admin_labels.py
    python3 scripts/apply_admin_labels.py --dry-run
"""

import os
import sys
import json
import requests
import argparse
from typing import List, Dict
import re


class AdminLabelApplier:
    """Applies Privileged label to admin entitlements"""

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
        self.admin_pattern = re.compile(r"admin", re.IGNORECASE)

    def get_privileged_label_info(self) -> Dict:
        """Get the labelId and labelValueId for Privileged label"""
        print("\n" + "="*80)
        print("GETTING PRIVILEGED LABEL INFO")
        print("="*80)

        try:
            url = f"{self.governance_base}/labels"
            response = self.session.get(url)
            response.raise_for_status()

            data = response.json()
            for label in data.get("data", []):
                if label.get("name") == "Privileged":
                    label_id = label.get("labelId")
                    values = label.get("values", [])
                    label_value_id = values[0].get("labelValueId") if values else None

                    print(f"✅ Found Privileged label:")
                    print(f"   labelId: {label_id}")
                    print(f"   labelValueId: {label_value_id}")

                    return {
                        "labelId": label_id,
                        "labelValueId": label_value_id,
                        "name": "Privileged"
                    }

            print("❌ Privileged label not found in environment")
            return None

        except Exception as e:
            print(f"❌ Error getting label info: {e}")
            return None

    def query_all_entitlements(self) -> List[Dict]:
        """Query all entitlement bundles from Okta"""
        print("\n" + "="*80)
        print("QUERYING ENTITLEMENT BUNDLES")
        print("="*80)

        try:
            # Use the entitlement bundles endpoint
            url = f"{self.governance_base}/entitlement-bundles"
            params = {"limit": 200}

            response = self.session.get(url, params=params)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                bundles = data.get("data", [])
                print(f"✅ Found {len(bundles)} entitlement bundles")
                return bundles
            elif response.status_code == 404:
                print("⚠️  Entitlement bundles endpoint not found")
                print("   OIG may not be fully configured")
                return []
            else:
                response.raise_for_status()
                return []

        except Exception as e:
            print(f"❌ Error querying entitlements: {e}")
            return []

    def find_admin_entitlements(self, bundles: List[Dict]) -> List[Dict]:
        """Filter bundles for those containing 'admin' in the name"""
        print("\n" + "="*80)
        print("FILTERING FOR ADMIN ENTITLEMENTS")
        print("="*80)

        admin_bundles = []
        for bundle in bundles:
            name = bundle.get("name", "")
            description = bundle.get("description", "")

            # Check if "admin" appears in name or description
            if self.admin_pattern.search(name) or self.admin_pattern.search(description):
                admin_bundles.append(bundle)
                print(f"  ✅ {name}")
                print(f"     ID: {bundle.get('id')}")
                print(f"     ORN: {bundle.get('orn')}")
                print()

        if not admin_bundles:
            print("  ℹ️  No entitlements with 'admin' found")
        else:
            print(f"Found {len(admin_bundles)} admin entitlements")

        return admin_bundles

    def apply_labels(self, label_info: Dict, bundles: List[Dict]) -> Dict:
        """Apply Privileged label to entitlement bundles"""
        print("\n" + "="*80)
        if self.dry_run:
            print("DRY RUN - WOULD APPLY LABELS")
        else:
            print("APPLYING LABELS")
        print("="*80)

        if not bundles:
            print("  ℹ️  No entitlements to label")
            return {"applied": 0, "failed": 0, "skipped": 0}

        label_value_id = label_info.get("labelValueId")
        resource_orns = [bundle.get("orn") for bundle in bundles if bundle.get("orn")]

        if not resource_orns:
            print("  ⚠️  No valid ORNs found for entitlements")
            return {"applied": 0, "failed": 0, "skipped": len(bundles)}

        print(f"\nLabel: Privileged (labelValueId: {label_value_id})")
        print(f"Resources: {len(resource_orns)}")
        print()

        for orn in resource_orns:
            print(f"  • {orn}")
        print()

        if self.dry_run:
            print("🔍 DRY RUN - Skipping actual API call")
            return {"applied": 0, "failed": 0, "skipped": len(resource_orns), "dry_run": True}

        try:
            # Apply labels in batches of 10 (API limit)
            url = f"{self.governance_base}/resource-labels/assign"
            batch_size = 10
            total_applied = 0
            total_failed = 0

            for i in range(0, len(resource_orns), batch_size):
                batch = resource_orns[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(resource_orns) + batch_size - 1) // batch_size

                print(f"Batch {batch_num}/{total_batches}: {len(batch)} resources")

                payload = {
                    "resourceOrns": batch,
                    "labelValueIds": [label_value_id]
                }

                response = self.session.post(url, json=payload)
                print(f"  Status Code: {response.status_code}")

                if response.status_code in [200, 201, 204]:
                    print(f"  ✅ Success")
                    total_applied += len(batch)
                    if response.text:
                        print(f"  Response: {response.text[:300]}")
                else:
                    print(f"  ❌ Failed")
                    print(f"  Response: {response.text[:300]}")
                    total_failed += len(batch)

                print()

            if total_applied > 0:
                print(f"✅ Successfully applied Privileged label to {total_applied} entitlements")
            if total_failed > 0:
                print(f"❌ Failed to apply labels to {total_failed} entitlements")

            return {"applied": total_applied, "failed": total_failed, "skipped": 0}

        except Exception as e:
            print(f"❌ Error applying labels: {e}")
            return {"applied": 0, "failed": len(resource_orns), "skipped": 0}

    def run(self) -> Dict:
        """Run the complete admin labeling process"""
        print("\n" + "="*80)
        print("APPLY PRIVILEGED LABELS TO ADMIN ENTITLEMENTS")
        print("="*80)
        print(f"Organization: {self.org_name}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'APPLY'}")
        print("="*80)

        results = {
            "label_found": False,
            "bundles_queried": 0,
            "admin_bundles_found": 0,
            "labels_applied": 0,
            "labels_failed": 0,
            "labels_skipped": 0,
            "dry_run": self.dry_run
        }

        # Step 1: Get Privileged label info
        label_info = self.get_privileged_label_info()
        if not label_info:
            print("\n❌ Cannot proceed without Privileged label")
            return results

        results["label_found"] = True

        # Step 2: Query all entitlement bundles
        bundles = self.query_all_entitlements()
        results["bundles_queried"] = len(bundles)

        if not bundles:
            print("\n⚠️  No entitlement bundles found - nothing to label")
            return results

        # Step 3: Filter for admin entitlements
        admin_bundles = self.find_admin_entitlements(bundles)
        results["admin_bundles_found"] = len(admin_bundles)

        if not admin_bundles:
            print("\n✅ No admin entitlements to label")
            return results

        # Step 4: Apply labels
        apply_results = self.apply_labels(label_info, admin_bundles)
        results["labels_applied"] = apply_results.get("applied", 0)
        results["labels_failed"] = apply_results.get("failed", 0)
        results["labels_skipped"] = apply_results.get("skipped", 0)

        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"  Entitlement bundles queried: {results['bundles_queried']}")
        print(f"  Admin entitlements found: {results['admin_bundles_found']}")
        if self.dry_run:
            print(f"  Labels that would be applied: {results['admin_bundles_found']}")
        else:
            print(f"  Labels applied: {results['labels_applied']}")
            print(f"  Labels failed: {results['labels_failed']}")
            print(f"  Labels skipped: {results['labels_skipped']}")
        print("="*80)

        return results


def main():
    parser = argparse.ArgumentParser(
        description="Apply Privileged labels to admin entitlements"
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
        "--dry-run",
        action="store_true",
        help="Show what would be labeled without applying"
    )

    args = parser.parse_args()

    if not args.org_name or not args.api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN must be set")
        sys.exit(1)

    applier = AdminLabelApplier(
        args.org_name,
        args.base_url,
        args.api_token,
        dry_run=args.dry_run
    )
    results = applier.run()

    # Save results
    output_file = "admin_labels_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Results saved to: {output_file}\n")

    # Exit with appropriate code
    if not results["label_found"]:
        sys.exit(1)
    if results["labels_failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
