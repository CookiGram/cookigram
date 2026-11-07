"""Regression gate for issue #634: never expose unqualified pressure cooking.

The pressure-cooker variant is intentionally withheld pending a model-specific
culinary and manufacturer-safety review. This does not qualify the remaining
recipe's culinary safety or change its other cooking instructions.
"""
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "recipes" / "osso-buco-milanaise.gram"


def frontmatter():
    source = RECIPE.read_text(encoding="utf-8")
    assert source.startswith("---\n"), "missing frontmatter"
    return yaml.safe_load(source.split("---\n", 2)[1]), source


class OssoBucoSafetyGateTests(unittest.TestCase):
    def test_unverified_instant_pot_variant_is_not_offered(self):
        metadata, source = frontmatter()
        ids = [variant["id"] for variant in metadata["variants"]]
        self.assertNotIn("instant-pot", ids)
        self.assertNotIn("Haute Pression Express", source)
        self.assertNotIn("Laisser retomber la pression ~{10 min} puis ouvrir la valve.", source)

    def test_unaffected_methods_remain_available(self):
        metadata, source = frontmatter()
        by_id = {variant["id"]: variant for variant in metadata["variants"]}
        self.assertEqual(set(by_id), {"thermomix", "cocotte-fonte"})
        self.assertTrue(by_id["thermomix"]["default"])
        self.assertEqual(by_id["thermomix"]["total_time"], "1 h 20 min")
        self.assertEqual(by_id["cocotte-fonte"]["total_time"], "2 h 20 min")
        self.assertIn("[simmer-veal | Braiser les rouelles de veau", source)
        self.assertIn("[simmer-veal | Braiser l'osso buco en cocotte]", source)

    def test_variant_step_boundaries_are_preserved(self):
        metadata, _ = frontmatter()
        cocotte = next(v for v in metadata["variants"] if v["id"] == "cocotte-fonte")
        self.assertEqual(
            set(cocotte["steps"]["replace"]),
            {"make-gremolata", "brown-soffritto", "simmer-veal"},
        )


if __name__ == "__main__":
    unittest.main()
