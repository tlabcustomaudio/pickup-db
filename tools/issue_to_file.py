"""GitHub Action helper: the 'Pickup capture' issue body -> pickups/<brand>/<model>/<id>.json, validated.
Usage: python3 tools/issue_to_file.py <issue-body-file>  -> prints the written path; exit 1 with the reason otherwise.
The profile is data, never code: only json.loads, schema validation, and a file name made of safe characters."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_index import ROOT, VAL  # noqa: E402

slug = lambda s: re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:60] or "unknown"


def main(path):
    body = open(path, encoding="utf-8").read()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", body, re.S) or re.search(r"(\{.*\})", body, re.S)
    if not m:
        sys.exit("no JSON profile found in the issue")
    try:
        p = json.loads(m[1])
    except ValueError as e:
        sys.exit(f"the profile is not valid JSON: {e}")
    errs = [e.message for e in VAL["pickup"].iter_errors(p)]
    if errs:
        sys.exit("the profile does not match the schema: " + "; ".join(errs[:5]))
    if not (p["brand"].strip() and p["model"].strip()):
        sys.exit("brand and model are required to share a capture")
    if not re.fullmatch(r"[0-9a-f-]{36}", p["id"]):
        sys.exit("bad id")
    out = os.path.join(ROOT, "pickups", slug(p["brand"]), slug(p["model"]), p["id"] + ".json")
    if os.path.exists(out):
        sys.exit("this capture is already in the database")
    p.pop("z", None) if len(json.dumps(p)) > 200_000 else None  # raw impedance only when small
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(p, open(out, "w"), indent=1)
    print(os.path.relpath(out, ROOT))


if __name__ == "__main__":
    main(sys.argv[1])
