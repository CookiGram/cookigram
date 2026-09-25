# Cycle 2 — expérience indépendante (#508)

Cycle 1 / gate 4 figé en `a5e7daa` : **ne rien y modifier**
(dev-set, holdout, résultats, code partagé). Ce dossier contient
l'intégralité du cycle 2 ; les modules cycle 1
(`store`, `corpus_manifest`, `chunk_facts`, `dense_qdrant`,
`policy.decide`, `retrieval_metrics`) sont réutilisés **sans
modification**. Collections Qdrant dédiées : `agent_memory_c2`,
`agent_memory_fact_c2`.

## Question

Le bras dense-faits + politique, calibré sur un dev-set neuf,
généralise-t-il à un holdout neuf ? (Le cycle 1 a montré faits 0.7 >
lexical 0.5 > sections 0.3 sur SON holdout ; ce cycle teste la
réplication sur données indépendantes, pas un retuning.)

Bras : lexical-sec (réf), dense-sec brut, dense-fact brut,
A2=sec+politique, B2=fact+politique (primaire). Bras cluster/γ
abandonné (résultat négatif cycle 1 : 1/8 à 0.001 près) ; MMR non
retesté (résultat cycle 3 conservé). Ce choix de design utilise les
*enseignements* du cycle 1, jamais ses holdouts pour calibrer.

## Ordre imposé (commits séparés)

1. `c2_dev.json` + `c2_calibrate.py` + ce README (règle pré-enregistrée).
2. Calibration dev → `c2_calibration.json` (grille complète publiée).
3. Freeze → `c2_freeze.json` (params, SHAs, critères) + push distant.
4. `c2_holdout.json` (requêtes écrites APRÈS freeze, docs réservés).
5. Mesure unique → `c2_results.json`, sans retuning.
6. Analyse dev vs holdout, limites, handoff. Aucune décision produit.

Garde-fous : `c2_calibrate.py` refuse de tourner si `c2_holdout.json`
existe ; `c2_measure.py` exigera `c2_freeze.json` et refusera tout
point non figé.

## Fichiers

| Fichier | Phase | Rôle |
|---|---|---|
| `c2_dev.json` | pré-calibration | 14 items (9 answer + 5 abstain), 0 gold commun cycle 1, règle de sélection, pool holdout réservé |
| `c2_calibrate.py` → `c2_calibration.json` | dev | mesure dev + grille tau×delta, point choisi par la règle |
| `c2_freeze.py` → `c2_freeze.json` | freeze | point, SHAs code/corpus, critères — commis+poussé avant holdout |
| `c2_holdout.json` | pré-mesure | 8 items aveugles, écrits après freeze |
| `c2_measure.py` → `c2_results.json` | mesure | UNE mesure holdout, point figé uniquement |
