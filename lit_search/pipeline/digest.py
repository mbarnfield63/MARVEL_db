"""Compact digest of the harvest for manual classification."""
import json, os, glob, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
d2k = json.load(open(os.path.join(ROOT, "doi2key.json")))

EXOMOL = re.compile(r"^\d{2}[A-Za-z]")

def key_for(doi):
    ks = [k["key"] for k in d2k.get(doi.lower(), [])]
    if not ks:
        return ""
    tags = sorted(set(k for k in ks if EXOMOL.match(k)))
    if tags:  # prefer plain tag over molecule-suffixed duplicate
        plain = [t for t in tags if "." not in t]
        return "/".join(dict.fromkeys((plain or tags) + [t for t in tags if t not in (plain or tags)]))
    return sorted(set(ks))[0]

recs = []
for p in sorted(glob.glob(os.path.join(ROOT, "harvest", "*.json")), key=lambda x: int(os.path.basename(x)[:-5])):
    recs.append(json.load(open(p, encoding="utf-8")))

lo, hi = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 10**9)
for r in recs:
    rk = int(r["rank"])
    if not (lo <= rk <= hi):
        continue
    cr = r.get("cr") or {}
    cont = (cr.get("container") or [""])[0]
    si = r.get("els_si") or []
    zen = r.get("zenodo") or []
    print(f"--- {r['rank']} | {r['year']} | {key_for(r['doi']) or '(NOKEY)'} | {r['doi']} | {cont[:38]}")
    print(f"    T: {r['title'][:150]}")
    if r.get("molecules_guess") or r.get("notes_old"):
        print(f"    old: mols={r.get('molecules_guess')} notes={r.get('notes_old')}")
    for f in si:
        print(f"    SI: {f['url'].split('-')[-1]:12s} {f.get('type','')} {f.get('len') or '?'}  {f['url']}")
    for z in zen:
        print(f"    ZEN: {z['doi']} | {str(z['title'])[:70]} | {z['url']} | files={z['files'][:6]}")
    oa = r.get("oa") or {}
    for l in (oa.get("locs") or [])[:2]:
        if l.get("host") == "repository":
            print(f"    OA: {l['url']}")
    ab = cr.get("abstract") or ""
    ab = re.sub(r"<[^>]+>", " ", ab)
    ab = re.sub(r"\s+", " ", ab).strip()
    if ab:
        print(f"    AB: {ab[:600]}")
