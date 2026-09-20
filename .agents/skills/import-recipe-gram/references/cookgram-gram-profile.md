# CookGram Gram profile

CookGram currently reads the following stable subset of Gram. Stay within this profile unless the generator is extended in the same change.

## Frontmatter

```gram
---
title: Poulet rôti au citron
portions: 4
prep_time: 15 min
total_time: 1 h 05 min
spiciness: 0
description: Poulet doré à la peau croustillante, jus court parfumé au citron et éclats d'ail en chemise.
tags: [poulet, four, familial]
source: https://example.org/recipe
author: Nom affiché sur la source
scaling:
  enabled: true
  min_portions: 2
  max_portions: 8
  step: 1
  note: Les temps de cuisson ne sont pas recalculés.
flavors:
  pairing: [poulet, citron, ail, thym]
  notes: [rôti, acidulé, herbacé]
  harmony: "L'acidité vive du citron dégraisse la chair du poulet tandis que le thym infuse le jus court."
  tips: "Arroser le poulet avec son jus à mi-cuisson pour une peau parfaitement dorée."
conservation:
  fridge_days: 3
  freezable: true
  reheat: "15 min au four à 150°C"
---
```

Required for a well-finished recipe:
- `title` : clear French culinary title.
- `portions` : baseline integer yield.
- `prep_time` & `total_time` : mandatory and distinct (`total_time` must account for all active, passive, baking and resting durations).
- `spiciness` : integer `0..3` (0: non épicé, 1: doux, 2: relevé, 3: pimenté).
- `description` : 100 to 120 characters, evocative of texture, key flavor and method. No generic filler.
- `tags` : lowercase categorized tags.
- `scaling` : explicit scaling rules.
- `flavors` : recommended for signature recipes (pairing, notes, harmony, tips).
- `source` and `author` : mandatory for web imports.

Every recipe must also declare scaling. For a fixed appliance recipe:

```yaml
scaling:
  enabled: false
  reason: "Quantités calibrées pour le bol du Thermomix TM31 ; volume et chauffe non validés à une autre échelle."
```

## Steps, actions and sub-steps

Each line beginning with `[Action]` becomes one guided cooking step:

```gram
[Préchauffer] Préchauffer le #four{} à ^{180 C}.
```

Use a short imperative action label. Keep one main operation per step so that mobile cooking mode remains clear.

### Sub-steps (Sous-étapes interactives)

When a step involves several sequential gestures or ingredients to combine, decompose it with bullet lines (`- `):

```gram
[Préparer le panier]
- Verser l'@eau{800 g} et le @sel{1 c. à café} dans le #bol Thermomix{}.
- Peser le @riz basmati{200 g} dans le #panier cuisson{}.
- Insérer le panier dans le bol et fermer le couvercle.
```

CookGram renders sub-steps as interactive checklists in Cook Mode, allowing cooks to tick them off on their screen or validate them hands-free with the voice command *« Validé »* / *« Fait »* before advancing to the next step. Annotations (`@ingredient{}`, `#equipment{}`, `~{timer}`, `^{temperature}`) are fully supported on sub-step lines.

## Ingredients

```gram
@pommes de terre{800 g}
@œufs{3}
@huile d'olive{1 c. à soupe}
@sel{1 pincée}
```

Rules for ingredients:
- **Step-Ingredient Systematic Annotation (Cooking First)** : Every ingredient incorporated during a step **MUST** be explicitly annotated with `@ingredient{quantity}` in the action line or sub-step (`- `). CookiGram extracts these to populate the "Ingrédients pour cette étape" card in Cook Mode. Never mention an ingredient in plain text only.
- **Nutritional Integrity (CIQUAL)** : Fats, proteins, dairy, produce, and carbs must always carry a concrete quantity or volume. Never leave empty brackets like `@huile{}` or `@eau{}` without a measure, as this prevents CIQUAL nutritional calculation and grocery list compilation.
- **Multi-step ingredients** : When an ingredient is used across multiple steps (e.g. part of the butter for dough, part for greasing), specify the step quantity clearly to ensure accurate grocery list consolidation.
- **Intermediate products** : `@ingredient{quantity}` is reserved for **entry ingredients** that belong in derived surfaces such as shopping, nutrition and scaling. A broth, juice, sauce or other product created, transformed or recovered during the recipe from already-declared ingredients is an **intermediate product**: when reused later, reference it in plain prose (with a quantity when useful) and do **not** create a new `@ingredient{}`. A split portion of a genuine entry ingredient remains an `@ingredient{}` and its quantities must be allocated explicitly across steps.

