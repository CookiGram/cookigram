import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read_frontmatter(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").split("---", 2)
    return yaml.safe_load(lines[1]) or {}


class MealCompositionFixtureTests(unittest.TestCase):
    def test_canonical_vertical_slice(self) -> None:
        porc = read_frontmatter(ROOT / "recipes/porc-au-caramel.gram")
        rice = read_frontmatter(ROOT / "recipes/riz-blanc-long-casserole.gram")

        self.assertEqual(
            porc["meal"],
            {
                "completeness": "partial",
                "role": "main",
                "needs": ["starch"],
                "benefits_from": ["vegetable"],
            },
        )
        self.assertEqual(rice["meal"], {"completeness": "component", "role": "starch"})
        self.assertEqual(porc["portions"], rice["portions"])

    def test_public_fixture_contract_covers_unknown_and_complete(self) -> None:
        fixture = yaml.safe_load(
            (ROOT / "tests/fixtures/meal-composition-v1.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(fixture["unknown_recipe"].get("meal"), None)
        self.assertEqual(fixture["complete_recipe"]["meal"], {"completeness": "complete"})
        self.assertEqual(fixture["invalid"]["duplicate_needs"]["meal"]["needs"], ["starch", "starch"])


if __name__ == "__main__":
    unittest.main()
