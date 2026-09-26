/**
 * Weekly nutrition-profile compass (CookiGram/cookigram#509, parent
 * CookiGram/cookigram-core#373 §7). Counts only planned meals that HAVE a
 * profile; `balanced` stays a distinct category; null/exempt profiles are
 * never invented; zero classified meals shows counts only (no percentage,
 * no division by zero); display is a compass, never a score.
 */
export const NUTRITION_PROFILE_VALUES = Object.freeze(["vitality", "balanced", "pleasure"]);

export const NUTRITION_PROFILE_LABELS = Object.freeze({
  vitality: "Vitalité",
  balanced: "Équilibré",
  pleasure: "Plaisir",
});

export const isNutritionProfile = value => NUTRITION_PROFILE_VALUES.includes(value);

export const profileFor = recipe => (isNutritionProfile(recipe?.nutrition_profile) ? recipe.nutrition_profile : null);

/** Aggregate planned meal items. `expected` = weekly denominator (0 = unknown). */
export const summarizeWeekProfiles = (items, recipeFor, expected = 0) => {
  const counts = { vitality: 0, balanced: 0, pleasure: 0 };
  let classified = 0;
  for (const item of items) {
    const profile = profileFor(recipeFor(item));
    if (profile) {
      counts[profile] += 1;
      classified += 1;
    }
  }
  const pleasureShare = classified > 0 ? counts.pleasure / classified : null;
  return { ...counts, classified, planned: items.length, expected, pleasureShare };
};

/** Descriptive wording only: `22 % plaisir` (+ repère, never a goal). */
export const formatPleasureShare = share => {
  if (share === null || share === undefined || !Number.isFinite(share)) return "";
  return `${Math.round(share * 100)} % plaisir`;
};

export const formatWeekCoverage = (planned, expected) => {
  if (!Number.isFinite(expected) || expected <= 0) return `${planned} repas planifiés`;
  return `${planned} repas planifiés sur ${expected}`;
};

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
