import test from "node:test";
import assert from "node:assert/strict";
import { moveMeal, normalizePortions, recipeMeal, removeMeal, setMeal, toShoppingPlannerInput } from "./planner-state.js";

function week() {
  return [0, 1].map(dayIndex => ({
    dateStr: `2026-09-0${dayIndex + 1}`,
    lunch: null,
    dinner: dayIndex === 0 ? recipeMeal("soupe", 3) : null
  }));
}

test("ajoute/remplace et normalise les portions", () => {
  const plan = week();
  setMeal(plan, 1, "lunch", recipeMeal("salade", "4"));
  assert.equal(plan[1].lunch.recipeId, "salade");
  assert.equal(plan[1].lunch.portions, 4);
  setMeal(plan, 1, "lunch", recipeMeal("dhal", 0));
  assert.equal(plan[1].lunch.portions, 2);
  assert.equal(normalizePortions("unknown"), 2);
});

test("déplace un repas en échangeant les créneaux", () => {
  const plan = week();
  setMeal(plan, 1, "dinner", recipeMeal("pates"));
  moveMeal(plan, 0, "dinner", 1, "dinner");
  assert.equal(plan[0].dinner.recipeId, "pates");
  assert.equal(plan[1].dinner.recipeId, "soupe");
});

test("supprime un repas sans modifier les autres créneaux", () => {
  const plan = week();
  removeMeal(plan, 0, "dinner");
  assert.equal(plan[0].dinner, null);
  assert.equal(plan[1].dinner, null);
});

test("expose une structure minimale pour Shopping Planner", () => {
  const input = toShoppingPlannerInput(week());
  assert.deepEqual(input[0], { dayIndex: 0, date: "2026-09-01", period: "lunch", recipeId: null, portions: null, type: "empty" });
  assert.equal(input[1].recipeId, "soupe");
  assert.equal(input[1].portions, 3);
  assert.equal(input[3].type, "empty");
});
