# Equipment audit — issue #495 (Lane A, read-only)

Scope: https://github.com/CookiGram/cookigram/issues/495 — audit/catalogue lane only.
No recipe, prototype, test, or contract file was modified for this audit.
Corpus: 222 `recipes/*.gram` files at base `3da24d4` (+ isolated branch, no parent changes).

## 1. Exhaustive inventory of `appliances:` keys

122 of 222 recipe files declare an `appliances:` frontmatter block. 100 do not.

| Key | Recipes | Values observed |
|---|---|---|
| `thermomix` | 86 | `[TM31]` (2), `[TM31, TM5, TM6, TM7]` (52), `[TM31, TM5, TM6]` (1), `[TM7]` (1), block-list form `- TM5/- TM6/- TM7` (~30) |
| `four` | 21 | `[standard, chaleur-tournante, convection]` (20), `[standard, convection, chaleur-tournante]` (1) |
| `pizza_oven` | 20 | `[ooni, koda, fyra, karu, roccbox, gozney]` (all 20, always paired with `four`) |
| `instant_pot` | 7 | block-list `- instant_pot_6qt` (all 7): barbacoa-boeuf-effiloche, bo-kho-boeuf-vietnamien, lu-rou-fan-porc-taiwanais, one-pot-pasta-soupe-oignon, plat-de-cote-boeuf-instant-pot, riz-cajun-saucisse-fumee, seafood-boil-louisiane |
| `sous_vide` | 6 | block-list `- anova_precision_cooker` (all 6): faux-filet-boeuf-sous-vide, magret-canard-sous-vide, oeuf-parfait-64c-creme-champignons, saumon-confit-sous-vide, souris-agneau-confite-sous-vide, supreme-poulet-estragon-sous-vide |
| `rice_cooker` | 1 | `[standard]`: riz-rice-cooker |
| `cookeo` | 1 | `[Cookeo]` (brand-cased value): sushi-cake-thon-mayonnaise-avocat |

Keys **never** used in `appliances:` (verified by full-corpus scan):
`stovetop`, `oven`, `pressure_cooker`, `air_fryer`, `stand_mixer`,
`blender`, `immersion_blender`, `food_processor`, `microwave`, `slow_cooker`.
(The 4 `oven` text hits are a source URL, a variant id, and step ids — not keys.)

## 2. Equipment present only outside `appliances:`

