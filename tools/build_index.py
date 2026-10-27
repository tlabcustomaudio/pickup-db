"""pickup-db: validate every capture in pickups/ and guitars/ against schema/, then write index.json = one entry per
brand + model + position + type + wiring, with the community average of each measured parameter.

How the average is made (CAPTURE.md explains why):
- Rdc is normalised to 20 C when the capture says the room temperature (copper: +0.393 %/C).
- A capture whose repeated scans disagree (f0 spread > 2 %) is listed but left out of the averages.
- Estimated parameters (not measured by that capture) never enter the average of that parameter.
- With 4 or more values, outliers (more than 3 robust sigmas from the median) are dropped.
- 'profile' = the values a simulator uses: the measured average, else the average of the estimates.

RackNAM and Coil of Duty download index.json at start. Run: python3 tools/build_index.py [--selftest | --check]"""
import glob
import json
import math
import os
import statistics
import sys
import uuid

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCH = {n: json.load(open(os.path.join(ROOT, "schema", n))) for n in ("pickup.schema.json", "guitar.schema.json")}
REG = Registry().with_resources([(s["$id"], Resource.from_contents(s)) for s in SCH.values()])
VAL = {k: Draft202012Validator(SCH[k + ".schema.json"], registry=REG) for k in ("pickup", "guitar")}
PARAMS = ("rdc_ohm", "L_H", "re_ohm", "cp_F")
ALPHA_CU, T_REF = 0.00393, 20.0
MAX_F0_SPREAD = 2.0
norm = lambda s: " ".join((s or "").lower().split())


def load(kind, folder):
    out, bad = [], []
    for f in sorted(glob.glob(os.path.join(folder, "**", "*.json"), recursive=True)):
        try:
            d = json.load(open(f))
        except ValueError as e:
            bad.append((f, [str(e)]))
            continue
        errs = [e.message for e in VAL[kind].iter_errors(d)]
        (bad if errs else out).append((f, errs) if errs else d)
    return out, bad


def rdc20(p):
    t = p["context"].get("temp_c")
    return p["params"]["rdc_ohm"] / (1 + ALPHA_CU * (t - T_REF)) if t is not None else p["params"]["rdc_ohm"]


def trusted(p):
    return (p["context"].get("repeats") or {}).get("f0_sd_pct", 0) <= MAX_F0_SPREAD


def robust(v):
    """drop values > 3 robust sigmas (1.4826 MAD) from the median, only with 4+ values."""
    if len(v) < 4:
        return v, 0
    med = statistics.median(v)
    mad = 1.4826 * statistics.median(abs(x - med) for x in v)
    keep = [x for x in v if mad == 0 or abs(x - med) <= 3 * mad]
    return keep, len(v) - len(keep)


