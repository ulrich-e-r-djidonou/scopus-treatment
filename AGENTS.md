# AGENTS.md — Instructions pour agents IA (OpenAI Codex, Claude Code, etc.)

Ce fichier décrit comment un agent IA doit interagir avec ce dépôt pour exécuter le pipeline de tri Scopus.

## Vue d'ensemble du projet

Pipeline Python en 7 étapes pour trier un corpus d'articles Scopus. Entrées : fichiers texte `Scopus_N.md`. Sorties : Excel, Word, Markdown avec les articles pertinents sélectionnés selon des critères d'inclusion définis par l'utilisateur.

## Environnement

- Python 3.8+
- Installer les dépendances : `pip install -r requirements.txt`
- Tous les scripts se lancent depuis le dossier contenant les fichiers `Scopus_*.md` (pas depuis la racine du dépôt).
- Sur Windows : préfixer `set PYTHONUTF8=1 &&` pour l'encodage UTF-8.

## Scripts disponibles et leur rôle

| Script | Rôle | Entrées | Sorties |
|---|---|---|---|
| `scripts/parse_scopus.py` | Parse les pages Scopus | `Scopus_*.md` | `articles_raw.json`, `articles_raw.csv` |
| `scripts/make_chunks.py` | Découpe en lots | `articles_raw.json` | `chunks/chunk_NN.json`, `results/` |
| `scripts/consolidate.py` | Fusionne et valide | `results/chunk_*.json`, `articles_raw.json` | `retenus.json`, `concern.json` |
| `scripts/score_and_finalize.py` | Scoring et corrections | `retenus.json`, `articles_raw.json` | `final.json`, `final.csv` |
| `scripts/enrich_doi.py` | Récupère les DOI | `final.json` | `doi_map.json`, `final.json` (mis à jour) |
| `scripts/build_outputs.py` | Produit les livrables | `final.json` | `*.xlsx`, `*.docx`, `*.md` |

## Instructions pour l'étape de tri (étape 3)

L'étape 3 nécessite un agent par lot. Le gabarit de prompt est dans `assets/screening_prompt_template.md`.

L'agent de tri doit :
1. Lire `chunks/chunk_NN.json` (tableau d'objets `{n, title, year, source, abstract}`)
2. Classifier chaque article selon les critères fournis dans le prompt
3. Écrire `results/chunk_NN.json` avec uniquement les articles INCLURE_SOUSNATIONAL, INCLURE_NATIONAL ou BORDERLINE (omettre les EXCLURE)
4. Format de sortie par article :
```json
{
  "n": 42,
  "decision": "INCLURE_SOUSNATIONAL",
  "country": "United States",
  "geo_level": "sous-national",
  "geo_unit": "states",
  "reason": "Studies xxxxxxxxxxxxxx in a single country."
}
```

## Paramètres à adapter par projet

### Dans `scripts/consolidate.py` (lignes 8-21)
Adapter les regex au sujet de l'étude :
- `TOPIC_RE` : mots-clés de la variable étudiée
- `ENV_RE` : mots-clés de la variable environnementale
- `SCALE_RE` : mots-clés de l'échelle sous-nationale voulue
- `MULTI_RE` : signaux d'exclusion (multi-pays, panels internationaux)

### Dans `scripts/score_and_finalize.py` (lignes 7-18)
- `HOME_COUNTRY` : pays cible (bonus de pertinence, en minuscules)
- `PROJECT_TAG` : tag utilisé dans les noms de fichiers de sortie
- `TOPIC_TITLE_RE`, `ENV_CORE_RE` : regex pour le scoring des titres
- `OVERRIDES`, `DROP`, `ADD` : corrections manuelles post-validation

## Ce que l'agent NE doit pas faire

- Ne pas modifier les fichiers `Scopus_*.md` (données brutes, ne pas altérer)
- Ne pas supprimer `articles_raw.json`, `retenus.json` ou `concern.json` (fichiers d'audit)
- Ne pas commiter les fichiers de données listés dans `.gitignore`
- Ne pas inventer un DOI : utiliser uniquement ce que retourne Crossref avec un ratio >= 0.90

## Flux de contrôle type

```
parse_scopus.py
    -> vérifier couverture (0 numéro manquant)
make_chunks.py
    -> lancer N agents en parallèle (un par chunk_NN.json)
    -> chaque agent écrit results/chunk_NN.json
consolidate.py
    -> relire concern.json (faux négatifs)
    -> relire INCLURE_SOUSNATIONAL (faux positifs)
    -> noter les corrections dans OVERRIDES/DROP/ADD
score_and_finalize.py
    -> éditer CONFIG et OVERRIDES avant de lancer
enrich_doi.py <email>   # optionnel
build_outputs.py
```

## Schéma JSON de final.json (référence)

Chaque objet du tableau `final.json` contient :
`n, decision, tier, score, country, geo_level, geo_unit, reason, title, authors, source, volume, year, doctype, doublon_possible, doi, access_link, link_type, abstract`
