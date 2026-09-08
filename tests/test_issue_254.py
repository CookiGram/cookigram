import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class Issue254PlannerDirectGestureTests(unittest.TestCase):
    def test_planner_uses_direct_recipe_and_slot_controls(self):
        source = (ROOT / "static/meal-planner/planner-app.js").read_text(encoding="utf-8")
        self.assertIn("data-select-planner", source)
        self.assertIn("data-unplan-card", source)
        self.assertIn("planner-slot-ready", source)
        self.assertIn("selectedSlug", source)
        self.assertNotIn("data-slot-add", source)
        self.assertNotIn("data-assign", source)
        self.assertNotIn("data-remove-selection", source)
        self.assertNotIn("openSlotDialog", source)

    def test_drag_and_click_paths_are_kept_separate(self):
        source = (ROOT / "static/meal-planner/planner-app.js").read_text(encoding="utf-8")
        self.assertIn("dragstart", source)
        self.assertIn("dragend", source)
        self.assertIn("ignoreClickSlug", source)
        self.assertIn('event.dataTransfer.effectAllowed = "move"', source)
        self.assertIn("activatePlaced", source)
        self.assertIn("activateSlot", source)

    def test_planner_markup_removes_intermediary_controls(self):
        source = (ROOT / "static/meal-planner/index.html").read_text(encoding="utf-8")
        self.assertIn('id="planner-all-placed"', source)
        self.assertIn('href="./direct-planner.css"', source)
        self.assertNotIn("planner-slot-dialog", source)
        self.assertNotIn("data-remove-unplanned", source)

    def test_direct_planner_styles_make_thumbnail_primary(self):
        source = (ROOT / "static/meal-planner/direct-planner.css").read_text(encoding="utf-8")
        self.assertIn(".planner-recipe-placed .planner-recipe-thumb", source)
        self.assertIn(".planner-recipe-overlay", source)
        self.assertIn(".planner-board-shell.planner-board-shell-full", source)
        self.assertIn('@media (max-width: 760px)', source)


if __name__ == "__main__":
    unittest.main()
