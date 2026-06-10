# ServiceNow ↔ Okta Identity Governance — Integration Demo

End-to-end integration between **ServiceNow** (`dev341881.service-now.com`) and **Okta Identity
Governance** (`demo-vita-oig.oktapreview.com`) for the VITA OIG demo. Four flows, all in-repo
code (no Okta Workflows), bridged by a small AWS Lambda.

> **10-minute demo tip:** the SC requests are already completed — show the finished
> `REQ`/`RITM` records and the resulting Okta state rather than waiting on live approvals.
> Suggested order: **Flow 3 (the catalog data) → Flow 2 (SN approves) → Flow 1 (Okta approves)**.

---

## Architecture at a glance

```
                         x-bridge-secret (shared)              SSWS token
   ServiceNow  ───────────────────────────────►  SN↔Okta Bridge  ──────────────►  Okta OIG
   (catalog,                HTTPS                 (AWS Lambda +                    (groups,
    business rules,   ◄───────────────────────    API Gateway)   ◄──────────────  access requests,
    tables)            basic auth (Table API)                                      entitlements)
```

- **Bridge** — Python AWS Lambda behind an API Gateway HTTP API (AWS acct `357013128720`,
  `us-east-1`). Base URL: `https://8n2advzr15.execute-api.us-east-1.amazonaws.com`.
  Routes: `POST /servicenow/request` (Flow 1), `POST /servicenow/approved` (Flow 2),
  `POST /sync/groups` + `POST /sync/catalog` (Flow 3), `POST /servicenow/onboarding` (Flow 4),
  `GET /healthz`.
- **Auth** — ServiceNow → bridge: header `x-bridge-secret` (GitHub env secret `SN_INBOUND_SECRET`).
  Bridge → Okta: SSWS token. Bridge → ServiceNow: basic auth. All held in one Secrets Manager
  secret `vita-oig-preview-servicenow-okta-bridge-creds`, populated by the deploy workflow.
- **No secrets in the repo** — ServiceNow creds, the Okta token, and the shared secret are GitHub
  Environment secrets on `vita-oig-preview`.

### ServiceNow objects (created by `scripts/setup_servicenow_integration.py`)
| Object | Name |
| --- | --- |
| Catalog category | **Okta Access** |
| Catalog item (Flow 1) | **Okta Group Access (Okta-approved)** |
| Catalog item (Flow 2) | **Okta Group Access (Manager approval)** |
| Catalog item (Flow 4) | **(1) Employee Onboarding (Pre-HR Feed)** — built directly via the Table API (see follow-ups) |
| Script Include | **OktaBridge** (POSTs to the bridge with `x-bridge-secret`) |
| Business Rule (Flow 1) | **Okta Bridge - Flow1 submit** (`sc_req_item`, on insert) |
| Business Rule (Flow 2) | **Okta Bridge - Flow2 approved** (`sc_req_item`, async on approval) |
| Business Rule (Flow 4) | **Okta Bridge - Flow4 onboarding** (`sc_req_item`, on insert) |
| Table | **`u_okta_groups`** — synced Okta groups (Flow 2 picker) |
| Table | **`u_okta_requestable`** — synced requestable OIG entries (Flow 1 picker) |
| System properties | `x_okta_bridge.url`, `x_okta_bridge.secret`, `x_okta_bridge.flow1_entry_id` |

### Okta objects (created by `scripts/make_groups_requestable.py`)
Three elevated-access groups, each assigned to its placeholder app, owned by the agency's
dept-admin group, and made **requestable** via an OIG **request condition** (requester = Everyone,
access scope = the group, approval sequence `6a2834ee7ba302ba900992d5`):

| Group | App | Owner | Requestable child entry |
| --- | --- | --- | --- |
| `APP-HealthApp-Admin` | Health App | VDH-dept-admin | `cen1d6xlgqn7DGiBJ1d7` |
| `APP-TransportationApp-Admin` | Transportation App | VDOT-dept-admin | `cen1d6xnd9EHarzHO1d7` |
| `APP-FinanceApp-Admin` | Finance App | DOA-dept-admin | `cen1d6xlgrwf5CrwE1d7` |

---

## Flow 1 — Request in ServiceNow, **approved & fulfilled in Okta**

A user requests elevated app access in the ServiceNow catalog; Okta OIG runs the approval and
provisions the group on approval.

```
SN catalog item "Okta Group Access (Okta-approved)"
  │  (user picks a Requestable access item + justification)
  ▼
Business Rule "Okta Bridge - Flow1 submit" (on insert)
  │  OktaBridge.post('/servicenow/request', {requested_for.email, catalog_entry_id, justification})
  ▼
Bridge  POST /governance/api/v2/requests
  │   requested = { type: CATALOG_ENTRY, entryId: <requestable child entry> }
  │   requestedFor = { type: OKTA_USER, externalId: <resolved from email> }
  │   requesterFieldValues = [ <required justification field, auto-filled> ]
  ▼
Okta OIG access request (status SUBMITTED)
  │   → approval sequence 6a2834ee… (the group/app owner approves)
  ▼
Okta provisions the group membership  ✅
```

