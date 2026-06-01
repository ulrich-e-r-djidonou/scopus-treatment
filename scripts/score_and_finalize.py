# -*- coding: utf-8 -*-
"""Applique les decisions/corrections, calcule un score de pertinence et produit
final.json + final.csv. Editer la CONFIG et les dictionnaires de correction."""
import json, re, csv, urllib.parse

# ===================== CONFIG (a adapter) =====================
HOME_COUNTRY = "canada"   # bonus de pertinence si l'etude porte sur ce pays (minuscules)
PROJECT_TAG = "articles"  # utilise dans le nom de fichier de sortie Excel par build_outputs
# Regex de centralite du sujet (titre = signal fort) :
TOPIC_TITLE_RE = re.compile(
    r"income inequalit|wealth inequalit|economic inequalit|income gap|income distribut|"
    r"gini|wage inequalit|earnings inequalit|top \d+%|income disparit|redistribut|"
    r"common prosperity|disposable income", re.I)
ENV_CORE_RE = re.compile(
    r"\bco2\b|carbon emiss|carbon dioxide|greenhouse gas|\bghg\b|carbon footprint|carbon intensit", re.I)

# Corrections issues de la validation manuelle (n -> nouvelle decision) :
OVERRIDES = {}            # ex : {456: "INCLURE_SOUSNATIONAL"}
DROP = set()              # n a exclure definitivement (faux positifs)
# Ajouts (faux negatifs rattrapes) : n -> dict de metadonnees complet
ADD = {}                  # ex : {661: {"decision": "...", "country": "...", ...}}
# =============================================================

raw = {r["n"]: r for r in json.load(open("articles_raw.json", encoding="utf-8"))}
ret = {o["n"]: o for o in json.load(open("retenus.json", encoding="utf-8"))}

for n, o in ADD.items():
    o = dict(o); o["n"] = n; ret[n] = o
for n, dec in OVERRIDES.items():
    if n in ret: ret[n]["decision"] = dec
for n in DROP:
    ret.pop(n, None)

TIER = {"INCLURE_SOUSNATIONAL": "A. Sous-national (analogue direct)",
        "INCLURE_NATIONAL": "B. National mono-pays",
        "BORDERLINE": "C. A reverifier"}
DEC_BASE = {"INCLURE_SOUSNATIONAL": 100, "INCLURE_NATIONAL": 55, "BORDERLINE": 25}

def scholar(title):
    return "https://scholar.google.com/scholar?q=" + urllib.parse.quote(title)

rows = []
for n, o in ret.items():
    r = raw[n]
    try: yr = int(r["year"])
    except Exception: yr = 2020
    blob = r["title"] + " " + r["abstract"]
    score = DEC_BASE.get(o["decision"], 0)
    if TOPIC_TITLE_RE.search(r["title"]): score += 15
    elif TOPIC_TITLE_RE.search(r["abstract"]): score += 8
    if ENV_CORE_RE.search(blob): score += 8
    country = o.get("country") or ""
    if HOME_COUNTRY and HOME_COUNTRY in country.lower(): score += 30
    score += max(0, (yr - 2019)) * 1.5
    link = scholar(r["title"])
    rows.append({
        "n": n, "decision": o["decision"], "tier": TIER.get(o["decision"], "?"),
        "score": round(score, 1), "country": country,
        "geo_level": o.get("geo_level", ""), "geo_unit": o.get("geo_unit", ""),
        "inequality_measure": o.get("inequality_measure", ""),
        "env_measure": o.get("env_measure", ""), "reason": o.get("reason", ""),
        "title": r["title"], "authors": r["authors"], "source": r["source"],
        "volume": r["volume"], "year": r["year"], "doctype": r["doctype"],
        "doi": "", "scholar_link": link, "access_link": link, "link_type": "Google Scholar",
        "abstract": r["abstract"],
    })

# Doublons possibles (titre normalise proche)
def norm(t): return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()
groups = {}
for row in rows:
    groups.setdefault(norm(row["title"])[:60], []).append(row["n"])
dupmap = {}; g = 0
for ns in groups.values():
    if len(ns) > 1:
        g += 1
        for n in ns: dupmap[n] = "DUP%d (%s)" % (g, ",".join(map(str, sorted(ns))))
for row in rows:
    row["doublon_possible"] = dupmap.get(row["n"], "")

order = {"INCLURE_SOUSNATIONAL": 0, "INCLURE_NATIONAL": 1, "BORDERLINE": 2}
rows.sort(key=lambda x: (order.get(x["decision"], 9), -x["score"], -int(x["year"] or 0)))

json.dump(rows, open("final.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
cols = ["n","decision","tier","score","country","geo_level","geo_unit","inequality_measure",
        "env_measure","reason","title","authors","source","volume","year","doctype",
        "doublon_possible","doi","access_link","abstract"]
with open("final.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader(); w.writerows(rows)

import collections
c = collections.Counter(r["decision"] for r in rows)
print("TOTAL final :", len(rows))
for k in ("INCLURE_SOUSNATIONAL", "INCLURE_NATIONAL", "BORDERLINE"):
    print("  ", k, ":", c.get(k, 0))
print("Doublons possibles :", g, "groupes")
