#!/usr/bin/env python3
"""
Make the APP-*-Admin groups requestable in Okta OIG via **request conditions**, so the
ServiceNow Flow 1 (SN request -> Okta OIG access request -> approval + provisioning) can target
them. Then print each resulting catalog entry id to drop into the SN property
`x_okta_bridge.flow1_entry_id`.

Request conditions in this org attach to the **app resource** and can scope access to specific
**GROUPS** (confirmed via /resources/{appId}/request-settings -> validAccessScopeSettings GROUPS).
The condition needs an `approvalSequenceId` — a 24-char id of an approval sequence. That object's
create/list API is NOT exposed (every approval-sequences endpoint returns 405), so create ONE
approval sequence in the Okta Admin Console (OIG > Access Requests) and pass its id here:

    OKTA_API_TOKEN=... APPROVAL_SEQUENCE_ID=<24-char id> python3 scripts/make_groups_requestable.py

Token: env OKTA_API_TOKEN, else ~/demo-vita-oig-apiKey. Org: env OKTA_ORG_URL (default vita).
Idempotent: skips a group that already has a matching request condition.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

ORG = os.environ.get("OKTA_ORG_URL", "https://demo-vita-oig.oktapreview.com").rstrip("/")
SEQ = os.environ.get("APPROVAL_SEQUENCE_ID", "").strip()

# The groups created by this work (name -> group id, app id).
GROUPS = [
    {"name": "APP-HealthApp-Admin", "group_id": "00gzs3t398ms3spDN1d7", "app_id": "0oazbsrw90E3OVYhF1d7"},
    {"name": "APP-TransportationApp-Admin", "group_id": "00gzs3yctbm1stdYx1d7", "app_id": "0oazbs2lnjG0dc5Xd1d7"},
    {"name": "APP-FinanceApp-Admin", "group_id": "00gzs3kp3kxv6bF6U1d7", "app_id": "0oaz9uli6l0JMmZ0W1d7"},
]


def _token():
    t = os.environ.get("OKTA_API_TOKEN", "").strip()
    if t:
        return t
    p = os.path.expanduser("~/demo-vita-oig-apiKey")
    if os.path.exists(p):
        return open(p).read().strip()
    sys.exit("OKTA_API_TOKEN env or ~/demo-vita-oig-apiKey required")


def call(method, path, body=None):
    url = f"{ORG}{path}"
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, method=method)
    req.add_header("Authorization", f"SSWS {_token()}")
    req.add_header("Accept", "application/json")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.getcode(), (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, raw.decode()[:300]


def make_requestable(g):
    """Create the request condition (if missing) and ACTIVATE it. Conditions are created
    status=INACTIVE, so the activate step is required."""
    name = f"Request {g['name']}"
    st, conds = call("GET", f"/governance/api/v2/resources/{g['app_id']}/request-conditions?limit=50")
    cond = next((c for c in (conds or {}).get("data", []) if c.get("name") == name), None) if st < 300 else None
    if not cond:
        body = {
            "name": name,
            "requesterSettings": {"type": "EVERYONE"},
            "accessScopeSettings": {"type": "GROUPS", "groups": [{"id": g["group_id"]}]},
            "approvalSequenceId": SEQ,
        }
        st, cond = call("POST", f"/governance/api/v2/resources/{g['app_id']}/request-conditions", body)
        if st >= 300:
            print(f"   {g['name']}: create FAILED {st} {cond}")
            return
        print(f"   {g['name']}: condition created ({cond.get('id')})")
    else:
        print(f"   {g['name']}: condition exists ({cond.get('id')}, status {cond.get('status')})")
    if cond.get("status") != "ACTIVE":
        ast, _ = call("POST", f"/governance/api/v2/resources/{g['app_id']}/request-conditions/{cond['id']}/activate")
        print(f"   {g['name']}: activate -> HTTP {ast}")


def list_entries():
    """The catalog entry created is the APP entry (e.g. 'Health App') — that's the Flow 1 target."""
    st, data = call("GET", "/governance/api/v2/catalogs/default/entries?filter=" +
                    urllib.parse.quote("name pr") + "&limit=100")
    for e in (data or {}).get("data", []):
        print(f"   requestable={e.get('requestable')} {e.get('id')} {e.get('name')}")


def main():
    if not SEQ or len(SEQ) < 24:
        sys.exit("APPROVAL_SEQUENCE_ID (24-char approval sequence id) is required. Create one approval "
                 "sequence in the OIG Admin Console, then re-run.")
    print("[request-conditions] making APP-*-Admin groups requestable")
    for g in GROUPS:
        make_requestable(g)
    print("[catalog entries] (the APP entry is the Flow 1 target)")
    list_entries()


if __name__ == "__main__":
    main()
