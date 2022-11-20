from datetime import datetime, timedelta

from plantpot import Plantpot, bad_request
from schemas.kvstore import InsertKVValuesReq, RetrieveKVValuesResp
from lib import is_hexstring

from models.kvstore import Value

app = Plantpot('kvstore')


@app.json(path="/insert",
          methods=["POST"],
          req_schema=InsertKVValuesReq,
          resp_status="202 Created")
def insert(body):
    now = datetime.now()

    for v in body['values']:
        expiry_time = datetime.fromtimestamp(v['expiryTime'])
        if expiry_time < now + timedelta(seconds=5):
            raise bad_request("Bad Expiry Time", "expiry time is in the past")

        xor_key = bytes.fromhex(v['xorKey'])
        key_hash = bytes.fromhex(v['key'])

        ins = Value.insert(key_hash=key_hash,
                           xor_key=xor_key,
                           value_str=v['value'],
                           expiry_time=expiry_time)
        ins.on_conflict_replace().execute()


@app.json(path="/retrieve",
          pass_query=True,
          resp_schema=RetrieveKVValuesResp)
def retrieve(**query):
    keys = []

    for k in query.get("key", []):
        if len(k) != 32 or not is_hexstring(k):
            raise bad_request("Invalid Key",
                              "keys must be hexstrings of 32 chars")
        keys.append(bytes.fromhex(k))

    if not keys:
        raise bad_request("Missing Key",
                          "the url must include at least one key param")

    expr = Value.key_hash == keys[0]
    for k in keys[1:]:
        expr = expr | (Value.key_hash == k)

    now = datetime.now()
    rows = {
        row.key_hash.hex(): row
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
