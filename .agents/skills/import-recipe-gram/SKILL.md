---
name: import-recipe-gram
description: Research a recipe on the web and add or improve a sourced `.gram` recipe in CookGram. Use when an agent is asked to import, adapt, translate, or create a recipe from an online page or video; do not use for purely local recipe edits that need no external research.
---

# Import a web recipe into CookGram

Produce a practical, traceable recipe in `recipes/` that compiles with the current CookGram generator. Preserve the culinary facts while rewriting the directions concisely; do not copy a source's introduction, anecdotes, photographs, or distinctive prose.

## Research

Browse the web because recipe contents and URLs are external facts. Prefer, in order:

1. the original author or publisher;
2. an authoritative manufacturer or culinary institution for appliance-specific methods;
3. a complete recipe page exposing Schema.org `Recipe` data;
4. a video only when it gives enough quantities and timings.

Use one primary source. Consult another reliable source when the primary source omits a safety-critical temperature, pressure-release method, doneness criterion, or other information needed to cook safely. Never silently invent a missing quantity or duration: leave it unquantified, mark the uncertainty in `description`, or ask the user when it materially affects the result.

Record the exact primary URL in frontmatter as `source:` and the displayed author or channel as `author:`. Do not invent an author. Keep a short source note in the final response.

## Convert

Read [CookGram Gram profile](references/cookgram-gram-profile.md) and [US Customary conversion guide](references/us-customary-conversion.md) (when importing American or imperial recipes) before writing or modifying a recipe.

Before choosing ingredient names, read `.gram/ingredients.yaml`. Match each researched ingredient against canonical keys, `name`, and `aliases`:

- reuse the existing canonical wording when an entry already represents the ingredient;
- do not create singular/plural, translated, or spelling variants as separate entries;
- when no entry matches, plan a new canonical lowercase kebab-case key and use a clear French `name`;
- add source wording as an alias only when it is genuinely useful for future matching.

When the official Gram CLI is installed and configured, prefer its structured importer for a compatible page or YouTube URL:

```bash
gram import "SOURCE_URL" -o recipes/slug.gram
```

Review the output rather than accepting it blindly. Otherwise convert manually from the researched facts. Normalize the result to French unless the user requests another language.

Structure the recipe into clear, readable, bite-sized steps with interactive sub-steps:

- **Granularité fine des étapes** : Never condense an entire multi-gesture phase into an opaque wall of text. Break operations down into discrete, focused steps (e.g., 6 to 10 logical steps for a complete meal).
- **Sous-étapes interactives (`- `)** : When an action involves multiple sequential gestures (such as weighing an ingredient, positioning a steamer tray, and adjusting seasoning), write each gesture as a bullet point (`- `) under the `[Action]`. CookGram parses these into interactive checklist items in Cook Mode so cooks can validate them as done before proceeding.
- **Annotations sur les sous-étapes** : Place `@ingredient{quantity}`, `#equipment{}`, `~{timer}`, and `^{temperature}` annotations directly within the relevant sub-step or action line.
- **Lisibilité mobile** : Keep each sub-step to 1 or 2 lines maximum so instructions remain comfortable to read on a phone at arm's length.
- Every ingredient first appears with its total useful quantity;
- Preparation details such as “émincé” or “à température ambiante” remain explicit;
- Timers and temperatures are annotations, not prose-only values;
- Equipment is annotated where it changes the method;
- Doneness cues accompany timing when timing alone is unreliable;
- Appliance instructions name the compatible model or capability without pretending to control the device.

### Normes de Qualité & Exigences Produit CookiGram

Toute recette importée ou adaptée dans CookiGram doit se conformer aux décisions produit actées (PDR-0001 à PDR-0004) et aux exigences du Mode Cuisine en temps réel :

