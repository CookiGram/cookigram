# #510 — Mécanisme d'ancrage/décision (chantier distinct post-#508)

#508 est clos et figé (`d8584dc`) : **ne rien y modifier, rejouer ni
recalibrer**. Ce dossier contient l'intégralité de #510. Modules
#508 (`store`, `corpus_manifest`, `chunk_facts`, `dense_qdrant`,
`policy`, `retrieval_metrics`) réutilisables **sans modification**.
Corpus documentaire autorisé : les 18 chemins cycle2b UNIQUEMENT
(décision Human Owner), usage documentaire seul.

## Question

Pour un point calibré sur dev neuf, quelle part des échecs
mémoire-agent vient (1) du retrieval (gold absent du top-k),
(2) de l'extraction (gold présent, span-réponse absent),
(3) de la décision (span présent mais abstention, ou span
absent mais réponse) ?

## Métriques (étagées, pré-enregistrées)

P(gold au top-k) ; P(ancre | gold) ; P(décision correcte | état
ancre) ; succès global. Plus rank-1/recall@3 + décision
stricte/indulgente (comparabilité #508). Locus statique
(titre/section/corps/code/liste + taille) par item answer.

## Dérogation ANCHOR_DISJOINT_GO (locale #510)

Dev et holdout peuvent partager les documents ; disjonction
stricte sur les **ancres** (précédent : cycle2b, 8/11 docs
partagés, 0 ancre commune). Seuls les 4 docs jamais golds #508
sont admissibles comme golds ; les 14 autres sont interdits.

## Ordre imposé (GO séparés)

1. Freeze méthodologique (ce dossier : pool 51, split dev 27 /
   réserve 24, règle aveugle) — FAIT, commis.
2. Dev-set + tests (GO courant).
3. Calibration DEV ONLY (nouveau GO).
4. Freeze point (nouveau GO).
5. Holdout ancres-réserve (nouveau GO).
6. Mesure unique (nouveau GO).

## Fichiers

| Fichier | Rôle |
|---|---|
| `a510_method_freeze.json` | dérogation, définitions, pool, split, règles |
| `test_a510_freeze.py` | preuve statique du freeze (stdlib, sans Qdrant) |
| `a510_dev.json` | dev-set (27 ancres dev + abstains frais) |
| `test_a510_dev.py` | preuve statique du dev (grounding, unicité, disjonctions) |