### 2a. `required_equipment` only (appliance-class candidates)
- **Air Fryer**: nothing in `required_equipment`. All 15 `air-fryer-*.gram`
  files carry the device only via the `#panier air fryer{}` step reference
  (e.g. air-fryer-colin-pane-herbes: "cuire dans le #panier air fryer{} à
  ^{200 C} ~{12 min}") — and none of the 15 declares `appliances:` or
  `required_equipment:` at all.
- **Rice cooker**: `riz-rice-cooker` declares `rice_cooker: [standard]` and
  mentions "Rice cooker" in equipment; `sushi-cake-saumon-aburi` lists
  "Cuiseur à riz ou casserole" (alternative, not exclusive — see §5);
  `riz-thermomix-mode-rice-cooker` mentions "Rice cooker" only as a cooking
  *mode* of the Thermomix, appliance stays `thermomix`.
- **Pressure-cooker family**: `required_equipment` strings vary per recipe —
  "Autocuiseur Instant Pot (ou Cookeo) ou Cocotte en fonte" (×4),
  "…ou Sauteuse" (×1), "…(ou Faitout traditionnel)" (×1, seafood-boil),
  plus "Moulinex Cookeo" brand mentions in step bodies (7 files).
  `carbonnade-flamande` and `osso-buco-milanaise` (both `thermomix` recipes)
  additionally expose `instant-pot` / `cocotte-fonte` cooking **variants**
  with their own `appliances:` sub-declarations — alternatives, not the
  recipe's primary appliance.
- **Blender / mixeur plongeant**: "Mixeur plongeant ou blender" in
  `required_equipment` of `barbacoa-boeuf-effiloche` and
  `oeuf-parfait-64c-creme-champignons` (either/or formulation);
  `sauce-green-goddess` references "le petit bol du mixeur" in notes only.
  No `blender` vs `immersion_blender` distinction exists anywhere yet.
- **Micro-ondes**: exactly one hit — `sushi-cake-saumon-thon-concombre-oeuf`
  lists "Four à micro-ondes" in `required_equipment`, and its timing note
  says the source only publishes "2 min de micro-ondes" (editorial estimate).
- **Batteur électrique** (stand-mixer-adjacent): one hit —
  `foret-noire-cyril-lignac`. No `stand_mixer` key exists.
- **Chalumeau de cuisine**: `sushi-cake-saumon-aburi`, `creme-brulee-vanille-sous-vide`
  (P3-class, out of scope per issue, listed here for completeness).

### 2b. Instructions / tags only
- Tag `air-fryer` on all 15 `air-fryer-*.gram` files (no corresponding key).
- Tag `instant pot` on the 7 `instant_pot` recipes (consistent with key).
- "mode pétrin" in `brioche-butchy`, `fougasse-au-levain` (+ 8 more bakery
  files): always the **Thermomix kneading mode** — every one of these files
  already declares `appliances: thermomix`. This is NOT evidence for
  `stand_mixer` migration; it only justifies introducing the `stand_mixer`
  contract for future dough/bread bases.
- "Cookeo" in step text of the 7 `instant_pot` files (used generically for
  the multicooker sauté/pressure steps).

### 2c. Deliberately out of scope (stay in `required_equipment`)
Verified still utensils, not appliances: Couteau de chef (63), Planche à
découper (62), Spatule (49), Pierre réfractaire / Pelle à pizza (20+20, pizza
stones stay utensils alongside the `pizza_oven` appliance), Varoma / Panier
cuisson (Thermomix accessories), Casserole/Poêle/Sauteuse/Wok family,
Passoire, Saladier, Fouet, Rouleau à pâtisserie, Moules/Plaques, Balance
(equivalent), Râpe, Film alimentaire. No `.gram` file promotes any of these
to an `appliances:` key.

## 3. Profile-vs-recipes divergences (`prototype/app.js`, `prototype/index.html`)

The prototype profile (`EQUIPMENT_LABELS`, `state.userEquipment`, chips) knows
exactly 5 ids: `stovetop`, `oven`, `thermomix`, `sous_vide`, `pressure_cooker`.

| # | Divergence |
|---|---|
| D1 | Recipes use **`four`**, profile uses **`oven`**. The 21 `four` recipes can never match the profile filter. Highest-impact divergence. |
| D2 | Recipes use **`instant_pot`** (7) + **`cookeo`** (1); profile uses **`pressure_cooker`** (0 recipes). The whole pressure family is invisible to filtering. |
| D3 | **`stovetop`** is profile-locked (`stovetop: true`, locked chip) but appears in **zero** recipe `appliances:` blocks — it is dead weight in matching, correct only as a default-on assumption. |
| D4 | `pizza_oven` (20 recipes, brand-model values), `rice_cooker` (1), and all of wave B have **no profile chip at all** — yet these are the only keys with real filtering value to add. |
| D5 | Profile labels carry brands/generic mixes ("Thermomix", "Cocotte minute"); issue §3 requires generic French labels without brands. No wave-A/B label exists yet. |
| D6 | Value-level mismatch: `cookeo: [Cookeo]` is brand-cased; `instant_pot_6qt` is a size-specific model; Thermomix lists mix inline `[TM31, …]` and block-list `- TM5` styles. A v2 contract must normalize value syntax. |

## 4. Canonical mapping proposal (waves A+B)

Generic French labels without brands (per issue §3). Key naming follows the
existing snake_case convention (`pizza_oven`, `rice_cooker`, `sous_vide`).

| Canonical key | UI label | Values | Status |
|---|---|---|---|
| `air_fryer` | Air Fryer | `[standard]` | NEW — §5 migration (15 files) |
| `stand_mixer` | Robot pâtissier | `[standard]` | NEW — contract only, no current recipe justifies it (pétrin = Thermomix mode) |
| `rice_cooker` | Rice cooker | `[standard]` | EXISTS — expose in profile, keep `riz-rice-cooker` |
| `pizza_oven` | Four à pizza | generic `standard` + preserve brand models (`ooni, koda, fyra, karu, roccbox, gozney`) | EXISTS — generic filter must match any model value |
| `pressure_cooker` family | Autocuiseur / Multicuiseur | see decision below | NORMALIZE |
| `four` (+ alias `oven`) | Four | `[standard, chaleur-tournante, convection]` | RENAME-ALIGN — D1: pick one id, alias the other |
| `blender` | Blender | `[standard]` | NEW — §5 migration (2 files, disjunction) |
| `immersion_blender` | Mixeur plongeant | `[standard]` | NEW — §5 migration (same 2 files, disjunction) |
| `food_processor` | Robot multifonction | `[standard]` | NEW — contract only, zero corpus hits |
| `microwave` | Micro-ondes | `[standard]` | NEW — 1 candidate file, weak source (§5) |
| `slow_cooker` | Mijoteuse | `[standard]` | NEW — contract only, zero corpus hits |
| `thermomix`, `sous_vide`, `stovetop` | unchanged | unchanged | KEEP |

### Pressure-cooker family decision input (flat vs hierarchical)
- **Flat option**: three independent keys `pressure_cooker` / `instant_pot` / `cookeo`.
  Corpus reality: 7 files keyed `instant_pot`, 1 file keyed `cookeo`, 0 keyed
  `pressure_cooker`, while `required_equipment` strings treat them as
  interchangeable ("Autocuiseur Instant Pot (ou Cookeo) ou Cocotte en fonte").
  Flat keys would force every current and future recipe to triple-declare and
  would false-block users owning exactly one device — contradicting the
  product principle (appliance = available capacity, not obligation).
- **Hierarchical option** (recommended): one canonical family key
  `pressure_cooker` with capability/model values, e.g.
  `pressure_cooker: [instant_pot]` / `[cookeo]` / `[standard]` (traditional),
  combined values allowed (`[instant_pot, cookeo]`). Profile owns a single
  "Autocuiseur / Multicuiseur" selector; per-model opt-in is a secondary
  refinement. Deterministic migration: `instant_pot: [instant_pot_6qt]` →
  `pressure_cooker: [instant_pot]`; `cookeo: [Cookeo]` → `pressure_cooker: [cookeo]`.
- **Decision required from owner**: confirm hierarchical
  (`pressure_cooker:` + model values) before Lane B implements; flat is
  documented here only as the rejected alternative.

## 5. Per-recipe migration list (content-justified only)

No compatibility is inferred. "Alternative/offer" formulations are NOT migrated
(product principle: a traditional recipe must not become device-dependent
because a robot variant exists).

| Recipe(s) | Proposed change | Justification |
|---|---|---|
| 15× `air-fryer-*.gram` (ailes-poulet, boulettes-boeuf, chou-fleur, colin-pane-herbes, courgettes-panees, crevettes-ail, cuisses-poulet-miel-moutarde, falafels, frites-patate-douce, pommes-terre-romarin, poulet-paprika, quesadillas, saucisses-poivrons, saumon-citron, tofu-croustillant) | add `appliances: air_fryer: [standard]` | file name + `air-fryer` tag + `#panier air fryer{}` cooking step at stated Air Fryer temperature/time |
| `riz-rice-cooker` | keep `rice_cooker: [standard]`; expose key in profile | already canonical |
| 20× `pizza-*.gram` with `four` + `pizza_oven` | keep both keys and brand models; generic "Four à pizza" filter matches any `pizza_oven` value | already canonical at key level |
| 7× `instant_pot` recipes (see §1) | migrate to `pressure_cooker: [instant_pot]` (pending §4 decision) | key + `required_equipment` + source (e.g. instantpot.com) agree |
| `sushi-cake-thon-mayonnaise-avocat` | `cookeo: [Cookeo]` → `pressure_cooker: [cookeo]` (pending §4 decision; at minimum lowercase value) | Cookeo-cooked rice per content; current value is brand-cased |
| `barbacoa-boeuf-effiloche`, `oeuf-parfait-64c-creme-champignons` | add `blender` + `immersion_blende
...[truncated 2085 chars]