#!/bin/bash
# build_test_org.sh
# Creates sample Okta resources for testing Terraformer import functionality

set -e

echo "============================================="
echo "  Build Test Okta Org for Terraformer"
echo "============================================="
echo ""

# Check environment variables
if [ -z "$OKTA_API_TOKEN" ] || [ -z "$OKTA_ORG_NAME" ] || [ -z "$OKTA_BASE_URL" ]; then
    echo "❌ Error: Required environment variables not set"
    echo ""
    echo "Please set:"
    echo "  export OKTA_API_TOKEN='your-token'"
    echo "  export OKTA_ORG_NAME='your-org-name'"
    echo "  export OKTA_BASE_URL='okta.com'"
    exit 1
fi

BASE_URL="https://${OKTA_ORG_NAME}.${OKTA_BASE_URL}"
HEADERS="Authorization: SSWS ${OKTA_API_TOKEN}"

echo "Creating test resources in: ${BASE_URL}"
echo ""

# ============================================
# Create Users
# ============================================
echo "Creating test users..."

# User 1: John Doe (Engineering)
USER1=$(curl -s -X POST "${BASE_URL}/api/v1/users?activate=true" \
  -H "${HEADERS}" \
  -H "Content-Type: application/json" \
  -d '{
    "profile": {
      "firstName": "John",
      "lastName": "Doe",
      "email": "john.doe@example.com",
      "login": "john.doe@example.com",
      "mobilePhone": "+14155551234",
      "department": "Engineering",
      "title": "Senior Software Engineer",
      "city": "San Francisco",
      "state": "CA",
      "countryCode": "US"
    },
    "credentials": {
      "password": {"value": "TempPass123!"}
    }
  }' | jq -r '.id')

echo "✓ Created user: john.doe@example.com (${USER1})"

# User 2: Jane Smith (Sales)
USER2=$(curl -s -X POST "${BASE_URL}/api/v1/users?activate=true" \
  -H "${HEADERS}" \
  -H "Content-Type: application/json" \
  -d '{
    "profile": {
      "firstName": "Jane",
      "lastName": "Smith",
      "email": "jane.smith@example.com",
      "login": "jane.smith@example.com",
      "mobilePhone": "+15125559876",
      "department": "Sales",
      "title": "Account Executive",
      "city": "Austin",
      "state": "TX",
      "countryCode": "US"
    },
    "credentials": {
      "password": {"value": "TempPass123!"}
    }
  }' | jq -r '.id')

echo "✓ Created user: jane.smith@example.com (${USER2})"

# User 3: Bob Johnson (Security)
USER3=$(curl -s -X POST "${BASE_URL}/api/v1/users?activate=true" \
  -H "${HEADERS}" \
  -H "Content-Type: application/json" \
  -d '{
    "profile": {
      "firstName": "Bob",
      "lastName": "Johnson",
      "email": "bob.johnson@example.com",
      "login": "bob.johnson@example.com",
      "mobilePhone": "+16175554321",
      "department": "Security",
      "title": "Security Engineer",
      "city": "Boston",
      "state": "MA",
      "countryCode": "US"
    },
    "credentials": {
      "password": {"value": "TempPass123!"}
    }
  }' | jq -r '.id')

echo "✓ Created user: bob.johnson@example.com (${USER3})"

echo ""

# ============================================
# Create Groups
# ============================================
echo "Creating test groups..."

# Group 1: Engineering Team
GROUP1=$(curl -s -X POST "${BASE_URL}/api/v1/groups" \
  -H "${HEADERS}" \
  -H "Content-Type: application/json" \
  -d '{
    "profile": {
      "name": "Engineering Team",
      "description": "Engineering team members with access to development resources"
    }
  }' | jq -r '.id')

echo "✓ Created group: Engineering Team (${GROUP1})"

# Group 2: Sales Team
GROUP2=$(curl -s -X POST "${BASE_URL}/api/v1/groups" \
  -H "${HEADERS}" \
  -H "Content-Type: application/json" \
  -d '{
    "profile": {
      "name": "Sales Team",
      "description": "Sales team members"
    }
  }' | jq -r '.id')

echo "✓ Created group: Sales Team (${GROUP2})"

# Group 3: Security Team
GROUP3=$(curl -s -X POST "${BASE_URL}/api/v1/groups" \
  -H "${HEADERS}" \
  -H "Content-Type: application/json" \
  -d '{
    "profile": {
      "name": "Security Team",
      "description": "Security team with access to security tools"
    }
  }' | jq -r '.id')

echo "✓ Created group: Security Team (${GROUP3})"

# Group 4: All Employees
GROUP4=$(curl -s -X POST "${BASE_URL}/api/v1/groups" \
  -H "${HEADERS}" \
  -H "Content-Type: application/json" \
  -d '{
    "profile": {
      "name": "All Employees",
      "description": "All company employees"
    }
  }' | jq -r '.id')

echo "✓ Created group: All Employees (${GROUP4})"

echo ""

# ============================================
# Add Users to Groups
# ============================================
echo "Adding users to groups..."

# Add John to Engineering Team
curl -s -X PUT "${BASE_URL}/api/v1/groups/${GROUP1}/users/${USER1}" \
  -H "${HEADERS}" > /dev/null
echo "✓ Added John Doe to Engineering Team"

# Add Jane to Sales Team
curl -s -X PUT "${BASE_URL}/api/v1/groups/${GROUP2}/users/${USER2}" \
  -H "${HEADERS}" > /dev/null
echo "✓ Added Jane Smith to Sales Team"

# Add Bob to Security Team
curl -s -X PUT "${BASE_URL}/api/v1/groups/${GROUP3}/users/${USER3}" \
  -H "${HEADERS}" > /dev/null
