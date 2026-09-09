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
        self.assertIn('plannerLink.hidden = items.length === 0', source)
        self.assertIn('shopping-review-icon', source)


if __name__ == "__main__":
    unittest.main()
