#!/usr/bin/env python3
"""
Create Compliance label with values (SOX, GDPR, PII) and apply SOX to specified apps.

This script:
1. Creates a "Compliance" label with three values: SOX, GDPR, PII
2. Applies the SOX label to Salesforce, Successfactors, Workday, and SAP applications
3. Demonstrates assigning labels to groups and entitlement bundles
"""

import os
import sys
import json
import requests
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.okta_api_manager import OktaAPIManager


def create_compliance_label_with_values(manager: OktaAPIManager) -> Optional[Dict]:
    """
    Create a Compliance label with multiple values (SOX, GDPR, PII).

    Note: Okta's governance label API creates simple labels by default.
    To create a label with multiple values, we need to use the full label creation API.
    """
    url = f"{manager.base_url}/governance/api/v1/labels"

    payload = {
        "name": "Compliance",
        "description": "Compliance framework label for regulatory requirements",
        "values": [
            {
                "name": "SOX",
                "description": "Sarbanes-Oxley Act compliance"
            },
            {
                "name": "GDPR",
                "description": "General Data Protection Regulation compliance"
            },
            {
                "name": "PII",
                "description": "Personally Identifiable Information"
            }
        ]
    }

    try:
        print("Creating Compliance label with values: SOX, GDPR, PII...")
        response = requests.post(
            url,
            headers={
                "Authorization": f"SSWS {manager.api_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        print(f"✅ Created Compliance label!")
        print(f"   Label ID: {result.get('labelId')}")
        print(f"   Values created:")
        for value in result.get('values', []):
            print(f"      - {value.get('name')} (ID: {value.get('labelValueId')})")
        return result
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            print("⚠️  Compliance label already exists. Fetching existing label...")
            return manager.get_label("Compliance")
        else:
            print(f"❌ Error creating label: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
            raise


def get_label_value_id(label_data: Dict, value_name: str) -> Optional[str]:
    """Get the labelValueId for a specific value name"""
    for value in label_data.get('values', []):
        if value.get('name') == value_name:
            return value.get('labelValueId')
    return None


def apply_sox_label_to_apps(manager: OktaAPIManager, label_value_id: str, app_ids: List[str]) -> None:
    """
    Apply SOX label to specified applications.

    Args:
        manager: OktaAPIManager instance
        label_value_id: The labelValueId for SOX
        app_ids: List of application IDs
    """
    # Get the Compliance label ID
    label_id = manager.get_label_id_from_name("Compliance")
    if not label_id:
        raise ValueError("Compliance label not found")

    # Convert app IDs to ORNs (Okta Resource Names)
    org_id = manager.base_url.split('//')[-1].split('.')[0]  # Extract org ID from URL
    resource_orns = [
        f"orn:okta:application:{org_id}:apps:{app_id}"
        for app_id in app_ids
    ]

    # Apply the specific label value (SOX) to the resources
    url = f"{manager.base_url}/governance/api/v1/labels/{label_id}/resources"

    payload = {
        "resourceOrns": resource_orns,
        "labelValueId": label_value_id  # Specify we want the SOX value
    }

    try:
        print(f"\nApplying SOX label to {len(app_ids)} applications...")
        response = requests.put(
            url,
            headers={
                "Authorization": f"SSWS {manager.api_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            json=payload
        )
        response.raise_for_status()
        print("✅ Successfully applied SOX label to applications:")
        for app_id in app_ids:
            print(f"   - {app_id}")
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error applying label: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        raise


def apply_label_to_group(manager: OktaAPIManager, label_value_id: str, group_id: str, value_name: str) -> None:
    """
    Apply a label to a group.

    Args:
        manager: OktaAPIManager instance
        label_value_id: The labelValueId to apply
        group_id: The Okta group ID
        value_name: Name of the label value (for display purposes)
    """
    label_id = manager.get_label_id_from_name("Compliance")
    if not label_id:
        raise ValueError("Compliance label not found")

    # Extract org ID from base URL
    org_id = manager.base_url.split('//')[-1].split('.')[0]
    resource_orn = f"orn:okta:directory:{org_id}:groups:{group_id}"

    url = f"{manager.base_url}/governance/api/v1/labels/{label_id}/resources"

    payload = {
        "resourceOrns": [resource_orn],
        "labelValueId": label_value_id
    }

    try:
        print(f"\nApplying {value_name} label to group {group_id}...")
        response = requests.put(
            url,
            headers={
                "Authorization": f"SSWS {manager.api_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            json=payload
        )
        response.raise_for_status()
        print(f"✅ Successfully applied {value_name} label to group")
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error applying label: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        raise


def apply_label_to_entitlement_bundle(manager: OktaAPIManager, label_value_id: str, bundle_id: str, value_name: str) -> None:
    """
    Apply a label to an entitlement bundle.

    Args:
        manager: OktaAPIManager instance
        label_value_id: The labelValueId to apply
        bundle_id: The entitlement bundle ID
        value_name: Name of the label value (for display purposes)
    """
    label_id = manager.get_label_id_from_name("Compliance")
    if not label_id:
        raise ValueError("Compliance label not found")

    # Extract org ID from base URL
    org_id = manager.base_url.split('//')[-1].split('.')[0]
    resource_orn = f"orn:okta:governance:{org_id}:entitlement-bundles:{bundle_id}"

    url = f"{manager.base_url}/governance/api/v1/labels/{label_id}/resources"

    payload = {
        "resourceOrns": [resource_orn],
        "labelValueId": label_value_id
    }

    try:
        print(f"\nApplying {value_name} label to entitlement bundle {bundle_id}...")
        response = requests.put(
            url,
            headers={
                "Authorization": f"SSWS {manager.api_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            json=payload
        )
        response.raise_for_status()
        print(f"✅ Successfully applied {value_name} label to entitlement bundle")
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error applying label: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        raise


def main():
    """Main execution"""
    # Initialize API manager
    manager = OktaAPIManager()

    print("="*80)
    print("COMPLIANCE LABEL SETUP")
    print("="*80)
    print()

    # Step 1: Create Compliance label with values
    label_data = create_compliance_label_with_values(manager)
    if not label_data:
        print("Failed to create/retrieve Compliance label")
        return 1

    # Step 2: Get SOX label value ID
    sox_value_id = get_label_value_id(label_data, "SOX")
    gdpr_value_id = get_label_value_id(label_data, "GDPR")
    pii_value_id = get_label_value_id(label_data, "PII")

    if not sox_value_id:
        print("❌ SOX value not found in label")
        return 1

    print(f"\nLabel Value IDs:")
    print(f"   SOX:  {sox_value_id}")
    print(f"   GDPR: {gdpr_value_id}")
    print(f"   PII:  {pii_value_id}")

    # Step 3: Apply SOX to the 4 applications
    app_ids = [
        "0oamxiwg4zsrWaeJF1d7",  # Salesforce
        "0oan4ssz4lmqTnQry1d7",  # Successfactors
        "0oaq4iodcifSLp30Q1d7",  # Workday
        "0oan6affwpltdcCci1d7",  # SAP
    ]

    apply_sox_label_to_apps(manager, sox_value_id, app_ids)

    # Step 4: DEMO - Apply PII label to a group (example)
    print("\n" + "="*80)
    print("DEMO: Applying labels to groups and entitlement bundles")
    print("="*80)

    # Example: Apply PII label to a group
    # Uncomment and replace with actual group ID when ready
    # apply_label_to_group(manager, pii_value_id, "00g...", "PII")

    # Example: Apply GDPR label to an entitlement bundle
    # Uncomment and replace with actual bundle ID when ready
    # apply_label_to_entitlement_bundle(manager, gdpr_value_id, "enb...", "GDPR")

    print("\n" + "="*80)
    print("✅ COMPLIANCE LABEL SETUP COMPLETE")
    print("="*80)
    print("\nTo apply labels to groups or entitlement bundles:")
    print("1. Edit this script and uncomment the example calls")
    print("2. Replace the placeholder IDs with actual group/bundle IDs")
    print("3. Run the script again")
    print("\nOr use the apply_label_to_group() and apply_label_to_entitlement_bundle()")
    print("functions programmatically.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
