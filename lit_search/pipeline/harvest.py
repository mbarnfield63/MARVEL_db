"""Bulk API harvest for one tier of the MARVEL citing-papers worklist.

Metadata + data-link probes only, no data downloads.

    python harvest.py [worklist.tsv] [tier]

The worklist is the ORIGINAL 9-column file (rank, doi, year, first_author,
title, molecules_mentioned, has_marvel_data_guess, data_location, notes) -- not
the rewritten schema. Recover it with:

    git show <rev>:lit_search/marvel_citing_papers.tsv > worklist.tsv
"""
import json, os, re, sys, time
import requests

MAILTO = "mbarnfield63@gmail.com"
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "harvest")
TSV = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "worklist.tsv")
TIER = sys.argv[2] if len(sys.argv) > 2 else "high"
S = requests.Session()
S.headers["User-Agent"] = f"db_MARVEL-litreview/1.0 (mailto:{MAILTO})"

# ponytail: extension list is the observed Elsevier mmc set; widen only if probes keep missing
ELS_EXT = ["zip", "txt", "pdf", "docx", "xlsx", "dat", "csv", "tar.gz"]


def get(url, **kw):
    try:
        r = S.get(url, timeout=40, **kw)
        return r
    except Exception as e:
        return None


def crossref(doi):
    r = get(f"https://api.crossref.org/works/{doi}", params={"mailto": MAILTO})
    if r is None or r.status_code != 200:
        return None
    return r.json().get("message")


def unpaywall(doi):
    r = get(f"https://api.unpaywall.org/v2/{doi}", params={"email": MAILTO})
    if r is None or r.status_code != 200:
        return None
    return r.json()


def zenodo(doi):
    r = get("https://zenodo.org/api/records", params={"q": f'"{doi}"', "size": 5})
    if r is None or r.status_code != 200:
        return []
    hits = r.json().get("hits", {}).get("hits", [])
    return [{"doi": h.get("doi"), "title": h.get("title"), "url": h.get("links", {}).get("self_html") or h.get("links", {}).get("html"),
             "files": [f.get("key") for f in (h.get("files") or [])][:30]} for h in hits]


def els_pii(cr):
    if not cr:
        return None
    for l in cr.get("link", []) or []:
        m = re.search(r"PII:([A-Z0-9]+)", l.get("URL", ""))
        if m:
            return m.group(1)
    for a in cr.get("alternative-id", []) or []:
        if re.fullmatch(r"S[0-9X]{16,17}", a):
            return a
    return None


def probe_els(pii):
    found = []
    for n in range(1, 7):
        hit_any = False
        for ext in ELS_EXT:
            u = f"https://ars.els-cdn.com/content/image/1-s2.0-{pii}-mmc{n}.{ext}"
            try:
                r = S.head(u, timeout=25, allow_redirects=True)
            except Exception:
                continue
            if r.status_code == 200 and "xml" not in (r.headers.get("content-type") or ""):
                found.append({"url": u, "type": r.headers.get("content-type"),
                              "len": r.headers.get("content-length"),
                              "cd": r.headers.get("content-disposition")})
                hit_any = True
                break
        if not hit_any and n > 1:
            break
    return found


def main():
    rows = []
    with open(TSV, encoding="utf-8") as f:
        hdr = f.readline()
        for line in f:
            c = line.rstrip("\n").split("\t")
            if len(c) >= 7 and c[6] == TIER:
                rows.append(c)
    os.makedirs(OUT, exist_ok=True)
    print(f"{len(rows)} {TIER} rows", flush=True)
    for i, c in enumerate(rows):
        rank, doi, year = c[0], c[1], c[2]
        p = os.path.join(OUT, f"{rank}.json")
        if os.path.exists(p):
            continue
        rec = {"rank": rank, "doi": doi, "year": year, "first_author": c[3],
               "title": c[4], "molecules_guess": c[5], "notes_old": c[8] if len(c) > 8 else ""}
        cr = crossref(doi)
        if cr:
            rec["cr"] = {
                "title": cr.get("title"), "type": cr.get("type"),
                "container": cr.get("container-title"), "publisher": cr.get("publisher"),
                "volume": cr.get("volume"), "issue": cr.get("issue"), "page": cr.get("page"),
                "article_number": cr.get("article-number"),
                "issued": cr.get("issued", {}).get("date-parts"),
                "authors": [f"{a.get('family','')}, {a.get('given','')}" for a in cr.get("author", [])],
                "relation": cr.get("relation"), "url": cr.get("URL"),
                "abstract": (cr.get("abstract") or "")[:1500],
                "alt_id": cr.get("alternative-id"),
            }
        up = unpaywall(doi)
        if up:
            rec["oa"] = {"is_oa": up.get("is_oa"),
                         "locs": [{"url": l.get("url"), "url_pdf": l.get("url_for_pdf"), "host": l.get("host_type"), "repo": l.get("repository_institution")}
                                  for l in (up.get("oa_locations") or [])][:5]}
        z = zenodo(doi)
        if z:
            rec["zenodo"] = z
        pii = els_pii(cr)
        if pii:
            rec["pii"] = pii
            rec["els_si"] = probe_els(pii)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=1)
        print(f"[{i+1}/{len(rows)}] {rank} {doi} si={len(rec.get('els_si',[]))} zen={len(z)}", flush=True)
        time.sleep(0.2)


if __name__ == "__main__":
    main()
