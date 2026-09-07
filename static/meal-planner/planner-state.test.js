import test from "node:test";
import assert from "node:assert/strict";
import {
  addIntention, buildShoppingAssessment, projectWeek, updateIntention
} from "./planner-state.js";

const recipes = {
  stew: { portions: 2, ingredients: [{ name: "Farine", qty: "200 g", aisle: "Sec" }] },
  soup: { portions: 2, ingredients: [{ name: "Lait", qty: "1 l", aisle: "Frais" }] }
};

test("intentions can be undated and week is only a projection", () => {
  let intentions = addIntention([], { id: "a", type: "recipe", recipeId: "stew", title: "Ragoût" });
  intentions = addIntention(intentions, { id: "b", type: "free", title: "Pâtes libres" });
  assert.equal(projectWeek(intentions).length, 0);
  intentions = updateIntention(intentions, "a", { date: "2026-09-09", moment: "dinner" });
  assert.deepEqual(projectWeek(intentions).map(i => i.id), ["a"]);
  intentions = updateIntention(intentions, "a", { date: null });
  assert.equal(projectWeek(intentions).length, 0);
});

test("shopping uses only selected intentions and explicit absence means buy", () => {
  const intentions = addIntention([], { id: "a", type: "recipe", recipeId: "stew", title: "Ragoût" });
  const result = buildShoppingAssessment(intentions, recipes, { farine: { status: "absent", certainty: "exact" } }, ["a"]);
  assert.equal(result.toBuy[0].qty, "200 g");
  assert.equal(result.toVerify.length, 0);
});

test("unknown presence is never treated as sufficient", () => {
  const intentions = addIntention([], { id: "a", type: "recipe", recipeId: "stew", title: "Ragoût" });
  const result = buildShoppingAssessment(intentions, recipes, { farine: { status: "present", certainty: "unknown" } }, ["a"]);
  assert.equal(result.toVerify[0].name, "Farine");
});

test("exact quantity can cover a requirement without an inventory ledger", () => {
  const intentions = addIntention([], { id: "a", type: "recipe", recipeId: "stew", title: "Ragoût" });
  const result = buildShoppingAssessment(intentions, recipes, { farine: { status: "present", certainty: "exact", quantity: "250 g" } }, ["a"]);
  assert.equal(result.covered[0].name, "Farine");
});

test("portion scaling without explicit recipe support goes to verify", () => {
  const intentions = addIntention([], { id: "a", type: "recipe", recipeId: "stew", title: "Ragoût", portions: 4 });
  const result = buildShoppingAssessment(intentions, recipes, {}, ["a"]);
  assert.equal(result.toVerify[0].name, "Farine");
});

test("free intentions do not invent shopping requirements", () => {
  const intentions = addIntention([], { id: "a", type: "free", title: "Omelette" });
  assert.deepEqual(buildShoppingAssessment(intentions, recipes, {}, ["a"]), { toBuy: [], toVerify: [], covered: [] });
});
