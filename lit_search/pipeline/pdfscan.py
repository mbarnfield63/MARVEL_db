"""Pull OA PDFs of high-tier papers and extract their data-availability / supplementary statements."""
import json, os, re, glob, sys
import requests, fitz

ROOT = os.path.dirname(os.path.abspath(__file__))
PDFS = os.path.join(ROOT, "pdfs")
os.makedirs(PDFS, exist_ok=True)
S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0 (compatible; db_MARVEL-litreview/1.0; mailto:mbarnfield63@gmail.com)"

CUE = re.compile(r"(data availability|supplementary (material|data|information)|supporting information|"
                 r"available (online|at|from|as)|can be (found|downloaded|obtained)|zenodo|vizier|cdsarc|"
                 r"exomol\.com|www\.exomol|doi\.org/10\.5281|marvel input|\.marvel)", re.I)


def pick_pdf(rec):
    for l in (rec.get("oa") or {}).get("locs", []):
        for u in (l.get("url_pdf"), l.get("url")):
            if not u:
                continue
            if "arxiv.org/pdf" in u or u.lower().endswith(".pdf"):
                return u
    return None


def main():
    lo, hi = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 10**9)
    for p in sorted(glob.glob(os.path.join(ROOT, "harvest", "*.json")), key=lambda x: int(os.path.basename(x)[:-5])):
        rec = json.load(open(p, encoding="utf-8"))
        rk = rec["rank"]
        if not lo <= int(rk) <= hi:
            continue
        u = pick_pdf(rec)
        if not u:
            continue
        fp = os.path.join(PDFS, f"{rk}.pdf")
        if not os.path.exists(fp):
            try:
                r = S.get(u, timeout=90)
                if r.status_code != 200 or not r.content[:4] == b"%PDF":
                    print(f"### {rk}: FETCHFAIL {r.status_code} {u}", flush=True)
                    continue
                open(fp, "wb").write(r.content)
            except Exception as e:
                print(f"### {rk}: ERR {e} {u}", flush=True)
                continue
        try:
            doc = fitz.open(fp)
            txt = "\n".join(pg.get_text() for pg in doc)
            doc.close()
        except Exception as e:
            print(f"### {rk}: PDFERR {e}", flush=True)
            continue
        txt = re.sub(r"[ \t]+", " ", txt)
        sents = re.split(r"(?<=[.;:])\s+|\n{2,}", txt)
        hits, seen = [], set()
        for i, s in enumerate(sents):
            if CUE.search(s):
                frag = " ".join(sents[i:i + 2])[:400].strip()
                k = frag[:60]
                if k not in seen:
                    seen.add(k)
                    hits.append(frag)
        print(f"### {rk} | {rec['doi']} | {rec['title'][:70]}", flush=True)
        for h in hits[:8]:
            print("   * " + re.sub(r"\s+", " ", h), flush=True)
        if not hits:
            print("   * (no data-availability cue found)", flush=True)


if __name__ == "__main__":
    main()
