# Illustrations d'Actions Atomiques CookiGram — Contrat d'Instance & Guide d'Intégration

> **Principe fondamental :**  
> *Le Core définit la sémantique des actions. Une instance définit leur représentation visuelle.*

---

## 1. Frontière Core / Instance

Dans l'écosystème CookiGram (conformément aux décisions d'architecture #346 et #391) :

* **Rôle du Core (`cookigram-core`) :**
  - Parse le langage culinaire Gram et extrait la structure des recettes.
  - Identifie les phases logiques et les sous-étapes atomiques.
  - Dérive des **tokens canoniques provider-neutral** (ex: `cut`, `rinse`, `mix`, `saute`, `simmer`, `rest`, etc.).
  - Définit les slots d'affichage (`.cook-phase-visual`), les dimensions UX responsives et les règles d'accessibilité.
  - Garantit les invariants : absence d'information UI interactive dans l'image (minuteurs, températures), et omission propre du slot sans régression si aucune illustration n'est disponible.
  - **Ne contient aucun asset, branding ou contrat de style propre à CookiGram.**

* **Rôle de l'Instance (ex: `CookiGram`) :**
  - Définit sa **Direction Artistique (DA)** et son profil visuel (manga éditorial chaleureux, gouache douce, fond crème lin `#FFF9F0`).
  - Produit et optimise les assets graphiques (`static/images/atomic-actions/*.webp`).
  - Gère le **mapping instance** (`canonical_token -> asset`) et la matrice de mutualisation des gestes.
  - Maintient la traçabilité des générations (modèle, prompt, version, SHA-256).

---

## 2. Emplacement des Assets & Arborescence

Dans le dépôt de l'instance (`cookigram`) :

```text
cookigram/
├── static/
│   ├── images/
│   │   └── atomic-actions/           # Assets finaux WebP (900×600 px, < 80 Ko)
│   │       ├── cut.webp
│   │       ├── rinse.webp
│   │       ├── mix.webp
│   │       ├── whisk.webp
│   │       ├── pour.webp
│   │       ├── saute.webp
│   │       ├── simmer.webp
│   │       ├── knead.webp
│   │       ├── rest.webp
│   │       └── serve.webp
│   └── illustrations/
│       └── cooking-actions/v1/       # Wrappers SVG vectoriels self-contained (fallback / bridge Core)
│           ├── cut.svg
│           ├── rinse.svg
│           └── ...
├── image-prompts/
│   └── atomic-actions/               # Fiches de prompts et métadonnées par action
│       ├── cut.md
│       ├── rinse.md
│       └── ...
├── assets/
│   └── atomic-actions/
│       └── manifest.json             # Manifeste complet de la collection instance
├── scripts/
│   └── action_visuals.py             # Résolveur, mapping d'instance et audit CLI
└── docs/
    └── ATOMIC_ACTION_ILLUSTRATIONS.md # Ce document
```

---

## 3. Mapping & Règles de Fallback

### 3.1 Mapping canonique du lot pilote

L'instance associe chaque token canonique du Core à un asset WebP de son identité :

| Token canonique | Fichier asset | Rôle & Gestuelle |
| :--- | :--- | :--- |
| `cut` | `images/atomic-actions/cut.webp` | Découpe de légumes au couteau de chef sur planche |
| `rinse` | `images/atomic-actions/rinse.webp` | Passoire inox sous un jet d'eau claire avec gouttelettes |
| `mix` | `images/atomic-actions/mix.webp` | Mélange doux à la cuillère en bois dans un saladier |
| `whisk` | `images/atomic-actions/whisk.webp` | Fouet ballon battant vigoureusement des œufs/crème en mousse |
| `pour` | `images/atomic-actions/pour.webp` | Filet diagonal doré d'huile ou de bouillon versé dans une poêle |
| `saute` | `images/atomic-actions/saute.webp` | Poêle chaude avec oignons/légumes saisis à la spatule |
| `simmer` | `images/atomic-actions/simmer.webp` | Cocotte en fonte entrouverte, bouillonnement doux et vapeur légère |
| `knead` | `images/atomic-actions/knead.webp` | Deux mains repliant une boule de pâte sur plan fariné |
| `rest` | `images/atomic-actions/rest.webp` | Pain tiédissant sur grille avec torchon, zéro main humaine |
| `serve` | `images/atomic-actions/serve.webp` | Cuillère de service dressant le plat sur une assiette en grès |

