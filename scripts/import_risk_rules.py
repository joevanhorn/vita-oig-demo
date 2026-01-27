#!/usr/bin/env python3
"""
import_risk_rules.py

Imports risk rules (SOD policies) from Okta OIG to the local config/risk_rules.json file.
This keeps the repository's risk rule configuration up-to-date with the Okta environment.

Usage:
    python3 scripts/import_risk_rules.py
    python3 scripts/import_risk_rules.py --output environments/myorg/config/risk_rules.json
    python3 scripts/import_risk_rules.py --filter 'name sw "Process"'
"""

import os
import sys
import json
import requests
import argparse
from typing import Dict, List
from datetime import datetime


class RiskRuleImporter:
    """Imports risk rules from Okta to local config"""

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

    def get_all_risk_rules(self, filter_expr: str = None, limit: int = 200) -> List[Dict]:
        """
        Fetch all risk rules from Okta

        Args:
            filter_expr: Optional filter (e.g., 'name sw "Process"')
            limit: Results per page (default 200)
        """
        print("="*80)
        print("FETCHING RISK RULES FROM OKTA")
        print("="*80)
        print()

        url = f"{self.governance_base}/risk-rules"
        params = {"limit": limit}

        if filter_expr:
            params["filter"] = filter_expr
            print(f"Applying filter: {filter_expr}")

        all_rules = []
        after = None

        try:
            while True:
                if after:
                    params["after"] = after

                print(f"Fetching risk rules (page {len(all_rules) // limit + 1})...")
                response = self.session.get(url, params=params)
                response.raise_for_status()

                data = response.json()
                rules = data.get("data", [])
                all_rules.extend(rules)

                print(f"  ✅ Retrieved {len(rules)} risk rules")

                # Check for pagination
                next_link = data.get("_links", {}).get("next", {}).get("href")
                if not next_link:
                    break

                # Extract 'after' cursor from next link
                if "after=" in next_link:
                    after = next_link.split("after=")[1].split("&")[0]
                else:
                    break

            print(f"\nTotal risk rules retrieved: {len(all_rules)}")
            return all_rules

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print("  ℹ️  Risk rules API not available (OIG may not be enabled or feature not available)")
                return []
            elif e.response.status_code == 403:
                print("  ❌ Access denied. Ensure API token has 'okta.governance.riskRule.read' scope")
                return []
            else:
                error_msg = str(e)
                try:
                    error_detail = e.response.json()
                    error_msg = error_detail.get("errorSummary", error_msg)
                except:
                    pass
                print(f"  ❌ Error fetching risk rules: {error_msg}")
                return []
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            return []

    def transform_risk_rules(self, raw_rules: List[Dict]) -> List[Dict]:
        """
        Transform raw API response to config file format

        Removes read-only fields like id, created, lastUpdated, etc.
        """
        print("\nTransforming risk rules for config file...")

        transformed_rules = []
        for rule in raw_rules:
            # Only keep fields that can be used for create/update
            transformed_rule = {
                "name": rule.get("name"),
                "description": rule.get("description"),
                "notes": rule.get("notes"),
                "type": rule.get("type"),
                "resources": rule.get("resources", []),
                "conflictCriteria": rule.get("conflictCriteria", {})
            }

            # Clean up None values
            transformed_rule = {k: v for k, v in transformed_rule.items() if v is not None and v != ""}

            # Add metadata as comment for reference
            transformed_rule["_metadata"] = {
                "id": rule.get("id"),
                "status": rule.get("status"),
                "created": rule.get("created"),
                "lastUpdated": rule.get("lastUpdated"),
                "createdBy": rule.get("createdBy"),
                "lastUpdatedBy": rule.get("lastUpdatedBy")
            }

            transformed_rules.append(transformed_rule)
            print(f"  ✅ {rule.get('name')} (ID: {rule.get('id')})")

        return transformed_rules

    def save_to_file(self, rules: List[Dict], output_file: str):
        """Save risk rules to JSON config file"""
        print(f"\nSaving risk rules to {output_file}...")

        config = {
            "description": "Risk rules (Separation of Duties policies) synced from Okta OIG",
            "last_synced": datetime.utcnow().isoformat() + "Z",
            "version": "1.0",
            "rules": rules,
            "notes": [
                "This file manages risk rules (SOD policies) for Access Certifications and Access Requests",
                "Risk rules define criteria for granted principal access that are a risk to your org",
                "To add a new risk rule, submit a PR adding the rule to the 'rules' array",
                "Run 'python3 scripts/apply_risk_rules.py' or the GitHub Actions workflow to apply changes to Okta",
                "Run 'python3 scripts/import_risk_rules.py' to sync this file from Okta",
                "",
                "The '_metadata' field in each rule contains read-only information from Okta:",
                "  - id: Risk rule ID (assigned by Okta, used for updates)",
                "  - status: Current status (ACTIVE, INACTIVE)",
                "  - created/lastUpdated: Timestamps",
                "  - createdBy/lastUpdatedBy: User IDs",
                "",
                "Operations:",
                "  - CONTAINS_ONE: Principal has at least one of the specified entitlements",
                "  - CONTAINS_ALL: Principal has all of the specified entitlements",
                "",
                "API Scopes Required:",
                "  - okta.governance.riskRule.read (for import)",
                "  - okta.governance.riskRule.manage (for apply/delete)"
            ]
        }

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"  ✅ Saved {len(rules)} risk rules")
        return config

    def import_rules(self, output_file: str, filter_expr: str = None) -> bool:
        """Run the complete import process"""
        # Fetch risk rules
        raw_rules = self.get_all_risk_rules(filter_expr=filter_expr)

        if not raw_rules:
            print("\n⚠️  No risk rules found to import")
            # Still save empty file
            self.save_to_file([], output_file)
            return True

        # Transform rules
        transformed_rules = self.transform_risk_rules(raw_rules)

        # Save to file
        self.save_to_file(transformed_rules, output_file)

        # Summary
        print("\n" + "="*80)
        print("IMPORT SUMMARY")
        print("="*80)
        print(f"  Total risk rules imported: {len(transformed_rules)}")
        print(f"  Output file: {output_file}")
        print("="*80)

        return True


def main():
    parser = argparse.ArgumentParser(
        description="Import risk rules from Okta to local config"
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
        default="config/risk_rules.json",
        help="Output file path"
    )
    parser.add_argument(
        "--filter",
        help="Filter expression (e.g., 'name sw \"Process\"' or 'resourceOrn eq \"orn:...\"')"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Results per page (default 200)"
    )

    args = parser.parse_args()

    if not args.org_name or not args.api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN must be set")
        sys.exit(1)

    importer = RiskRuleImporter(args.org_name, args.base_url, args.api_token)
    success = importer.import_rules(args.output, filter_expr=args.filter)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
