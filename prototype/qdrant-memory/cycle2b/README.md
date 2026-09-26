# Cycle 2b — redéfinition méthodologique du corpus (REDEFINE_CORPUS_GO)

Freeze méthodologique, **sans calibration, sans dev-set, sans holdout, sans mesure**.
Autorisation Human Owner : option 2(b) — extension du corpus gold-capable,
rupture de comparabilité assumée et documentée.

## 1. Pourquoi une redéfinition (fait durable)

- Ancien corpus (`corpus_manifest.build_corpus` @ `ce5f3dd`) :
  `docs/**/*.md` (24) + `decisions/*` (1 : PDR-0010) + `.agents/claims.json`
  (résumé 1 chunk) = **26 chemins gold-capables**.
- Chemins consommés comme golds (bannis, §4) : **26/26**.
  Gate 4 (13) + dev-14 (8) + holdout-8 mesuré (5) couvrent exactement
  les 26 chemins. Docs libres restants : **0**.
- Donc EXTEND_30 ≥30/≥30 disjoint est **impossible** dans l'ancien périmètre.
  Le premier essai Cycle 2 (`cycle2/`, freeze `252fffd`, mesure `ce5f3dd`)
  a épuisé le pool. Ce constat est le fondement du présent GO.

## 2. Nouveau corpus proposé (plus petit élargissement suffisant)

Ajout déterministe, **sans toucher l'ancien corpus** (toujours construit
à l'identique pour Gate 4 / Cycle 2) :

- **A. Racine gouvernante (8 fichiers .md)** : `AGENTS.md`, `CHARTER.md`,
  `CONTRIBUTING.md`, `GEMINI.md`, `PRODUCT_PRINCIPLES.md`, `README.md`,
  `README.en.md`, `TODO.md`.
- **B. Gouvernance agent (7 fichiers)** : `.agents/STATUS.md`,
  `.agents/roles/README.md`, `.agents/rules/cooking-execution.md`,
  `.agents/rules/git-workflow.md`, `.agents/rules/image-assets.md`,
  `.agents/rules/ingredient-icons.md`,
  `.agents/rules/multi-agent-orchestration.md`,
  `.agents/rules/product-governance.md`, `.agents/rules/task-claiming.md`,
  `.agents/rules/token-frugality.md`.
  (10 chemins ; `roles/*.md` experts, `skills/*` et `scripts/*` exclus :
  pas de sections stables / pas de contenu produit/agent requêtable.)

Soit **18 chemins neufs**, tous hors ancien corpus, aucun chevauchement.

Écarté délibérément (documenté, pas oublié) :
- `recipes/*.gram` (233) : requêtes par slug/titre trivialement ambiguës,
  doublons inter-recettes massifs, ancres non uniques ; exigerait une
  méthodologie par recette distincte (hors comparabilité).
- `image-prompts/*.md` (233) : miroir 1:1 des recettes, même problème.
- `.gram/*.yaml` : données tabulaires (ingrédients), pas du texte
  requêtable en top-k sémantique ; contient en outre l'ancre bannie
  `clous-de-girofle` (collision directe avec dev-14).
- `.agents/skills/*`, `.agents/roles/*experts`, `.agents/scripts/*` :
  volumineux mais sans structure `##` stable (0 section pour 3 rôles),
  ou outillage, pas contenu mémoire.
- `.agents/claims.json` : déjà consommé (gold dev-14 C1/C2) → banni.

## 3. Règle déterministe d'inclusion / exclusion (pré-enregistrée)

INCLUS ssi, cumulativement :
1. fichier versionné au commit de freeze, encodage UTF-8 lisible ;
2. liste fermée ci-dessus (§2 A+B, 18 chemins — aucune autre source) ;
3. pertinent produit/agent : gouvernance du dépôt, principes, contribution,
   roadmap, statuts, règles d'orchestration des agents ;
4. contenu textuel : ≥1 section `##` OU (cas `AGENTS.md`, 5 sections OK) ;
   `image-assets.md` (0 `##`, 832 o) et `git-workflow.md` (1 `##`, 604 o)
   sont conservés comme distracteurs indexés mais **jamais golds**
   (taille insuffisante pour une ancre robuste — voir §6) ;
