import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class ShoppingUxContractTests(unittest.TestCase):
    def test_selection_page_uses_automatic_shopping_and_header_planner(self):
        html = (ROOT / "static/selection/index.html").read_text(encoding="utf-8")
        self.assertNotIn('data-open-shopping', html)
        self.assertIn('data-selection-shopping hidden', html)
        self.assertNotIn('Gardez ici les recettes que vous envisagez', html)
        self.assertNotIn('data-shopping-summary', html)
        self.assertIn('selection-planner-link', html)
        self.assertIn('class="shopping-action shopping-action--copy"', html)
        self.assertNotIn('class="btn secondary" data-copy-shopping', html)

    def test_shopping_action_bar_uses_cookigram_svg_icons_not_raw_glyphs(self):
        html = (ROOT / "static/selection/index.html").read_text(encoding="utf-8")
        for action in ('shopping-action--copy', 'shopping-action--share', 'shopping-action--export'):
            self.assertIn(action, html)
        self.assertIn('shopping-action-icon--planner', html)
        self.assertGreaterEqual(html.count('<svg class="shopping-action-icon'), 4)
        self.assertNotIn('>⧉</button>', html)
        self.assertNotIn('>↗</button>', html)
        self.assertNotIn('>↓</button>', html)
        self.assertNotIn('hidden>→</a>', html)

    def test_shopping_groups_before_render_and_exports_only_items_to_buy(self):
        source = (ROOT / "static/selection/selection-app.js").read_text(encoding="utf-8")
        self.assertIn('shoppingSection.hidden = getRecipeSelection().length === 0', source)
        self.assertIn('const shoppingItemsToBuy = () =>', source)
        self.assertIn('group.items.map(item =>', source)
        self.assertIn('}).join("")}</ul></section>`).join("")', source)
        self.assertIn('data-shopping-item', source)
        self.assertIn('const itemKey = item =>', source)
        self.assertIn('const isShoppingChecked = (item, state) =>', source)
        self.assertIn('${checked ? "checked" : ""}', source)
        self.assertIn('next[cb.dataset.shoppingItem] = cb.checked', source)
        self.assertIn('recipeShoppingChoice', source)
        self.assertIn('filter(item => recipeShoppingChoice(recipe, item))', source)
        self.assertIn('cookigram:${recipe.slug}:main:checked', source)
        self.assertIn('normalizeIngredientName', source)
        self.assertIn('plannerLink.hidden = items.length === 0', source)
        self.assertNotIn('shopping-review-icon', source)
        self.assertIn('shopping-item-copy', source)

    def test_selection_rows_no_longer_expose_reorder_or_text_remove_controls(self):
        source = (ROOT / "static/selection/selection-app.js").read_text(encoding="utf-8")
        self.assertNotIn('data-move=', source)
        self.assertNotIn('selection-reorder', source)
        self.assertNotIn('>Retirer</button>', source)
        self.assertIn('title="Retirer de Ma sélection">×</button>', source)

    def test_selection_css_uses_light_checkboxes_flat_groups_and_illustrated_actions(self):
        css = (ROOT / "static/selection/style.css").read_text(encoding="utf-8")
        self.assertIn('appearance:none', css)
        self.assertIn('.shopping-item input:checked', css)
        self.assertIn('text-decoration:line-through', css)
        self.assertIn('.shopping-group{padding:0;background:transparent}', css)
        self.assertNotIn('.shopping-review-icon', css)
        self.assertIn('.shopping-action-icon', css)
        self.assertIn('.icon-accent', css)
        self.assertIn('.icon-planner-arrow', css)


if __name__ == "__main__":
    unittest.main()
