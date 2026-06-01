# -*- coding: utf-8 -*-
"""Parse les pages de resultats Scopus (texte) en enregistrements structures.
Lance depuis le dossier contenant les fichiers Scopus_*.md.
Sortie: articles_raw.json + articles_raw.csv"""
import re, json, csv, glob, os

DOCTYPES = {
    "Article", "Review", "Book chapter", "Book Chapter", "Conference paper",
    "Conference Paper", "Book", "Erratum", "Note", "Editorial", "Short survey",
    "Data paper", "Conference review", "Letter", "Retracted article", "Retracted",
}
DOCTYPES_LC = {d.lower() for d in DOCTYPES}
YEAR_RE = re.compile(r"^(19|20)\d{2}$")
INT_RE = re.compile(r"^\d{1,5}$")

FILES = sorted(glob.glob("Scopus_*.md"),
               key=lambda p: int(re.search(r"_(\d+)\.md$", p).group(1)))

def doctype_of(line):
    base = line.split("•")[0].strip()  # avant le bullet
    return base if base.lower() in DOCTYPES_LC else None

def prev_nonblank(lines, i):
    j = i - 1
    while j >= 0 and lines[j].strip() == "":
        j -= 1
    return (lines[j].strip() if j >= 0 else ""), j

def next_nonblank_idx(lines, i):
    j = i + 1
    while j < len(lines) and lines[j].strip() == "":
        j += 1
    return j

records = []
for fpath in FILES:
    with open(fpath, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh]
    m = re.search(r"showing results (\d+) through (\d+)", "\n".join(lines[:400]))
    if not m:
        print("ATTENTION: pas d'entete de plage dans", fpath, "(fichier ignore)")
        continue
    start, end = int(m.group(1)), int(m.group(2))
    header_i = 0
    for i, raw in enumerate(lines):
        if raw.strip().startswith("Results list, showing results"):
            header_i = i
            break
    starts = []
    seen = set()
    for i in range(header_i, len(lines)):
        if doctype_of(lines[i].strip()) is None:
            continue
        ni = next_nonblank_idx(lines, i)
        if ni >= len(lines):
            continue
        s = lines[ni].strip()
        if not INT_RE.match(s):
            continue
        num = int(s)
        if not (start <= num <= end) or num in seen:
            continue
        ti = next_nonblank_idx(lines, ni)
        if ti >= len(lines):
            continue
        tt = lines[ti].strip()
        if tt == "" or INT_RE.match(tt) or doctype_of(tt) is not None:
            continue
        starts.append((ni, num, doctype_of(lines[i].strip())))
        seen.add(num)
    starts.sort(key=lambda x: x[0])

    for k, (li, num, dtype) in enumerate(starts):
        block_end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
        ti = next_nonblank_idx(lines, li)
        title = lines[ti].strip() if ti < block_end else ""
        abstract = ""
        bound = block_end
        for j in range(li, block_end):
            if lines[j].strip() == "Hide abstract":
                bound = j
                aj = next_nonblank_idx(lines, j)
                if aj < block_end:
                    abstract = lines[aj].strip()
                break
        year = ""
        for j in range(li, bound):
            if YEAR_RE.match(lines[j].strip()):
                year = lines[j].strip()
        source = ""; vol = ""; yi = -1
        for j in range(ti + 1, bound):
            if year and lines[j].strip() == year:
                yi = j
        if yi > 0:
            prevy, pj = prev_nonblank(lines, yi)
            if prevy.startswith(","):
                vol = prevy.lstrip(", ").strip()
                source, _ = prev_nonblank(lines, pj)
            else:
                source = prevy
        authors = []
        for j in range(ti + 1, bound):
            s = lines[j].strip()
            if source and s == source:
                break
            if s in (",", "") or s.startswith(",..."):
                continue
            if YEAR_RE.match(s):
                break
            authors.append(s)
        authors_str = "; ".join(a.rstrip(",").strip() for a in authors if a)
        records.append({
            "n": num, "file": os.path.basename(fpath), "doctype": dtype,
            "title": title, "authors": authors_str, "source": source,
            "volume": vol, "year": year, "abstract": abstract,
        })

records.sort(key=lambda r: r["n"])
json.dump(records, open("articles_raw.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open("articles_raw.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["n","file","doctype","title","authors","source","volume","year","abstract"])
    w.writeheader(); w.writerows(records)

nums = [r["n"] for r in records]
print("Enregistrements parses :", len(records))
if nums:
    full = set(range(min(nums), max(nums) + 1))
    missing = sorted(full - set(nums))
    dups = sorted({n for n in nums if nums.count(n) > 1})
    print("plage :", min(nums), "->", max(nums))
    print("numeros manquants :", missing if missing else "aucun")
    print("doublons :", dups if dups else "aucun")
    print("sans abstract :", sum(1 for r in records if not r["abstract"]),
          "| sans annee :", sum(1 for r in records if not r["year"]))
