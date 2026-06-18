"""
ServiceNow <-> Okta bridge (AWS Lambda behind API Gateway HTTP API).

Three flows for the VITA OIG demo (org demo-vita-oig.oktapreview.com); the access
object throughout is Okta groups (the VITA agency groups):

  Flow 1  POST /servicenow/request   ServiceNow catalog request -> create an Okta OIG
                                      access request (governance/api/v2/requests). Okta
                                      runs the approval sequence AND provisions.
  Flow 2  POST /servicenow/approved  ServiceNow already approved -> fulfill in Okta now
                                      by adding the user to the target group. Optionally
                                      closes the RITM.
  Flow 3  POST /sync/groups          Pull Okta groups -> upsert a ServiceNow custom table
          (also EventBridge schedule) (x_okta_groups) so a SN catalog can list them.

Auth: ServiceNow -> bridge uses a shared secret header (x-bridge-secret). bridge ->
Okta uses an SSWS token; bridge -> ServiceNow uses basic auth. All secret material is
in one Secrets Manager secret: {okta_token, sn_base_url, sn_user, sn_pass, inbound_secret}.

Env: OKTA_ORG_URL, BRIDGE_SECRET_NAME, SN_TABLE (default x_okta_groups),
     GROUP_SYNC_FILTER (default type eq "OKTA_GROUP"), JUSTIFICATION_FIELD_ID (optional).
Pure stdlib + boto3.
"""

import base64
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

OKTA_ORG_URL = os.environ.get("OKTA_ORG_URL", "").strip().rstrip("/")
BRIDGE_SECRET_NAME = os.environ.get("BRIDGE_SECRET_NAME", "").strip()
SN_TABLE = os.environ.get("SN_TABLE", "x_okta_groups").strip()
GROUP_SYNC_FILTER = os.environ.get("GROUP_SYNC_FILTER", 'type eq "OKTA_GROUP"').strip()
JUSTIFICATION_FIELD_ID = os.environ.get("JUSTIFICATION_FIELD_ID", "").strip()
SN_CATALOG_TABLE = os.environ.get("SN_CATALOG_TABLE", "u_okta_requestable").strip()

# Flow 4 — Okta Access Requests V1 "Employee Onboarding (Pre-HR Feed)" request type.
# Field ids verified 2026-06-10. NOTE: editing the request type in Okta regenerates these ids
# (and SELECT options) — if creates start 409'ing, re-pull from a recent request of this type.
ONBOARD_REQUEST_TYPE_ID = os.environ.get("ONBOARD_REQUEST_TYPE_ID", "6a14744c947ae2aa8be1c098").strip()
ONBOARD_FIELD_IDS = {
    "first_name":           "ce49d104-85aa-41e4-866f-bf26ef8f2f72",
    "last_name":            "667f7565-a780-426f-9ba7-80d86fe16331",
    "agency":               "a8807066-0af4-4d5d-bbc5-95f4236c9d98",  # SELECT (value -> array)
    "job_title":            "452386bb-2e84-4aae-8773-59bbca36d976",
    "manager":              "caa5363b-dc1f-4dac-9136-30654dbc3bef",
    "manager_email":        "a7740982-222b-43a1-a244-acda23468575",
    "start_date":           "f90e6301-da17-4274-b047-c67aaa1b2f24",  # DATE (ISO 8601)
    "cardinal_employee_id": "448b6dd9-4dd5-465b-b43f-327c6ad858a7",
    "email":                "5b97b903-19a2-450d-9bc1-642a2a044e11",
    "username":             "ea0bb581-f50e-448d-a7b4-7b803e446bcc",
}
ONBOARD_SELECT_FIELDS = {"agency"}

_secret_cache = None


# ---------------------------------------------------------------------------
# Secrets + HTTP helpers (stdlib urllib)
# ---------------------------------------------------------------------------
def _secret():
    global _secret_cache
    if _secret_cache is None:
        c = boto3.client("secretsmanager")
        _secret_cache = json.loads(c.get_secret_value(SecretId=BRIDGE_SECRET_NAME)["SecretString"])
    return _secret_cache


def _http(method, url, headers, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method.upper())
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read()
            return r.getcode(), (json.loads(raw) if raw else None), r.headers
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            parsed = json.loads(raw) if raw else None
        except ValueError:
            parsed = {"_raw": raw.decode("utf-8", "ignore")}
        return e.code, parsed, e.headers


