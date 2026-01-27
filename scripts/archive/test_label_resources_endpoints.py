#!/usr/bin/env python3
"""
Test different endpoint patterns for listing resources with labels.

Based on user hint about "list all label resources" API.
"""

import os
import sys
import json
import requests


def test_endpoints(org_name: str, base_url: str, api_token: str):
    """Test various endpoint patterns to find the correct one"""

    base = f"https://{org_name}.{base_url}"
    headers = {
        "Authorization": f"SSWS {api_token}",
        "Accept": "application/json"
    }

    # Label IDs we know exist
    label_ids = {
        "Privileged": "lbc11keklyNa6KhMi1d7",
        "Crown Jewel": "lbc11keklwxBrRatm1d7"
    }

    endpoints_to_try = [
        # Different patterns for listing resources with labels
        "/governance/api/v1/label-resources",
        "/governance/api/v1/labels/resources",
        "/governance/api/v1/resources/labels",
        "/governance/api/v1/resources?includeLabels=true",

        # With specific label ID
        f"/governance/api/v1/label-resources?labelId={label_ids['Privileged']}",
        f"/governance/api/v1/labels/{label_ids['Privileged']}/label-resources",

        # Catalog endpoints that might include labels
        "/governance/api/v1/catalog/label-resources",
        "/governance/api/v1/resources?hasLabel=true",

        # List all labeled resources
        "/governance/api/v1/labeled-resources",
        "/governance/api/v1/resource-labels",
    ]

    print("="*80)
    print("TESTING LABEL RESOURCES ENDPOINTS")
    print("="*80)
    print()

    for endpoint in endpoints_to_try:
        url = f"{base}{endpoint}"
        print(f"Testing: {endpoint}")

        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                print(f"  ✅ SUCCESS!")
                data = response.json()
                print(f"  Response keys: {list(data.keys())}")
                if 'data' in data:
                    print(f"  Data count: {len(data.get('data', []))}")
                    if data.get('data'):
                        print(f"  First item keys: {list(data['data'][0].keys())}")
                        print(f"  First item:")
                        print(json.dumps(data['data'][0], indent=2)[:500])
                print()
            elif response.status_code == 404:
                print(f"  404 Not Found")
            elif response.status_code == 405:
                print(f"  405 Method Not Allowed")
            else:
                print(f"  Response: {response.text[:200]}")
            print()

        except Exception as e:
            print(f"  Error: {str(e)[:100]}")
            print()


if __name__ == "__main__":
    org_name = os.environ.get("OKTA_ORG_NAME")
    base_url = os.environ.get("OKTA_BASE_URL", "okta.com")
    api_token = os.environ.get("OKTA_API_TOKEN")

    if not org_name or not api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN must be set")
        sys.exit(1)

    test_endpoints(org_name, base_url, api_token)
