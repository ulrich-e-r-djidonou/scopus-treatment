# -*- coding: utf-8 -*-
"""Fusionne results/chunk_*.json en retenus.json, valide, et lance le filet de
securite faux-negatifs (concern.json). Adapter TOPIC_RE et SCALE_RE au sujet."""
import json, glob, re, collections

# --- Regex a adapter au sujet et a l'echelle voulue ---
# Exemple par defaut : inegalite de revenus x emissions, echelle sous-nationale.
TOPIC_RE = re.compile(
    r"income inequal|wealth inequal|economic inequal|income gap|income distribut|"
    r"distribution of income|gini|wage inequal|earnings inequal|top \d+%|"
    r"income disparit|income polari|income concentration", re.I)
ENV_RE = re.compile(
    r"\bco2\b|carbon emiss|carbon dioxide|greenhouse gas|\bghg\b|\bemission|"
    r"carbon footprint|ecological footprint|pm2\.5|air pollut|environmental degradation", re.I)
SCALE_RE = re.compile(
    r"provinc|prefectur|\bcount(y|ies)\b|municipal|state-level|u\.s\. states|"
    r"chinese provinces|interprovin|inter-provin|city-level|cities|metropolitan|district", re.I)
MULTI_RE = re.compile(
    r"\bcountries\b|cross-country|\boecd\b|\bbrics\b|\bg7\b|\bg-7\b|\bg20\b|"
    r"member states|\bnations\b|global panel|belt and road|sub-saharan|\basean\b|"
    r"\bmena\b|developing countries|asian countries|african countries|panel of \d+", re.I)

raw = {r["n"]: r for r in json.load(open("articles_raw.json", encoding="utf-8"))}
rows, seen, problems = [], set(), []
for f in sorted(glob.glob("results/chunk_*.json")):
    for o in json.load(open(f, encoding="utf-8")):
        n = o.get("n")
        if n in seen: problems.append(("doublon", n, f)); continue
        if n not in raw: problems.append(("hors corpus", n, f)); continue
        seen.add(n); rows.append(o)

cnt = collections.Counter(o["decision"] for o in rows)
json.dump(rows, open("retenus.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("Retenus (INCLURE + BORDERLINE) :", len(rows))
for k in ("INCLURE_SOUSNATIONAL", "INCLURE_NATIONAL", "BORDERLINE"):
    print("  ", k, ":", cnt.get(k, 0))
extra = {k: v for k, v in cnt.items()
         if k not in ("INCLURE_SOUSNATIONAL", "INCLURE_NATIONAL", "BORDERLINE")}
if extra: print("  LABELS INATTENDUS :", extra)
print("Problemes :", problems if problems else "aucun")

# Filet faux-negatifs : exclus qui ont sujet + echelle, sans signal multi-pays
retenus = {o["n"] for o in rows}
concern = []
for n, r in raw.items():
    if n in retenus:
        continue
    t = r["title"] + " " + r["abstract"]
    if TOPIC_RE.search(t) and ENV_RE.search(t) and SCALE_RE.search(t) and not MULTI_RE.search(t):
        concern.append(n)
concern.sort()
json.dump(concern, open("concern.json", "w"), indent=0)
print("\nCandidats faux-negatifs a relire (concern.json) :", len(concern))
print(concern)