### 3.2 Matrice de mutualisation
Pour éviter la prolifération de variantes visuellement indiscernables sur petit écran, les gestes secondaires sont mutualisés :
- `chop`, `slice`, `dice`, `mince`, `julienne` $\rightarrow$ `cut`
- `drain`, `wash`, `strain` $\rightarrow$ `rinse`
- `stir`, `combine`, `toss` $\rightarrow$ `mix`
- `beat`, `emulsify`, `froth` $\rightarrow$ `whisk`
- `drizzle`, `add_liquid`, `deglaze` $\rightarrow$ `pour`
- `sear`, `brown`, `fry` $\rightarrow$ `saute`
- `stew`, `braise`, `reduce` $\rightarrow$ `simmer`
- `fold_dough`, `shape_dough`, `punch_down` $\rightarrow$ `knead`
- `cool`, `stand`, `settle` $\rightarrow$ `rest`
- `plate`, `garnish_final`, `dish_out` $\rightarrow$ `serve`

### 3.3 Politique de fallback
1. **Token non illustré dans le pilote (ex: `boil`, `steam`, `air_fry`, `preheat`) :**  
   L'instance laisse le Core afficher son visuel vectoriel standard.
2. **Action inconnue ou générique (`generic`) :**  
   Le Core résout un asset vide (`""`). Le template `cook.html` omet purement et simplement le bloc `.cook-phase-visual`. **Pas d'illustration vaut infiniment mieux qu'une illustration erronée.**
3. **Fichier manquant sur le disque :**  
   Le résolveur `resolve_action_asset(token, root)` vérifie l'existence du fichier avant de le renvoyer. Si le fichier est absent, il bascule silencieusement sur le fallback sans lever d'exception.

---

## 4. Contrat Visuel d'Instance CookiGram

* **Rendu :** Non-photoréaliste. Hybride gouache numérique et *soft cel-shading*.
* **Palette :** Fonds crème lin (`#FFF9F0`), grège (`#F7EFE2`), touches terracotta (`#E07A5F`), vert sauge (`#819B88`), bois clair.
* **Cadrage :** Vue plongeante 3/4 (40°–45°) ou vue rapprochée au plan de travail. Ratio source `3:2`.
* **Éléments humains :** Avant-bras et mains uniquement en cours de geste. **Aucun visage, aucun regard, aucun corps entier**.
* **Ustensiles :** Bois clair, céramique/grès émaillé, inox satiné, fonte émaillée. **Aucune marque commerciale ni logo**.
* **Règle UI d'or :** **Aucune information UI interactive dans l'image** (pas de minuteur, pas de température, pas de chiffre, pas de flèche). Ces données appartiennent au moteur d'exécution pas-à-pas (PWA).
* **Contrainte d'échelle :** Lisibilité conservée du grand écran (300×150 px) au smartphone (260×130 px) et à la vignette compacte (120×80 px).

---

## 5. Traçabilité & Manifeste

Chaque illustration d'action fait l'objet d'un enregistrement complet dans [`assets/atomic-actions/manifest.json`](file:///home/pierrecsn/Work/cookigram/assets/atomic-actions/manifest.json) :

