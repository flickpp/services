from datetime import datetime, timedelta

from framework import post_json_endpoint, get_json_endpoint, EmptyResponse, bad_request, app
from schemas import InsertKVValuesReq, RetrieveKVValuesResp, is_hexstring

from kvstore.model import Value


def insert(_ctx, body, **params):
    for v in body['values']:
        expiry_time = datetime.fromtimestamp(v['expiryTime'])
        if expiry_time < datetime.now() + timedelta(seconds=5):
            raise bad_request("Bad Expiry Time", "expiry time is in the past")

        xor_key = bytes.fromhex(v['xorKey'])
        key_id = bytes.fromhex(v['key'])

        ins = Value.insert(key_id=key_id, xor_key=xor_key, value_str=v['value'], expiry_time=expiry_time)
        ins.on_conflict_replace().execute()

    return EmptyResponse("202 Created", [])


def retrieve(_ctx, **params):
    keys = []

    for k in params.get("key", []):
        if len(k) != 32 or not is_hexstring(k):
            raise bad_request("Invalid Key", "keys must be hexstrings of 32 chars")
        keys.append(bytes.fromhex(k))

    if not keys:
        raise bad_request("Missing Key", "the url must include at least one key param")

    expr = Value.key_id == keys[0]
    for k in keys[1:]:
        expr = expr | (Value.key_id == k)

    now = datetime.now()
    rows = {
        row.key_id.hex(): row
        for row in Value.select().where(expr)
        if row.expiry_time > (now + timedelta(seconds=5))
    }

    values = []
    for k in keys:
        k = k.hex()

        if k in rows:
            values.append({
                "key": k,
                "value": rows[k].value_str,
                "xorKey": rows[k].xor_key.hex(),
                "expiryTime": rows[k].expiry_time.timestamp(),
            })
        else:
            values.append({
                "key": k,
                "value": None,
                "xorKey": None,
                "expiryTime": None,
            })

    return dict(values=values)


post_json_endpoint("/insert", InsertKVValuesReq, insert, require_session_id=False)
get_json_endpoint("/retrieve", RetrieveKVValuesResp, retrieve, require_session_id=False)
