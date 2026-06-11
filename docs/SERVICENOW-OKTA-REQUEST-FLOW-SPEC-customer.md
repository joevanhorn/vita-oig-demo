# ServiceNow → Okta Access Request — ServiceNow Build Guide

A guide for a **ServiceNow administrator** to build a Service Catalog request that
**submits an Okta Identity Governance (OIG) access request**. When a user orders
the catalog item, ServiceNow calls a small relay service (the "bridge"), which
creates and submits the access request in Okta. Okta then runs the approval and
fulfillment.

You build the ServiceNow objects in this guide. The bridge and the Okta-side
configuration are provided to you (see *What you need* below).

---

## What you need before you start

**Provided to you (by the Okta/integration team):**
| Item | Used for |
| --- | --- |
| **Bridge base URL** — e.g. `https://<your-bridge-host>` | endpoint ServiceNow calls |
| **Bridge secret** — a shared string | sent as the `x-bridge-secret` header |
| **Okta OIG catalog entry id(s)** — e.g. `<child-catalog-entry-id>` | the requestable access; goes in the request as `entryId` |

> The bridge holds the Okta API token and performs the Okta call — **no Okta
> credentials are stored in ServiceNow.** ServiceNow only needs the bridge URL +
> secret.

**You provide (in your ServiceNow instance):**
- Admin access to create tables, catalog items, a Script Include, a Business
  Rule, and system properties (or build them via the REST calls in §7).

**Assumption:** the requestable access already exists in Okta OIG (a requestable
resource with an approval sequence, and **request-on-behalf enabled**). Your Okta
admin supplies the resulting **catalog entry id**. If multiple options should be
selectable in the form, you'll load them into a lookup table (§3).

---

## 1. How it works

```
ServiceNow                                    Bridge                  Okta OIG
──────────                                    ──────                  ────────
Catalog item  ──order──▶  sc_req_item         POST /servicenow/request   POST /governance/api/v2/requests
      │ (after-insert Business Rule)               (x-bridge-secret)  ──▶  {CATALOG_ENTRY, OKTA_USER,
      └── OktaBridge Script Include ───────────────┘                       justification}
          (RESTMessageV2 POST)                                        ◀──  201 SUBMITTED
```

1. A requester orders the **catalog item** (the form), choosing who it's for, the
   access, and a justification.
2. An **after-insert Business Rule** on the Requested Item (`sc_req_item`) fires
   once and calls the **OktaBridge** Script Include.
3. OktaBridge `POST`s to the bridge; the bridge submits the OIG request to Okta.
4. Okta routes it through the approval sequence and provisions on approval.

---

## 2. Object checklist