def _okta(method, path, body=None, params=None):
    url = f"{OKTA_ORG_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    h = {"Authorization": f"SSWS {_secret()['okta_token']}",
         "Accept": "application/json", "Content-Type": "application/json"}
    status, data, _ = _http(method, url, h, body)
    logger.info("OKTA %s %s -> %s", method, path, status)
    return status, data


def _okta_paginate(path, params=None):
    """GET, following Link rel=next. Okta list endpoints return a JSON array."""
    out = []
    url = f"{OKTA_ORG_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    h = {"Authorization": f"SSWS {_secret()['okta_token']}", "Accept": "application/json"}
    while url:
        status, data, hdrs = _http("GET", url, h)
        logger.info("OKTA GET %s -> %s (%d items)", url, status, len(data) if isinstance(data, list) else -1)
        if status >= 300 or not isinstance(data, list):
            break
        out.extend(data)
        url = _next_link(hdrs.get("Link") or hdrs.get("link"))
    return out


def _next_link(link_header):
    if not link_header:
        return None
    for part in link_header.split(","):
        seg = part.split(";")
        if len(seg) >= 2 and 'rel="next"' in seg[1]:
            return seg[0].strip().strip("<>")
    return None


def _sn(method, path, body=None, params=None):
    s = _secret()
    url = f"{s['sn_base_url'].rstrip('/')}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    token = base64.b64encode(f"{s['sn_user']}:{s['sn_pass']}".encode()).decode()
    h = {"Authorization": f"Basic {token}", "Accept": "application/json",
         "Content-Type": "application/json"}
    status, data, _ = _http(method, url, h, body)
    logger.info("SN %s %s -> %s", method, path, status)
    return status, data


def _resolve_user_id(email):
    """Okta user id from email/login."""
    status, data = _okta("GET", "/api/v1/users",
                         params={"search": f'profile.email eq "{email}" or profile.login eq "{email}"',
                                 "limit": 1})
    if status < 300 and isinstance(data, list) and data:
        return data[0]["id"]
    return None


# ---------------------------------------------------------------------------
# Flows
# ---------------------------------------------------------------------------
def flow1_request(body):
    """ServiceNow request -> Okta OIG access request (Okta approves + fulfills)."""
    email = (body.get("requested_for") or {}).get("email") or body.get("email")
    entry_id = body.get("catalog_entry_id") or body.get("entryId")
    if not email or not entry_id:
        return _json(400, {"error": "requested_for.email and catalog_entry_id are required"})
    uid = _resolve_user_id(email)
    if not uid:
        return _json(404, {"error": f"no Okta user for {email}"})
    req = {"requested": {"type": "CATALOG_ENTRY", "entryId": entry_id},
           "requestedFor": {"type": "OKTA_USER", "externalId": uid}}
    rfv = body.get("requester_field_values")
    if not rfv:
        # Auto-fill the entry's REQUIRED request fields (e.g. business justification) so the
        # ServiceNow side only has to pass justification text, not Okta field ids.
        # Only fill free-text fields — system fields like OKTA_REQUESTED_FOR (type OKTA_USER_ID)
        # are satisfied by the top-level requestedFor; stuffing them with justification text makes
        # Okta auto-reject the request.
        just = body.get("justification") or "Requested via ServiceNow"
        fst, fields = _okta("GET", f"/governance/api/v2/my/catalogs/default/entries/{entry_id}/request-fields")
        rfv = [{"id": f["id"], "values": [just]}
               for f in (fields or {}).get("data", [])
               if f.get("required") and f.get("type") == "TEXT"] if fst < 300 else []
        if JUSTIFICATION_FIELD_ID and not any(x["id"] == JUSTIFICATION_FIELD_ID for x in rfv):
            rfv.append({"id": JUSTIFICATION_FIELD_ID, "values": [just]})
    if rfv:
        req["requesterFieldValues"] = rfv
    status, data = _okta("POST", "/governance/api/v2/requests", body=req)
    if status >= 300:
        return _json(status, {"error": "okta request failed", "okta": data})
    return _json(201, {"okta_request_id": (data or {}).get("id"), "status": (data or {}).get("status"),
                       "ritm_sys_id": body.get("ritm_sys_id")})


