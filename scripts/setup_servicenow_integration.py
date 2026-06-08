#!/usr/bin/env python3
"""
Provision the ServiceNow side of the SN<->Okta bridge (VITA OIG demo) via the SN REST API.

Idempotent: each create checks for an existing record first. Reads SN admin creds + the bridge
URL/secret from env:
    SN_URL, SN_USER, SN_PASS     ServiceNow instance + admin creds
    BRIDGE_URL                   the bridge API Gateway base URL (e.g. https://xxxx.execute-api...)
    BRIDGE_SECRET                value ServiceNow sends as the x-bridge-secret header
    FLOW1_ENTRY_ID               (optional) Okta OIG catalog entry id for the Flow 1 demo group

Steps (run all, or one via --only):
    table            custom table u_okta_groups (+ columns) the Flow-3 sync writes / the catalog reads
    properties       x_okta_bridge.url / .secret / .flow1_entry_id system properties
    script_include   OktaBridge (POSTs to the bridge with the x-bridge-secret header)
    catalog          'Okta Access' category + two catalog items (Flow 1 / Flow 2) with variables
    business_rules   sc_req_item rules that call the bridge on submit (Flow 1) / approval (Flow 2)

Flow 2 (SN approval -> Okta group add) works end-to-end as soon as this runs. Flow 1 (SN request
-> Okta OIG access request) additionally needs ONE manual OIG step in the Okta Admin Console:
make a group/resource *requestable* with an approval sequence, then set its catalog entry id as the
FLOW1_ENTRY_ID env (re-run the `properties` step) or in the `x_okta_bridge.flow1_entry_id` property.
The SN catalog item + business rule + bridge then create the OIG request automatically. (Not
automated here: creating the requestable resource mutates the hand-built governance org.)
"""

import argparse
import os
import sys
import requests

SN_URL = os.environ.get("SN_URL", "").rstrip("/")
SN_AUTH = (os.environ.get("SN_USER", ""), os.environ.get("SN_PASS", ""))
BRIDGE_URL = os.environ.get("BRIDGE_URL", "").rstrip("/")
BRIDGE_SECRET = os.environ.get("BRIDGE_SECRET", "")
FLOW1_ENTRY_ID = os.environ.get("FLOW1_ENTRY_ID", "")

TABLE = "u_okta_groups"
COLUMNS = [
    ("u_okta_group_id", "Okta Group ID", "string", 100),
    ("u_name", "Name", "string", 255),
    ("u_description", "Description", "string", 1000),
    ("u_okta_group_type", "Okta Group Type", "string", 40),
    ("u_last_sync", "Last Sync", "glide_date_time", 40),
]
FLOW1_ITEM = "Okta Group Access (Okta-approved)"
FLOW2_ITEM = "Okta Group Access (Manager approval)"

S = requests.Session()
S.auth = SN_AUTH
S.headers.update({"Accept": "application/json", "Content-Type": "application/json"})


def _get(table, query, fields="sys_id"):
    r = S.get(f"{SN_URL}/api/now/table/{table}",
              params={"sysparm_query": query, "sysparm_limit": 1, "sysparm_fields": fields})
    r.raise_for_status()
    return (r.json().get("result") or [None])[0]


def _post(table, body):
    r = S.post(f"{SN_URL}/api/now/table/{table}", json=body)
    if not r.ok:
        print(f"   POST {table} -> {r.status_code}: {r.text[:300]}")
        r.raise_for_status()
    return r.json()["result"]


def _patch(table, sys_id, body):
    r = S.patch(f"{SN_URL}/api/now/table/{table}/{sys_id}", json=body)
    r.raise_for_status()
    return r.json()["result"]


