"""Smoke check against a running API with data loaded.

    uv run --env-file .env uvicorn api.main:app &
    uv run python -m api.check [base_url]
"""

import json
import sys
from urllib.error import HTTPError
from urllib.request import urlopen

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"


def get(path):
    try:
        with urlopen(BASE + path) as r:
            body = r.read()
            return r.status, json.loads(body) if r.headers.get_content_type() == "application/json" else body
    except HTTPError as e:
        return e.code, None


slug = get("/molecules")[1][0]["slug"]
run = get(f"/molecules/{slug}/runs")[1][0]
assert {"id", "version", "publication", "n_levels", "files"} <= run.keys(), run
rid = run["id"]

qn_names = get(f"/runs/{rid}")[1]["qn_names"]
level = get(f"/runs/{rid}/levels?limit=1")[1][0]
assert get(f"/runs/{rid}/levels?qn_key={level['qn_key'].replace(' ', '%20').replace('+', '%2B')}")[1][0]["id"] == level["id"]
first = qn_names[0]
hits = get(f"/runs/{rid}/levels?qn.{first}={level['quantum_numbers'][first].replace('+', '%2B')}&limit=10000")[1]
assert all(h["quantum_numbers"][first] == level["quantum_numbers"][first] for h in hits) and hits
assert get(f"/runs/{rid}/levels?qn.not_a_qn=1")[0] == 422

role, size = next(iter(run["files"].items()))
status, body = get(f"/runs/{rid}/files/{role}")
assert status == 200 and len(body) == size

assert get("/runs/999999")[0] == 404
assert all("isotopologues" in p for p in get("/publications")[1])
print("ok")
