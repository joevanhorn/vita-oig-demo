# ServiceNow → Okta Access Request Flow — Build Spec

A buildable specification for the ServiceNow side of an access-request flow that
**submits an Okta Identity Governance (OIG) access request** when a user orders a
catalog item. This documents the VITA implementation ("Flow 1") — the Service
Catalog **forms**, the supporting ServiceNow objects, and every **REST API call**
tied to them: both the Table-API calls that *provision* the artifacts and the
runtime call chain that *submits the request*.

Reference implementation: `scripts/setup_servicenow_integration.py` (provisions
the ServiceNow side over REST) and `modules/servicenow-okta-bridge/app/handler.py`
(the bridge that calls Okta). VITA-specific IDs/URLs appear as examples; treat
anything in `<…>` or under "Environment values" as per-deployment.

---

## 1. Architecture

```
ServiceNow                                   Bridge (Lambda/API GW)        Okta OIG
──────────                                   ─────────────────────        ────────
Catalog item "Okta Group Access             POST /servicenow/request      POST /governance/api/v2/requests
(Okta-approved)"  ──order──▶ sc_req_item     (x-bridge-secret header)  ──▶  {requested: CATALOG_ENTRY,
        │ (after-insert Business Rule)              │                          requestedFor: OKTA_USER,
        └── OktaBridge Script Include ──────────────┘                          requesterFieldValues}
            (RESTMessageV2 POST)                                          ◀── 201 SUBMITTED
```

- The **catalog item** is the user-facing form. Ordering it creates a Requested
  Item (`sc_req_item`) with the form's variables.
- An **after-insert Business Rule** on `sc_req_item` fires once, calls the
  **OktaBridge** Script Include, which `POST`s to the bridge.
- The **bridge** resolves the Okta user, fills the OIG entry's required request
  fields, and submits `POST /governance/api/v2/requests`. Okta runs the approval
  sequence + fulfillment.

> The bridge is an intermediary so ServiceNow never holds an Okta API token and
> only needs a shared `x-bridge-secret`. A direct ServiceNow→Okta RESTMessage is
> possible but then the SSWS token lives in ServiceNow.

---

## 2. Prerequisites

**Okta OIG (one-time, Admin Console — mutates the governance org):**
1. A **requestable resource** with an **approval sequence**. In this org, request
   conditions attach to the **app resource**
   (`POST /governance/api/v2/resources/{appId}/request-conditions`) with
   `accessScopeSettings.type = GROUPS` scoping to the target group, plus a 24-char
   `approvalSequenceId` (the approval-sequence API is not exposed — create it in
   OIG → Access Requests). Activate the condition
   (`POST …/request-conditions/{id}/activate`).
2. Enable **request-on-behalf** on the resource:
   `PATCH /governance/api/v2/resources/{appId}/request-settings`
   `{"requestOnBehalfOfSettings":{"allowed":true,"type":"EVERYONE"}}` (else 409).
3. Note the **child catalog entry id** (the group entry *under* the app, not the
   parent app entry). This is the `entryId` the request targets. Its
   `…/my/catalogs/default/entries/{id}/request-fields` must return 200.

**Bridge:** a deployed endpoint exposing `POST /servicenow/request`, accepting an
`x-bridge-secret` header, holding an Okta SSWS token. (VITA: API Gateway →
Lambda, `modules/servicenow-okta-bridge/`.)

**ServiceNow:** admin credentials for the setup REST calls; the catalog item is
ordered by any requester at runtime.

**Environment values (VITA example):**
| Key | Value |
| --- | --- |
| SN instance | `https://dev341881.service-now.com` |
| Bridge URL | `https://8n2advzr15.execute-api.us-east-1.amazonaws.com` |
| Okta org | `demo-vita-oig.oktapreview.com` |
| Flow-1 child entry id | e.g. `cen1d6xlgqn7DGiBJ1d7` (APP-HealthApp-Admin) |
| Approval sequence id | `6a2834ee7ba302ba900992d5` |

---

## 3. ServiceNow data model (custom tables)

Two custom tables (Global scope, `u_` prefix). Flow 1 reads `u_okta_requestable`;
`u_okta_groups` supports the manager-approval variant (Flow 2).

