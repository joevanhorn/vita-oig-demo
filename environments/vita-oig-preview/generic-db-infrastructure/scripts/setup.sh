#!/bin/bash
# Generic Database Connector ("HR System") - Post-deployment Setup
# Run this after `terraform apply` to initialize the HR schema and seed data.
#
# Requires: awscli, jq, and psql (PostgreSQL client) with network access to the
# RDS endpoint (it is publicly accessible in the demo).

set -e

# Configuration
REGION="${AWS_REGION:-us-east-1}"
SECRET_NAME="${SECRET_NAME:-vita-oig-preview-use1-generic-db-credentials}"
SCHEMA_FILE="$(dirname "$0")/schema.sql"

echo "=========================================="
echo "VITA HR System - Generic DB Connector Setup"
echo "=========================================="
echo ""

# Get credentials from Secrets Manager
echo "1. Fetching credentials from Secrets Manager ($SECRET_NAME)..."
CREDS=$(aws secretsmanager get-secret-value \
  --secret-id "$SECRET_NAME" \
  --region "$REGION" \
  --query SecretString \
  --output text)

DB_HOST=$(echo "$CREDS" | jq -r '.host')
DB_PORT=$(echo "$CREDS" | jq -r '.port')
DB_NAME=$(echo "$CREDS" | jq -r '.database')
DB_USER=$(echo "$CREDS" | jq -r '.username')
DB_PASS=$(echo "$CREDS" | jq -r '.password')

echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   Database: $DB_NAME"
echo "   Username: $DB_USER"
echo ""

# Test connection
echo "2. Testing database connection..."
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1 AS connected;" > /dev/null
echo "   Connection successful!"
echo ""

# Initialize schema
echo "3. Initializing HR schema and seed data..."
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$SCHEMA_FILE"
echo ""

# Verify
echo "4. Verifying setup..."
echo ""
echo "   Users:"
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT user_id, username, email, department, status FROM users ORDER BY user_id;"
echo ""
echo "   Entitlements:"
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT entitlement_id, name, category, risk_level FROM entitlements ORDER BY entitlement_id;"
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "JDBC URL for OPC / Generic Database Connector configuration:"
echo "jdbc:postgresql://$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "Next Steps:"
echo "1. Connect to the OPC agent (SSM) and run the OPP installer (see /installers/SETUP.md)."
echo "2. Create the 'On-prem Connector for Generic Databases' app in Okta Admin Console."
echo "3. Configure provisioning SQL queries (see SQL_QUERIES.md)."
echo ""
