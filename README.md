# scopus-treatment

Pipeline Python pour trier un grand corpus Scopus en vue d'une revue de littérature systématique.
Transforme des pages de résultats Scopus sauvegardées (format texte/markdown) en une liste validée d'articles pertinents, avec livrables Excel, Word et Markdown.

## Ce que fait ce pipeline

1. **Parse** les pages Scopus exportées (`Scopus_1.md`, `Scopus_2.md`, ...) en base structurée JSON/CSV.
2. **Découpe** le corpus en lots et **classe** chaque abstract (INCLURE/BORDERLINE/EXCLURE) via un agent IA configuré par l'utilisateur.
3. **Consolide et valide** : fusionne les résultats, détecte les faux négatifs par regex, signale les doublons.
4. **Adjudique** les cas limites (BORDERLINE) et applique les corrections manuelles.
5. **Calcule un score** de pertinence et produit `final.json` + `final.csv`.
6. **Enrichit les DOI** via l'API Crossref (correspondance de titre, seuil 0.90).
7. **Produit les livrables** : Excel (mise en forme, filtres, liens cliquables), Word (liens cliquables par catégorie), Markdown.

## Cas d'usage typique

L'utilisateur a sauvegardé plusieurs pages de résultats Scopus en texte/markdown et veut isoler, parmi des centaines ou milliers d'articles, ceux qui correspondent à son sujet de recherche (variables cibles + échelle géographique).

Fonctionne sur des corpus de quelques centaines à plusieurs milliers d'articles, pour tout sujet combinant deux variables (économique, environnementale, sociale, etc.) et une échelle géographique précise.

## Prérequis

- Python 3.8+
- Dépendances :

```
pip install -r requirements.txt
```

## Structure du dépôt

```
scripts/
  parse_scopus.py          # Étape 1 : parser les fichiers Scopus_*.md
  make_chunks.py           # Étape 2 : découper en lots pour tri parallèle
  consolidate.py           # Étape 4 : fusionner et valider (adapter les regex)
  score_and_finalize.py    # Étape 6a : scorer et produire final.json/csv
  enrich_doi.py            # Étape 6b : récupérer les DOI via Crossref
  build_outputs.py         # Étape 7 : générer Excel, Word, Markdown

assets/
  screening_prompt_template.md   # Gabarit de prompt pour l'agent de tri (étape 3)
```

## Utilisation pas à pas

**Travailler depuis le dossier contenant les fichiers `Scopus_*.md`.**

```bash
# Étape 1 : parser le corpus
python scripts/parse_scopus.py
# Vérifier : nombre parsé == total annoncé, aucun numéro manquant

# Étape 2 : découper en lots
python scripts/make_chunks.py
# Produit chunks/chunk_NN.json et crée le dossier results/

# Étape 3 : trier avec un agent IA (un par lot, en parallèle)
# Utiliser le gabarit assets/screening_prompt_template.md
# Adapter les placeholders au sujet, puis lancer un agent par chunk
# Chaque agent écrit son results/chunk_NN.json

# Étape 4 : consolider et valider
# Adapter TOPIC_RE, ENV_RE, SCALE_RE dans consolidate.py au sujet
python scripts/consolidate.py
# Relire concern.json (faux négatifs potentiels) et retenus.json (faux positifs)

# Étape 5 : adjudiquer les BORDERLINE manuellement

# Étape 6a : appliquer corrections et scorer
# Éditer OVERRIDES, DROP, ADD dans score_and_finalize.py
python scripts/score_and_finalize.py

# Étape 6b : enrichir les DOI (optionnel)
python scripts/enrich_doi.py votre@email.com

# Étape 7 : générer les livrables
python scripts/build_outputs.py
```

Sur Windows, préfixer avec `set PYTHONUTF8=1 &&` pour éviter les erreurs d'encodage :

```cmd
set PYTHONUTF8=1 && python scripts/parse_scopus.py
```

## Format d'entrée

Chaque fichier `Scopus_N.md` doit être du texte propre (copier-coller depuis Scopus, non du HTML brut) avec la structure standard : ligne `Results list, showing results X through Y of N results`, puis pour chaque article le type, le numéro, le titre, les auteurs, la source, l'année, et l'abstract précédé de `Hide abstract`.

## Fichiers intermédiaires (non commités)

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

## Avertissement

Le tri repose sur les abstracts uniquement. Toujours vérifier le texte intégral avant de citer un article retenu.

## Auteur

Ulrich Djidonou, économiste-chercheur.
