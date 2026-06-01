# scopus-treatment

Python pipeline to screen a large Scopus corpus for a systematic literature review.
Transforms Scopus search results into a validated list of relevant articles, with Excel, Word, and Markdown outputs.

---

## Table of contents

- [English](#english)
- [Français](#français)

---

## English

### What this pipeline does

1. **Parses** Scopus results (CSV export or saved pages) into a structured JSON/CSV database.
2. **Splits** the corpus into batches and **classifies** each abstract (INCLUDE/BORDERLINE/EXCLUDE) using a parallel AI agent.
3. **Consolidates and validates**: merges results, detects false negatives via regex, flags duplicates.
4. **Adjudicates** borderline cases manually and applies corrections.
5. **Scores** each retained article for relevance and produces `final.json` + `final.csv`.
6. **Enriches DOIs** via the Crossref API (title similarity threshold: 0.90).
7. **Generates outputs**: Excel (formatted, filterable, clickable links), Word (clickable titles by category), Markdown.

### How to export from Scopus

There are two ways to get your data into the pipeline. **Case 1 is strongly recommended.**

#### Case 1 — Bulk CSV export (recommended)

Scopus allows exporting up to 2 000 articles at once as a CSV file, including abstracts.

Steps:
1. Run your Scopus search.
2. Click **"Select all"** to select all results on the page, then click **"Select all X results"** to extend to the full set.
3. Click **Export**, choose **CSV**, and under "Information to export" tick at minimum: *Citation information* and *Abstract & keywords*.
4. Save the file (e.g. `scopus_export.csv`) in your working folder.
5. If your corpus exceeds 2 000 results, repeat the export in batches of 2 000 (filter by year or document type) and save each file as `scopus_export_01.csv`, `scopus_export_02.csv`, etc.

Then run:
```bash
python scripts/parse_scopus_csv.py scopus_export.csv
```
Or, with multiple files:
```bash
python scripts/parse_scopus_csv.py scopus_export_01.csv scopus_export_02.csv
```

#### Case 2 — Page-by-page saved pages (fallback)

If bulk export is not available or the abstract column is missing from your CSV, you can save each results page manually.

Steps:
1. On each Scopus results page, expand all abstracts ("Show abstract" / "Hide abstract" toggle).
2. Save the page as plain text or copy-paste the content into a file named `Scopus_1.md`, `Scopus_2.md`, etc. (one file per page).
3. Place all `Scopus_N.md` files in your working folder.

Then run:
```bash
python scripts/parse_scopus.py
```

### Prerequisites

- Python 3.8+
- Install dependencies:

```bash
pip install -r requirements.txt
```

### Repository structure

```
scripts/
  parse_scopus_csv.py      # Step 1 (Case 1): parse a Scopus CSV bulk export
  parse_scopus.py          # Step 1 (Case 2): parse saved Scopus page files
  make_chunks.py           # Step 2: split corpus into batches for parallel screening
  consolidate.py           # Step 4: merge results and run false-negative safety net
  score_and_finalize.py    # Step 6a: apply corrections and compute relevance scores
  enrich_doi.py            # Step 6b: retrieve DOIs via Crossref
  build_outputs.py         # Step 7: generate Excel, Word, Markdown

assets/
  screening_prompt_template.md   # Prompt template for the screening agent (step 3)
```

### Step-by-step usage

**Run all scripts from the folder that contains your data files.**

```bash
# Step 1: parse the corpus (choose the script matching your export method)
python scripts/parse_scopus_csv.py scopus_export.csv   # Case 1
python scripts/parse_scopus.py                         # Case 2
# Check: parsed count == announced total, no missing numbers

# Step 2: split into batches
python scripts/make_chunks.py
# Produces chunks/chunk_NN.json and creates results/

# Step 3: screen with AI agents (one per batch, run in parallel)
# Use assets/screening_prompt_template.md, fill in the placeholders
# Each agent reads chunks/chunk_NN.json and writes results/chunk_NN.json

# Step 4: consolidate and validate
# First, adapt TOPIC_RE, ENV_RE, SCALE_RE in consolidate.py to your topic
python scripts/consolidate.py
# Review concern.json (potential false negatives) and retenus.json (false positives)

# Step 5: manually adjudicate BORDERLINE articles

# Step 6a: apply corrections and score
# Edit OVERRIDES, DROP, ADD at the top of score_and_finalize.py
python scripts/score_and_finalize.py

# Step 6b: enrich DOIs (optional)
python scripts/enrich_doi.py your@email.com

# Step 7: generate outputs
python scripts/build_outputs.py
```

On Windows, prefix with `set PYTHONUTF8=1 &&` to avoid encoding issues:

```cmd
set PYTHONUTF8=1 && python scripts/parse_scopus_csv.py scopus_export.csv
```

### Intermediate files (not committed)

| File | Role |
|---|---|
| `articles_raw.json/csv` | Full parsed corpus |
| `chunks/chunk_NN.json` | Batches for parallel screening |
| `results/chunk_NN.json` | Agent screening outputs |
| `retenus.json` | INCLUDE + BORDERLINE articles merged |
| `concern.json` | Potential false negatives to review |
| `doi_map.json` | Crossref DOI matches |
| `final.json/csv` | Final list with relevance scores |
| `*.xlsx / *.docx` | Final outputs |

### Warning

Screening is based on abstracts only. Always verify the full text before citing a retained article.

### Author

Ulrich Djidonou, research economist.

---

## Français

### Ce que fait ce pipeline

1. **Parse** les résultats Scopus (export CSV ou pages sauvegardées) en base structurée JSON/CSV.
2. **Découpe** le corpus en lots et **classe** chaque abstract (INCLURE/BORDERLINE/EXCLURE) via un agent IA en parallèle.
3. **Consolide et valide** : fusionne les résultats, détecte les faux négatifs par regex, signale les doublons.
4. **Adjudique** les cas limites manuellement et applique les corrections.
5. **Calcule un score** de pertinence et produit `final.json` + `final.csv`.
6. **Enrichit les DOI** via l'API Crossref (seuil de similarité de titre : 0.90).
7. **Génère les livrables** : Excel (mise en forme, filtres, liens cliquables), Word (titres cliquables par catégorie), Markdown.

### Comment exporter depuis Scopus

Il y a deux façons d'alimenter le pipeline. **Le cas 1 est fortement recommandé.**

#### Cas 1 — Export CSV en masse (recommandé)

Scopus permet d'exporter jusqu'à 2 000 articles à la fois en CSV, abstracts inclus.

Étapes :
1. Lancer la recherche Scopus.
2. Cliquer sur **"Sélectionner tout"** sur la page, puis sur **"Sélectionner les X résultats"** pour étendre à l'ensemble.
3. Cliquer sur **Exporter**, choisir **CSV**, et cocher au minimum : *Informations bibliographiques* et *Résumé et mots-clés*.
4. Sauvegarder le fichier (ex. `scopus_export.csv`) dans le dossier de travail.
5. Si le corpus dépasse 2 000 résultats, répéter l'export par tranches de 2 000 (filtrer par année ou type de document) et nommer les fichiers `scopus_export_01.csv`, `scopus_export_02.csv`, etc.

Puis lancer :
```bash
python scripts/parse_scopus_csv.py scopus_export.csv
```
Ou avec plusieurs fichiers :
```bash
python scripts/parse_scopus_csv.py scopus_export_01.csv scopus_export_02.csv
```

#### Cas 2 — Pages sauvegardées une par une (solution de repli)

Si l'export CSV n'est pas disponible ou si la colonne abstract est absente du CSV.

Étapes :
1. Sur chaque page de résultats Scopus, déplier tous les abstracts.
2. Sauvegarder la page en texte brut ou copier-coller le contenu dans un fichier nommé `Scopus_1.md`, `Scopus_2.md`, etc. (un fichier par page).
3. Placer tous les fichiers `Scopus_N.md` dans le dossier de travail.

Puis lancer :
```bash
python scripts/parse_scopus.py
```

### Prérequis

- Python 3.8+
- Installer les dépendances :

```bash
pip install -r requirements.txt
```

### Structure du dépôt

```
scripts/
  parse_scopus_csv.py      # Étape 1 (Cas 1) : parser un export CSV Scopus en masse
  parse_scopus.py          # Étape 1 (Cas 2) : parser des pages Scopus sauvegardées
  make_chunks.py           # Étape 2 : découper en lots pour tri parallèle
  consolidate.py           # Étape 4 : fusionner et valider (filet faux-négatifs)
  score_and_finalize.py    # Étape 6a : corrections et calcul de score de pertinence
  enrich_doi.py            # Étape 6b : récupérer les DOI via Crossref
  build_outputs.py         # Étape 7 : générer Excel, Word, Markdown

assets/
  screening_prompt_template.md   # Gabarit de prompt pour l'agent de tri (étape 3)
```

### Utilisation pas à pas

**Lancer tous les scripts depuis le dossier qui contient les fichiers de données.**

```bash
# Étape 1 : parser le corpus (choisir le script selon la méthode d'export)
python scripts/parse_scopus_csv.py scopus_export.csv   # Cas 1
python scripts/parse_scopus.py                         # Cas 2
# Vérifier : nombre parsé == total annoncé, aucun numéro manquant

# Étape 2 : découper en lots
python scripts/make_chunks.py
# Produit chunks/chunk_NN.json et crée le dossier results/

# Étape 3 : trier avec des agents IA (un par lot, en parallèle)
# Utiliser assets/screening_prompt_template.md, adapter les placeholders au sujet
# Chaque agent lit chunks/chunk_NN.json et écrit results/chunk_NN.json

# Étape 4 : consolider et valider
# Adapter TOPIC_RE, ENV_RE, SCALE_RE dans consolidate.py au sujet
python scripts/consolidate.py
# Relire concern.json (faux négatifs) et retenus.json (faux positifs)

# Étape 5 : adjudiquer les BORDERLINE manuellement

# Étape 6a : appliquer corrections et scorer
# Éditer OVERRIDES, DROP, ADD en tête de score_and_finalize.py
python scripts/score_and_finalize.py

# Étape 6b : enrichir les DOI (optionnel)
python scripts/enrich_doi.py votre@email.com

# Étape 7 : générer les livrables
python scripts/build_outputs.py
```

Sur Windows, préfixer avec `set PYTHONUTF8=1 &&` pour éviter les erreurs d'encodage :

```cmd
set PYTHONUTF8=1 && python scripts/parse_scopus_csv.py scopus_export.csv
```

### Fichiers intermédiaires (non commités)

| Fichier | Rôle |
|---|---|
| `articles_raw.json/csv` | Corpus complet parsé |
| `chunks/chunk_NN.json` | Lots pour tri parallèle |
| `results/chunk_NN.json` | Sorties des agents de tri |
| `retenus.json` | Articles INCLURE + BORDERLINE fusionnés |
| `concern.json` | Candidats faux-négatifs à relire |
| `doi_map.json` | Correspondances DOI Crossref |
| `final.json/csv` | Liste finale avec scores |
| `*.xlsx / *.docx` | Livrables finaux |

### Avertissement

Le tri repose sur les abstracts uniquement. Toujours vérifier le texte intégral avant de citer un article retenu.

### Auteur

Ulrich Djidonou, économiste-chercheur.