5. stabilité : documents de gouvernance, pas de sortie générée ;
6. **aucun des 26 golds historiques (§4)**, aucun item dev-14/holdout-8.

EXCLU : tout le reste (dont recettes, prompts, yaml, skills, rôles experts,
scripts). La sélection ne dépend d'**aucune mesure retrieval**
(aucun Qdrant lancé pour ce freeze ; ancres §6 vérifiées par `grep`/comptage
d'occurrences uniquement, pas par score).

## 4. Les 26 golds historiques bannis (rappel intangible)

Gate 4 / Cycle 1 (13) : `docs/ATOMIC_ACTION_ILLUSTRATIONS.md`,
`docs/CATALOGUE-CONTRACT-CORE.md`, `docs/CI-ARTIFACT-STORAGE.md`,
`docs/E2E-LEDGER.md`, `docs/HERDR-WORKSPACE-NAMING.md`,
`docs/IMAGE-PROVENANCE.md`, `docs/INSTANCE-IDENTITY.md`,
`docs/MEAL-COMPOSITION-V1.md`, `docs/MEAL_PLANNING_NUTRITION.md`,
`docs/PUBLIC-CONTENT-LINT.md`, `docs/equipment-add-appliance.md`,
`docs/equipment-audit-495.md`, `docs/equipment-contract-495.md`.
Dev-14 (8) : `.agents/claims.json`, `docs/E2E-LEAD-PROTOCOL.md`,
`docs/E2E-WORK-ITEM.md`, `docs/PUBLIC-CONTRACT.md`,
`docs/nutrition-profile-issue-136.md`, `docs/review-169-design.md`,
`docs/work-items/391-lot-icons.md`, `docs/work-items/391-lot-ui-icons.md`.
Holdout-8 mesuré (5) :
`decisions/PDR-0010-nutrition-plaisir-sante-meal-planning.md`,
`docs/review-169-cooking.md`, `docs/review-169-recipe.md`,
`docs/work-items/391-lot-header-brand.md`,
`docs/work-items/391-lot-typography.md`.
Test `test_corpus2b.py::test_banned_golds_absent` verrouille cette liste.

## 5. Rupture méthodologique et comparabilité (assumée)

- Le corpus d'indexation change : sections 209 → ~209+~90,
  faits 881 → ~881+~N (pins SHA au freeze de calibration, pas ici).
  Disque/RSS/latences ne seront pas comparables aux cycles précédents.
- La nature des golds change (docs techniques → gouvernance/roadmap) :
  les taux retrieval/succès **ne sont pas comparables** entre cycles.
  Seule la *question de réplication* reste comparable : « le bras
  fact+politique calibré sur dev neuf généralise-t-il au holdout neuf ? ».
- Payload, filtres, top_k=3, métriques (rank-1, recall@3, décision
  stricte/indulgente), règle de sélection τ×δ : **inchangés**.
- Aucun résultat Gate 4 / Cycle 2 n'a servi à choisir ce corpus
  (choix par structure et pertinence, pas par performance).

## 6. Capacité démontrée : 30 ancres OK → dev ≥30 et holdout ≥30 disjoints

30 ancres vérifiées le 2026-09-26 : **1 occurrence dans le nouveau
périmètre ET 0 dans l'ancien** (`docs/`+`decisions/`, grep exact),
formulations inédites, jamais utilisées en Cycle 1 / dev-14 / holdout-8 :

| # | Ancre | Gold neuf |
|---|---|---|
| 1 | `Six Piliers` | `CHARTER.md` |
| 2 | `Contrôles locaux réellement disponibles` | `CONTRIBUTING.md` |
| 3 | `Contributions assistées par agent` | `CONTRIBUTING.md` |
| 4 | `Règles d'Or Développeurs` | `.agents/STATUS.md` |
| 5 | `Jalons de Maturité` | `.agents/STATUS.md` |
| 6 | `Mobile first` | `PRODUCT_PRINCIPLES.md` |
| 7 | `Nutrition positive` | `PRODUCT_PRINCIPLES.md` |
| 8 | `spécialistes conseillent` | `PRODUCT_PRINCIPLES.md` |
| 9 | `P0 — Stabiliser` | `TODO.md` |
| 10 | `P1 — Mettre en place` | `TODO.md` |
| 11 | `P2 — Fiabiliser` | `TODO.md` |
| 12 | `P3 — Qualité produit` | `TODO.md` |
| 13 | `Vocabulaire officiel` | `README.md` |
| 14 | `Frontière avec le moteur` | `README.md` |
| 15 | `Roadmap — Entrée` | `README.md` |
| 16 | `Verrou Distribué` | `.agents/rules/multi-agent-orchestration.md` |
| 17 | `Watchdog de 15 minutes` | `.agents/rules/task-claiming.md` |
| 18 | `INTERDICTION DE DOUBLON` | `.agents/rules/task-claiming.md` |
| 19 | `Frugalité Éclairée` | `.agents/rules/token-frugality.md` |
| 20 | `Model Tiering` | `.agents/rules/token-frugality.md` |
| 21 | `Context Pruning` | `.agents/rules/token-frugality.md` |
| 22 | `Taxonomie Obligatoire` | `.agents/rules/cooking-execution.md` |
| 23 | `Règle 24` | `.agents/rules/cooking-execution.md` |
| 24 | `Graceful Degradation` | `.agents/rules/ingredient-icons.md` |
| 25 | `Direction artistique` | `.agents/rules/ingredient-icons.md` |
| 26 | `Unité de Travail` | `.agents/rules/cooking-execution.md` |
| 27 | `Quotas & Runtimes` | `.agents/rules/multi-agent-orchestration.md` |
| 28 | `Matrice d'Attribution` | `.agents/rules/multi-agent-orchestration.md` |
| 29 | `Dernières Livraisons` | `.agents/STATUS.md` |
| 30 | `snapshot 3 sept` | `TODO.md` |

11 docs neufs distincts porteurs, 90 chunks (sections, `chunk_markdown`) :
`README.md` 18, `TODO.md` 13, `PRODUCT_PRINCIPLES.md` 10, `CHARTER.md` 8,
`CONTRIBUTING.md` 7, `task-claiming.md` 7, `STATUS.md` 6,
`multi-agent-orchestration.md` 6, `token-frugality.md` 6,
`ingredient-icons.md` 5, `cooking-execution.md` 4.
Plan imposé (prochain GO, **pas ce tour**) : ≥30 items dev (23 answer
sur golds neufs + traps/OOD sans gold) et ≥30 items holdout sur les
mêmes 11 docs avec **ancres et formulations disjointes du dev**
(2 ancres distinctes par doc en moyenne : 11 docs × ~3 ancres
exploitables > 60 slots ; distracteurs : tout le reste du corpus
étendu). Réserve identifiée : `AGENTS.md`, `GEMINI.md`, `README.en.md`,
`.agents/roles/README.md`, `git-workflow.md` (indexés, non golds ici).

## 7. Procédure prévue (GO futurs, pas ce tour)

1. GO dev : construire `c2b_dev.json` (≥30 : ~23 answer + ~7-9 trap/OOD),
   ancres du §6 réparties sans réutilisation inter-dev/holdout à venir.
2. Calibration DEV ONLY (grille τ×δ, bras fact primaire, sec même point,
   règle Cycle 2) → `c2b_calibration.json`.
3. Freeze pré-holdout commité+poussé (point, SHAs, preuve d'absence du
   holdout) → STOP.
4. GO holdout : `c2b_holdout.json` (≥30, golds §6 disjoints du dev).
5. Une mesure unique → `c2b_results.json`, sans retuning.

## 8. Fichiers de ce freeze (aucune mesure)

| Fichier | Rôle |
|---|---|
| `cycle2b/README.md` | ce document |
| `cycle2b/corpus2b.py` | extension déterministe (anciens + 18 chemins, kind `doc-c2b`) |
| `cycle2b/c2b_method_freeze.json` | règles, 26 bannis, 30 ancres, pins |
| `cycle2b/test_corpus2b.py` | tests déterministes (stdlib, sans Qdrant) |
