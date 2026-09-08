import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class PlannerThumbnailContractTests(unittest.TestCase):
    def test_planner_enriches_selection_from_catalog_without_changing_state(self):
        source = (ROOT / "static/meal-planner/planner-app.js").read_text(encoding="utf-8")
        self.assertIn('fetch("../recipes.json")', source)
        self.assertIn("let catalog = new Map()", source)
        self.assertIn("const recipeFor = item => catalog.get(item.slug) || item", source)
        self.assertIn('class="planner-recipe-thumb"', source)
        self.assertIn('draggable="true"', source)
        self.assertIn('import { buildCalendarExport } from "./calendar-export.js"', source)

    def test_thumbnail_cards_remain_accessible_and_responsive(self):
        source = (ROOT / "static/meal-planner/style.css").read_text(encoding="utf-8")
        self.assertIn("cursor: grab", source)
        self.assertIn("cursor: grabbing", source)
        self.assertIn(".planner-recipe:hover", source)
        self.assertIn("@media (max-width: 760px)", source)
        self.assertIn(".planner-recipe-placed .planner-recipe-thumb", source)


if __name__ == "__main__":
    unittest.main()