**`u_okta_requestable`** — one row per requestable OIG child entry (kept in sync
by the bridge's `/sync/catalog`). The catalog item's reference variable points
here; the Business Rule reads `u_entry_id`.

| Column | Label | Type | Len |
| --- | --- | --- | --- |
| `u_entry_id` | Okta Catalog Entry ID | string | 100 |
| `u_name` | Name | string (display) | 255 |
| `u_description` | Description | string | 1000 |
| `u_last_sync` | Last Sync | glide_date_time | 40 |

(`u_okta_groups` mirrors this with `u_okta_group_id` / `u_okta_group_type` for the
group-add flow.)

---

## 4. The form — Service Catalog item + variables

**Category:** "Okta Access" (`sc_category`) under the **Service Catalog**
(`sc_catalog`).

**Catalog item (`sc_cat_item`):** `Okta Group Access (Okta-approved)`
- `short_description`: "Request Okta group access; Okta runs the approval and provisioning."
- `active = true`, linked to the category + catalog.

**Variables (`item_option_new`)** — these are the form fields:

| Variable name | Question | Type | `type` code | Reference table | Order | Mandatory |
| --- | --- | --- | --- | --- | --- | --- |
| `requested_for` | Requested for | Reference | `8` | `sys_user` | 100 | yes |
| `okta_requestable` | Requestable access | Reference | `8` | `u_okta_requestable` | 200 | yes |
| `justification` | Business justification | Single Line Text | `6` | — | 300 | yes |

> `item_option_new.type`: `8` = Reference, `6` = Single Line Text. Reference
> variables also set `reference` to the target table.

---

## 5. ServiceNow glue — Script Include, Properties, Business Rule

### 5.1 System properties (`sys_properties`)
| Name | Value | Purpose |
| --- | --- | --- |
| `x_okta_bridge.url` | bridge base URL | endpoint base for RESTMessage |
| `x_okta_bridge.secret` | shared secret | sent as `x-bridge-secret` |
| `x_okta_bridge.flow1_entry_id` | OIG child entry id | fallback entry if the variable is empty |

### 5.2 Script Include — `OktaBridge` (`sys_script_include`)
`api_name = global.OktaBridge`, `active`, `access = public`. Posts JSON to the
bridge with the secret header:

```javascript
var OktaBridge = Class.create();
OktaBridge.prototype = {
    initialize: function() {},
    post: function(path, payload) {
        var r = new sn_ws.RESTMessageV2();
        r.setEndpoint(gs.getProperty('x_okta_bridge.url') + path);
        r.setHttpMethod('POST');
        r.setRequestHeader('Content-Type', 'application/json');
        r.setRequestHeader('x-bridge-secret', gs.getProperty('x_okta_bridge.secret'));
        r.setRequestBody(JSON.stringify(payload));
        var resp = r.execute();
        gs.info('[OktaBridge] ' + path + ' -> ' + resp.getStatusCode() + ' ' + resp.getBody());
        return resp.getStatusCode();
    },
    type: 'OktaBridge'
};
```

### 5.3 Business Rule — `Okta Bridge - Flow1 submit` (`sys_script`)
- **Table:** `sc_req_item` · **When:** `after` · **Insert:** true · **Update:** false
  (fires once, on submit) · `advanced = true`, `order = 200`
- **Condition:** `current.cat_item == '<sys_id of the Flow-1 catalog item>'`
- **Script:** resolves the requested-for user, derives the OIG entry id from the
  `okta_requestable` reference variable (`u_entry_id`), falling back to the
  `x_okta_bridge.flow1_entry_id` property, and posts to the bridge:

```javascript
(function executeRule(current, previous) {
    try {
        var user = new GlideRecord('sys_user');
        if (!user.get(current.variables.requested_for)) return;
        var entry = '';
        var rec = new GlideRecord('u_okta_requestable');
        if (rec.get(current.variables.okta_requestable)) entry = rec.u_entry_id.toString();
        if (!entry) entry = gs.getProperty('x_okta_bridge.flow1_entry_id');
        new OktaBridge().post('/servicenow/request', {
            ritm_sys_id: current.getUniqueValue(),
            requested_for: { email: user.email.toString() },
            catalog_entry_id: entry,
            justification: current.variables.justification ? current.variables.justification.toString() : ''
        });
    } catch (e) { gs.error('[OktaBridge BR1] ' + e); }
})(current, previous);
```

---

## 6. REST API calls

### 6.1 Provisioning — create the ServiceNow artifacts (Table API)
Base: `{SN_URL}/api/now/table/{table}`, **Basic auth** (admin),
`Content-Type: application/json`. Each create is idempotent (GET-by-query first).

| # | Method · Table | Body (key fields) | Creates |
| --- | --- | --- | --- |
| 1 | `POST sys_db_object` | `{name:"u_okta_requestable", label:"Okta Requestable"}` | the custom table |
| 2 | `POST sys_dictionary` (per column) | `{name:"u_okta_requestable", element:"u_entry_id", column_label:"…", internal_type:"string", max_length:100, active:true, display:false}` | each column (`display:true` for `u_name`) |
| 3 | `POST sys_properties` (×3) | `{name:"x_okta_bridge.url", value:"<bridge>", type:"string"}` … | the 3 properties |
| 4 | `POST sys_script_include` | `{name:"OktaBridge", api_name:"global.OktaBridge", script:"<JS>", active:true, access:"public"}` | the Script Include |
| 5 | `GET  sc_catalog?title=Service Catalog` | — | resolve the Service Catalog sys_id |
| 6 | `POST sc_category` | `{title:"Okta Access", sc_catalog:"<catId>", description:"…"}` | the category |
| 7 | `POST sc_cat_item` | `{name:"Okta Group Access (Okta-approved)", short_description:"…", active:true, category:"<catSysId>", sc_catalogs:"<catId>"}` | the catalog item |
| 8 | `POST item_option_new` (per variable) | `{cat_item:"<itemSysId>", name:"requested_for", question_text:"Requested for", type:"8", order:"100", mandatory:true, active:true, reference:"sys_user"}` | each form variable |
| 9 | `POST sys_script` | `{name:"Okta Bridge - Flow1 submit", collection:"sc_req_item", when:"after", action_insert:true, action_update:false, advanced:true, order:"200", condition:"current.cat_item=='<itemSysId>'", script:"<JS>", active:true}` | the Business Rule |

### 6.2 Runtime — order the item (Service Catalog API)
Order via the **Service Catalog API** (not the Table API), which materializes the
variables into a `sc_req_item` and fires the Business Rule:

```
POST {SN_URL}/api/sn_sc/servicecatalog/items/{cat_item_sys_id}/order_now
Authorization: Basic <requester>
{
  "sysparm_quantity": "1",
  "variables": {
    "requested_for": "<sys_user sys_id>",
    "okta_requestable": "<u_okta_requestable sys_id>",
    "justification": "Need admin access for Q3 project"
  }
}
```
(In the UI this is the normal "Order Now"/"Submit" on the catalog item.)

### 6.3 Bridge → Okta — submit the OIG access request
The Business Rule's `OktaBridge.post('/servicenow/request', …)` reaches the bridge,
which calls Okta. The bridge:

1. Resolves the Okta user id from the email:
   `GET /api/v1/users?search=profile.email eq "<email>" or profile.login eq "<email>"&limit=1`
2. Fetches the entry's required fields and fills free-text ones with the
   justification (system fields like `OKTA_REQUESTED_FOR` are **not** filled —
   they're satisfied by `requestedFor`; stuffing them makes Okta auto-reject):
   `GET /governance/api/v2/my/catalogs/default/entries/{entryId}/request-fields`
3. Submits the request:

```
POST {OKTA_ORG_URL}/governance/api/v2/requests
Authorization: SSWS <token>
{
  "requested":   { "type": "CATALOG_ENTRY", "entryId": "<child entry id>" },
  "requestedFor":{ "type": "OKTA_USER", "externalId": "<okta user id>" },
  "requesterFieldValues": [
    { "id": "<required TEXT field id>", "values": ["<justification>"] }
  ]
}
→ 201 { "id": "<request id>", "status": "SUBMITTED" }
```

The request then routes through the approval sequence and provisions on approval.

---

## 7. End-to-end sequence

1. Requester orders **Okta Group Access (Okta-approved)**, picking `requested_for`,
   `okta_requestable`, and `justification` → `POST …/order_now`.
2. ServiceNow creates the `sc_req_item`; the **after-insert Business Rule** fires.
3. Business Rule resolves the user + the entry id (`u_entry_id` / property) and
   calls **OktaBridge** → `POST {bridge}/servicenow/request` with
   `{ritm_sys_id, requested_for.email, catalog_entry_id, justification}` +
   `x-bridge-secret`.
4. Bridge resolves the Okta user, fills required fields, and
   `POST /governance/api/v2/requests` → **201 SUBMITTED**.
5. Okta runs the approval sequence; on approval it provisions the access.

---

## 8. Field/variable reference

| Layer | Field | Maps to |
| --- | --- | --- |
| Catalog variable | `requested_for` (ref `sys_user`) | → user `email` → Okta `requestedFor.externalId` |
| Catalog variable | `okta_requestable` (ref `u_okta_requestable`) | → `u_entry_id` → Okta `requested.entryId` |
| Catalog variable | `justification` (text) | → bridge `justification` → `requesterFieldValues[].values` |
| Property | `x_okta_bridge.flow1_entry_id` | fallback `entryId` |
| Bridge payload | `catalog_entry_id` | Okta `requested.entryId` (type `CATALOG_ENTRY`) |

---

## 9. Notes & gotchas (from the build)

- **Target the CHILD entry**, not the parent app entry. Activating a GROUPS-scoped
  request condition creates a non-requestable parent app entry *and* a requestable
  child entry for the group — the child id is what `/requests` accepts.
- **Don't fill system request fields.** Only fill `required && type=="TEXT"`
  fields with the justification; filling `OKTA_REQUESTED_FOR` (type
  `OKTA_USER_ID`) causes Okta to auto-reject.
- **`requestedFor.type` must be `OKTA_USER`** and `requested.type` must be
  `CATALOG_ENTRY` (not "USER"/group id).
- **Business Rule scoping:** condition pins it to the one catalog item by
  `cat_item` sys_id, and it's **insert-only** so it fires exactly once per order
  (an update-only sibling rule drives the manager-approval variant).
- **Order via the Service Catalog API** (`/api/sn_sc/servicecatalog/items/{id}/order_now`),
  not the `sc_req_item` Table API, so the variables + Business Rule engage.
- **Auth separation:** ServiceNow holds only `x-bridge-secret`; the Okta SSWS
  token lives in the bridge.
