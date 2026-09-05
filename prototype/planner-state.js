/**
 * Pure Meal Planner operations.
 *
 * This is intentionally not a Meal Composition model and does not aggregate
 * ingredients. It stores only a reference to a recipe and the household
 * serving count needed by a future Shopping Planner adapter.
 */

export const MEAL_PERIODS = ["lunch", "dinner"];

export function recipeMeal(recipeId, portions = 2, icon = "🍳") {
  return { type: "recipe", recipeId, portions: normalizePortions(portions), icon };
}

export function normalizePortions(value, fallback = 2) {
  const portions = Number(value);
  return Number.isInteger(portions) && portions > 0 ? portions : fallback;
}

export function setMeal(weekPlan, dayIndex, period, meal) {
  assertSlot(weekPlan, dayIndex, period);
  weekPlan[dayIndex][period] = meal;
}

export function removeMeal(weekPlan, dayIndex, period) {
  setMeal(weekPlan, dayIndex, period, null);
}

export function moveMeal(weekPlan, fromDayIndex, fromPeriod, toDayIndex, toPeriod) {
  assertSlot(weekPlan, fromDayIndex, fromPeriod);
  assertSlot(weekPlan, toDayIndex, toPeriod);
  if (fromDayIndex === toDayIndex && fromPeriod === toPeriod) return;
  const source = weekPlan[fromDayIndex][fromPeriod];
  weekPlan[fromDayIndex][fromPeriod] = weekPlan[toDayIndex][toPeriod];
  weekPlan[toDayIndex][toPeriod] = source;
}

/** Stable boundary for a future Shopping Planner; no ingredient aggregation. */
export function toShoppingPlannerInput(weekPlan) {
  return weekPlan.flatMap((day, dayIndex) => MEAL_PERIODS.map(period => {
    const meal = day[period];
    return {
      dayIndex,
      date: day.dateStr ?? null,
      period,
      recipeId: meal?.type === "recipe" ? meal.recipeId : null,
      portions: meal?.type === "recipe" ? normalizePortions(meal.portions) : null,
      type: meal?.type ?? "empty"
    };
  }));
}

function assertSlot(weekPlan, dayIndex, period) {
  if (!weekPlan[dayIndex] || !MEAL_PERIODS.includes(period)) {
    throw new RangeError(`Créneau Meal Planner invalide: ${dayIndex}/${period}`);
  }
}
