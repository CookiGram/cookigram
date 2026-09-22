# Validation publique du contrat `.gram`

## Contrat utilisé par la CI

La CI installe le paquet public [`cookigram-contract`](https://github.com/PierreCsn/cookigram-contract)
directement depuis GitHub, à la référence immuable `v1.0.0`.

```text
CONTRACT_VERSION=1.0.0
CONTRACT_REF=v1.0.0
CONTRACT_SHA=b567e88acdcee69302c926caa6f5222508b7a051
CLI=python -m cookigram_contract validate .
```

Le job vérifie d'abord que le tag annoté `v1.0.0` résout vers
`b567e88acdcee69302c926caa6f5222508b7a051`, puis installe cette référence et
valide le corpus complet, y compris `recipes/`, `.gram/ingredients.yaml` et
`.gram/ingredient-provenance.yaml`. Le parser et le schéma ne sont pas copiés
dans ce dépôt.

## Chemins de validation

| Contexte | Validation | Secret privé |
| --- | --- | --- |
| PR, y compris depuis un fork | `cookigram-contract` v1.0.0 et audit des illustrations | Non |
| Push de confiance / exécution hors PR | `cookigram-core` épinglé par `.core-version`, `recipe_check` et build | Oui |

Le workflow ne transmet donc jamais `CORE_SSH_KEY` à une exécution de PR.
L'intégration privée reste complémentaire : elle vérifie le build et les
règles propres au moteur, mais ne remplace pas le contrat public.

La validation privée reste conditionnelle à `CORE_SSH_KEY` et ne s'exécute que
sur les pushes/exécutions de confiance; elle ne peut donc pas faire échouer
les forks. L'audit des illustrations reste public et bloquant pour toutes les
PR.

## Pipeline qualifié (Contract 1.1.0)

Le job `qualified-pages-artifact` (`ci.yml:70`) construit le site avec le
builder public pinné par `.builder.json`, sous `CONTRACT_VERSION=1.1.0`.

`.builder.json` contient 8 clés : `release`, `artifact`, `sha256`, `core_sha`,
`contract_version`, `contract_source_sha`, `contract_artifact`,
`contract_sha256`. Le contrat embarqué est la version `1.1.0` à
`contract_source_sha=ad0a53107de370e8dc3118f780f85b6cbabc4425`.

Le job écrit `_site/provenance.json` avec `contract_source_sha` (nommage
canonique, D1) et les autres pins. `pages.yml` vérifie `provenance.json`
avant déploiement, sans rebuild.

La bascule d'étiquette de `recipe-check` (1.0.0 → 1.1.0) reste séquencée et
en attente. Détail dans
[`CATALOGUE-CONTRACT-CORE.md`](CATALOGUE-CONTRACT-CORE.md) (D1, suite 4).

## Contrôle déterministe des pins

[`scripts/check-pins.py`](../scripts/check-pins.py) vérifie les références
utilisées par les workflows, sans recopier le parseur `.gram` :

```bash
python scripts/check-pins.py --json
python scripts/check-pins.py --markdown --no-remote
```

Le code de sortie `0` signifie que les pins contrôlables sont cohérents ; `1`
signale une incohérence ou une référence introuvable ; `2` signale une erreur
d'utilisation ou d'exécution. Le rapport JSON contient les valeurs et les
codes de contrôle, et le rapport Markdown est lisible dans les logs ou par un
agent.

`CONTENT_SHA` est comparé au commit checkouté. `CONTRACT_VERSION` et
`CONTRACT_SHA` sont lus dans le job public de CI, puis le tag public est résolu
avec `git ls-remote`. `.core-version` est comparé au checkout local de Core
dans les jobs privés. Si `CORE_SSH_KEY` est absent, la vérification distante de
Core est explicitement ignorée : ce cas est attendu pour une PR depuis un fork
et ne désactive aucun contrôle public.

## Frontière Catalogue / Contract / Core

La séparation des responsabilités entre le catalogue, le contrat et le moteur
— cartographie CI, écarts et chemin self-hosting tiers — est décrite dans
[`CATALOGUE-CONTRACT-CORE.md`](CATALOGUE-CONTRACT-CORE.md)
(référence [`cookigram-core#318`](https://github.com/CookiGram/cookigram-core/issues/318)).