1. **Description éditoriale calibrée et évocatrice** (`description:`) :
   - Obligatoire dans le frontmatter YAML.
   - Longueur : 100 à 120 caractères.
   - Contenu : Évocatrice, descriptive des textures, saveurs clés et méthode (ex: *« Pavé de saumon fondant nappé d'une sauce onctueuse à la crème, parmesan et épinards frais. »*).
   - Proscrire impérativement les textes génériques du type « [Titre] — recette pas-à-pas sur CookiGram » ou la simple répétition du titre.

2. **Intégrité temporelle (`prep_time` et `total_time`)** :
   - `prep_time` et `total_time` doivent être TOUS LES DEUX renseignés, distincts et fiables.
   - `total_time` englobe la totalité du processus : préparation active, mijotages passifs, passage au four, cuissons vapeur (Varoma) et temps de repos/refroidissement indispensables avant dégustation.
   - Ne jamais déclarer un `total_time` égal au `prep_time` lorsqu'une cuisson ou un temps d'attente intervient.

3. **Indicateur de piquant décisionnel (`spiciness: 0..3`)** :
   - Obligatoire dans le frontmatter pour guider le choix du repas au quotidien :
     - `0` : non épicé (doux pour les enfants)
     - `1` : doux / chaleureux
     - `2` : relevé
     - `3` : pimenté / très épicé

4. **Profil sensoriel et accords de saveurs (`flavors:`)** :
   - Fortement recommandé pour les recettes signatures ou emblématiques :
     ```yaml
     flavors:
       pairing: [saumon, épinards, parmesan, citron]  # 2 à 4 ingrédients signature
       notes: [crémeux, acidulé, iodé]                # Dominantes sensorielles
       harmony: "L'acidité vive du citron vient trancher la richesse du saumon et de la crème."
       tips: "Pour une note printanière, remplacer les épinards par des pousses d'oseille."
     ```

5. **Traçabilité stricte des ingrédients par étape (`step.ingredients`)** :
   - En Mode Cuisine, CookiGram isole et affiche la carte « Ingrédients pour cette étape » directement au-dessus de chaque action.
   - **RÈGLE : Chaque ingrédient d'entrée incorporé à une étape DOIT être formellement balisé `@ingrédient{quantité}`** dans la ligne d'action ou de sous-étape (`- `).
   - **Exception — produits intermédiaires** : un bouillon, jus, sauce ou autre préparation produit/récupéré pendant la recette à partir d'ingrédients déjà déclarés se référence en prose lorsqu'il est réutilisé et ne doit pas créer un nouveau `@ingrédient{}`. La règle normative complète est dans [CookGram Gram profile](references/cookgram-gram-profile.md).
   - Hors de cette exception, ne jamais mentionner un ingrédient d'entrée uniquement en texte brut sans balise (ex: *« Verser l'huile dans la poêle »* est interdit ; écrire *« Faire chauffer l'@huile d'olive{1 c. à soupe} dans une #poêle{}. »*).

6. **Zéro ingrédient fantôme ou quantité vide pour la nutrition CIQUAL** :
   - Ne jamais laisser de crochet vide `@eau{}` ou de matière grasse non quantifiée `@huile{}`.
   - Les féculents, protéines, produits laitiers et huiles de cuisson doivent tous porter une quantité mesurable pour alimenter le calculateur nutritionnel CIQUAL et la liste de courses consolidée.

7. **Syntaxe stricte des minuteurs scalaires (`~{}`)** :
   - Chaque balise minuteur doit porter une unité scalaire unique et standard : `~{90 s}`, `~{4 min}`, `~{1 h}`.
   - Ne jamais générer de durées composées (`~{4 min 50 s}` ou `~{1 min 30 s}`) ni de plages (`~{30-35 min}`) qui brisent le parseur.
   - Pour une plage de cuisson, annoter la durée minimale dans le minuteur (ex: `~{30 min}`) et préciser le critère sensoriel de fin de cuisson dans le texte.

8. **Cohérence des modèles Thermomix (120°C vs TM31)** :
   - Une recette prescrivant `^{120 C}` est physiquement incompatible avec le TM31 (qui plafonne à 100°C et Varoma). Déclarer `appliances.thermomix: [TM5, TM6, TM7]`.
   - Si une compatibilité TM31 est revendiquée, utiliser `^{Varoma}` ou adapter la consigne thermique.

9. **Conservation et Batch Cooking (`conservation:`)** :
   - Déclarer les métadonnées de conservation lorsque pertinent :
     ```yaml
     conservation:
       fridge_days: 3
       freezable: true
       reheat: "10 min au four à 160°C"
     ```

10. **Gestion des illustrations et image placeholder (`image:`)** :
    - Si une illustration personnalisée (1280×720) est disponible : `image: images/<slug>.jpg`.
    - Si aucune image n'est générée immédiatement : utiliser l'image officielle d'attente `image: images/placeholder-recipe.jpg` avec :
      ```yaml
      image_credit:
        author: CookiGram
        source: https://github.com/PierreCsn/cookigram
        license: Illustration temporaire
      image_generation:
        prompt_file: image-prompts/<slug>.md
      ```
      Rédiger impérativement le prompt de description culinaire dans `image-prompts/<slug>.md`.

### Marmiton

When importing from marmiton.org:

- The ingredient icons and links point to affiliate products (Amazon, Puget…), not recipe facts. Never derive nutrition or density values from them during `gram db enrich`.
- Several quantities are deliberately vague: `1 pot de sauce tomate`, `fromage râpé` without weight, feuilles de lasagne without count, herbs without measures. Keep them unquantified (`@fromage râpé{}`) or record the unit as given (`@sauce tomate{1 pot}`); never invent a weight or count.
- Confirm the author against the Schema.org `Recipe` JSON-LD metadata. Marmiton labels unnamed contributors `Anonyme`; keep that label instead of inventing a name.
- Default portions are usually 4, matching the interactive `- +` personnes selector on the page. Use them when the JSON-LD `recipeYield` is missing or ambiguous.
- User ratings and comments can surface practical doneness or salting issues (e.g. « trop salé si on ne rince pas les aubergines »). Mention them only as a quality cue in the final response; prefer the method body's quantities and doneness cues for the recipe itself.

### Thermomix and Cookomix-style instructions

When importing from Cookomix or adapting a Thermomix recipe:

1. **Avoid micro-step fragmentation** : Cookomix often generates 25-35 atomic lines (e.g. "Ajouter couvercle", "Mettre gobelet", "Transvaser"). Regroup these into **6 to 10 logical culinary phases**, placing micro-actions as checklist sub-steps (`- `).
2. **Declare appliance metadata** :
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
   `source_appliances` records only the models explicitly supported by the
   source. Add another model to `appliances` only after a documented adaptation
   or a human test. List every indispensable device or accessory in
   `required_equipment` so the recipe page warns the cook before starting.
3. **Write Thermomix parameters with standard vocabulary** :
   - **Durée** : annotate with `~{10 s}`, `~{4 min}`, `~{16 min}`.
   - **Température** : annotate with `^{100 C}`, `^{120 C}`, `^{95 C}` or mention `Varoma`.
   - **Sens inverse** : explicitly state `sens inverse` or `rotation inverse` when blades must not cut.
   - **Vitesse** : use `vitesse cuillère` (or `vitesse mijotage`), `vitesse 1` to `10`, `turbo`, or `mode pétrin` / `épi`.
   - **Accessoires** : annotate with `#bol Thermomix{}`, `#gobelet doseur{}`, `#panier cuisson{}`, `#Varoma{}`, `#fouet papillon{}`, `#spatule{}`.
4. **Automatic Cookomix-style visual badges** :
   CookGram automatically extracts these parameters and generates Cookomix-style parameter badges with dedicated SVG icons:
   - ⏱ **Durée** (chronomètre)
   - 🌡 **Température** (thermomètre ou Varoma)
   - 🔄 **Sens inverse** (flèche circulaire antihoraire, comme `icon-rotate_cw_2` de Cookomix)
   - 🥄 **Vitesse cuillère** (icône cuillère de mijotage, comme `icon-step_spoon` de Cookomix)
   - 🔪 **Vitesse lames** (icône lames de couteaux 4 branches, comme `icon-lames` de Cookomix)

When a person has actually cooked a version on a model not declared by the
source, record that evidence instead of rewriting history:

```yaml
appliance_validation:
  TM31:
    status: human-tested
    portions: 6
    note: Version 6 portions testée par le propriétaire du projet sur un TM31.
```

Never infer `human-tested`. The user must explicitly report the test, and the
validated yield must match what they tested. Keep source support in
`source_appliances` and the combined usable models in `appliances`.

Choose a lowercase kebab-case filename. Do not overwrite a similarly named recipe until its identity and intended replacement are clear.

## Update the ingredient database

Updating `.gram/ingredients.yaml` is part of the recipe import, not an optional cleanup. After drafting the recipe:

1. run `gram db sync` when the CLI is available so every new ingredient receives an entry;
2. inspect the diff and merge accidental duplicates into one canonical entry with aliases;
3. ensure every ingredient used by the new recipe resolves through a key, `name`, or alias;
4. add a defensible `category` when obvious;
5. leave `physical` and `nutrition` absent until their values are verified or accepted by a human during `gram db enrich`.

When the CLI is unavailable, add the missing minimal entries manually. A valid minimal entry contains `name`; aliases and category are optional. Never postpone missing database entries to an unspecified later task.

For physical or nutritional values, also read `.gram/ingredient-provenance.yaml`. Prefer CIQUAL/ANSES for generic foods used in France. Use Open Food Facts only for an identified branded product and treat its community data as an estimate. Every populated estimate must have a source entry and one of these statuses:

- `estimated`: sourced approximation not reviewed by a human;
- `verified`: value checked by a human against the cited source;
- `manual`: value deliberately chosen by a human;
- `incomplete`: no usable value yet.

`locked: true` means a human owns the values in `.gram/ingredients.yaml`. Never overwrite or “improve” a locked entry automatically. A human may set any Gram-valid value directly in `ingredients.yaml`, then record `status: manual`, `locked: true`, and an explanatory note in the provenance file. The provenance sidecar is project metadata; Gram continues to consume only `ingredients.yaml`.

## Decide whether portions can scale

Every imported recipe must declare a `scaling` block. Use `enabled: true` only when multiplying ingredient quantities is meaningful, and define `min_portions`, `max_portions`, `step`, and a note explaining which timings do not scale. Use `enabled: false` with a concrete `reason` when vessel capacity, appliance programs, emulsion ratios, fermentation geometry, or another precision constraint makes automatic scaling unsafe or misleading.

Do not assume every Thermomix recipe is fixed, but treat bowl capacity, minimum mixing volume, blade coverage, heating behavior, and model-specific guided programs as reasons to assess it carefully. When unsure, mark the recipe fixed instead of presenting unverified scaled quantities.

## Validate

1. **Validation atomique rapide (< 2 s)** :
```bash
python -m generator.recipe_check recipes/<slug>.gram
```

2. **Validation globale avant soumission de PR** :
```bash
python -m pytest tests/test_schema.py tests/test_gram.py tests/test_ingredients_database.py tests/test_variants.py
python -m generator.build
```

If the official CLI is available, also run:

```bash
gram db sync
gram db lint
gram db validate --strict
gram check recipes/<slug>.gram --skip-db
```

Review changes made by `gram db sync` and keep `.gram/ingredients.yaml` in the same commit as the new recipe. `gram db lint` may require the configured AI provider; when it is unavailable, report that the semantic deduplication step was skipped rather than faking its result. Do not accept nutrition or density estimates without human review.

Fix parser or build errors before handing off. Inspect the generated recipe page and `recipes.json` when the change uses a new syntax construct. Do not commit or push unless the user's request authorizes repository changes.