**Why it works (the OIG specifics):** the requestable entity is the **child (group) entry** under
the app (not the parent app entry); the entry has a **required justification field** the bridge
auto-fetches and fills; and the resource has **`requestOnBehalfOfSettings.allowed=true`** so the
bridge can request for another user.

**Demo:** open the completed `REQ`/`RITM` for "Okta Group Access (Okta-approved)" → show the
linked **Okta access request** (SUBMITTED/approved) in the Okta Access Requests portal → show the
user landing in the `APP-*-Admin` group. Talking point: *approval lives in Okta; ServiceNow is just
the front door.*

---

## Flow 2 — Approved in ServiceNow, **fulfilled in Okta**

ServiceNow owns the approval; once approved, Okta provisions the group automatically.

```
SN catalog item "Okta Group Access (Manager approval)"
  │  (user picks an Okta group; ServiceNow approval runs)
  ▼  RITM approval = approved
Business Rule "Okta Bridge - Flow2 approved" (async, on approval change)
  │  OktaBridge.post('/servicenow/approved', {requested_for.email, group_id, ritm_sys_id})
  ▼
Bridge  PUT /api/v1/groups/{groupId}/users/{userId}     (adds the user to the Okta group)
  │     PATCH /api/now/table/sc_req_item/{ritm} state=3  (closes the RITM)
  ▼
User is in the Okta group; the RITM is Closed Complete  ✅
```

**Demo:** open the completed `REQ`/`RITM` for "Okta Group Access (Manager approval)" → show the SN
approval record + the closed RITM → show the user in the Okta group. Talking point: *approval lives
in ServiceNow; Okta is the fulfillment engine.*

---

## Flow 3 — Sync Okta into ServiceNow for the catalog

Keeps ServiceNow's catalog data driven by Okta, so requests reference real Okta objects.

```
Bridge  POST /sync/groups    GET /api/v1/groups            → upsert u_okta_groups       (127 groups)
Bridge  POST /sync/catalog   GET .../my/catalogs/.../entries (+children, requestable)
                                                            → upsert u_okta_requestable  (requestable items)
```

- **`u_okta_groups`** backs the Flow 2 picker (any Okta group).
- **`u_okta_requestable`** backs the Flow 1 picker (only items made requestable in Okta OIG). Add a
  request condition to **any** app/group in Okta and it appears here automatically on the next sync.
- Runs on demand (the HTTP routes) or on a schedule (EventBridge — currently off pending an IAM
  permission; see Operations).

**Demo:** open the **`u_okta_requestable`** / **`u_okta_groups`** tables in ServiceNow and show they
mirror Okta. Talking point: *the catalog never drifts from Okta — it's synced.*

---

## Flow 4 — Employee Onboarding (Pre-HR Feed) via **Access Requests V1**

A pre-HR-feed new hire is submitted in the ServiceNow catalog; on submit, an **Okta Access Requests
V1** onboarding request is created and Okta runs the request type's approval + actions.

> **Different API surface than Flow 1.** Flow 1 uses Governance **v2** (`/governance/api/v2/requests`,
> catalog *entries*). Flow 4 targets the **Access Requests V1** request type
> (`/governance/api/v1/requests`, `requestTypeId`) — same SSWS token, different endpoint.

```
SN catalog item "(1) Employee Onboarding (Pre-HR Feed)"   (10 fields; submitter = opened_by)
  │
  ▼
Business Rule "Okta Bridge - Flow4 onboarding" (on insert)
  │  OktaBridge.post('/servicenow/onboarding', {requester_email: <submitter>, first_name, last_name,
  │                   agency, job_title, manager, manager_email, start_date, cardinal_employee_id,
  │                   email, username})
  ▼
Bridge  POST /governance/api/v1/requests
  │   requestTypeId     = 6a14744c947ae2aa8be1c098 ("(1) Employee Onboarding (Pre-HR Feed)")
  │   requesterUserIds  = [ <submitter, resolved from email> ]
  │   requesterFieldValues = [ {id, value} × 10 ]   (Agency → array; Start Date → ISO 8601)
  ▼
Okta Access Requests V1 request (status OPEN) → approval + request-type actions  ✅
```

**Field mapping (verified 2026-06-10):**