echo "✓ Added Bob Johnson to Security Team"

# Add all users to All Employees
curl -s -X PUT "${BASE_URL}/api/v1/groups/${GROUP4}/users/${USER1}" \
  -H "${HEADERS}" > /dev/null
curl -s -X PUT "${BASE_URL}/api/v1/groups/${GROUP4}/users/${USER2}" \
  -H "${HEADERS}" > /dev/null
curl -s -X PUT "${BASE_URL}/api/v1/groups/${GROUP4}/users/${USER3}" \
  -H "${HEADERS}" > /dev/null
echo "✓ Added all users to All Employees"

echo ""

# ============================================
# Create OAuth Applications
# ============================================
echo "Creating test OAuth applications..."

# App 1: Internal CRM
APP1=$(curl -s -X POST "${BASE_URL}/api/v1/apps" \
  -H "${HEADERS}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "oidc_client",
    "label": "Internal CRM System",
    "signOnMode": "OPENID_CONNECT",
    "credentials": {
      "oauthClient": {
        "autoKeyRotation": true,
        "token_endpoint_auth_method": "client_secret_basic"
      }
    },
    "settings": {
      "oauthClient": {
        "client_uri": "https://internalcrm.example.com",
        "logo_uri": null,
        "redirect_uris": [
          "https://internalcrm.example.com/callback"
        ],
        "post_logout_redirect_uris": [
          "https://internalcrm.example.com/logout"
        ],
        "response_types": [
          "code"
        ],
        "grant_types": [
          "authorization_code",
          "refresh_token"
        ],
        "application_type": "web",
        "consent_method": "REQUIRED",
        "issuer_mode": "ORG_URL"
      }
    }
  }' | jq -r '.id')

echo "✓ Created app: Internal CRM System (${APP1})"

# App 2: Project Management
APP2=$(curl -s -X POST "${BASE_URL}/api/v1/apps" \
  -H "${HEADERS}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "oidc_client",
    "label": "Project Management Tool",
    "signOnMode": "OPENID_CONNECT",
    "credentials": {
      "oauthClient": {
        "autoKeyRotation": true,
        "token_endpoint_auth_method": "client_secret_basic"
      }
    },
    "settings": {
      "oauthClient": {
        "client_uri": "https://projectmanagement.example.com",
        "redirect_uris": [
          "https://projectmanagement.example.com/callback"
        ],
        "post_logout_redirect_uris": [
          "https://projectmanagement.example.com/logout"
        ],
        "response_types": [
          "code"
        ],
        "grant_types": [
          "authorization_code",
          "refresh_token"
        ],
        "application_type": "web",
        "consent_method": "REQUIRED",
        "issuer_mode": "ORG_URL"
      }
    }
  }' | jq -r '.id')

echo "✓ Created app: Project Management Tool (${APP2})"

echo ""

# ============================================
# Assign Groups to Applications
# ============================================
echo "Assigning groups to applications..."

# Assign Engineering Team to CRM
curl -s -X PUT "${BASE_URL}/api/v1/apps/${APP1}/groups/${GROUP1}" \
  -H "${HEADERS}" \
  -H "Content-Type: application/json" \
  -d '{}' > /dev/null
echo "✓ Assigned Engineering Team to Internal CRM"

# Assign Sales Team to CRM
curl -s -X PUT "${BASE_URL}/api/v1/apps/${APP1}/groups/${GROUP2}" \
  -H "${HEADERS}" \
  -H "Content-Type: application/json" \
  -d '{}' > /dev/null
echo "✓ Assigned Sales Team to Internal CRM"

# Assign All Employees to Project Management
curl -s -X PUT "${BASE_URL}/api/v1/apps/${APP2}/groups/${GROUP4}" \
  -H "${HEADERS}" \
  -H "Content-Type: application/json" \
  -d '{}' > /dev/null
echo "✓ Assigned All Employees to Project Management Tool"

echo ""

# ============================================
# Create Network Zone
# ============================================
echo "Creating test network zone..."

ZONE1=$(curl -s -X POST "${BASE_URL}/api/v1/zones" \
  -H "${HEADERS}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "IP",
    "name": "Corporate Network",
    "gateways": [
      {
        "type": "CIDR",
        "value": "192.168.1.0/24"
      },
      {
        "type": "CIDR",
        "value": "10.0.0.0/8"
      }
    ],
    "proxies": null
  }' | jq -r '.id')

echo "✓ Created network zone: Corporate Network (${ZONE1})"

echo ""

# ============================================
# Summary
# ============================================
echo "============================================="
echo "✅ Test org build complete!"
echo "============================================="
echo ""
echo "📊 Created Resources:"
echo ""
echo "Users:"
echo "  - john.doe@example.com (${USER1})"
echo "  - jane.smith@example.com (${USER2})"
echo "  - bob.johnson@example.com (${USER3})"
echo ""
echo "Groups:"
echo "  - Engineering Team (${GROUP1})"
echo "  - Sales Team (${GROUP2})"
echo "  - Security Team (${GROUP3})"
echo "  - All Employees (${GROUP4})"
echo ""
echo "Applications:"
echo "  - Internal CRM System (${APP1})"
echo "  - Project Management Tool (${APP2})"
echo ""
echo "Network Zones:"
echo "  - Corporate Network (${ZONE1})"
echo ""
echo "🧪 Now you can test Terraformer import:"
echo ""
echo "  terraformer import okta --resources=okta_user,okta_group,okta_app_oauth,okta_network_zone"
echo ""
echo "📋 Or use the automated script:"
echo ""
echo "  ./scripts/import_okta_resources.sh"
echo ""
