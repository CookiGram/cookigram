"""Contract tests for CookiGram/cookigram#495 (Lane B — contract/model).

Reference implementation of the canonical equipment contract v2 defined in
``docs/equipment-contract-495.md`` plus corpus tests pinning the
``origin/main`` recipe vocabulary. Lane B edits no recipes and no prototype
files: the contract lives here (tests) and in the docs.

Covers (per issue §5 + Lane B brief):
- parsing of new keys;
- retrocompat of all existing keys on the origin/main corpus;
- four/oven alias;
- pizza generic-vs-model matching;
- blender vs immersion_blender disjunction (either/or, no false block);
- pressure-cooker normalization incl. brand-cased Cookeo;
- standard-utensil recipes never blocked;
- no-brand UI-label rule (generic French labels).
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
RECIPES = ROOT / "recipes"

# --- Canonical contract (§1, §7 of docs/equipment-contract-495.md) ---

CANONICAL_KEYS = frozenset({
    "air_fryer",
    "stand_mixer",
    "rice_cooker",
    "pizza_oven",
    "pressure_cooker",
    "four",
    "blender",
    "immersion_blender",
    "food_processor",
    "microwave",
    "slow_cooker",
    "thermomix",
    "sous_vide",
    "stovetop",
})

# Read aliases: accepted on read, normalized to canonical (§4, §5, §7).
READ_ALIASES = {
    "oven": "four",
    "instant_pot": "pressure_cooker",
    "cookeo": "pressure_cooker",
}

KNOWN_KEYS = CANONICAL_KEYS | frozenset(READ_ALIASES)

# Generic French UI labels, no brands (§1, §9). `thermomix` keeps its
# established family name; no other label may carry a brand/model token.
UI_LABELS = {
    "air_fryer": "Air Fryer",
    "stand_mixer": "Robot pâtissier",
    "rice_cooker": "Rice cooker",
    "pizza_oven": "Four à pizza",
    "pressure_cooker": "Autocuiseur / Multicuiseur",
    "four": "Four",
    "blender": "Blender",
    "immersion_blender": "Mixeur plongeant",
    "food_processor": "Robot multifonction",
    "microwave": "Micro-ondes",
    "slow_cooker": "Mijoteuse",
    "thermomix": "Thermomix",
    "sous_vide": "Sous-vide",
    "stovetop": "Plaques & Poêles",
}

# Utensils that must never become appliance keys (issue out-of-scope list, §8).
UTENSILS_OUT = frozenset({
    "casserole", "faitout", "cocotte", "poele", "poêle", "sauteuse", "wok",
    "passoire", "saladier", "fouet", "spatule", "mandoline", "rape", "râpe",
    "moules", "plaques", "pierre", "pelle", "balance", "thermometre",
    "thermomètre", "couteaux",
})

# Expected origin/main corpus inventory (Lane A audit, re-verified here).
# thermomix re-pinned 63 -> 87 after the #492 wave (24 new TM31 hits,
# verified one by one against the merged corpus; all other counts unchanged).
EXPECTED_KEY_COUNTS = {
    "thermomix": 87,
    "four": 21,
    "pizza_oven": 20,
    "instant_pot": 7,
    "sous_vide": 6,
    "rice_cooker": 1,
    "cookeo": 1,
}

BRAND_TOKENS = (
    "ooni", "koda", "fyra", "karu", "roccbox", "gozney", "cookeo",
    "instant pot", "instant_pot", "anova", "moulinex", "magimix",
)


# --- Minimal reference implementation of the contract ---

def parse_appliances_block(text):
    """Parse every top-level ``appliances:`` dict in a .gram source.

    Returns a list of dicts ``{key: [values]}`` supporting both inline
    (``key: [a, b]``) and block-list (``key:\\n  - a``) syntax.
    """
    blocks = []
    for match in re.finditer(r"^appliances:\s*\n((?:^[ \t]+\S.*\n?)+)", text, re.M):
        parsed = {}
        current = None
        for line in match.group(1).splitlines():
            keyed = re.match(r"^\s{2}(\w+)\s*:\s*(.*)$", line)
            item = re.match(r"^\s+-\s+(\S.*)$", line)
            if keyed and not line.startswith("   ") and not line.startswith("\t "):
                # Two-space top-level key; deeper lines belong to variants.
                if len(line) - len(line.lstrip()) != 2:
                    break
                current = keyed.group(1)
                rest = keyed.group(2).strip()
                if rest.startswith("["):
                    parsed[current] = [v.strip() for v in rest.strip("[]").split(",") if v.strip()]
                    current = None
                else:
                    parsed[current] = []
            elif item and current is not None:
                parsed[current].append(item.group(1).strip())
            else:
                break
        blocks.append(parsed)
    return blocks


def normalize_appliances(raw):
    """Normalize a raw appliances dict to canonical keys/values.

    - ``oven`` -> ``four``; ``instant_pot``/``cookeo`` keys fold into
      ``pressure_cooker`` (merging values when both appear);
    - values are lowercased (``Cookeo`` -> ``cookeo``);
    - legacy ``instant_pot_6qt`` model maps to the ``instant_pot`` capability.
    Raises ``ValueError("unknown appliance key: ...")`` on unknown keys.
    """
    normalized = {}
    for key, values in raw.items():
        if key not in KNOWN_KEYS:
            raise ValueError(f"unknown appliance key: {key!r}")
        canonical = READ_ALIASES.get(key, key)
        mapped = []
        for value in values:
            lowered = value.strip().lower()
            if lowered == "instant_pot_6qt":
                lowered = "instant_pot"
            mapped.append(lowered)
        normalized.setdefault(canonical, [])
        for value in mapped:
            if value not in normalized[canonical]:
                normalized[canonical].append(value)
    return normalized


def is_satisfied(requirements, user):
    """Filter predicate: does ``user`` equipment satisfy ``requirements``?

    Both are canonical ``{key: [values]}`` dicts (requirements normalized via
    :func:`normalize_appliances`; user profile uses the same shape, where a
    generic family ownership is ``[standard]`` and multi-model ownership
    lists each capability, e.g. ``[instant_pot, cookeo]``).

    - ``blender`` + ``immersion_blender`` combine with OR (either/or offer);
    - ``pizza_oven``: any owned value satisfies any required value;
    - ``pressure_cooker``: intersection of owned/required capabilities;
    - every other key: ownership of the key (any value) satisfies ``[standard]``
      and exact-value requirements alike (single-value families).
    """
    req = dict(requirements)
    # Blender disjunction: owning either device satisfies a both-listed recipe.
    blend_keys = {"blender", "immersion_blender"} & set(req)
    if len(blend_keys) == 2:
        if "blender" in user or "immersion_blender" in user:
            req = {k: v for k, v in req.items() if k not in blend_keys}
        else:
            return False
    for key, values in req.items():
        if key not in user:
            return False
        if key == "pizza_oven":
            continue  # generic filter matches any model value
        if key == "pressure_cooker":
            if not set(user[key]) & set(values):
                return False
        # Other families: key ownership suffices (single-value `[standard]`
        # families and exact model lists such as thermomix TM variants, where
        # any owned model entry counts as family ownership in this contract).
    return True


def corpus_appliance_hits():
    """Yield ``(recipe_path, key, values)`` for every appliances entry."""
    for path in sorted(RECIPES.glob("*.gram")):
        for block in parse_appliances_block(path.read_text(encoding="utf-8")):
            for key, values in block.items():
                yield path, key, values


class ParsingTests(unittest.TestCase):
    def test_new_keys_parse_inline(self):
        blocks = parse_appliances_block("appliances:\n  air_fryer: [standard]\n")
        self.assertEqual(blocks, [{"air_fryer": ["standard"]}])
        for key in ("stand_mixer", "blender", "immersion_blender",
                    "food_processor", "microwave", "slow_cooker"):
            with self.subTest(key=key):
                self.assertEqual(
                    parse_appliances_block(f"appliances:\n  {key}: [standard]\n"),
                    [{key: ["standard"]}],
                )

    def test_new_keys_normalize_cleanly(self):
        raw = {"air_fryer": ["standard"], "blender": ["standard"],
               "immersion_blender": ["standard"], "slow_cooker": ["standard"]}
        self.assertEqual(normalize_appliances(raw), raw)

    def test_block_list_syntax_parses(self):
        text = "appliances:\n  thermomix:\n  - TM5\n  - TM6\n"
        self.assertEqual(
            parse_appliances_block(text), [{"thermomix": ["TM5", "TM6"]}]
        )

    def test_unknown_keys_fail_closed_with_explicit_message(self):
        with self.assertRaisesRegex(ValueError, "unknown appliance key: 'barbecue'"):
            normalize_appliances({"barbecue": ["standard"]})
        with self.assertRaisesRegex(ValueError, "unknown appliance key: 'airfryer'"):
            normalize_appliances({"airfryer": ["standard"]})


class RetrocompatTests(unittest.TestCase):
    def test_every_corpus_key_is_known(self):
        for path, key, _values in corpus_appliance_hits():
            self.assertIn(key, KNOWN_KEYS, f"{path.name}: {key}")

    def test_corpus_inventory_matches_audit(self):
        from collections import Counter
        counts = Counter()
        for _path, key, _values in corpus_appliance_hits():
            counts[key] += 1
        self.assertEqual(dict(counts), EXPECTED_KEY_COUNTS)

    def test_every_corpus_value_list_is_nonempty_strings(self):
        for path, key, values in corpus_appliance_hits():
            self.assertTrue(values, f"{path.name}: {key} has no values")
            for value in values:
                self.assertIsInstance(value, str)
                self.assertTrue(value.strip(), f"{path.name}: {key} has blank value")

    def test_existing_keys_keep_working_after_normalization(self):
        for path, key, values in corpus_appliance_hits():
            with self.subTest(recipe=path.name, key=key):
                normalized = normalize_appliances({key: values})
                self.assertTrue(normalized)  # nothing dropped, nothing rejected


class AliasTests(unittest.TestCase):
    def test_oven_is_a_read_alias_for_four(self):
        self.assertEqual(normalize_appliances({"oven": ["standard"]}),
                         {"four": ["standard"]})
        self.assertEqual(
            normalize_appliances({"oven": ["standard, chaleur-tournante"]}),
            normalize_appliances({"four": ["standard, chaleur-tournante"]}),
        )

    def test_four_values_preserved(self):
        normalized = normalize_appliances(
            {"four": ["standard", "chaleur-tournante", "convection"]})
        self.assertEqual(
            normalized, {"four": ["standard", "chaleur-tournante", "convection"]}
        )

    def test_oven_user_satisfies_four_recipe(self):
        recipe = normalize_appliances({"four": ["standard"]})
        self.assertTrue(is_satisfied(recipe, {"four": ["standard"]}))


class PizzaMatchingTests(unittest.TestCase):
    def test_generic_filter_matches_any_brand_model(self):
        recipe = normalize_appliances(
            {"pizza_oven": ["ooni", "koda", "fyra", "karu", "roccbox", "gozney"]})
        self.assertTrue(is_satisfied(recipe, {"pizza_oven": ["standard"]}))
        self.assertTrue(is_satisfied(recipe, {"pizza_oven": ["ooni"]}))

    def test_missing_pizza_oven_blocks(self):
        recipe = normalize_appliances({"pizza_oven": ["ooni"]})
        self.assertFalse(is_satisfied(recipe, {"four": ["standard"]}))

    def test_corpus_pizza_values_preserved(self):
        for path, key, values in corpus_appliance_hits():
            if key == "pizza_oven":
                self.assertEqual(
                    sorted(v.lower() for v in values),
                    ["fyra", "gozney", "karu", "koda", "ooni", "roccbox"],
                    path.name,
                )


class BlenderDisjunctionTests(unittest.TestCase):
    def test_either_device_satisfies_both_listed(self):
        recipe = normalize_appliances(
            {"blender": ["standard"], "immersion_blender": ["standard"]})
        self.assertTrue(is_satisfied(recipe, {"blender": ["standard"]}))
        self.assertTrue(is_satisfied(recipe, {"immersion_blender": ["standard"]}))

    def test_neither_device_blocks(self):
        recipe = normalize_appliances(
            {"blender": ["standard"], "immersion_blender": ["standard"]})
        self.assertFalse(is_satisfied(recipe, {"stovetop": ["standard"]}))

    def test_no_false_block_for_single_device_owner(self):
        # Single-device owners are the norm: each alone must pass.
        for owned in ({"blender": ["standard"]}, {"immersion_blender": ["standard"]}):
            with self.subTest(owned=owned):
                self.assertTrue(is_satisfied(
                    {"blender": ["standard"], "immersion_blender": ["standard"]},
                    owned,
                ))


class PressureCookerTests(unittest.TestCase):
    def test_size_model_maps_to_capability(self):
        self.assertEqual(normalize_appliances({"instant_pot": ["instant_pot_6qt"]}),
                         {"pressure_cooker": ["instant_pot"]})

    def test_brand_cased_cookeo_normalizes(self):
        self.assertEqual(normalize_appliances({"cookeo": ["Cookeo"]}),
                         {"pressure_cooker": ["cookeo"]})

    def test_exact_model_matching(self):
        self.assertTrue(is_satisfied({"pressure_cooker": ["instant_pot"]},
                                     {"pressure_cooker": ["instant_pot"]}))
        self.assertFalse(is_satisfied({"pressure_cooker": ["cookeo"]},
                                      {"pressure_cooker": ["instant_pot"]}))

    def test_either_or_list_does_not_false_block(self):
        recipe = {"pressure_cooker": ["instant_pot", "cookeo"]}
        self.assertTrue(is_satisfied(recipe, {"pressure_cooker": ["instant_pot"]}))
        self.assertTrue(is_satisfied(recipe, {"pressure_cooker": ["cookeo"]}))

    def test_traditional_standard_stays_distinct(self):
        self.assertTrue(is_satisfied({"pressure_cooker": ["standard"]},
                                     {"pressure_cooker": ["standard"]}))
        self.assertFalse(is_satisfied({"pressure_cooker": ["standard"]},
                                      {"pressure_cooker": ["instant_pot"]}))


class UtensilTests(unittest.TestCase):
    def test_no_utensil_is_an_appliance_key_in_corpus(self):
        for path, key, _values in corpus_appliance_hits():
            self.assertNotIn(key.lower(), UTENSILS_OUT, path.name)

    def test_standard_utensil_recipes_never_blocked(self):
        # A recipe with no appliances block (utensils only) is satisfied by
        # any equipment profile, including the bare default.
        bare = {"stovetop": ["standard"]}
        without_block = [
            p for p in sorted(RECIPES.glob("*.gram"))
            if not parse_appliances_block(p.read_text(encoding="utf-8"))
        ]
        self.assertTrue(without_block, "expected utensil-only recipes in corpus")
        for path in without_block:
            with self.subTest(recipe=path.name):
                self.assertTrue(is_satisfied({}, bare))


class UILabelTests(unittest.TestCase):
    def test_labels_cover_all_contract_families(self):
        for key in ("air_fryer", "stand_mixer", "rice_cooker", "pizza_oven",
                    "pressure_cooker", "four", "blender", "immersion_blender",
                    "food_processor", "microwave", "slow_cooker"):
            self.assertIn(key, UI_LABELS, key)

    def test_no_brands_in_primary_labels(self):
        for key, label in UI_LABELS.items():
            if key == "thermomix":
                continue  # established family name, documented in §9
            for token in BRAND_TOKENS:
                self.assertNotIn(token, label.lower(),
                                 f"label for {key} carries a brand: {label}")


if __name__ == "__main__":
    unittest.main()