| SN variable | Okta field id | Type |
| --- | --- | --- |
| `first_name` | `ce49d104-…2f72` | Text |
| `last_name` | `667f7565-…6331` | Text |
| `agency` | `a8807066-…9d98` | **SELECT** (value → array) |
| `job_title` | `452386bb-…d976` | Text |
| `manager` | `caa5363b-…dbef` | Text |
| `manager_email` | `a7740982-…8575` | Text |
| `start_date` | `f90e6301-…2f24` | **DATE** (ISO 8601) |
| `cardinal_employee_id` | `448b6dd9-…58a7` | Text |
| `email` | `5b97b903-…4e11` | Text |
| `username` | `ea0bb581-…6bcc` | Text |

> ⚠️ **V1 field ids change when the request type is edited** and are **not** returned by the
> request-type GET. If creates start returning `409 … invalid according to requesterFields`, re-pull
> the current ids from a recent request (`GET /governance/api/v1/requests/{id}` → `requesterFieldValues`)
> and update `ONBOARD_FIELD_IDS` in `handler.py`. SELECT values must match exactly — only
> **`VDH - Virginia Department of Health`** is currently a valid Agency option.

**Submitter → requester:** the SN submitter (`opened_by`) email is mapped to an Okta user and set as
`requesterUserIds`, so the submitter must exist in Okta. The new-hire details live in the form fields
(the hire has no Okta account yet — "Pre-HR Feed").

**Demo:** Service Catalog → **Okta Access** → **(1) Employee Onboarding (Pre-HR Feed)** → fill the
form → submit → show the resulting **Okta Access Requests** request (10 fields populated, pending
approval). Talking point: *HR-style onboarding originates in ServiceNow; Okta governs approval + provisioning.*

---

## Repository map

| Path | What |
| --- | --- |
| `modules/servicenow-okta-bridge/app/handler.py` | The bridge (all routes/flows) |
| `modules/servicenow-okta-bridge/*.tf` | Lambda + API Gateway + Secrets Manager (+ optional schedule) |
| `environments/vita-oig-preview/infrastructure/servicenow-okta-bridge/` | Terraform env root |
| `.github/workflows/deploy-servicenow-bridge.yml` | Deploy (plan/apply/destroy) + populate the secret |
| `scripts/setup_servicenow_integration.py` | Build the ServiceNow side (tables, catalog, BRs, Script Include) |
| `scripts/make_groups_requestable.py` | Create + activate OIG request conditions; enable on-behalf |

---

## Operations / runbook

- **Deploy/update the bridge:** GitHub Actions → *Deploy ServiceNow-Okta Bridge* → `apply`
  (env `vita-oig-preview`). The post-apply step repopulates the Secrets Manager secret from the
  GitHub Environment secrets. (The Lambda caches the secret per container — after rotating a secret,
  cycle the function.)
- **Re-build the ServiceNow side (idempotent):**
  `SN_URL=… SN_USER=… SN_PASS=… BRIDGE_URL=… BRIDGE_SECRET=… python3 scripts/setup_servicenow_integration.py`
- **Make a new app/group requestable (Flow 1):** create + activate a request condition + enable
  on-behalf via `OKTA_API_TOKEN=… APPROVAL_SEQUENCE_ID=… python3 scripts/make_groups_requestable.py`,
  then `POST /sync/catalog` so it appears in `u_okta_requestable`.
- **Refresh the catalog data:** `POST /sync/groups` and `POST /sync/catalog` with header
  `x-bridge-secret: <SN_INBOUND_SECRET>` (the full group sync runs longer than API Gateway's 30s
  cap — it completes in the background; use the async/scheduled path for large syncs).

### Known follow-ups (non-blocking)
- Re-enable the EventBridge schedule on a CI role that has `events:TagResource` (currently the
  group/catalog sync is run on demand).
- Make `POST /sync/groups` return `202` and self-invoke async so it doesn't `503` on large syncs
  (the work still completes today).
- Fold the **Flow 4** catalog item + business rule into `scripts/setup_servicenow_integration.py`
  (currently built directly via the Table API).
- Confirm the full **Agency** option list for the V1 onboarding type — only
  `VDH - Virginia Department of Health` is verified; `DSS - Department of Social Services` is **not**
  a current option.

---

## Quick reference

- **Bridge:** `https://8n2advzr15.execute-api.us-east-1.amazonaws.com` · header `x-bridge-secret`
- **ServiceNow:** `https://dev341881.service-now.com` · catalog category **Okta Access**
- **Okta:** `https://demo-vita-oig.oktapreview.com` · approval sequence `6a2834ee7ba302ba900992d5`
- **Onboarding (Flow 4):** Access Requests **V1** request type `6a14744c947ae2aa8be1c098` · SN item
  **(1) Employee Onboarding (Pre-HR Feed)** · only verified Agency option `VDH - Virginia Department of Health`
- **Requestable demo items:** `APP-HealthApp-Admin`, `APP-TransportationApp-Admin`,
  `APP-FinanceApp-Admin` (Health/Transportation/Finance Apps)