```json
{
  "action_id": "cut",
  "action_label": "Couper / Émincer",
  "canonical_token": "cut",
  "status": "pilot_approved",
  "asset_path": "images/atomic-actions/cut.webp",
  "model_name": "Imagen 3",
  "model_version": "imagegeneration@006",
  "generation_date": "2026-09-21",
  "aspect_ratio": "3:2",
  "dimensions": "900x600",
  "file_size_bytes": 30448,
  "file_size_kb": 29.7,
  "sha256": "4b6f12ab73fc6654b03666d925827ae924df39c5a176840d5138139dffab032f",
  "contract_version": "1.0.0",
  "prompt": "Modern editorial culinary illustration of cutting vegetables on a wooden cutting board, hands holding a chef knife slicing carrots...",
  "negative_prompt": "photorealism, 3d render, photograph, cartoon, anime chibi, faces, full body, text, letters, watermarks, timer, clock, digital icons, kitchen chaos, blurry",
  "mutualized_tokens": ["chop", "slice", "dice", "mince", "julienne"],
  "justification": "Cadrage 3/4 net sur la lame et la rondelle..."
}
```

Les prompts sources sont documentés individuellement dans `image-prompts/atomic-actions/<token>.md`.

---

## 6. Gouvernance de Régénération & Cycle de Vie

### 6.1 Règle cardinale
> **Un changement de version d'un modèle d'IA ne déclenche JAMAIS automatiquement le remplacement du lot en production.**

### 6.2 Processus de régénération maîtrisé
1. **Phase candidate :** Générer l'intégralité du lot candidate avec le nouveau modèle sous un dossier de travail temporaire.
2. **Comparaison visuelle en double aveugle :** Générer la matrice comparative (équivalent de `test-scale.html`) mettant en regard lot en production vs lot candidat à 300×150, 260×130 et 120×80 px.
3. **Décision explicite :** Le Product Owner et le Web Design Lead valident collectivement le gain ergonomique.
4. **Remplacement atomique :** Si le nouveau lot est approuvé, remplacer l'ensemble de la série d'un seul coup (commit atomique) avec mise à jour du manifeste. Interdiction absolue d'avoir un panachage de styles entre étapes d'une même recette.

---

## 7. Procédure d'Ajout d'un Nouveau Token (P1 / P2)

1. S'assurer que le token canonique est formellement reconnu par le Core (`generator/cooking_actions.py`).
2. Définir le prompt d'illustration conformément au contrat visuel d'instance.
3. Générer l'illustration en ratio `3:2`.
4. Normaliser le fichier à 900×600 px en WebP (`q=82`), vérifier que le poids est `< 80 Ko`.
5. Placer l'asset sous `static/images/atomic-actions/<token>.webp`.
6. Générer le wrapper SVG vectoriel sous `static/illustrations/cooking-actions/v1/<token>.svg`.
7. Créer la fiche de prompt sous `image-prompts/atomic-actions/<token>.md`.
8. Enregistrer l'entrée enrichie dans `assets/atomic-actions/manifest.json`.
9. Déclarer le mapping dans `scripts/action_visuals.py` (`INSTANCE_ACTION_MAPPING` et `MUTUALIZED_ALIASES`).
10. Valider avec `python scripts/action_visuals.py --check` et `pytest tests/test_action_visuals.py`.

---

## 8. Guide pour une Instance Tierce (Custom Instance)

Une personne ou organisation déployant sa propre instance (ex: *La Cuisine de Mamie*, *TechCook*) avec son propre style visuel (ex: flat vector minimaliste, gravure victorienne, photo réaliste) doit simplement :

1. Créer son propre dossier `static/images/atomic-actions/` ou `static/illustrations/cooking-actions/v1/`.
2. Définir son propre fichier `assets/atomic-actions/manifest.json` avec sa DA et ses prompts.
3. Déclarer ses mappings dans sa configuration d'instance.
4. Aucun fork du Core n'est requis : le Core consomme les tokens canoniques et s'adapte automatiquement à la présence ou l'absence des assets de l'instance.