# --------------------------------------------------------------------------- table
def setup_table():
    print(f"[table] ensuring {TABLE}")
    if _get("sys_db_object", f"name={TABLE}"):
        print("   table exists")
    else:
        print(f"   created table (sys_id={_post('sys_db_object', {'name': TABLE, 'label': 'Okta Groups'})['sys_id']})")
    for element, label, itype, maxlen in COLUMNS:
        if _get("sys_dictionary", f"name={TABLE}^element={element}"):
            continue
        _post("sys_dictionary", {"name": TABLE, "element": element, "column_label": label,
                                 "internal_type": itype, "max_length": maxlen, "active": "true",
                                 "display": "true" if element == "u_name" else "false"})
        print(f"   created column {element}")


# ---------------------------------------------------------------------- properties
def ensure_property(name, value, desc=""):
    rec = _get("sys_properties", f"name={name}")
    if rec:
        _patch("sys_properties", rec["sys_id"], {"value": value})
        print(f"   property {name} updated")
    else:
        _post("sys_properties", {"name": name, "value": value, "type": "string",
                                 "description": desc, "suffix": "", "is_private": "false"})
        print(f"   property {name} created")


def setup_properties():
    print("[properties]")
    if not BRIDGE_URL or not BRIDGE_SECRET:
        sys.exit("BRIDGE_URL and BRIDGE_SECRET env are required for the properties step")
    ensure_property("x_okta_bridge.url", BRIDGE_URL, "SN<->Okta bridge base URL")
    ensure_property("x_okta_bridge.secret", BRIDGE_SECRET, "x-bridge-secret header value")
    ensure_property("x_okta_bridge.flow1_entry_id", FLOW1_ENTRY_ID, "Okta OIG catalog entry id for Flow 1")


# ------------------------------------------------------------------- script include
SCRIPT_INCLUDE = """var OktaBridge = Class.create();
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
};"""


def setup_script_include():
    print("[script_include] OktaBridge")
    rec = _get("sys_script_include", "name=OktaBridge")
    body = {"name": "OktaBridge", "api_name": "global.OktaBridge", "script": SCRIPT_INCLUDE,
            "active": "true", "access": "public",
            "description": "POST to the SN<->Okta bridge with the x-bridge-secret header"}
    if rec:
        _patch("sys_script_include", rec["sys_id"], {"script": SCRIPT_INCLUDE, "active": "true"})
        print("   updated")
    else:
        _post("sys_script_include", body)
        print("   created")


# ------------------------------------------------------------------------- catalog
def _service_catalog_id():
    cat = _get("sc_catalog", "title=Service Catalog") or _get("sc_catalog", "")
    return cat["sys_id"] if cat else ""


def _ensure_category(catalog_id):
    rec = _get("sc_category", "title=Okta Access")
    if rec:
        return rec["sys_id"]
    return _post("sc_category", {"title": "Okta Access", "sc_catalog": catalog_id,
                                 "description": "Request Okta group access"})["sys_id"]


def _ensure_item(name, short_desc, catalog_id, category_id):
    rec = _get("sc_cat_item", f"name={name}")
    if rec:
        print(f"   item exists: {name}")
        return rec["sys_id"]
    item = _post("sc_cat_item", {"name": name, "short_description": short_desc, "active": "true",
                                 "category": category_id, "sc_catalogs": catalog_id})
    print(f"   created item: {name}")
    return item["sys_id"]


def _ensure_variable(item_id, name, question, vtype, order, reference=""):
    # item_option_new types: 6=Single Line Text, 8=Reference
    if _get("item_option_new", f"cat_item={item_id}^name={name}"):
        return
    body = {"cat_item": item_id, "name": name, "question_text": question, "type": str(vtype),
            "order": str(order), "active": "true", "mandatory": "true"}
    if reference:
        body["reference"] = reference
    _post("item_option_new", body)
    print(f"      var {name} ({'ref ' + reference if reference else 'text'})")


