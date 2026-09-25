# Adding a new appliance (equipment contract v2)

Parent issue: https://github.com/CookiGram/cookigram/issues/495.
Canonical contract: `docs/equipment-contract-495.md`.
Corpus audit: `docs/equipment-audit-495.md`.

## 1. Key naming

- `snake_case`, English, singular family noun: `air_fryer`, `stand_mixer`,
  `rice_cooker`, `pizza_oven`, `pressure_cooker`.
- One key per device **family**, not per brand or size. Brands, sizes, and
  model variants go in the **values** list (`pizza_oven: [ooni, koda, …]`,
  `pressure_cooker: [instant_pot, cookeo]`), never in the key.
- Utensils (casserole, poêle, fouet, spatule, … — full list in contract §8)
  must never become keys; they stay in `required_equipment`.

## 2. Values

- Default value is `[standard]` — the generic device of the family. Use it
  unless models genuinely change matching (pizza brand models, Thermomix TM
  list, `four` heat modes, pressure-cooker capabilities).
- Canonical stored values are lowercase; parsers normalize case on read
  (`Cookeo` → `cookeo`).
- If the new device is a model/capability of an existing family (a new
  multicooker brand, a new pizza-oven make), add a **value** to the existing
  key — do not create a key.

## 3. Label rule

- Primary UI label is generic French with **no brands**: Air Fryer, Robot
  pâtissier, Rice cooker, Four à pizza, Autocuiseur / Multicuiseur, Blender,
  Mixeur plongeant, Robot multifonction, Micro-ondes, Mijoteuse.
- Brands/models appear only in secondary refinements, tooltips, or variant
  names. Add the label to the `UI_LABELS` table in
  `tests/test_equipment_model_495.py` and to the contract §1 table.

## 4. Tests to extend

When adding a key (or a value with matching semantics), extend
`tests/test_equipment_model_495.py`:

1. parsing: the new key in inline and (if used) block-list syntax;
2. normalization/matching: any alias or value mapping, with the
   both-directions cases (match + block);
3. disjunction, if the device is an either/or alternative to another key
   (like `blender` / `immersion_blender` — OR, never AND);
4. the `UILabelTests` brand-token check automatically covers the new label —
   keep it green.

## 5. Core shape constraint

`cookigram-core` validates `appliances` as a dict of key → **list of model
strings** (`generator/schema.py` §8) with no key allowlist. New keys need no
core change as long as that shape holds. A core change is only needed if you
want new display groupings/labels in core surfaces — file it separately.
