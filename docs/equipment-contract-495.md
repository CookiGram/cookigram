# Equipment contract v2 — issue #495 (Lane B)

Scope: https://github.com/CookiGram/cookigram/issues/495 — contract/model lane.
Read-only audit this contract implements: `docs/equipment-audit-495.md` (Lane A).
Product-owner decision applied here: the pressure-cooker family is
**hierarchical** — one canonical key `pressure_cooker` with capability/model
values `[standard | instant_pot | cookeo]`. The flat alternative (three
independent keys) is rejected, see §4.

This contract was extended by issue [#520](https://github.com/CookiGram/cookigram/issues/520):
`barbecue` and `plancha` are now canonical families, barbecue and sous-vide
have explicit capability matching, and fuels use the independent
`fuel_requirements` metadata described in §11.

Lane B edits **no recipes and no prototype files** — contract + tests + docs
only. Recipe migration belongs to its own lane; prototype profile/filter
integration belongs to Lane C.

## 1. Canonical key set (12 A+B+#520 families + kept legacy keys)

All keys are `snake_case`, matching the existing convention
(`pizza_oven`, `rice_cooker`, `sous_vide`).

| # | Canonical key | Wave | UI label (generic French, no brands) | Values |
|---|---|---|---|---|
| 1 | `air_fryer` | A | Air Fryer | `[standard]` |
| 2 | `stand_mixer` | A | Robot pâtissier | `[standard]` |
| 3 | `rice_cooker` | A | Rice cooker | `[standard]` |
| 4 | `pizza_oven` | A | Four à pizza | generic `standard` + preserved brand models (see §2) |
| 5 | `pressure_cooker` | A | Autocuiseur / Multicuiseur | `[standard \| instant_pot \| cookeo]`, combinable (see §4) |
| 6 | `four` (alias `oven`, see §5) | A (align) | Four | `[standard, chaleur-tournante, convection]` (preserved) |
| 7 | `blender` | B | Blender | `[standard]` |
| 8 | `immersion_blender` | B | Mixeur plongeant | `[standard]` |
| 9 | `food_processor` | B | Robot multifonction | `[standard]` |
| 10 | `microwave` | B | Micro-ondes | `[standard]` |
| 11 | `slow_cooker` | B | Mijoteuse | `[standard]` |
| 12 | `barbecue` | #520 | Barbecue | `[charcoal_kettle \| gas_grill]` |
| 13 | `plancha` | #520 | Plancha | `[standard]` |

Kept legacy keys (unchanged, still valid): `thermomix`, `sous_vide`,
`stovetop`. `thermomix` keeps its TM model list. `sous_vide` keeps
`anova_precision_cooker` and adds `standard` for a non-branded generic device
(see §2 and §12).

Note on counting: waves A+B name 10 families; #520 adds two more. `four`/`oven`
alignment normalizes an existing key (§5), while `thermomix`, `sous_vide`, and
`stovetop` remain established families. The full closed vocabulary is §7.

## 2. Preserved variants (must not be lost)

- `pizza_oven`: brand models `ooni, koda, fyra, karu, roccbox, gozney`
  (all 20 `pizza-*.gram` files on `origin/main` declare the full list).
  A generic "Four à pizza" filter matches a recipe when `pizza_oven` is
  present with **any** value, including `standard`.
- `thermomix`: model list `TM31, TM5, TM6, TM7`, in both inline
  (`thermomix: [TM31, TM5, TM6, TM7]`) and block-list (`- TM5`) syntax.
- `four`: values `[standard, chaleur-tournante, convection]` (order-insensitive).
- `sous_vide`: device-model/capability values `standard` and
  `anova_precision_cooker`. A recipe requiring `[standard]` accepts any
  sous-vide capability. A profile declaring `[standard]` does not satisfy an
  explicitly Anova-specific recipe. A legacy profile value `true` migrates
  to `[generic]`, preserving the old family-wide match until the user chooses
  an explicit capability.
- `barbecue`: `charcoal_kettle` and `gas_grill` are distinct values under one
  family key. A requirement naming one value matches that value only; the
  family-only profile toggle means any barbecue. `plancha` is a separate
  family even when the physical gas grill also has a plancha surface.

## 3. `[standard]` default

Any appliance key with no meaningful model/capability distinction uses the
single value `[standard]`:

```yaml
appliances:
  air_fryer: [standard]
```

`standard` means "the generic device of this family". It is the default value
for `air_fryer`, `stand_mixer`, `rice_cooker`, `blender`,
`immersion_blender`, `food_processor`, `microwave`, `slow_cooker`, and for
`pizza_oven`/`pressure_cooker`/`four` when no model refinement applies.
`plancha` uses `[standard]`. Barbecue and sous-vide use their explicit
capabilities from §2.

## 3.1 BBQ and generic sous-vide capabilities (#520)

Canonical Gram examples:

```yaml
appliances:
  barbecue: [charcoal_kettle]
```

```yaml
appliances:
  barbecue: [gas_grill]
```

```yaml
appliances:
  plancha: [standard]
  sous_vide: [standard]
```

`barbecue` is one family with two distinct capabilities, not two appliances.
A charcoal kettle never satisfies a recipe requiring `gas_grill`, or vice
versa. A profile can own both. `plancha` matches independently from
`barbecue: [gas_grill]`; declare both when the recipe genuinely needs both
functions. No brand or kettle size is a canonical key or capability.

The profile's legacy `sous_vide: true` migrates to `[generic]` to preserve
historical compatibility with the existing Anova-valued corpus. New profiles
may declare `sous_vide: [standard]` for a generic circulator; it satisfies
generic `[standard]` recipes but not a requirement explicitly naming
`anova_precision_cooker`. An Anova capability satisfies generic `[standard]`
requirements as well as the matching Anova-specific requirement.

## 4. Pressure-cooker family (hierarchical — decided)

One canonical key, capability/model values:

```yaml
appliances:
  pressure_cooker: [instant_pot]   # Instant Pot
  pressure_cooker: [cookeo]        # Cookeo
  pressure_cooker: [standard]      # traditional stovetop autocuiseur
  pressure_cooker: [instant_pot, cookeo]  # accepts either
```

Matching rule: a user owning capability `c` satisfies a recipe requiring
`pressure_cooker: [...vs...]` iff `c ∈ vs`, **or** the user owns the generic
`pressure_cooker` capability and the recipe requires `[standard]`. A generic
"Autocuiseur / Multicuiseur" profile selector sets the family capability;
per-model opt-in (`instant_pot`, `cookeo`) is a secondary refinement owned by
Lane C. Owners of exactly one device must never be false-blocked on a recipe
that accepts their model.

Deterministic migration rules (for the migration lane, recorded here so the
mapping is unambiguous):

| Legacy declaration | Canonical form |
|---|---|
| `instant_pot:` block-list `- instant_pot_6qt` (7 recipes) | `pressure_cooker: [instant_pot]` |
| `cookeo: [Cookeo]` — brand-cased value (1 recipe: `sushi-cake-thon-mayonnaise-avocat`) | `pressure_cooker: [cookeo]` (lowercased) |

Normalization is case-insensitive on read (`Cookeo` → `cookeo`); canonical
stored values are lowercase. Rejected alternative: three flat independent keys
`pressure_cooker` / `instant_pot` / `cookeo` — it would force triple
declarations and false-block single-device owners, contradicting the product
principle (appliance = available capacity, not obligation).

## 5. `four` / `oven` alias rule

Recipes use `four` (21 files on `origin/main`); the prototype profile uses
`oven`. The canonical recipe key is **`four`**; **`oven` is a read alias**
for the same family:

- Parsers and filters must treat `oven` exactly as `four` (normalize `oven`
  → `four` on read).
- Writers (recipes, migrations) always emit `four`.
- Values are shared: `[standard, chaleur-tournante, convection]`.

## 6. Blender disjunction (either/or, no false block)

`barbacoa-boeuf-effiloche` and `oeuf-parfait-64c-creme-champignons` declare
"Mixeur plongeant ou blender" — an either/or offer. The contract expresses
this as a **disjunction**: a recipe listing both `blender` and
`immersion_blender` (each `[standard]`) is satisfied when the user owns
**either** device, never both. Filter logic must be OR across these two keys
for such recipes (in general: within one recipe, `blender` and
`immersion_blender` requirements combine with OR, not AND).

## 7. Retrocompatibility rule

- Every key present on `origin/main` keeps working unchanged:
  `thermomix`, `four`, `pizza_oven`, `instant_pot`, `sous_vide`,
  `rice_cooker`, `cookeo` (see `tests/test_equipment_model_495.py` corpus test).
  Legacy `instant_pot` / `cookeo` keys and the `oven` alias normalize to the
  canonical form on read (§4–§5); both syntaxes (inline `[...]` and block-list
  `- ...`) keep parsing.
- **Unknown keys fail closed with an explicit message**: a parser encountering
  an appliance key outside the closed vocabulary below must reject it with an
  error naming the key (e.g. `unknown appliance key: 'barbacue'`) instead of
  silently ignoring it. Silent ignore would hide typos (`airfryer`) and block
  future keys from being added deliberately via `docs/equipment-add-appliance.md`.
- Closed vocabulary (canonical + read aliases): `air_fryer`, `stand_mixer`,
  `rice_cooker`, `pizza_oven`, `pressure_cooker`, `four`, `oven` (alias),
  `blender`, `immersion_blender`, `food_processor`, `microwave`,
  `slow_cooker`, `barbecue`, `plancha`, `thermomix`, `sous_vide`, `stovetop`, plus migration-read
  aliases `instant_pot`, `cookeo` (normalized per §4; new content must emit
  `pressure_cooker`).

## 8. Utensils stay OUT

The following remain in `required_equipment` and must never become
`appliances:` keys (out-of-scope list from issue #495): casserole, faitout,
cocotte en fonte, poêle, sauteuse, wok, passoire, saladier, fouet, spatule,
mandoline, râpe, moules, plaques, pierre/pelle à pizza, balance, thermomètre,
couteaux, pizza stone/peel, searing grate, charcoal ring, heat diffuser,
charcoal dividers, and chimney starter. These functional accessories remain
descriptive entries in `required_equipment`, never `appliances` keys, and do
not block the equipment filter.

Deferred P2/P3 devices (not in this contract): deep fryer, bread maker, ice
cream maker, waffle maker, dehydrator,
yogurt maker, raclette/fondue/etc.

## 9. No brands in primary UI labels

Primary profile/filter labels are generic French (§1 table). Brands and model
names (`Ooni`, `Cookeo`, `Instant Pot`, `Anova`, `Thermomix` as a device brand)
appear only in secondary refinements, tooltips, or variant names — never as
the main family label. (`Thermomix` stays the family label for `thermomix`
because it is the established generic name for that robot-cooker family in the
catalogue; no new brand labels are introduced.)

## 10. Core shape constraint

`appliances` is a dict mapping each key to a **list of model strings**
(`generator/schema.py` §8, `generator/models.py`: open `dict` shape, no key
allowlist in `cookigram-core`). This contract introduces no core change: new
canonical keys validate as long as the shape holds. See
`docs/equipment-add-appliance.md` for the procedure to add a future appliance.

## 11. Fuel requirements (#520)

Fuels are recipe metadata, separate from both `ingredients` and `appliances`.
The optional field is a closed, deterministic mapping named
`fuel_requirements`; its keys are fuel classes and its values are lists of
canonical fuel types:

```yaml
fuel_requirements:
  charcoal: [briquettes]
  smoking_wood: [oak]
```

The initial vocabulary is `charcoal: [briquettes]` and `smoking_wood: [oak]`.
Add a value only for an explicit recipe need and matching support; do not put
charcoal or smoking wood in the food ingredient list or appliance map. The
pinned Core recipe uses a generic metadata dictionary and validates
`appliances` as key-to-list-of-strings, so the optional metadata field needs
no Core schema change. Consumers needing fuel matching must opt into this
contract explicitly; there is no fuel-profile filter in the current UI.

## 12. Accessory and fuel boundary (#520)

Examples for `required_equipment` are `anneau à charbon`, `diffuseur
thermique`, `séparateurs à charbon`, `cheminée d'allumage`, and `grille de
saisie en fonte`. Accessories are human-readable and non-blocking to equipment
filtering so a functional equivalent can be used. They are not combustibles;
fuel choices belong only in `fuel_requirements`.
