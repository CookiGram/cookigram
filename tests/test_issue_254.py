import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class Issue254PlannerDirectGestureTests(unittest.TestCase):
    def test_planner_uses_direct_recipe_and_slot_controls(self):
        source = (ROOT / "static/meal-planner/planner-app.js").read_text(encoding="utf-8")
        self.assertIn("data-select-planner", source)
        self.assertIn("data-unplan=", source)
        self.assertNotIn("data-unplan-card", source)
        self.assertIn("planner-slot-ready", source)
        self.assertIn("selectedSlug", source)
        self.assertNotIn("data-slot-add", source)
        self.assertNotIn("data-assign", source)
        # #308 supersedes the original #254 rule forbidding removal from À placer.
        self.assertIn("data-remove-selection", source)
        self.assertNotIn("openSlotDialog", source)

    def test_drag_and_click_paths_are_kept_separate(self):
        source = (ROOT / "static/meal-planner/planner-app.js").read_text(encoding="utf-8")
        self.assertIn("dragstart", source)
        self.assertIn("dragend", source)
        self.assertIn("ignoreClickSlug", source)
        self.assertIn('event.dataTransfer.effectAllowed = "move"', source)
        self.assertIn("activateSlot", source)

    def test_unplaced_removal_is_isolated_from_placement(self):
        source = (ROOT / "static/meal-planner/planner-app.js").read_text(encoding="utf-8")
        self.assertIn("removeFromSelection", source)
        self.assertIn('new CustomEvent("cookigram:selection-change")', source)
        self.assertIn("event.stopPropagation()", source)
        self.assertIn("if (event.target !== card) return;", source)
        self.assertIn('aria-label="Retirer ${esc(title)} de Ma sélection"', source)

    def test_planner_markup_removes_intermediary_controls(self):
        source = (ROOT / "static/meal-planner/index.html").read_text(encoding="utf-8")
        self.assertIn('id="planner-all-placed"', source)
        self.assertIn('class="sr-only"', source)
        self.assertIn('href="./direct-planner.css"', source)
        self.assertNotIn("planner-slot-dialog", source)
        self.assertNotIn("data-remove-unplanned", source)

    def test_planner_visible_copy_stays_minimal(self):
        markup = (ROOT / "static/meal-planner/index.html").read_text(encoding="utf-8")
        app = (ROOT / "static/meal-planner/planner-app.js").read_text(encoding="utf-8")
        self.assertNotIn("Répartissez les recettes", markup)
        self.assertNotIn("Glissez pour placer", markup)
        self.assertNotIn("Exporte une photo", markup)
        self.assertNotIn("← Ma sélection", markup)
        self.assertNotIn("Cette semaine ·", app)
        self.assertNotIn(">Déposer ici<", app)
        self.assertNotIn(">Placer ici<", app)
        self.assertIn('aria-label="Exporter cette semaine"', markup)
        self.assertIn("À placer", markup)

    def test_direct_planner_styles_make_thumbnail_primary(self):
        source = (ROOT / "static/meal-planner/direct-planner.css").read_text(encoding="utf-8")
        self.assertIn(".planner-recipe-placed .planner-recipe-thumb", source)
        self.assertIn(".planner-recipe-overlay", source)
        self.assertIn(".planner-board-shell.planner-board-shell-full", source)
        self.assertIn(".planner-selection-remove", source)
        self.assertIn("grid-template-columns: 64px minmax(0, 1fr) 44px", source)
        self.assertIn('@media (max-width: 760px)', source)


if __name__ == "__main__":
    unittest.main()
