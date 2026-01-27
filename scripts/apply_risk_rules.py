#!/usr/bin/env python3
"""
apply_risk_rules.py

Applies risk rule (SOD policy) configuration from config/risk_rules.json to Okta.

This script:
1. Reads risk rules from config/risk_rules.json
2. Compares with existing risk rules in Okta
3. Creates new rules, updates existing rules, optionally deletes removed rules
4. Supports dry-run mode to preview changes
5. Reports results

Usage:
    python3 scripts/apply_risk_rules.py
    python3 scripts/apply_risk_rules.py --dry-run
    python3 scripts/apply_risk_rules.py --config config/risk_rules.json
    python3 scripts/apply_risk_rules.py --delete-removed  # Delete rules not in config
"""

import os
import sys
import json
import requests
import argparse
from typing import List, Dict, Tuple


class RiskRuleApplier:
    """Applies risk rule configuration to Okta"""

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

    def load_config(self, config_file: str) -> Dict:
        """Load risk rules from config file"""
        print("\n" + "="*80)
        print("LOADING RISK RULES CONFIG")
        print("="*80)

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)

            rules = config.get("rules", [])
            print(f"✅ Loaded {len(rules)} risk rules from config")

            return config

        except FileNotFoundError:
            print(f"❌ Config file not found: {config_file}")
            return None
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return None

    def get_existing_rules(self) -> Dict[str, Dict]:
        """Fetch existing risk rules from Okta, indexed by name"""
        print("\n" + "="*80)
        print("FETCHING EXISTING RISK RULES FROM OKTA")
        print("="*80)

        url = f"{self.governance_base}/risk-rules"
        params = {"limit": 200}

        all_rules = {}
        after = None

        try:
            while True:
                if after:
                    params["after"] = after

                response = self.session.get(url, params=params)
                response.raise_for_status()

                data = response.json()
                rules = data.get("data", [])

                for rule in rules:
                    rule_name = rule.get("name")
                    all_rules[rule_name] = rule

                # Check for pagination
                next_link = data.get("_links", {}).get("next", {}).get("href")
                if not next_link or not rules:
                    break

                if "after=" in next_link:
                    after = next_link.split("after=")[1].split("&")[0]
                else:
                    break

            print(f"✅ Found {len(all_rules)} existing risk rules in Okta")
            return all_rules

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print("  ℹ️  Risk rules API not available")
                return {}
            elif e.response.status_code == 403:
                print("  ❌ Access denied. Ensure API token has 'okta.governance.riskRule.read' scope")
                return {}
            else:
                print(f"  ⚠️  Error fetching existing rules: {e}")
                return {}
        except Exception as e:
            print(f"  ⚠️  Unexpected error: {e}")
            return {}

    def create_risk_rule(self, rule_config: Dict) -> Dict:
        """Create a new risk rule in Okta"""
        url = f"{self.governance_base}/risk-rules"

        # Remove metadata if present
        rule_payload = {k: v for k, v in rule_config.items() if not k.startswith("_")}

        try:
            if self.dry_run:
                print(f"  [DRY RUN] Would create risk rule: {rule_config.get('name')}")
                return {"status": "dry_run"}

            response = self.session.post(url, json=rule_payload)
            response.raise_for_status()

            created_rule = response.json()
            return {
                "status": "success",
                "rule": created_rule
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

    def update_risk_rule(self, rule_id: str, rule_config: Dict) -> Dict:
        """Update an existing risk rule in Okta"""
        url = f"{self.governance_base}/risk-rules/{rule_id}"

        # Build update payload with required id field
        rule_payload = {
            "id": rule_id,
            **{k: v for k, v in rule_config.items() if not k.startswith("_")}
        }

        try:
            if self.dry_run:
                print(f"  [DRY RUN] Would update risk rule: {rule_config.get('name')} (ID: {rule_id})")
                return {"status": "dry_run"}

            response = self.session.put(url, json=rule_payload)
            response.raise_for_status()

            updated_rule = response.json()
            return {
                "status": "success",
                "rule": updated_rule
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

    def delete_risk_rule(self, rule_id: str, rule_name: str) -> Dict:
        """Delete a risk rule from Okta"""
        url = f"{self.governance_base}/risk-rules/{rule_id}"

        try:
            if self.dry_run:
                print(f"  [DRY RUN] Would delete risk rule: {rule_name} (ID: {rule_id})")
                return {"status": "dry_run"}

            response = self.session.delete(url)
            response.raise_for_status()

            return {"status": "success"}

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

    def plan_changes(self, config_rules: List[Dict], existing_rules: Dict[str, Dict], delete_removed: bool) -> Dict:
        """
        Determine what changes need to be made

        Returns:
            Dictionary with 'create', 'update', 'delete' lists
        """
        print("\n" + "="*80)
        print("PLANNING CHANGES")
        print("="*80)

        changes = {
            "create": [],
            "update": [],
            "delete": []
        }

        # Track which existing rules are matched
        matched_existing = set()

        # Check each config rule
        for config_rule in config_rules:
            rule_name = config_rule.get("name")

            # Check if rule has _metadata.id (from import)
            metadata_id = config_rule.get("_metadata", {}).get("id") if config_rule.get("_metadata") else None

            # Try to find existing rule by name
            if rule_name in existing_rules:
                # Rule exists, plan update
                existing_rule = existing_rules[rule_name]
                existing_id = existing_rule.get("id")
                matched_existing.add(rule_name)

                changes["update"].append({
                    "config": config_rule,
                    "existing_id": existing_id,
                    "existing": existing_rule
                })
                print(f"  📝 UPDATE: {rule_name} (ID: {existing_id})")

            elif metadata_id:
                # Rule has metadata ID but name doesn't match - possible rename
                # Treat as update using the ID from metadata
                matched_existing.add(rule_name)
                changes["update"].append({
                    "config": config_rule,
                    "existing_id": metadata_id,
                    "existing": None  # Don't have the current version
                })
                print(f"  📝 UPDATE: {rule_name} (ID from metadata: {metadata_id})")

            else:
                # Rule doesn't exist, plan create
                changes["create"].append({
                    "config": config_rule
                })
                print(f"  ➕ CREATE: {rule_name}")

        # Find rules to delete (in Okta but not in config)
        if delete_removed:
            for existing_name, existing_rule in existing_rules.items():
                if existing_name not in matched_existing:
                    # Check if any config rule references this by ID
                    existing_id = existing_rule.get("id")
                    id_matched = any(
                        r.get("_metadata", {}).get("id") == existing_id
                        for r in config_rules
                    )

                    if not id_matched:
                        changes["delete"].append({
                            "existing": existing_rule
                        })
                        print(f"  ❌ DELETE: {existing_name} (ID: {existing_rule.get('id')})")

        print(f"\nPlanned changes:")
        print(f"  Create: {len(changes['create'])}")
        print(f"  Update: {len(changes['update'])}")
        print(f"  Delete: {len(changes['delete'])}")

        return changes

    def apply_changes(self, changes: Dict) -> Dict:
        """Execute the planned changes"""
        print("\n" + "="*80)
        if self.dry_run:
            print("APPLYING CHANGES (DRY RUN)")
        else:
            print("APPLYING CHANGES")
        print("="*80)

        results = {
            "create": [],
            "update": [],
            "delete": [],
            "summary": {
                "total": 0,
                "success": 0,
                "errors": 0,
                "dry_run": self.dry_run
            }
        }

        # Create new rules
        if changes["create"]:
            print("\n--- Creating New Risk Rules ---")
            for item in changes["create"]:
                rule_config = item["config"]
                rule_name = rule_config.get("name", "Unknown")

                print(f"\n{rule_name}:")
                result = self.create_risk_rule(rule_config)
                result["rule_name"] = rule_name
                results["create"].append(result)
                results["summary"]["total"] += 1

                if result["status"] == "success":
                    print(f"✅ Created successfully")
                    results["summary"]["success"] += 1
                elif result["status"] == "dry_run":
                    results["summary"]["success"] += 1
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")
                    results["summary"]["errors"] += 1

        # Update existing rules
        if changes["update"]:
            print("\n--- Updating Existing Risk Rules ---")
            for item in changes["update"]:
                rule_config = item["config"]
                existing_id = item["existing_id"]
                rule_name = rule_config.get("name", "Unknown")

                print(f"\n{rule_name} (ID: {existing_id}):")
                result = self.update_risk_rule(existing_id, rule_config)
                result["rule_name"] = rule_name
                result["rule_id"] = existing_id
                results["update"].append(result)
                results["summary"]["total"] += 1

                if result["status"] == "success":
                    print(f"✅ Updated successfully")
                    results["summary"]["success"] += 1
                elif result["status"] == "dry_run":
                    results["summary"]["success"] += 1
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")
                    results["summary"]["errors"] += 1

        # Delete removed rules
        if changes["delete"]:
            print("\n--- Deleting Removed Risk Rules ---")
            for item in changes["delete"]:
                existing_rule = item["existing"]
                rule_id = existing_rule.get("id")
                rule_name = existing_rule.get("name", "Unknown")

                print(f"\n{rule_name} (ID: {rule_id}):")
                result = self.delete_risk_rule(rule_id, rule_name)
                result["rule_name"] = rule_name
                result["rule_id"] = rule_id
                results["delete"].append(result)
                results["summary"]["total"] += 1

                if result["status"] == "success":
                    print(f"✅ Deleted successfully")
                    results["summary"]["success"] += 1
                elif result["status"] == "dry_run":
                    results["summary"]["success"] += 1
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")
                    results["summary"]["errors"] += 1

        return results

    def run(self, config_file: str, delete_removed: bool = False):
        """Main execution"""
        print("="*80)
        if self.dry_run:
            print("RISK RULE APPLIER (DRY RUN MODE)")
        else:
            print("RISK RULE APPLIER")
        print("="*80)

        # Load config
        config = self.load_config(config_file)
        if not config:
            return False

        config_rules = config.get("rules", [])
        if not config_rules:
            print("\n⚠️  No risk rules defined in config file")
            return True

        # Get existing rules from Okta
        existing_rules = self.get_existing_rules()

        # Plan changes
        changes = self.plan_changes(config_rules, existing_rules, delete_removed)

        # Check if there are any changes
        total_changes = len(changes["create"]) + len(changes["update"]) + len(changes["delete"])
        if total_changes == 0:
            print("\n✅ No changes needed - config matches Okta")
            return True

        # Apply changes
        results = self.apply_changes(changes)

        # Print summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total operations: {results['summary']['total']}")
        print(f"  Created: {len(results['create'])}")
        print(f"  Updated: {len(results['update'])}")
        print(f"  Deleted: {len(results['delete'])}")
        print(f"Successful: {results['summary']['success']}")
        print(f"Errors: {results['summary']['errors']}")
        if self.dry_run:
            print("\n⚠️  DRY RUN MODE - No changes were made to Okta")
        print("="*80)

        return results['summary']['errors'] == 0


def main():
    parser = argparse.ArgumentParser(
        description="Apply risk rule configuration from config to Okta"
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
        default="config/risk_rules.json",
        help="Risk rules config file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    parser.add_argument(
        "--delete-removed",
        action="store_true",
        help="Delete risk rules that exist in Okta but not in config (default: false)"
    )

    args = parser.parse_args()

    if not args.org_name or not args.api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN must be set")
        sys.exit(1)

    applier = RiskRuleApplier(
        args.org_name,
        args.base_url,
        args.api_token,
        dry_run=args.dry_run
    )

    success = applier.run(args.config, delete_removed=args.delete_removed)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
