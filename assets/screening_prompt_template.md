Gabarit de prompt pour un agent de tri (un par lot, lances en parallele, modele sonnet).
Remplacer les {{PLACEHOLDERS}} par les criteres convenus avec l'utilisateur, puis passer le texte comme `prompt` d'un appel Agent (subagent_type: general-purpose).

---

Tu es analyste pour une revue de litterature systematique. Tache : classer des articles scientifiques (titre + abstract) selon des criteres precis.

CONTEXTE DE L'ETUDE CIBLE
{{RESEARCH_CONTEXT}}
(ex : L'auteur etudie la relation entre l'inegalite de revenus et les emissions de CO2/GES au niveau provincial du Canada. Il cherche les etudes methodologiquement comparables.)

FICHIER A LIRE
Lis le fichier JSON : {{CHUNK_PATH}}
C'est un tableau d'objets {n, title, year, source, abstract}. Traite CHAQUE element.

CRITERES D'INCLUSION (les DEUX doivent etre vrais)
1. SUJET : {{TOPIC_CRITERIA}}
   (ex : l'etude examine un lien entre INEGALITE ECONOMIQUE (revenus/richesse : Gini de revenu, ecart riches-pauvres, top incomes, redistribution) ET un resultat environnemental carbone (CO2, GES, empreinte carbone, pollution de l'air).)
2. ECHELLE GEOGRAPHIQUE :
   - {{SCALE_A}} => decision INCLURE_SOUSNATIONAL
     (ex : SOUS-NATIONAL d'un SEUL pays : provinces, regions, Etats, prefectures, comtes, villes.)
   - {{SCALE_B}} => decision INCLURE_NATIONAL
     (ex : NATIONAL d'un SEUL pays : serie temporelle d'un seul pays.)

EXCLUSION (decision EXCLURE)
{{EXCLUSION_CRITERIA}}
(ex : - Multi-pays / international (panels de plusieurs pays, OCDE, BRICS, "27 Etats membres de l'UE" = multi-pays). 
      - Type d'inegalite NON cible seul (inegalite carbone/environnementale, pauvrete energetique, genre, sante) sauf si l'inegalite de revenus/richesse est aussi etudiee. 
      - Sujet environnemental seulement tangentiel.)

CAS LIMITE => decision BORDERLINE (lien plausible mais abstract ambigu sur le type d'inegalite ou l'echelle).

REGLE DE PRUDENCE : si la variable cible est presente mais l'echelle ambigue, mettre BORDERLINE plutot qu'EXCLURE. Ne pas jeter un article pertinent par doute.

SORTIE
Ecris un fichier JSON : {{RESULT_PATH}}
Tableau d'objets, UN objet pour CHAQUE article INCLURE_SOUSNATIONAL, INCLURE_NATIONAL ou BORDERLINE (NE PAS ecrire les EXCLURE). Format :
{
 "n": <numero>,
 "decision": "INCLURE_SOUSNATIONAL" | "INCLURE_NATIONAL" | "BORDERLINE",
 "country": "<pays etudie, ou 'inconnu'>",
 "geo_level": "sous-national" | "national" | "incertain",
 "geo_unit": "<provinces/Etats/regions/villes/pays unique...>",
 "inequality_measure": "<type d'inegalite etudiee>",
 "env_measure": "<CO2 / GES / empreinte carbone / pollution...>",
 "reason": "<1 phrase justifiant la decision>"
}

Dans ton message final : nombre total traite, compte par decision (INCLURE_SOUSNATIONAL, INCLURE_NATIONAL, BORDERLINE, EXCLURE), et liste des n inclus. Sois rigoureux, n'invente rien.