def setup_catalog():
    print("[catalog]")
    catalog_id = _service_catalog_id()
    category_id = _ensure_category(catalog_id)
    for name, sd in [(FLOW1_ITEM, "Request Okta group access; Okta runs the approval and provisioning."),
                     (FLOW2_ITEM, "Request Okta group access; approved in ServiceNow, provisioned in Okta.")]:
        item_id = _ensure_item(name, sd, catalog_id, category_id)
        _ensure_variable(item_id, "requested_for", "Requested for", 8, 100, "sys_user")
        _ensure_variable(item_id, "okta_group", "Okta group", 8, 200, TABLE)
        if name == FLOW1_ITEM:
            _ensure_variable(item_id, "justification", "Business justification", 6, 300)


# ------------------------------------------------------------------ business rules
BR1 = """(function executeRule(current, previous) {
    try {
        var user = new GlideRecord('sys_user');
        if (!user.get(current.variables.requested_for)) return;
        var entry = current.variables.okta_catalog_entry_id
            ? current.variables.okta_catalog_entry_id.toString()
            : gs.getProperty('x_okta_bridge.flow1_entry_id');
        new OktaBridge().post('/servicenow/request', {
            ritm_sys_id: current.getUniqueValue(),
            requested_for: { email: user.email.toString() },
            catalog_entry_id: entry,
            justification: current.variables.justification ? current.variables.justification.toString() : ''
        });
    } catch (e) { gs.error('[OktaBridge BR1] ' + e); }
})(current, previous);"""

BR2 = """(function executeRule(current, previous) {
    try {
        var groupRec = new GlideRecord('u_okta_groups');
        if (!groupRec.get(current.variables.okta_group)) return;
        var user = new GlideRecord('sys_user');
        if (!user.get(current.variables.requested_for)) return;
        new OktaBridge().post('/servicenow/approved', {
            ritm_sys_id: current.getUniqueValue(),
            requested_for: { email: user.email.toString() },
            group_id: groupRec.u_okta_group_id.toString()
        });
    } catch (e) { gs.error('[OktaBridge BR2] ' + e); }
})(current, previous);"""


def _ensure_business_rule(name, when, script, condition):
    rec = _get("sys_script", f"name={name}")
    body = {"name": name, "collection": "sc_req_item", "when": when, "active": "true",
            "order": "200", "advanced": "true", "script": script, "condition": condition,
            "action_insert": "true" if when == "after" else "false",
            "action_update": "true"}
    if rec:
        _patch("sys_script", rec["sys_id"], {"script": script, "condition": condition, "active": "true"})
        print(f"   business rule updated: {name}")
    else:
        _post("sys_script", body)
        print(f"   business rule created: {name}")


def setup_business_rules():
    print("[business_rules]")
    f1 = _get("sc_cat_item", f"name={FLOW1_ITEM}")
    f2 = _get("sc_cat_item", f"name={FLOW2_ITEM}")
    if not f1 or not f2:
        sys.exit("run the catalog step first (catalog items missing)")
    _ensure_business_rule(
        "Okta Bridge - Flow1 submit", "after", BR1,
        f"current.cat_item == '{f1['sys_id']}'")
    # Flow 2: fire when the RITM approval flips to approved
    _ensure_business_rule(
        "Okta Bridge - Flow2 approved", "async", BR2,
        f"current.cat_item == '{f2['sys_id']}' && current.approval == 'approved' "
        f"&& current.approval.changes()")


STEPS = {"table": setup_table, "properties": setup_properties, "script_include": setup_script_include,
         "catalog": setup_catalog, "business_rules": setup_business_rules}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=list(STEPS), default=None)
    args = ap.parse_args()
    if not SN_URL or not SN_AUTH[0]:
        sys.exit("SN_URL / SN_USER / SN_PASS env required")
    me = S.get(f"{SN_URL}/api/now/table/sys_user",
               params={"sysparm_query": f"user_name={SN_AUTH[0]}", "sysparm_limit": 1, "sysparm_fields": "user_name"})
    print(f"auth check -> HTTP {me.status_code}")
    me.raise_for_status()
    for name, fn in STEPS.items():
        if args.only and name != args.only:
            continue
        fn()
    print("done.")


if __name__ == "__main__":
    main()
