/** Small, deterministic nutrition projection for the weekly planner. */

const caloriesFor = recipe => {
  const calories = Number(recipe?.nutrition?.calories);
  return Number.isFinite(calories) && calories >= 0 ? calories : null;
};

/**
 * Return a daily estimate only when every planned recipe has a usable value.
 * Nutrition in recipes.json is expressed per portion; the planner currently
 * has no separate portion selector, so the detail states that scope explicitly.
 */
export const summarizeDayNutrition = (slots, recipeFor) => {
  const entries = slots.flatMap(({ moment, items }) => items.map(item => ({ moment, item, recipe: recipeFor(item) })));
  if (!entries.length) return null;
  const calories = entries.map(entry => caloriesFor(entry.recipe));
  if (calories.some(value => value === null)) return null;
  return {
    total: Math.round(calories.reduce((sum, value) => sum + value, 0)),
    entries: entries.map((entry, index) => ({
      moment: entry.moment,
      title: entry.recipe.title || entry.item.title || entry.item.slug,
      calories: Math.round(calories[index]),
    })),
  };
};
