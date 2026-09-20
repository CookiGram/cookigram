"""Non-regression tests for CookiGram/cookigram#384.

Intermediate cooking products (a broth, juice or preparation produced by an
earlier step and reused later) must be written as plain prose, never as
``@ingredient{}`` references: an ``@`` tag always creates an entry
ingredient, which then leaks into derived surfaces (shopping list,
nutrition breakdown, scaling, variants).
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
RECIPE = ROOT / "recipes/roti-de-porc-sauce-echalote.gram"
INGREDIENT_REF = re.compile(r"@([^@{}]+)\{([^}]*)\}")

# Intermediate-product vocabulary that must never appear as an @ingredient
# name in this recipe. Kept intentionally narrow: only the two certain
# cases of #384, so the test cannot produce false positives elsewhere.
FORBIDDEN_NAMES = {
    "bouillon de légumes réservé",
    "jus de cuisson sous vide",
}


class IntermediateProductsTests(unittest.TestCase):
    def test_no_intermediate_product_is_an_ingredient_reference(self):
        text = RECIPE.read_text(encoding="utf-8")
        names = {match.group(1).strip().casefold() for match in INGREDIENT_REF.finditer(text)}
        for forbidden in FORBIDDEN_NAMES:
            self.assertNotIn(forbidden, names, f"@{forbidden} must not be an ingredient reference")

    def test_reuse_is_plain_prose_with_culinary_quantities(self):
        text = RECIPE.read_text(encoding="utf-8")
        self.assertIn("300 g du bouillon de cuisson réservé", text)
        self.assertIn("tout le jus de cuisson récupéré", text)

    def test_entry_ingredients_stay_declared(self):
        text = RECIPE.read_text(encoding="utf-8")
        names = {match.group(1).strip().casefold() for match in INGREDIENT_REF.finditer(text)}
        for entry in ("eau", "bouillon de légumes", "vin blanc", "maïzena", "échalotes"):
            self.assertIn(entry, names, f"@{entry} must remain an entry ingredient")


if __name__ == "__main__":
    unittest.main()
