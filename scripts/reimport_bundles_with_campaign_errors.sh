#!/bin/bash
#
# Script to remove and re-import entitlement bundles that have stale campaign associations
# causing "Error reading campaign: 404" during terraform refresh
#
# Usage: ./reimport_bundles_with_campaign_errors.sh [environment]
# Example: ./reimport_bundles_with_campaign_errors.sh lowerdecklabs
#

set -e

ENVIRONMENT=${1:-lowerdecklabs}
TERRAFORM_DIR="$(dirname "$0")/../environments/${ENVIRONMENT}/terraform"

if [ ! -d "$TERRAFORM_DIR" ]; then
    echo "❌ Error: Terraform directory not found: $TERRAFORM_DIR"
    exit 1
fi

cd "$TERRAFORM_DIR"

echo "🔍 Working in: $TERRAFORM_DIR"
echo ""

# List of bundles known to have campaign association issues
# Format: terraform_resource_name:bundle_id
BUNDLES_TO_REIMPORT=(
    "okta_entitlement_bundle.purchasing:enb13o2ewjNG3y8LM1d7"
    "okta_entitlement_bundle.datadog_read_only:enb12zbvfgMan9Qak1d7"
    "okta_entitlement_bundle.datadog_standard:enb12zbvfc1Rwq0uN1d7"
    "okta_entitlement_bundle.datadog_admin_role:enb12zcvwl8qvb6Xv1d7"
    "okta_entitlement_bundle.request_report_of_my_company_s_users:enb12x0qhaHpOxq6C1d7"
    "okta_entitlement_bundle.developer_bundle:enb12pob86e9ExVBm1d7"
    "okta_entitlement_bundle.asset_administrator:enb12pob80LpIChdk1d7"
    "okta_entitlement_bundle.it_service_desk_agent_bundle:enb12pmq4gjryR0E31d7"
    "okta_entitlement_bundle.b2b_marketing_role:enb10ufnbov67EfIn1d7"
    "okta_entitlement_bundle.example_bundle:enb10nq3zlAGkuY4F1d7"
    "okta_entitlement_bundle.customer_trial_finance:enbywatjlhTpz7SPd1d6"
    "okta_entitlement_bundle.customer_content_management:enbywatjaevWrlrOJ1d6"
    "okta_entitlement_bundle.sales_associate:enbywatj5ljTAfV0O1d6"
)

echo "📊 Will re-import ${#BUNDLES_TO_REIMPORT[@]} entitlement bundles"
echo ""

# Step 1: Remove from state
echo "🗑️  Step 1: Removing bundles from Terraform state..."
for bundle in "${BUNDLES_TO_REIMPORT[@]}"; do
    resource_name="${bundle%%:*}"
    echo "   Removing: $resource_name"
    terraform state rm "$resource_name" 2>&1 | grep -v "Successfully removed" || true
done
echo "✅ State cleanup complete"
echo ""

# Step 2: Re-import
echo "📥 Step 2: Re-importing bundles with fresh state..."
for bundle in "${BUNDLES_TO_REIMPORT[@]}"; do
    resource_name="${bundle%%:*}"
    bundle_id="${bundle##*:}"
    echo "   Importing: $resource_name (ID: $bundle_id)"
    terraform import "$resource_name" "$bundle_id" 2>&1 | tail -1
done
echo "✅ Import complete"
echo ""

# Step 3: Verify
echo "🔍 Step 3: Verifying state..."
terraform state list | grep "okta_entitlement_bundle" | wc -l | xargs echo "   Total bundles in state:"

echo ""
echo "✅ Re-import complete! Run 'terraform plan' to verify."
echo ""
echo "⚠️  Note: This is a workaround. If bundles are added to campaigns in the future,"
echo "   this issue may recur. Consider filing a bug report with Okta:"
echo "   https://github.com/okta/terraform-provider-okta/issues/new"
