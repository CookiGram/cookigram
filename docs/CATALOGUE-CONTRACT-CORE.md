# Frontière Catalogue / Contract / Core

> Référence d'architecture pour
> [`cookigram-core#318`](https://github.com/CookiGram/cookigram-core/issues/318)
> — découpler catalogue, contrat et Core pour le self-hosting.
> Complète [`PUBLIC-CONTRACT.md`](PUBLIC-CONTRACT.md), qui décrit le chemin de
> validation publique en détail.

```text
cookigram-contract
        ↓
valide la conformité
        ↓
catalogue

cookigram-core
        ↓
consomme un catalogue conforme
        ↓
build/runtime

Core × catalogue
        ↓
compatibility workflow séparé
```

## Qui possède quoi

| Responsabilité | Propriétaire | Dépôt |
| --- | --- | --- |
| Définition de la validité d'un catalogue (structure, Gram, ingrédients, provenance, métadonnées, artefacts attendus) | `cookigram-contract` | [`CookiGram/cookigram-contract`](https://github.com/CookiGram/cookigram-contract) |
| Conformité du contenu officiel (recettes, `.gram/`, images, prompts, SEO éditorial) | CI catalogue, via Contract uniquement | ce dépôt (`CookiGram/cookigram`) |
| Moteur, générateur, parsing/modèle, UI/JS, fixtures contractuelles intentionnelles | CI Core | `CookiGram/cookigram-core` (privé) |
| Preuve qu'un Core donné construit le catalogue officiel | workflow de compatibilité séparé (hors CI normale) | `cookigram-core` (cible) |
| Qualification de l'artefact publié et sa provenance | chaîne `ci.yml` → `pages.yml` | ce dépôt |

Invariants :

* la validité d'un catalogue est définie **exclusivement** par Contract ;
* si un catalogue passe Contract mais casse Core, c'est un **bug Core ou une
  lacune du contrat**, pas une recette invalide ;
* le catalogue officiel est **un catalogue parmi d'autres** ;
* une PR Core ordinaire ne nécessite pas le corpus officiel (~199 recettes) ;
* un catalogue se déclare conforme **sans Core** ;
* la qualification Pages et sa provenance ne sont jamais affaiblies.

## Cartographie CI réelle (état audité 2026-09-21)

### `cookigram-contract`

| Job | Valide | Propriétaire | Dépend de Core | Dépend du catalogue officiel | Corpus | Déclenchement | Bloque les PR | Duplication |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `test` (`ci.yml`) | tests unitaires + `validate examples/minimal-content` | Contract | non | non | fixture | push `main` + PR | oui | non |

### `CookiGram/cookigram` (ce dépôt)

| Job | Valide | Propriétaire | Dépend de Core | Dépend du catalogue officiel | Corpus | Déclenchement | Bloque les PR | Duplication |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `recipe-check` (`ci.yml`) | pin Contract (`CONTRACT_VERSION`/`CONTRACT_SHA`), `cookigram_contract validate .`, images/prompts, lint SEO, planner JS, tests unitaires | Catalogue | non | soi-même | complet | PR + push `main` + dispatch | oui | non — c'est la validation de référence |
| `qualified-pages-artifact` (`ci.yml`) | build complet avec le **builder public pinné** (`.builder.json` + `.core-version`, SHA256 vérifié), `check-generated-surfaces`, `provenance.json`, upload `cookigram-pages-<sha>` | Publication | builder public pinné, sans secret | soi-même | complet | PR + push `main` + dispatch | oui (gate de qualification) | non — c'est la preuve de constructibilité |
| `private-integration` (`ci.yml`) | `generator.recipe_check --root .` + build complet avec **checkout privé** de Core (`CORE_SSH_KEY`) | ambiguë (logique moteur hébergée côté catalogue) | oui, privé, secret | soi-même | complet | push de confiance uniquement (jamais les PR) | non | **oui** — voir écarts E1/E2 |
| `build` (`pages.yml`) | déploie **exactement** l'artefact qualifié (vérification `provenance.json`, pas de rebuild) | Publication | non (artefact déjà qualifié) | soi-même | artefact | `workflow_run` CI `main` verte + dispatch manuel | n/a | non |
| `sync` (`sync-core-pin.yml`) | converge `.core-version` + `.builder.json` vers le builder vérifié, rejoue la CI candidate puis `main`, puis Pages | Publication | release publique du builder | soi-même | complet (via CI rejouées) |toutes les 15 min + `repository_dispatch` + dispatch | n/a | amplification assumée (voir E5) |

### `CookiGram/cookigram-core` (privé)

| Job | Valide | Propriétaire | Dépend de Core | Dépend du catalogue officiel | Corpus | Déclenchement | Bloque les PR | Duplication |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `recipe-check` | `generator.recipe_check tests/fixtures/recipes` (7 fixtures) | Core | soi-même | non | fixtures | PR + push `main` + dispatch | oui | non — conforme à la cible |
| `fast-checks` | `pre_pr_check --fast` (lint, types, JS) | Core | soi-même | non | fixtures | PR + push `main` + dispatch | oui | non |
| `engine-tests` | `pytest` (couverture 80 %) + `generator.build` (contenu Core local) | Core | soi-même | non | local | PR + push `main` + dispatch | oui | non |
| `e2e` (Playwright) | PWA complète construite depuis `CookiGram/cookigram@b5faade` (`CONTENT_DIR=cookigram-content`) | Core | soi-même | **oui — checkout pinné du catalogue officiel à chaque run** | officiel complet | PR + push `main` + dispatch | oui | voir écart E3 |
| `publish` (`publish-builder.yml`) | exige la CI Core verte pour le SHA exact, publie le wheel immuable `core-<sha7>` + `builder-provenance.json` vers les releases publiques, déclenche `core-builder-published` | Release Core | soi-même | transitivement (via `e2e`) | n/a | CI `main` verte + dispatch | n/a | non |

## Écarts classés (selon #318)

* **E1 — duplication évidente.** `private-integration` (`recipe_check` + build
  complet, corpus officiel) refait ce que `qualified-pages-artifact` prouve
  déjà avec le même Core pinné (via le builder public vérifié), en plus de la
  validation Contract de `recipe-check`. Trois validations du corpus complet
  sur chaque push `main`.
* **E2 — responsabilité mal placée.** `private-integration` fait du dépôt
  catalogue le porteur d'une logique moteur (`generator.recipe_check`) :
  le catalogue ne doit devoir sa conformité qu'à Contract. Si Contract passe
  mais Core échoue, l'invariant dit bug Core / lacune Contract — pas une
  recette invalide.
* **E3 — dépendance Core → catalogue officiel en CI normale.** Le job `e2e`
  de Core checkout le catalogue officiel à chaque PR Core. Les specs e2e
  n'utilisent pourtant que des contenus génériques ou des slugs présents dans
  les fixtures (`butter-chicken`, `curry-poulet-noix-coco`, comptes `> 0`) ;
  `playwright.config.js` bascule déjà sur
  `--recipes-dir tests/fixtures/recipes` quand `CONTENT_DIR` est absent.
  Cible : e2e de PR sur fixtures ; catalogue officiel réservé au workflow de
  compatibilité.
* **E4 — intégration légitime mais trop fréquente (à conserver au bon
  niveau).** La preuve « tel Core construit tel catalogue » reste utile, mais
  elle n'a pas sa place dans chaque PR Core ni dans chaque push catalogue :
  workflow dédié `compat-catalog.yml` côté Core — `workflow_dispatch`,
  hebdomadaire, après release Core / changement de Contract — avec
  validation Contract du catalogue, build avec le Core ciblé, smoke E2E
  minimal, résultat visible. Aucun équivalent n'existe aujourd'hui.
* **E5 — amplification assumée, conforme.** `sync-core-pin` rejoue la CI
  (candidate puis `main`) puis Pages : chaque run qualifie un commit distinct
  avec provenance vérifiée. Ce n'est pas une duplication de logique, c'est la
  chaîne de qualification. À conserver.
* **E6 — déjà conforme, aucune action.** Validation Contract du catalogue sans
  Core ; CI Core (`recipe-check`, `fast-checks`, `engine-tests`) sans
  catalogue officiel ; CI Contract sur exemples ; déploiement Pages sans
  rebuild avec vérification de provenance.

## Dérive de version connue (non corrigée ici)

Le contrat est publié en **1.1.0** (opt-in Meal Composition, rétrocompatible)
et Core exige la lib `cookigram-contract` **1.1.0**
(`generator/meal_composition.py`), mais la chaîne de qualification affiche
partout `contract_version: 1.0.0` (CI catalogue, `builder-provenance.json`,
garde `sync-core-pin`). Fonctionnel aujourd'hui, mais l'étiquette de
provenance ne reflète plus le contrat réellement embarqué. La bascule
coordonnée 1.0.0 → 1.1.0 (3 dépôts + releases) recoupe le builder hermétique
(`cookigram-core#298`) : traitée comme suite, pas dans ce slice.

Note : `scripts/check-pins.py` résout le tag Contract via l'URL historique
`PierreCsn/cookigram-contract.git` alors que les workflows et la documentation
utilisent `CookiGram/cookigram-contract.git`. Les deux résolvent aujourd'hui
vers le même SHA (`b567e88…`), donc simple note d'hygiène, sans changement.

## Self-hosting tiers : chemin explicite

Pour construire sa propre Cuisine sans secret ni dépendance privée :

```bash
# 1. Valider son catalogue avec le contrat public (aucun Core requis)
pip install "git+https://github.com/CookiGram/cookigram-contract.git@v1.0.0"
python -m cookigram_contract validate .

# 2. Construire avec un builder Core versionné et vérifié (SHA256)
#    voir releases "core-*" de CookiGram/cookigram : wheel + builder-provenance.json
pip install "<builder-wheel-vérifié>"
python -m generator.build --content-dir . --output _site
```

Le POC multi-sources reste décrit dans `cookigram-core#248` (assemblage
`staging-content/`, collision = erreur explicite, aucun `latest` implicite).
L'identité déclarative / white-label relève de `cookigram-core#324` et la
frontière visuelle Core / instance de `CookiGram/cookigram#391` : ce document
ne les recouvre pas.

## Suites proposées (hors slice, à décider)

1. Core : faire passer `e2e` de la CI normale sur fixtures (retirer le
   checkout `cookigram-content` de `ci.yml`) — après vérification locale que
   les 18 specs passent sur les 7 fixtures.
2. Core : créer `compat-catalog.yml` (`schedule` hebdo + `workflow_dispatch`
   + déclenchement post-release) : checkout catalogue officiel, validation
   Contract, build avec le Core ciblé, smoke E2E minimal.
3. Catalogue : reconvertir ou supprimer `private-integration` une fois (2) en
   place, sans affaiblir `qualified-pages-artifact` ni `pages.yml`.
4. Coordonner la bascule `contract_version` 1.0.0 → 1.1.0 avec #298 (provenance
   du builder = version réellement embarquée).
