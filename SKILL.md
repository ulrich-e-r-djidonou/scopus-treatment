---
name: scopus_treatment
description: Trie un grand corpus d'articles Scopus (pages de resultats sauvegardees en .md) pour une revue de litterature. Parse les documents en base structuree, classe chaque abstract selon des criteres d'inclusion/exclusion definis avec l'utilisateur (sujet + echelle geographique), valide contre faux negatifs et faux positifs, recupere les DOI via Crossref, et produit des livrables Excel, Word (liens cliquables) et Markdown. A utiliser quand l'utilisateur depose des fichiers Scopus_*.md (ou un export Scopus) et veut isoler les articles pertinents a son etude. Declencheurs : "trie ces articles scopus", "revue de litterature", "quels articles sont pertinents", "scopus".
---

# Traitement de corpus Scopus pour revue de litterature

Pipeline pour transformer des pages de resultats Scopus sauvegardees en un ensemble valide d'articles pertinents, avec livrables Excel / Word / Markdown.

## Quand l'utiliser

L'utilisateur a sauvegarde plusieurs pages de resultats Scopus au format texte/markdown (`Scopus_1.md`, `Scopus_2.md`, ...) et veut isoler, parmi des centaines/milliers de documents, ceux qui correspondent a son etude (sujet precis + type de donnees/echelle geographique). Fonctionne aussi a partir d'un seul gros fichier si chaque document suit le format de liste Scopus.

## Format d'entree attendu

Chaque page Scopus sauvegardee contient une ligne `Results list, showing results X through Y of N results.` puis, pour chaque document : une ligne de type (`Article`, `Review`, `Conference Paper`...), le numero, le titre, les auteurs, la source, le volume, l'annee, les citations, `Hide abstract`, puis l'abstract. Le parser s'appuie sur ces ancres. Verifier au depart que les fichiers sont du texte propre et non du HTML brut (si HTML, demander a l'utilisateur de re-sauvegarder en "texte" / copier-coller du contenu de la page).

## Procedure

Travailler dans le dossier qui contient les fichiers `Scopus_*.md`. Les scripts sont dans le sous-dossier `scripts/` de ce skill ; les lancer avec `PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python <chemin_du_script>` (Windows console = cp1252, sinon erreurs d'encodage sur les caracteres comme CO2 en indice). Dependance : `openpyxl` et `python-docx` (installer si absent : `python -m pip install openpyxl python-docx`).

### 1. Cadrer les criteres (AVANT de coder)

Confirmer avec l'utilisateur, via AskUserQuestion si besoin :
- Le **sujet** exact (quelles variables doivent etre liees ; ex. inegalite de revenus x emissions CO2).
- L'**echelle geographique** voulue (ex. sous-national d'un seul pays vs national mono-pays vs multi-pays ; lesquelles inclure/separer/exclure).
- Le **format de sortie** (Excel, Word, Markdown ; lesquels).
Ecrire ces criteres dans un `INSTRUCTIONS.md` du projet : requete Scopus, filtres, criteres d'inclusion, criteres d'exclusion, classification, avertissement (tri base sur abstracts).

### 2. Parser le corpus

`python scripts/parse_scopus.py` -> produit `articles_raw.json` et `articles_raw.csv`.
Verifier la sortie : nombre parse == total annonce, aucun numero manquant, aucun doublon. Si des numeros manquent, c'est souvent un type de document non liste : ajouter le type dans `DOCTYPES` (la comparaison est insensible a la casse) et relancer. Ne pas continuer tant que la couverture n'est pas complete.

### 3. Decouper en lots et trier par agents paralleles

`python scripts/make_chunks.py` -> produit `chunks/chunk_NN.json` (un lot par page source, ~200 articles) et cree le dossier `results/`.
Lancer un agent general-purpose (modele sonnet) par lot, EN PARALLELE (plusieurs appels Agent dans un seul message). Utiliser le gabarit `assets/screening_prompt_template.md` en remplacant les placeholders par les criteres convenus et le chemin du lot. Chaque agent lit son `chunks/chunk_NN.json`, classe chaque article, et ecrit `results/chunk_NN.json` (uniquement les INCLURE et BORDERLINE ; les EXCLURE sont omis pour garder la sortie legere). Schema de sortie par article : `{n, decision, country, geo_level, geo_unit, inequality_measure, env_measure, reason}` ou `decision` est `INCLURE_SOUSNATIONAL` | `INCLURE_NATIONAL` | `BORDERLINE`.

### 4. Consolider et valider (etape critique)

`python scripts/consolidate.py` -> fusionne `results/*.json` en `retenus.json`, verifie l'absence de doublons et de numeros hors corpus, et lance le **filet de securite faux-negatifs** : il liste dans `concern.json` les articles EXCLUS par les agents qui mentionnent pourtant a la fois le sujet et l'echelle voulue (regex configurables en tete du script).
- Relire soi-meme `concern.json` (lire titres + abstracts) et rattraper les vrais oublis.
- Relire aussi l'ensemble `INCLURE_SOUSNATIONAL` (categorie prioritaire) pour ecarter les faux positifs (souvent : inegalite "carbone"/"regionale"/"spatiale" confondue avec inegalite de revenus).
- Verifier que les "national" ne cachent pas du multi-pays mal etiquete.
Consigner les corrections (ajouts/retrogradations) ; elles seront appliquees a l'etape suivante.

### 5. Adjudiquer les BORDERLINE

Lire integralement chaque BORDERLINE (un par un) et trancher : reclasser en INCLURE_* ou exclure. Regle type : INCLURE si la variable d'inegalite visee ET la variable environnementale sont toutes deux substantielles, l'etude est empirique sur un seul pays (sous-national ou national), et un lien est analyse ; EXCLURE si multi-pays, inegalite non ciblee (carbone/regionale/genre...), modele purement theorique sans pays, ou revue sans donnees localisees.

### 6. Finaliser, scorer, enrichir, produire

- `python scripts/score_and_finalize.py` -> applique les decisions/corrections (editer le bloc `OVERRIDES`/`DROP`/config en tete), calcule un score de pertinence et produit `final.json` + `final.csv`.
- `python scripts/enrich_doi.py "email@exemple.com"` -> recupere les DOI via Crossref (controle de similarite de titre, seuil 0.90), ecrit `doi_map.json` et fusionne les liens dans `final.json` (DOI direct, repli Google Scholar sinon). Verifier par sondage que les DOI correspondent au bon titre.
- `python scripts/build_outputs.py` -> produit `Articles_<projet>.xlsx`, `.docx` (liens cliquables) et `Synthese_articles_pertinents.md`.

## Principes de qualite

- Le tri repose sur les abstracts seuls : toujours afficher cet avertissement et recommander la verification au texte integral avant citation.
- Ne jamais inventer un DOI ou un lien : DOI seulement si Crossref donne une correspondance de titre fiable, sinon repli sur une recherche Google Scholar par titre.
- Tracer chaque decision dans le champ `reason`. Garder les fichiers intermediaires (`articles_raw.*`, `retenus.json`, `concern.json`, `doi_map.json`) pour audit.
- En cas de doute sur la pertinence, classer BORDERLINE plutot qu'EXCLURE : un faux negatif coute plus cher qu'un faux positif dans une revue.
