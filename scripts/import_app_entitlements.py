#!/usr/bin/env python3
"""
Import all entitlements from applications (not just those in bundles).

This script:
1. Lists all applications
2. For each app, queries all entitlements
3. For each entitlement, gets all values
4. Exports to JSON for analysis and labeling

Usage:
    python3 scripts/import_app_entitlements.py --output environments/lowerdecklabs/imports/all_entitlements.json
"""

import argparse
import json
import os
import sys
import requests
from urllib.parse import quote
from typing import List, Dict

def fetch_all_apps(org_name: str, base_url: str, token: str) -> List[Dict]:
    """Fetch all applications from Okta."""

    url = f'https://{org_name}.{base_url}/api/v1/apps'
    headers = {
        'Authorization': f'SSWS {token}',
        'Accept': 'application/json'
    }

    print("Fetching all applications...")
    apps = []

    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching apps: {response.status_code}")
            print(response.text)
            break

        apps.extend(response.json())

        # Check for pagination
        links = response.links
        url = links.get('next', {}).get('url') if links else None

    print(f"  Found {len(apps)} applications")
    return apps

def fetch_entitlements_for_app(app_id: str, org_name: str, base_url: str, token: str) -> List[Dict]:
    """Fetch all entitlements for a specific app."""

    filter_query = f'parent.externalId eq "{app_id}" AND parent.type eq "APPLICATION"'
    encoded_filter = quote(filter_query)

    url = f'https://{org_name}.{base_url}/governance/api/v1/entitlements?filter={encoded_filter}&limit=200'

    headers = {
        'Authorization': f'SSWS {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return []

    data = response.json()
    return data.get('data', [])

def main():
    parser = argparse.ArgumentParser(
        description='Import all entitlements from all applications'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output JSON file path'
    )

    args = parser.parse_args()

    org_name = os.getenv('OKTA_ORG_NAME')
    base_url = os.getenv('OKTA_BASE_URL')
    token = os.getenv('OKTA_API_TOKEN')

    if not all([org_name, base_url, token]):
        print("Error: Missing required environment variables:")
        print("  OKTA_ORG_NAME, OKTA_BASE_URL, OKTA_API_TOKEN")
        sys.exit(1)

    # Fetch all apps
    apps = fetch_all_apps(org_name, base_url, token)

    # For each app, fetch entitlements
    all_app_entitlements = []

    for app in apps:
        app_id = app.get('id')
        app_name = app.get('label')
        app_status = app.get('status')

        print(f"\nProcessing: {app_name} ({app_id}) - Status: {app_status}")

        entitlements = fetch_entitlements_for_app(app_id, org_name, base_url, token)

        if entitlements:
            print(f"  Found {len(entitlements)} entitlements")

            total_values = 0
            for ent in entitlements:
                values_count = len(ent.get('values', []))
                total_values += values_count

            print(f"  Total entitlement values: {total_values}")

            all_app_entitlements.append({
                'app_id': app_id,
                'app_name': app_name,
                'app_label': app.get('label'),
                'app_status': app_status,
                'entitlements': entitlements
            })

    # Save to JSON
    output_data = {
        'imported_at': requests.utils.default_headers()['User-Agent'],  # Timestamp placeholder
        'total_apps': len(apps),
        'apps_with_entitlements': len(all_app_entitlements),
        'app_entitlements': all_app_entitlements
    }

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n{'='*80}")
    print(f"Export complete!")
    print(f"  Total apps: {len(apps)}")
    print(f"  Apps with entitlements: {len(all_app_entitlements)}")
    print(f"  Output: {args.output}")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()
