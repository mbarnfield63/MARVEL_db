"""Map DOI -> existing ExoMol bibtex key across C:\\Code\\bib tree."""
import json, os, re, glob

ROOT = r"C:\Code\bib"
ENTRY = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.I)
DOIF = re.compile(r"doi\s*=\s*[{\"]\s*(?:https?://(?:dx\.)?doi\.org/)?([^}\"]+?)\s*[}\"]", re.I)

out = {}
files = glob.glob(os.path.join(ROOT, "**", "*.bib"), recursive=True)
for fp in files:
    try:
        txt = open(fp, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    # split on @ at line start
    parts = re.split(r"\n(?=@)", txt)
    for p in parts:
        m = ENTRY.search(p)
        if not m:
            continue
        key = m.group(2)
        d = DOIF.search(p)
        if not d:
            continue
        doi = d.group(1).strip().lower().rstrip(".")
        out.setdefault(doi, []).append({"key": key, "file": os.path.relpath(fp, ROOT)})

print(len(files), "bib files;", len(out), "DOIs mapped")
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "doi2key.json"), "w"), indent=0)
