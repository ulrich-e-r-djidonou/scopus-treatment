# -*- coding: utf-8 -*-
"""Decoupe articles_raw.json en lots (un par fichier source) pour le tri par agents.
Sortie: chunks/chunk_NN.json + cree le dossier results/"""
import json, os, collections

recs = json.load(open("articles_raw.json", encoding="utf-8"))
by = collections.OrderedDict()
for r in recs:
    by.setdefault(r["file"], []).append(
        {"n": r["n"], "title": r["title"], "year": r["year"],
         "source": r["source"], "abstract": r["abstract"]})

os.makedirs("chunks", exist_ok=True)
os.makedirs("results", exist_ok=True)
groups = sorted(by.items(), key=lambda kv: kv[1][0]["n"])
for i, (f, rs) in enumerate(groups, 1):
    out = "chunks/chunk_%02d.json" % i
    json.dump(rs, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(out, "n=%d-%d" % (rs[0]["n"], rs[-1]["n"]), "count", len(rs))
print("Total lots :", len(groups), "| dossier results/ pret")
