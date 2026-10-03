export const NUTRITION_PROFILES = ["vitality", "balanced", "pleasure"];

export function summarizeNutritionProfiles(weekPlan, recipes) {
  const counts = Object.fromEntries(NUTRITION_PROFILES.map(profile => [profile, 0]));

  for (const day of weekPlan) {
    for (const slot of [day.lunch, day.dinner]) {
      if (slot?.type !== "recipe") continue;
      const profile = recipes[slot.recipeId]?.profile;
      if (Object.hasOwn(counts, profile)) counts[profile] += 1;
    }
  }

  const total = Object.values(counts).reduce((sum, count) => sum + count, 0);
  const percentages = Object.fromEntries(NUTRITION_PROFILES.map(profile => [
    profile,
    total === 0 ? 0 : Math.round((counts[profile] / total) * 100)
  ]));

  return { counts, percentages, total };
}
