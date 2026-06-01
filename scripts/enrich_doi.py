# -*- coding: utf-8 -*-
"""Recupere les DOI via Crossref pour final.json (controle de similarite de titre)
et fusionne les liens d'acces. Usage: python enrich_doi.py <email>"""
import urllib.request, urllib.parse, json, time, re, difflib, sys

MAIL = sys.argv[1] if len(sys.argv) > 1 else "anonymous@example.com"
UA = "ScopusTreatment/1.0 (mailto:%s)" % MAIL
THRESHOLD = 0.90

rows = json.load(open("final.json", encoding="utf-8"))

def norm(t): return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()

def query(title):
    q = urllib.parse.urlencode({
        "query.bibliographic": title, "rows": 5,
        "select": "DOI,title", "mailto": MAIL})
    req = urllib.request.Request("https://api.crossref.org/works?" + q,
                                 headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["message"]["items"]

doi_map = {}
for i, row in enumerate(rows, 1):
    n, title = row["n"], row["title"]
    best, best_ratio = None, 0.0
    try:
        for it in query(title):
            cand = (it.get("title") or [""])[0]
            ratio = difflib.SequenceMatcher(None, norm(title), norm(cand)).ratio()
            if ratio > best_ratio:
                best_ratio, best = ratio, (it.get("DOI"), cand)
    except Exception as e:
        doi_map[n] = {"doi": "", "ratio": 0, "matched": "", "err": str(e)[:60]}
        time.sleep(0.5); continue
    accept = best_ratio >= THRESHOLD
    doi_map[n] = {"doi": (best[0] if best else "") if accept else "",
                  "ratio": round(best_ratio, 3),
                  "matched": best[1] if best else "", "accepted": accept}
    if i % 20 == 0:
        print("  ...%d/%d" % (i, len(rows)))
    time.sleep(0.15)

json.dump({str(k): v for k, v in doi_map.items()},
          open("doi_map.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

nd = 0
for row in rows:
    v = doi_map.get(row["n"], {})
    doi = v.get("doi", "") if v.get("accepted") else ""
    row["doi"] = doi
    if doi:
        row["access_link"] = "https://doi.org/" + doi
        row["link_type"] = "DOI"; nd += 1
    else:
        row["access_link"] = row.get("scholar_link") or (
            "https://scholar.google.com/scholar?q=" + urllib.parse.quote(row["title"]))
        row["link_type"] = "Google Scholar"
json.dump(rows, open("final.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

low = sorted(n for n, v in doi_map.items() if not v.get("accepted"))
print("DOI directs :", nd, "/", len(rows), "| repli Scholar :", len(rows) - nd)
print("Sans correspondance fiable (a verifier a la main) :", low)
