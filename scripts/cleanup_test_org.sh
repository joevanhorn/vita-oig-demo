#!/bin/bash
# cleanup_test_org.sh
# Removes test resources created by build_test_org.sh

set -e

echo "============================================="
echo "  Cleanup Test Okta Org Resources"
echo "============================================="
echo ""

# Check environment variables
if [ -z "$OKTA_API_TOKEN" ] || [ -z "$OKTA_ORG_NAME" ] || [ -z "$OKTA_BASE_URL" ]; then
    echo "❌ Error: Required environment variables not set"
    exit 1
fi

BASE_URL="https://${OKTA_ORG_NAME}.${OKTA_BASE_URL}"
HEADERS="Authorization: SSWS ${OKTA_API_TOKEN}"

echo "⚠️  WARNING: This will DELETE test resources from: ${BASE_URL}"
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Finding and deleting test resources..."
echo ""

# ============================================
# Delete Applications
# ============================================
echo "Deleting test applications..."

# Find apps by label
APPS=$(curl -s "${BASE_URL}/api/v1/apps?limit=200" \
  -H "${HEADERS}" | jq -r '.[] | select(.label | test("Internal CRM System|Project Management Tool")) | .id')

for APP_ID in $APPS; do
    APP_LABEL=$(curl -s "${BASE_URL}/api/v1/apps/${APP_ID}" -H "${HEADERS}" | jq -r '.label')
    
    # Deactivate first
    curl -s -X POST "${BASE_URL}/api/v1/apps/${APP_ID}/lifecycle/deactivate" \
      -H "${HEADERS}" > /dev/null 2>&1 || true
    
    # Then delete
    curl -s -X DELETE "${BASE_URL}/api/v1/apps/${APP_ID}" \
      -H "${HEADERS}" > /dev/null 2>&1
    
    echo "✓ Deleted app: ${APP_LABEL} (${APP_ID})"
done

echo ""

# ============================================
# Delete Users
# ============================================
echo "Deleting test users..."

# Find users by email domain
USERS=$(curl -s "${BASE_URL}/api/v1/users?limit=200" \
  -H "${HEADERS}" | jq -r '.[] | select(.profile.email | test("@example.com")) | .id')

for USER_ID in $USERS; do
    USER_EMAIL=$(curl -s "${BASE_URL}/api/v1/users/${USER_ID}" -H "${HEADERS}" | jq -r '.profile.email')
    
    # Deactivate first
    curl -s -X POST "${BASE_URL}/api/v1/users/${USER_ID}/lifecycle/deactivate" \
      -H "${HEADERS}" > /dev/null 2>&1 || true
    
    # Then delete
    curl -s -X DELETE "${BASE_URL}/api/v1/users/${USER_ID}" \
      -H "${HEADERS}" > /dev/null 2>&1
    
    echo "✓ Deleted user: ${USER_EMAIL} (${USER_ID})"
done

echo ""

# ============================================
# Delete Groups
# ============================================
echo "Deleting test groups..."

# Find groups by name
GROUPS=$(curl -s "${BASE_URL}/api/v1/groups?limit=200" \
  -H "${HEADERS}" | jq -r '.[] | select(.profile.name | test("Engineering Team|Sales Team|Security Team|All Employees")) | .id')

for GROUP_ID in $GROUPS; do
    GROUP_NAME=$(curl -s "${BASE_URL}/api/v1/groups/${GROUP_ID}" -H "${HEADERS}" | jq -r '.profile.name')
    
    curl -s -X DELETE "${BASE_URL}/api/v1/groups/${GROUP_ID}" \
      -H "${HEADERS}" > /dev/null 2>&1
    
    echo "✓ Deleted group: ${GROUP_NAME} (${GROUP_ID})"
done

echo ""

# ============================================
# Delete Network Zones
# ============================================
echo "Deleting test network zones..."

# Find zones by name
ZONES=$(curl -s "${BASE_URL}/api/v1/zones?limit=200" \
  -H "${HEADERS}" | jq -r '.[] | select(.name | test("Corporate Network")) | .id')

for ZONE_ID in $ZONES; do
    ZONE_NAME=$(curl -s "${BASE_URL}/api/v1/zones/${ZONE_ID}" -H "${HEADERS}" | jq -r '.name')
    
    # Deactivate first
    curl -s -X POST "${BASE_URL}/api/v1/zones/${ZONE_ID}/lifecycle/deactivate" \
      -H "${HEADERS}" > /dev/null 2>&1 || true
    
    # Then delete
    curl -s -X DELETE "${BASE_URL}/api/v1/zones/${ZONE_ID}" \
      -H "${HEADERS}" > /dev/null 2>&1
    
    echo "✓ Deleted zone: ${ZONE_NAME} (${ZONE_ID})"
done

echo ""
echo "============================================="
echo "✅ Cleanup complete!"
echo "============================================="
echo ""
