import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class Issue247ContractTests(unittest.TestCase):
    def test_catalogue_has_the_shared_selection_entry_point(self):
        source = (ROOT / "static/selection/index.html").read_text(encoding="utf-8")
        self.assertIn('data-selection-shopping hidden', source)
        self.assertIn('href="../meal-planner/"', source)

    def test_placed_recipe_has_only_the_unplan_action(self):
        source = (ROOT / "static/meal-planner/planner-app.js").read_text(encoding="utf-8")
        start = source.index("const renderPlacedRecipe")
        end = source.index("const renderSlot", start)
        placed = source[start:end]
        self.assertIn("data-unplan", placed)
        self.assertIn("Remettre", placed)
        self.assertIn("dans À placer", placed)
        self.assertNotIn("data-remove-selection", placed)
        self.assertNotIn("planner-recipe-menu", placed)

    def test_planner_state_and_calendar_hooks_remain(self):
        source = (ROOT / "static/meal-planner/planner-app.js").read_text(encoding="utf-8")
        self.assertIn('import { addPlacement, loadPlanning, MOMENTS, removePlacement, savePlanning }', source)
        self.assertIn('import { buildCalendarExport }', source)
        self.assertIn('draggable="true"', source)


if __name__ == "__main__":
    unittest.main()
