# -*- coding: utf-8 -*-
"""Parse a Scopus bulk CSV export into articles_raw.json + articles_raw.csv.
Scopus allows selecting all results and exporting up to 2000 articles at once
as CSV (Include: Citation information + Abstract & keywords).
Usage: python scripts/parse_scopus_csv.py scopus_export.csv
       python scripts/parse_scopus_csv.py   # auto-detects scopus_export*.csv in current folder
Produces the same articles_raw.json / articles_raw.csv as parse_scopus.py."""

import csv, json, glob, os, re, sys

# Column name variants found in Scopus CSV exports (case-insensitive matching)
COL_ALIASES = {
    "title":    ["title"],
    "authors":  ["authors", "author names", "author(s)"],
    "year":     ["year", "publication year"],
    "source":   ["source title", "source"],
    "volume":   ["volume"],
    "abstract": ["abstract"],
    "doctype":  ["document type"],
    "doi":      ["doi"],
    "eid":      ["eid"],
}

def find_col(headers, aliases):
    hl = [h.strip().lower() for h in headers]
    for a in aliases:
        if a in hl:
            return hl.index(a)
    return None

def get(row, idx):
    if idx is None or idx >= len(row):
        return ""
    return row[idx].strip()

# --- locate input file(s) ---
if len(sys.argv) > 1:
    files = sys.argv[1:]
else:
    files = sorted(glob.glob("scopus_export*.csv") + glob.glob("Scopus_export*.csv")
                   + glob.glob("scopus*.csv") + glob.glob("Scopus*.csv"))
    files = [f for f in files if os.path.isfile(f)]
    if not files:
        raise SystemExit(
            "No CSV file found. Pass the filename as argument:\n"
            "  python scripts/parse_scopus_csv.py your_export.csv")

records = []
counter = 0
for fpath in files:
    with open(fpath, encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        headers = next(reader)
        cols = {k: find_col(headers, v) for k, v in COL_ALIASES.items()}
        missing = [k for k, v in cols.items() if v is None and k not in ("doi", "eid", "volume")]
        if missing:
            print("WARNING: columns not found in %s: %s" % (fpath, missing))
        for row in reader:
            if not any(row):
                continue
            counter += 1
            records.append({
                "n":        counter,
                "file":     os.path.basename(fpath),
                "doctype":  get(row, cols["doctype"]),
                "title":    get(row, cols["title"]),
                "authors":  get(row, cols["authors"]),
                "source":   get(row, cols["source"]),
                "volume":   get(row, cols["volume"]),
                "year":     get(row, cols["year"]),
                "abstract": get(row, cols["abstract"]),
            })

json.dump(records, open("articles_raw.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

import csv as _csv
with open("articles_raw.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = _csv.DictWriter(fh, fieldnames=["n","file","doctype","title","authors",
                                         "source","volume","year","abstract"])
    w.writeheader()
    w.writerows(records)

print("Records parsed:", len(records))
no_abstract = sum(1 for r in records if not r["abstract"])
no_year     = sum(1 for r in records if not r["year"])
print("Without abstract:", no_abstract, "| Without year:", no_year)
print("Output: articles_raw.json + articles_raw.csv")
