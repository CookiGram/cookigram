# Provenance des images générées (#393)

## Chaîne traçable

```text
asset
  -> sémantique / sujet (subject)
  -> prompt
  -> profil visuel + révision (visual_profile)
  -> outil de génération (generation.tool)
  -> provider
  -> modèle (generation.model)
  -> batch
  -> date (generated_at)
  -> sha256
```

Manifest : [`assets/provenance/images.yaml`](../assets/provenance/images.yaml).
Audit : `scripts/audit-recipe-images.py --check`.

## Deux formes d'entrée, frontière explicite

La présence d'un bloc `generation:` distingue les nouvelles générations ;
son absence conserve les règles historiques sans réinterprétation :

| | Historique (sans `generation:`) | Nouveau (avec `generation:`) |
| --- | --- | --- |
| Sujet | clé `recipe: <slug>` | `subject: {type: recipe, recipe: <slug>}` ou `{type: cooking_action, action, context}` |
| Origine outil | `generator: <label>` requis | `generation.tool` requis (`generator` non exigé) |
| Batch / provider / modèle | — | `generation.batch`, `generation.provider`, `generation.model` requis |
| Profil visuel | — | `visual_profile: {name, revision >= 1}` requis |
| Commun | `origin: generated`, `prompt`, `generated_at`, `sha256`, `attribution` ; le fichier doit exister et le SHA-256 correspondre |

## Politique modèle : ne jamais deviner

`generation.model` porte l'identifiant réellement rapporté par l'outil.
Si l'outil ne l'expose pas, la valeur explicite `unknown` est obligatoire :
l'audit accepte toute chaîne non vide, y compris `unknown`, et rejette
l'absence — une hypothèse ne doit jamais passer pour une provenance factuelle.

## Sujets supportés

- `recipe` : image dédiée à une fiche ; un slug ne peut être mappé qu'une fois
  (forme `subject.recipe` ou clé historique `recipe`, détection unifiée).
- `cooking_action` : illustration partagée (`action` + `context`, ex.
  `cut` / `board`), déclarée une seule fois même si plusieurs recettes
  l'utilisent. Ces assets vivent hors de `static/images/` (ex.
  `static/illustrations/cooking-actions/v1/`) et ne sont pas soumis au
  contrôle d'orphelins des images de recette.

## Relations

- #391 : la direction artistique et le profil visuel appartiennent à
  l'instance ; Core ne porte que slots, fallbacks et invariants UX.
- #396 : le compilateur déterministe de prompts lira le profil visuel
  versionné et alimentera les champs `prompt`, `visual_profile`, `batch`
  et `subject` de ce manifest.
- Contrat UX des illustrations d'action (Mode Cuisine) :
  `CookiGram/cookigram-core#346`. Premier batch pilote prévu :
  `cooking-actions-v1-pilot-01`.

Aucune de ces métadonnées n'est affichée dans l'UI et aucune n'introduit
de besoin runtime.
