"""Build one tier's rows of the new marvel_citing_papers.tsv from harvest + decisions.

    python build_tsv.py [lo] [hi] [out.tsv]     # defaults: high tier, 1 137
"""
import json, os, re, glob, sys, unicodedata
from decisions import D, EXTRA_LINKS
from sweep import SWEEP

ROOT = os.path.dirname(os.path.abspath(__file__))
LO = int(sys.argv[1]) if len(sys.argv) > 1 else 1
HI = int(sys.argv[2]) if len(sys.argv) > 2 else 137
OUT = sys.argv[3] if len(sys.argv) > 3 else "high_tier_rows.tsv"
d2k = json.load(open(os.path.join(ROOT, "doi2key.json")))
EXOMOL = re.compile(r"^\d{2}[A-Za-z]")

recs = {}
for p in glob.glob(os.path.join(ROOT, "harvest", "*.json")):
    r = json.load(open(p, encoding="utf-8"))
    recs[int(r["rank"])] = r


def mint(rec):
    """ExoMol-style tag: YY + 2-letter surname prefixes of the first three authors."""
    yr = str(rec.get("year") or "")[-2:]
    auth = (rec.get("cr") or {}).get("authors") or []
    parts = []
    for a in auth[:3]:
        fam = a.split(",")[0].strip()
        fam = "".join(c for c in unicodedata.normalize("NFKD", fam) if not unicodedata.combining(c))
        fam = re.sub(r"[^A-Za-z]", "", fam)
        parts.append((fam[:2].capitalize() or "Xx"))
    while len(parts) < 3:
        parts.append("xx")
    return yr + "".join(parts)


def key_for(rank, rec):
    ks = [k["key"] for k in d2k.get((rec.get("doi") or "").lower(), [])]
    tags = sorted(set(k for k in ks if EXOMOL.match(k)))
    plain = [t for t in tags if "." not in t]
    if plain:
        return plain[0], ""
    if tags:
        return tags[0], ""
    return mint(rec), "minted key"


def links_for(rank, rec):
    urls, kinds = [], []
    for u, k in EXTRA_LINKS.get(rank, []):
        urls.append(u); kinds.append(k)
    si = rec.get("els_si") or []
    non_pdf = [f for f in si if "pdf" not in (f.get("type") or "")]
    for f in (non_pdf or si):
        u = f["url"]
        urls.append(u)
        kinds.append("SI_zip" if u.endswith(".zip") else "SI_file")
    return urls, kinds


rows, browser, dropped = [], [], []
for rank in sorted(r for r in D if LO <= r <= HI):
    verdict, mols, method, status, note = D[rank]
    rec = recs.get(rank, {"rank": rank, "doi": "", "year": "", "title": ""})
    if verdict != "K":
        dropped.append((rank, verdict.split(":", 1)[1], rec.get("doi", ""), rec.get("title", "")[:70]))
        continue
    key, kn = key_for(rank, rec)
    urls, kinds = links_for(rank, rec)
    sw_note = ""
    if rank in SWEEP:
        status, sw_links, sw_note = SWEEP[rank]
        for u, k in sw_links:
            urls.append(u); kinds.append(k)
    notes = "; ".join(x for x in (note, sw_note, kn) if x)
    if status == "pending":
        browser.append((rank, key, rec.get("doi", ""), rec.get("cr", {}).get("container", [""])[0] if rec.get("cr") else "", note))
    rows.append([key, rec.get("doi", ""), str(rec.get("year", "")), mols, method, status,
                 "|".join(urls), "|".join(kinds), notes])

missing = [i for i in range(LO, HI + 1) if i not in D]

# ponytail: disambiguate colliding keys with a/b suffixes (plan rule), oldest first
seen = {}
for r in sorted(rows, key=lambda r: (r[0], r[2])):
    seen.setdefault(r[0], []).append(r)
for k, group in seen.items():
    if len(group) > 1:
        for i, r in enumerate(group):
            r[0] = k + chr(ord("a") + i)
            r[8] = "; ".join(x for x in (r[8], f"key suffixed - collided with {k}") if x)

rows.sort(key=lambda r: (r[3], -int(r[2] or 0)))

out = os.path.join(ROOT, OUT)
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write(f"# ranks {LO}-{HI}\n")
    f.write("\t".join(["bibtex_key", "doi", "year", "molecules", "method", "data_status",
                       "data_links", "link_kind", "notes"]) + "\n")
    for r in rows:
        f.write("\t".join(r) + "\n")

print(f"kept {len(rows)}  dropped {len(dropped)}  pending-browser {len(browser)}  unclassified {missing}")
dupkeys = {}
for r in rows:
    dupkeys.setdefault(r[0], []).append(r[1])
print("DUPLICATE KEYS:", {k: v for k, v in dupkeys.items() if len(v) > 1})
print("\n--- NEEDS BROWSER ---")
for b in browser:
    print(f"{b[0]:>4} {b[1]:<14} {b[2]:<34} {b[3][:32]:<34} {b[4][:60]}")
print("\n--- DROPPED ---")
for d in dropped:
    print(f"{d[0]:>4} {d[1]:<22} {d[2]:<34} {d[3]}")