## Equipment

```gram
#four{}
#cocotte{}
#poêle{}
#bol Thermomix{}
```

Annotate equipment when it is required or affects instructions. Ordinary utensils need not all be listed.

## Timers

CookGram recognizes seconds, minutes, and hours as single scalar units:

```gram
~{30 s}
~{90 s}
~{8 min}
~{2 h}
```

Strict rules for timers:
- Put the timer in the step that starts it. Prefer `min` over ambiguous abbreviations in new files.
- **Single scalar unit only** : Never use composite timers like `~{4 min 50 s}` or `~{1 min 30 s}` (convert to `~{290 s}` or `~{90 s}`).
- **No timer ranges** : Never use ranges like `~{30-35 min}` that break the parser. Annotate the minimum duration in the timer (`~{30 min}`) and describe the visual/sensory doneness cue in prose (*« prolonger de 5 min si le dessus n'est pas doré »*).

## Temperatures

```gram
^{180 C}
^{63 C à cœur}
```

Use the value and meaning supplied by the source. For food safety, distinguish oven temperature from internal temperature.

## Thermomix and Cookomix conventions

For Thermomix recipes, declare the appliance in frontmatter:
```yaml
appliances:
  thermomix: [TM31, TM5, TM6]
source_appliances:
  thermomix: [TM5, TM6]
required_equipment:
  - Thermomix TM31, TM5 ou TM6
  - Varoma
tags: [..., thermomix]
```

`source_appliances` is the compatibility stated by the imported source;
`appliances` is CookiGram's supported set after any documented adaptations.
`required_equipment` is displayed before cooking. A model may be marked as
tested only after an explicit human report:

```yaml
appliance_validation:
  TM31:
    status: human-tested
    portions: 6
    note: Version 6 portions testée par le propriétaire du projet sur un TM31.
```

Do not invent a human validation or apply it to untested yields.

When formulating steps, specify:
- **Durée** : `~{10 s}`, `~{4 min}`, `~{16 min}`
- **Température** : `^{100 C}`, `^{120 C}`, `Varoma`
- **Sens inverse** : mentionner `sens inverse`
- **Vitesse** : `vitesse cuillère` (ou `vitesse mijotage`), `vitesse 1` à `10`, `turbo`, `pétrin`
- **Accessoires** : `#bol Thermomix{}`, `#gobelet doseur{}`, `#panier cuisson{}`, `#Varoma{}`, `#fouet papillon{}`, `#spatule{}`

CookGram automatically detects these parameters and displays a Cookomix-style badge with SVG icons:
- ⏱ Minuteur (chronomètre)
- 🌡 Température / Varoma (thermomètre)
- 🔄 Sens inverse (flèche circulaire antihoraire)
- 🥄 Vitesse cuillère (icône cuillère de mijotage)
- 🔪 Vitesse lames (icône lames de mixage)

## Complete example

```gram
---
title: Pommes de terre rôties
portions: 4
description: Quartiers croustillants et fondants.
tags: [accompagnement, four]
source: https://example.org/pommes-de-terre
---

## Pommes de terre rôties

[Préchauffer] Préchauffer le #four{} à ^{200 C}.

[Assaisonner] Mélanger les @pommes de terre{800 g} en quartiers avec l'@huile d'olive{2 c. à soupe} et le @sel{}.

[Rôtir] Étaler sur une #plaque{} et cuire ~{35 min}, en retournant à mi-cuisson, jusqu'à ce que les quartiers soient dorés et tendres.
```

## Current compatibility boundary

The official Gram language supports more constructs than CookGram's MVP parser. In particular, treat modules, intermediate variables, relative quantities, named timers, composite ingredients, and advanced calculations as unsupported unless the generator and its tests are updated together.

## Ingredient database matching

Before writing an `@ingredient{}`, inspect `.gram/ingredients.yaml`. Prefer the canonical French name already present in the database. Matching must consider:

- the YAML key, such as `magret-de-canard`;
- `name`, such as `Magret de canard`;
- every string in `aliases`.

For a missing ingredient, add a minimal entry alongside the recipe:

```yaml
ingredients:
  huile-olive:
    name: "Huile d'olive"
    aliases: ["huile d’olive"]
    category: "Huiles et matières grasses"
```

Do not add estimated `physical` or `nutrition` blocks merely to make the database look complete.
