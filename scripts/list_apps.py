#!/usr/bin/env python3
"""
List all applications in the Okta tenant.
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.okta_api_manager import OktaAPIManager

def main():
    # Get credentials from environment
    org_name = os.environ.get("OKTA_ORG_NAME")
    base_url = os.environ.get("OKTA_BASE_URL", "okta.com")
    api_token = os.environ.get("OKTA_API_TOKEN")

    if not org_name or not api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN must be set")
        sys.exit(1)

    manager = OktaAPIManager(
        org_name=org_name,
        base_url=base_url,
        api_token=api_token
    )

    # Get all apps
    url = f"{manager.base_url}/api/v1/apps"
    response = manager.session.get(url)
    response.raise_for_status()
    apps = response.json()

    print(f"Found {len(apps)} applications in {org_name}:")
    print("=" * 100)
    print(f"{'ID':<25} {'Label':<40} {'Sign-On Mode':<20} {'Status':<10}")
    print("=" * 100)

    for app in apps:
        app_id = app.get('id', 'N/A')
        label = app.get('label', 'N/A')
        sign_on_mode = app.get('signOnMode', 'N/A')
        status = app.get('status', 'N/A')

        print(f"{app_id:<25} {label:<40} {sign_on_mode:<20} {status:<10}")

    print("=" * 100)
    print(f"\nTotal: {len(apps)} applications")

if __name__ == "__main__":
    main()
