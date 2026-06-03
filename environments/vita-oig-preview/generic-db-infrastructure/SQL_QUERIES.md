# Generic DB Connector - SQL Queries

SQL queries for the Okta "On-prem Connector for Generic Databases" provisioning configuration.

> **CRITICAL: Downstream provisioning (Provisioning to App) MUST be enabled for entitlement import to work.** Without it, Okta silently ignores entitlement data — imports succeed and users appear, but `ent-*` attributes are never created on user profiles. You must enable "Provisioning to App" AND configure the Update User SQL query before entitlements will be imported. This is undocumented by Okta.

## Import Users (Get All Users)

```sql
SELECT user_id AS "id", username AS "userName", email, first_name AS "givenName", last_name AS "familyName", display_name AS "displayName", department, title, status FROM users WHERE status = 'ACTIVE'
```

## Get Specific User

```sql
SELECT user_id AS "id", username AS "userName", email, first_name AS "givenName", last_name AS "familyName", display_name AS "displayName", department, title, status FROM users WHERE user_id = ?
```

## Create User

```sql
SELECT create_user(?, ?, ?, ?, ?, ?, ?)
```

Parameters: `externalId, userName, email, firstName, lastName, department, title`

## Update User

```sql
SELECT update_user(?, ?, ?, ?, ?, ?)
```

Parameters: `externalId, email, firstName, lastName, department, title`

## Deactivate User

```sql
SELECT deactivate_user(?)
```

Parameter: `externalId`

## Import Entitlements

```sql
SELECT entitlement_id AS "id", name AS "displayName", description, category FROM entitlements WHERE status = 'ACTIVE'
```

## Assign Entitlement

```sql
SELECT assign_entitlement(?, ?)
```

Parameters: `userExternalId, entitlementExternalId`

## Revoke Entitlement

```sql
SELECT revoke_entitlement(?, ?)
```

Parameters: `userExternalId, entitlementExternalId`

## Connector Configuration Settings

| Setting | Value | Notes |
|---------|-------|-------|
| User ID Column | `id` | Maps to `user_id` via AS alias |
| Entitlement ID Column | `id` | Maps to `entitlement_id` via AS alias |
| Single user per entitlement | No | Users can have multiple entitlements |
| Single entitlement per user | No | Entitlements can be assigned to multiple users |

## SCIM Attribute Mapping

**Important:** The SCIM server only maps the User ID Column to core SCIM `id`/`externalId`/`userName`. All other SQL columns become enterprise extension attributes prefixed with `ext_`. These must be added to the app profile via **Directory → Profile Editor** and mapped in **Provisioning → To Okta**.

| DB Column | AS Alias | App Profile Attribute | → Okta Profile |
|-----------|----------|-----------------------|----------------|
| `user_id` | `id` | _(core SCIM id)_ | External ID |
| `username` | `userName` | `ext_userName` | `login` (via Okta Username Format) |
| `email` | _(none)_ | `ext_email` | `email` |
| `first_name` | `givenName` | `ext_givenName` | `firstName` |
| `last_name` | `familyName` | `ext_familyName` | `lastName` |
| `display_name` | `displayName` | `ext_displayName` | `displayName` |
| `department` | _(none)_ | `ext_department` | `department` |
| `title` | _(none)_ | `ext_title` | `title` |
| `entitlement_id` | `id` | _(core SCIM id)_ | Entitlement ID |
| `name` | `displayName` | `ext_displayName` | Entitlement display name |

### Okta Username Format

The SCIM server sets core `userName` to the User ID Column value (not the actual username). To fix this:

**Provisioning → To Okta → General → Okta Username Format** = `appuser.ext_userName`

## Write-Back Support

The `users` table has a `write_back` TEXT column that Okta can push values to via the Update User operation. This enables Okta to write flags or status information back to the source database.

**Key concept:** The `writeBack` column must be included in the import SELECT so the SCIM server exposes it as a schema attribute (`ext_writeBack`). However, it is only mapped in the **To App** direction (Okta → DB), not **To Okta** (DB → Okta).

### Import Query (includes writeBack for schema discovery)

```sql
SELECT user_id AS "id", username AS "userName", email, first_name AS "givenName", last_name AS "familyName", display_name AS "displayName", department, title, status, write_back AS "writeBack" FROM users WHERE status = 'ACTIVE'
```

### Get Specific User (includes writeBack for schema discovery)

```sql
SELECT user_id AS "id", username AS "userName", email, first_name AS "givenName", last_name AS "familyName", display_name AS "displayName", department, title, status, write_back AS "writeBack" FROM users WHERE user_id = ?
```

### Update User (7 parameters)

```sql
SELECT update_user(?, ?, ?, ?, ?, ?, ?)
```

Parameters: `externalId, email, firstName, lastName, department, title, writeBack`

### Write-Back Attribute Mapping

| DB Column | AS Alias | App Profile Attribute | Direction |
|-----------|----------|-----------------------|-----------|
| `write_back` | `writeBack` | `ext_writeBack` | **To App only** (Okta → DB) |

### Setup Steps

1. Include `write_back AS "writeBack"` in the import SELECT queries (above)
2. Add `ext_writeBack` to the app profile via **Directory → Profile Editor**
3. In **Provisioning → To App**: map the Okta attribute to `ext_writeBack`
4. Do **NOT** map `ext_writeBack` in Provisioning → To Okta (write-only, not read-back)

---

## Connection Details

| Field | Value |
|-------|-------|
| IP/DomainName | `taskvantage-prod-use2-generic-db.chmqcmc8w93i.us-east-2.rds.amazonaws.com` |
| Port | `5432` |
| Database | `okta_connector` |
| Username | `oktaadmin` |
| JDBC Driver | `org.postgresql.Driver` |
| JDBC URL | `jdbc:postgresql://taskvantage-prod-use2-generic-db.chmqcmc8w93i.us-east-2.rds.amazonaws.com:5432/okta_connector` |

## SCIM Server Details

### taskvantage.okta.com (generic-db-2)

| Field | Value |
|-------|-------|
| Instance | generic-db-2 |
| Private IP | `10.5.1.58` |
| Bearer Token | `2d66af55343ace749d5c6451ead29991` |
| Certificate | `certs/generic-db-2-scim.crt` |
| App ID | `0oa21ettm67r8Sy6X1d8` |
| SCIM Base URL | `10.5.1.58` |

### demo-netappdemo.okta.com (generic-db-1)

| Field | Value |
|-------|-------|
| Instance | generic-db-1 |
| Private IP | `10.5.1.104` |
| Bearer Token | `08e00ce4b44911f791025087d559e0fe` |
| Certificate | `certs/generic-db-1-scim-netappdemo.crt` |
| App ID | `0oa109idos6pO7sWL698` |
| SCIM Base URL | `10.5.1.104` |
