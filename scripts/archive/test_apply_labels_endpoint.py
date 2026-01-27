#!/usr/bin/env python3
"""
Test different methods and endpoints for applying labels to resources.
"""

import os
import sys
import json
import requests


def test_apply_endpoints(org_name: str, base_url: str, api_token: str):
    """Test various patterns for applying labels"""

    base = f"https://{org_name}.{base_url}"
    headers = {
        "Authorization": f"SSWS {api_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Known values
    label_id = "lbc11keklyNa6KhMi1d7"  # Privileged
    label_value_id = "lbl11keklzHO41LJ11d7"
    # Use a test entitlement bundle ORN
    test_orn = "orn:okta:governance:00omx5xxhePEbjFNp1d7:entitlement-bundles:enb12zcvwl8qvb6Xv1d7"

    print("="*80)
    print("TESTING LABEL APPLICATION ENDPOINTS")
    print("="*80)
    print(f"Label ID: {label_id}")
    print(f"Label Value ID: {label_value_id}")
    print(f"Test ORN: {test_orn}")
    print()

    tests = [
        # Test 1: PUT /labels/{labelId}/resources
        {
            "name": "PUT /labels/{labelId}/resources",
            "method": "PUT",
            "url": f"{base}/governance/api/v1/labels/{label_id}/resources",
            "payload": {"resourceOrns": [test_orn]}
        },
        # Test 2: POST /labels/{labelId}/resources
        {
            "name": "POST /labels/{labelId}/resources",
            "method": "POST",
            "url": f"{base}/governance/api/v1/labels/{label_id}/resources",
            "payload": {"resourceOrns": [test_orn]}
        },
        # Test 3: PATCH /labels/{labelId}/resources
        {
            "name": "PATCH /labels/{labelId}/resources",
            "method": "PATCH",
            "url": f"{base}/governance/api/v1/labels/{label_id}/resources",
            "payload": {"resourceOrns": [test_orn]}
        },
        # Test 4: POST /resource-labels
        {
            "name": "POST /resource-labels",
            "method": "POST",
            "url": f"{base}/governance/api/v1/resource-labels",
            "payload": {
                "resourceOrn": test_orn,
                "labelValueIds": [label_value_id]
            }
        },
        # Test 5: PUT /resource-labels
        {
            "name": "PUT /resource-labels",
            "method": "PUT",
            "url": f"{base}/governance/api/v1/resource-labels",
            "payload": {
                "resourceOrn": test_orn,
                "labelValueIds": [label_value_id]
            }
        },
        # Test 6: POST /labels/{labelId}/label-values/{labelValueId}/resources
        {
            "name": "POST /labels/{labelId}/label-values/{labelValueId}/resources",
            "method": "POST",
            "url": f"{base}/governance/api/v1/labels/{label_id}/label-values/{label_value_id}/resources",
            "payload": {"resourceOrns": [test_orn]}
        },
        # Test 7: PUT /labels-assignments
        {
            "name": "PUT /labels-assignments",
            "method": "PUT",
            "url": f"{base}/governance/api/v1/labels-assignments",
            "payload": {
                "labelId": label_id,
                "resourceOrns": [test_orn]
            }
        },
        # Test 8: POST /labels-assignments
        {
            "name": "POST /labels-assignments",
            "method": "POST",
            "url": f"{base}/governance/api/v1/labels-assignments",
            "payload": {
                "labelId": label_id,
                "resourceOrns": [test_orn]
            }
        },
    ]

    for test in tests:
        print(f"Test: {test['name']}")
        print(f"  {test['method']} {test['url']}")
        print(f"  Payload: {json.dumps(test['payload'], indent=4)}")

        try:
            response = requests.request(
                method=test['method'],
                url=test['url'],
                headers=headers,
                json=test['payload'],
                timeout=10
            )

            print(f"  Status Code: {response.status_code}")

            if response.status_code in [200, 201, 204]:
                print(f"  ✅ SUCCESS!")
                if response.text:
                    print(f"  Response: {response.text[:500]}")
            elif response.status_code == 405:
                print(f"  ❌ 405 Method Not Allowed")
                print(f"  Response: {response.text[:300]}")
            elif response.status_code == 404:
                print(f"  ❌ 404 Not Found")
            else:
                print(f"  ⚠️  Status {response.status_code}")
                print(f"  Response: {response.text[:300]}")

        except Exception as e:
            print(f"  ❌ Error: {str(e)[:200]}")

        print()


if __name__ == "__main__":
    org_name = os.environ.get("OKTA_ORG_NAME")
    base_url = os.environ.get("OKTA_BASE_URL", "okta.com")
    api_token = os.environ.get("OKTA_API_TOKEN")

    if not org_name or not api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN must be set")
        sys.exit(1)

    test_apply_endpoints(org_name, base_url, api_token)
