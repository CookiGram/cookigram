# Stockage des artefacts GitHub Actions (#482)

## Constat

Le seul poste significatif de stockage Actions est le build complet de `_site`
(~85 Mo brut, ~64 Mo compressé, ~900 fichiers) publié par le job
`qualified-pages-artifact` de [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
via `actions/upload-artifact`, y compris sur les pull requests où aucun job
downstream ne le consomme.

## Politique

- Les PR **construisent et valident `_site` intégralement** (build qualifié,
  `check-generated-surfaces.py`, `provenance.json`) mais **ne l'uploadent pas** :
  l'étape d'upload est conditionnée à `github.ref == 'refs/heads/main'` hors
  `pull_request`. La qualité de validation est inchangée.
- Seuls les runs qualifiés sur `main` (push, ou `workflow_dispatch` sur `main`
  via `sync-core-pin`) publient `cookigram-pages-<sha>`, consommé ensuite par
  [`pages.yml`](../.github/workflows/pages.yml) (`download-artifact` par
  `run-id`, vérification de provenance, puis `upload-pages-artifact` imposé
  par le déploiement Pages).
- Après un déploiement réussi, `pages.yml` **supprime l'artefact consommé**
  (best-effort : `continue-on-error`, n'invalide jamais un déploiement).
  `retention-days: 1` reste le filet pour les artefacts non consommés.
- Conservés volontairement : le cache pip de `setup-python` (quota cache
  séparé, faible volume, accélère la CI) et les Release publiques du builder
  Core (quota Releases séparé, hors sujet — voir #482).
- Aucun artefact de diagnostic (type Playwright) n'existe aujourd'hui ; s'il
  s'en ajoute un jour, il devra être limité à `failure()` avec rétention
  minimale.

## Estimation (journée chargée : ~15 runs PR + ~3 runs main, ~64 Mo/artefact)

| Situation | Artefacts conservés | Stockage max (~1 jour) |
| --- | --- | --- |
| Avant | 18 builds `_site` | ~1,1 Go |
| Après | 3 builds `_site` sur `main`, supprimés après déploiement | ~0 Go en régime stable (~190 Mo transitoires) |

Filet : si Pages ne consomme pas un artefact `main`, il expire après 1 jour
(~190 Mo max pour 3 runs).

## Risques résiduels

- Rejouer manuellement un déploiement Pages après suppression de l'artefact
  échoue au téléchargement : relancer la CI `main` pour requalifier.
- `upload-pages-artifact` reste requis par GitHub Pages (stockage interne au
  déploiement, incompressible).
- Un artefact `main` non consommé (Pages non déclenché) vit jusqu'à 1 jour.