def stats(v):
    mu = sum(v) / len(v)
    return {"mean": mu, "sd": math.sqrt(sum((x - mu) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else None, "n": len(v)}


def value(p, k):
    return rdc20(p) if k == "rdc_ohm" else p["params"][k]


def index(pickups, guitars):
    groups = {}
    for p in pickups + [s["pickup"] for g in guitars for s in g["pickups"]]:
        if not (p["brand"] and p["model"]):
            continue  # anonymous captures stay out of the catalog
        wiring = p["context"].get("wiring") or ("series" if "humbucker" in p["type"] else "single")
        groups.setdefault((norm(p["brand"]), norm(p["model"]), p["position"], p["type"], wiring), []).append(p)
    entries = []
    for (_b, _m, pos, typ, wiring), ps in sorted(groups.items()):
        good = [p for p in ps if trusted(p)]
        e = {"name": f"{ps[0]['brand']} {ps[0]['model']} ({pos})", "brand": ps[0]["brand"], "model": ps[0]["model"], "position": pos,
             "type": typ, "wiring": wiring, "count": len(ps), "used": len(good), "ids": [p["id"] for p in ps],
             "protocol_captures": sum(1 for p in ps if p["context"].get("protocol")), "params": {}, "profile": {}, "outliers": 0}
        for k in PARAMS:
            measured = [value(p, k) for p in good if k not in p["quality"]["estimated"]]
            measured, dropped = robust(measured)
            e["outliers"] += dropped
            if measured:
                e["params"][k] = stats(measured)
                e["profile"][k] = e["params"][k]["mean"]
            elif good or ps:
                est = [value(p, k) for p in (good or ps)]
                e["profile"][k] = sum(est) / len(est)  # nobody measured it: the estimate, flagged
                e.setdefault("estimated", []).append(k)
        for k in ("f0_std_load_hz", "q_std_load"):
            v = [p["derived"][k] for p in (good or ps)]
            e[k] = sum(v) / len(v)
        entries.append(e)
    return {"schema": "pickupdb.index/1", "pickups": entries, "guitars": [{"id": g["id"], "name": g["name"]} for g in guitars]}


def build(check=False):
    pk, bp = load("pickup", os.path.join(ROOT, "pickups"))
    gt, bg = load("guitar", os.path.join(ROOT, "guitars"))
    for f, errs in bp + bg:
        print("INVALID", os.path.relpath(f, ROOT), "|", "; ".join(errs[:3]))
    if bp + bg:
        sys.exit(1)
    ids = [p["id"] for p in pk] + [g["id"] for g in gt]
    if len(ids) != len(set(ids)):
        sys.exit("duplicate ids")
    idx = index(pk, gt)
    if not check:
        json.dump(idx, open(os.path.join(ROOT, "index.json"), "w"), indent=1)
    print(f"index.json: {len(idx['pickups'])} pickups from {len(pk)} captures + {len(gt)} guitars")


def selftest():
    def prof(rdc, method="xray", est=(), brand="Acme", model="Vintage 59", **ctx):
        return {"schema": "coilofduty.pickup/1", "id": str(uuid.uuid4()), "brand": brand, "model": model, "position": "bridge",
                "type": "humbucker", "params": {"rdc_ohm": rdc, "L_H": 4.4, "re_ohm": 250e3, "cp_F": 1.1e-10},
                "quality": {"method": method, "fit_rms_db": 0.01, "estimated": list(est)},
                "derived": {"f0_unloaded_hz": 7000, "q_unloaded": 3, "f0_std_load_hz": 3000, "q_std_load": 1.9,
                            "std_load": {"r_ohm": 2e5, "c_F": 4.7e-10}}, "context": {"tool": "test", "date": "2026-10-27", **ctx}}
    a, b, c = prof(8000), prof(8400), prof(8200, "scan", ["re_ohm"], brand="ACME ", model="vintage  59")
    warm = prof(8000 * (1 + ALPHA_CU * 10), temp_c=30.0, protocol="capture/1")  # same coil measured at 30 C
    shaky = prof(5000, repeats={"n": 3, "f0_sd_pct": 5.0})                        # repeats disagree: not averaged
    wild = prof(20000)                                                           # outlier among 5
    assert all(not list(VAL["pickup"].iter_errors(p)) for p in (a, b, c, warm, shaky))
    assert list(VAL["pickup"].iter_errors(dict(a, position="headstock"))), "schema must reject bad enums"
    idx = index([a, b, c, warm, shaky, wild, prof(1, brand="")], [])
    assert len(idx["pickups"]) == 1, idx  # same pickup despite case/spaces; anonymous left out
    e = idx["pickups"][0]
    assert e["count"] == 6 and e["used"] == 5 and e["outliers"] == 1 and e["protocol_captures"] == 1, e
    assert abs(e["params"]["rdc_ohm"]["mean"] - 8150) < 1e-6 and e["params"]["re_ohm"]["n"] == 4, e["params"]
    split = prof(4100, model="Vintage 59", wiring="split")
    assert len(index([a, split], [])["pickups"]) == 2  # a split humbucker is another entry
    only_est = index([prof(7000, "manual", ["re_ohm", "cp_F"], model="X")], [])["pickups"][0]
    assert only_est["estimated"] == ["re_ohm", "cp_F"] and only_est["profile"]["cp_F"] == 1.1e-10 and "cp_F" not in only_est["params"]
    print("SELFTEST OK")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else build("--check" in sys.argv)