You will create, in this order:
1. A custom table **`u_okta_requestable`** (lookup of requestable access). *(Skip
   if you'll hardcode a single entry id in a property instead — see §3.)*
2. Three **system properties** (`x_okta_bridge.url`, `.secret`, `.flow1_entry_id`).
3. A **Script Include** `OktaBridge`.
4. A **Service Catalog category** + **catalog item** with three variables.
5. An after-insert **Business Rule** on `sc_req_item`.

---

## 3. Lookup table (optional) — `u_okta_requestable`

One row per requestable Okta access option. The form's reference variable points
here; the Business Rule reads `u_entry_id`.

| Column | Label | Type | Max length |
| --- | --- | --- | --- |
| `u_entry_id` | Okta Catalog Entry ID | String | 100 |
| `u_name` | Name *(display value)* | String | 255 |
| `u_description` | Description | String | 1000 |

Populate it with the entry id(s) your Okta admin gave you (`u_entry_id` =
`<child-catalog-entry-id>`, `u_name` = a friendly label).

> **Simpler alternative:** if only one fixed access option is needed, skip this
> table and the `okta_requestable` variable, and put the entry id in the
> `x_okta_bridge.flow1_entry_id` property (§4). The Business Rule falls back to it.

---

## 4. System properties (`sys_properties`)

| Name | Value | Purpose |
| --- | --- | --- |
| `x_okta_bridge.url` | `https://<your-bridge-host>` | bridge base URL |
| `x_okta_bridge.secret` | `<bridge secret>` | sent as `x-bridge-secret` |
| `x_okta_bridge.flow1_entry_id` | `<child-catalog-entry-id>` or blank | fallback entry id when the form variable is empty |

---

## 5. Script Include — `OktaBridge`

Name `OktaBridge`, API name `global.OktaBridge`, Active, Accessible from **All
application scopes**. Sends JSON to the bridge with the secret header. Use
verbatim:

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

---

## 6. The form — Service Catalog item + variables

**Category** (`sc_category`): e.g. "Okta Access", under your Service Catalog.

**Catalog item** (`sc_cat_item`): e.g. **"Okta Group Access"**
- Short description: "Request Okta access; Okta runs the approval and provisioning."
- Active, in the category above.

**Variables** (these are the form fields):

| Variable name | Question | Type | Reference table | Order | Mandatory |
| --- | --- | --- | --- | --- | --- |
| `requested_for` | Requested for | Reference | `sys_user` | 100 | Yes |
| `okta_requestable` | Requestable access | Reference | `u_okta_requestable` | 200 | Yes |
| `justification` | Business justification | Single Line Text | — | 300 | Yes |

> If you used the single-entry property approach (§3), omit the
> `okta_requestable` variable.

---

## 7. Business Rule — submit the request

**Table** `sc_req_item` · **When** `after` · **Insert** ✔ · **Update** ✘ (fires
once, on submit) · **Advanced** ✔.

**Condition** — pin it to your catalog item so it only runs for this request:
```
current.cat_item == '<sys_id of your catalog item>'
```

**Script** — resolves the user, derives the Okta entry id (from the variable,
falling back to the property), and calls the bridge:

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

## 8. Optional — build it all over REST instead of the UI

Every object above can be created with the **Table API**
(`{instance}/api/now/table/{table}`, Basic auth as an admin,
`Content-Type: application/json`). Make each idempotent by GET-ing by query first.

| # | Method · Table | Body (key fields) |
| --- | --- | --- |
| 1 | `POST sys_db_object` | `{"name":"u_okta_requestable","label":"Okta Requestable"}` |
| 2 | `POST sys_dictionary` *(per column)* | `{"name":"u_okta_requestable","element":"u_entry_id","column_label":"Okta Catalog Entry ID","internal_type":"string","max_length":100,"active":"true","display":"false"}` *(`display:"true"` for `u_name`)* |
| 3 | `POST sys_properties` *(×3)* | `{"name":"x_okta_bridge.url","value":"https://<your-bridge-host>","type":"string"}` … |
| 4 | `POST sys_script_include` | `{"name":"OktaBridge","api_name":"global.OktaBridge","script":"<JS from §5>","active":"true","access":"public"}` |
| 5 | `GET  sc_catalog?sysparm_query=title=Service Catalog` | *(resolve the catalog sys_id)* |
| 6 | `POST sc_category` | `{"title":"Okta Access","sc_catalog":"<catalog sys_id>","description":"Request Okta access"}` |
| 7 | `POST sc_cat_item` | `{"name":"Okta Group Access","short_description":"…","active":"true","category":"<category sys_id>","sc_catalogs":"<catalog sys_id>"}` |
| 8 | `POST item_option_new` *(per variable)* | `{"cat_item":"<item sys_id>","name":"requested_for","question_text":"Requested for","type":"8","order":"100","mandatory":"true","active":"true","reference":"sys_user"}` *(`type` `8`=Reference, `6`=Single Line Text)* |
| 9 | `POST sys_script` | `{"name":"Okta Bridge submit","collection":"sc_req_item","when":"after","action_insert":"true","action_update":"false","advanced":"true","order":"200","condition":"current.cat_item=='<item sys_id>'","script":"<JS from §7>","active":"true"}` |

---

## 9. Submitting a request

**In the UI:** open the catalog item, fill the three fields, and **Order Now /
Submit**.

**Over REST** (note: use the **Service Catalog API**, not the Table API, so the
variables and Business Rule engage):
```
POST {instance}/api/sn_sc/servicecatalog/items/{catalog_item_sys_id}/order_now
Authorization: Basic <requester>
Content-Type: application/json
{
  "sysparm_quantity": "1",
  "variables": {
    "requested_for": "<sys_user sys_id>",
    "okta_requestable": "<u_okta_requestable sys_id>",
    "justification": "Need admin access for the Q3 project"
  }
}
```

---

## 10. What the bridge does (for reference)

You don't build this — it's provided — but for validation, on
`POST /servicenow/request` the bridge:

1. Looks up the Okta user by email
   (`GET /api/v1/users?search=profile.email eq "<email>"`).
2. Reads the entry's required request fields
   (`GET /governance/api/v2/my/catalogs/default/entries/{entryId}/request-fields`)
   and fills the required **free-text** fields with the justification.
3. Submits the access request:
   ```
   POST /governance/api/v2/requests
   {
     "requested":    { "type": "CATALOG_ENTRY", "entryId": "<entry id>" },
     "requestedFor": { "type": "OKTA_USER", "externalId": "<okta user id>" },
     "requesterFieldValues": [ { "id": "<field id>", "values": ["<justification>"] } ]
   }
   → 201 { "status": "SUBMITTED" }
   ```

---

## 11. Troubleshooting

| Symptom | Likely cause / fix |
| --- | --- |
| Business Rule doesn't fire | Condition `cat_item` sys_id wrong, or it's not **after-insert**. Check it's pinned to your item's sys_id. |
| Bridge call fails (401/403) | `x_okta_bridge.secret` doesn't match the value the bridge expects, or `x_okta_bridge.url` is wrong. |
| Okta returns an error / auto-rejects | Wrong `entryId` (must be the **child** catalog entry id from your Okta admin, not an app/parent id); or request-on-behalf isn't enabled on the Okta resource. |
| Request created but never routes for approval | The Okta requestable resource has no approval sequence attached — an Okta-side configuration item. |
| `order_now` ignores the variables | You called the Table API on `sc_req_item` instead of the Service Catalog `order_now` endpoint. |

---

## 12. Field reference

| Form field | Flows to |
| --- | --- |
| `requested_for` (→ `sys_user`) | user email → Okta `requestedFor.externalId` |
| `okta_requestable` (→ `u_okta_requestable`) | `u_entry_id` → Okta `requested.entryId` |
| `justification` (text) | bridge `justification` → Okta `requesterFieldValues[].values` |