def flow4_onboarding(body):
    """ServiceNow onboarding catalog request -> Okta Access Requests V1 request
    ('Employee Onboarding (Pre-HR Feed)'). The SN submitter is mapped to an Okta user by email
    and set as the requester; the new-hire details map to the request type's field values.
    Okta runs the request type's approval + actions."""
    email = (body.get("requested_for") or {}).get("email") or body.get("requester_email") or body.get("email")
    if not email:
        return _json(400, {"error": "requester email is required"})
    uid = _resolve_user_id(email)
    if not uid:
        return _json(404, {"error": f"no Okta user for {email}"})
    field_values = []
    for key, fid in ONBOARD_FIELD_IDS.items():
        val = body.get(key)
        if val in (None, ""):
            continue
        if key in ONBOARD_SELECT_FIELDS and not isinstance(val, list):
            val = [val]
        field_values.append({"id": fid, "value": val})
    subject = body.get("subject") or (
        f"{body.get('first_name', '')} {body.get('last_name', '')} "
        "— Employee Onboarding (Pre-HR Feed) via ServiceNow").strip()
    req = {"requestTypeId": ONBOARD_REQUEST_TYPE_ID, "subject": subject,
           "requesterUserIds": [uid], "requesterFieldValues": field_values}
    status, data = _okta("POST", "/governance/api/v1/requests", body=req)
    if status >= 300:
        return _json(status, {"error": "okta v1 onboarding request failed", "okta": data})
    return _json(201, {"okta_request_id": (data or {}).get("id"),
                       "permalink_id": (data or {}).get("permalinkId"),
                       "ritm_sys_id": body.get("ritm_sys_id")})


def flow2_approved(body):
    """ServiceNow approved -> add user to the Okta group, optionally close the RITM."""
    email = (body.get("requested_for") or {}).get("email") or body.get("email")
    group_id = body.get("group_id")
    if not email or not group_id:
        return _json(400, {"error": "email and group_id are required"})
    uid = _resolve_user_id(email)
    if not uid:
        return _json(404, {"error": f"no Okta user for {email}"})
    status, _ = _okta("PUT", f"/api/v1/groups/{group_id}/users/{uid}")
    if status >= 300:
        return _json(status, {"error": "group assignment failed"})
    result = {"assigned": True, "user_id": uid, "group_id": group_id}
    ritm = body.get("ritm_sys_id")
    if ritm:  # best-effort: close the RITM (state 3 = Closed Complete)
        st, _ = _sn("PATCH", f"/api/now/table/sc_req_item/{ritm}",
                    body={"state": "3", "comments": f"Provisioned in Okta: user {uid} added to group {group_id}"})
        result["ritm_closed"] = st < 300
    return _json(200, result)


def flow3_sync_groups():
    """Upsert Okta groups into the ServiceNow custom table for the catalog."""
    groups = _okta_paginate("/api/v1/groups", {"filter": GROUP_SYNC_FILTER, "limit": 200})
    now = datetime.now(timezone.utc).isoformat()
    synced = errors = 0
    for g in groups:
        gid = g.get("id")
        prof = g.get("profile") or {}
        row = {"u_okta_group_id": gid, "u_name": prof.get("name", ""),
               "u_description": prof.get("description") or "", "u_okta_group_type": g.get("type", ""),
               "u_last_sync": now}
        st, data = _sn("GET", f"/api/now/table/{SN_TABLE}",
                       params={"sysparm_query": f"u_okta_group_id={gid}", "sysparm_limit": 1,
                               "sysparm_fields": "sys_id"})
        existing = (data or {}).get("result") if isinstance(data, dict) else None
        if st < 300 and existing:
            ust, _ = _sn("PATCH", f"/api/now/table/{SN_TABLE}/{existing[0]['sys_id']}", body=row)
        else:
            ust, _ = _sn("POST", f"/api/now/table/{SN_TABLE}", body=row)
        synced += 1 if ust < 300 else 0
        errors += 0 if ust < 300 else 1
    logger.info("sync complete: %d ok, %d errors of %d groups", synced, errors, len(groups))
    return _json(200, {"groups": len(groups), "synced": synced, "errors": errors})


def _okta_gov_paginate(path, params=None):
    """GET a governance v2 list ({data:[...], _links.next.href}), following next."""
    out = []
    url = f"{OKTA_ORG_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    h = {"Authorization": f"SSWS {_secret()['okta_token']}", "Accept": "application/json"}
    while url:
        status, data, _ = _http("GET", url, h)
        logger.info("OKTA GET %s -> %s", url, status)
        if status >= 300 or not isinstance(data, dict):
            break
        out.extend(data.get("data", []))
        url = (((data.get("_links") or {}).get("next") or {}).get("href"))
    return out


def flow_sync_catalog():
    """Upsert REQUESTABLE OIG catalog entries (apps/groups with a request condition) into the
    SN catalog table, so anything made requestable in Okta auto-appears for Flow 1 with its
    catalog entry id."""
    # The end-user ("my") catalog reflects accurate requestable flags; the requestable item is
    # usually a CHILD entry (the group within an app, when access scope = GROUPS). Collect
    # requestable parents + their children.
    base = "/governance/api/v2/my/catalogs/default/entries"
    parents = _okta_gov_paginate(base, {"filter": "not(parent pr)", "limit": 200})
    entries = list(parents)
    for p in parents:
        entries.extend(_okta_gov_paginate(base, {"filter": f'parent eq "{p.get("id")}"', "limit": 200}))
    req = [e for e in entries if e.get("requestable")]
    now = datetime.now(timezone.utc).isoformat()
    synced = errors = 0
    for e in req:
        eid = e.get("id")
        row = {"u_entry_id": eid, "u_name": e.get("name", ""),
               "u_description": e.get("description") or "", "u_last_sync": now}
        st, data = _sn("GET", f"/api/now/table/{SN_CATALOG_TABLE}",
                       params={"sysparm_query": f"u_entry_id={eid}", "sysparm_limit": 1,
                               "sysparm_fields": "sys_id"})
        existing = (data or {}).get("result") if isinstance(data, dict) else None
        if st < 300 and existing:
            ust, _ = _sn("PATCH", f"/api/now/table/{SN_CATALOG_TABLE}/{existing[0]['sys_id']}", body=row)
        else:
            ust, _ = _sn("POST", f"/api/now/table/{SN_CATALOG_TABLE}", body=row)
        synced += 1 if ust < 300 else 0
        errors += 0 if ust < 300 else 1
    logger.info("catalog sync: %d entries, %d requestable, %d ok, %d errors", len(entries), len(req), synced, errors)
    return _json(200, {"entries": len(entries), "requestable": len(req), "synced": synced, "errors": errors})


# ---------------------------------------------------------------------------
# Handler / routing
# ---------------------------------------------------------------------------
def handler(event, context):
    # EventBridge scheduled invoke (no HTTP context) -> run the group sync.
    http = (event.get("requestContext") or {}).get("http")
    if not http:
        if event.get("source") == "aws.events" or event.get("scheduled"):
            g = json.loads(flow3_sync_groups()["body"])
            c = json.loads(flow_sync_catalog()["body"])
            return _json(200, {"groups": g, "catalog": c})
        return _json(400, {"error": "unrecognized event"})

    method, path = http.get("method", "GET"), event.get("rawPath", "/")
    if path == "/healthz":
        return _json(200, {"status": "ok"})
    if not OKTA_ORG_URL or not BRIDGE_SECRET_NAME:
        return _json(500, {"error": "bridge not configured"})

    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    try:
        if headers.get("x-bridge-secret", "") != _secret().get("inbound_secret"):
            return _json(401, {"error": "invalid bridge secret"})
    except ClientError:
        return _json(500, {"error": "bridge secret unavailable"})

    raw = event.get("body")
    if raw and event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    try:
        body = json.loads(raw) if raw else {}
    except ValueError:
        return _json(400, {"error": "invalid JSON body"})

    try:
        if method == "POST" and path == "/servicenow/onboarding":
            return flow4_onboarding(body)
        if method == "POST" and path == "/servicenow/request":
            return flow1_request(body)
        if method == "POST" and path == "/servicenow/approved":
            return flow2_approved(body)
        if method == "POST" and path == "/sync/groups":
            return flow3_sync_groups()
        if method == "POST" and path == "/sync/catalog":
            return flow_sync_catalog()
        return _json(404, {"error": f"no route for {method} {path}"})
    except Exception as e:  # noqa
        logger.exception("handler error")
        return _json(500, {"error": str(e)})


def _json(status, obj):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"},
            "body": json.dumps(obj), "isBase64Encoded": False}
