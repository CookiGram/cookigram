import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { NUTRITION_PROFILES, summarizeNutritionProfiles } from "./nutrition-stats.js";

test("répartition descriptive déterministe des trois profils planifiés", () => {
  const plan = [
    { lunch: { type: "recipe", recipeId: "soupe" }, dinner: { type: "recipe", recipeId: "tarte" } },
    { lunch: { type: "eating_out" }, dinner: { type: "recipe", recipeId: "dhal" } },
    { lunch: { type: "recipe", recipeId: "profil-inconnu" }, dinner: null }
  ];
  const recipes = {
    soupe: { profile: "vitality" },
    tarte: { profile: "pleasure" },
    dhal: { profile: "balanced" },
    "profil-inconnu": { profile: "other" }
  };

  assert.deepEqual(NUTRITION_PROFILES, ["vitality", "balanced", "pleasure"]);
  assert.deepEqual(summarizeNutritionProfiles(plan, recipes), {
    counts: { vitality: 1, balanced: 1, pleasure: 1 },
    percentages: { vitality: 33, balanced: 33, pleasure: 33 },
    total: 3
  });
});

test("semaine sans profil connu : parts nulles et aucune division implicite", () => {
  assert.deepEqual(summarizeNutritionProfiles([{ lunch: null, dinner: { type: "eating_out" } }], {}), {
    counts: { vitality: 0, balanced: 0, pleasure: 0 },
    percentages: { vitality: 0, balanced: 0, pleasure: 0 },
    total: 0
  });
});

test("le prototype ne réintroduit pas la cible 80/20 ni les conseils correctifs", async () => {
  const files = ["index.html", "app.js", "style.css"];
  const contents = await Promise.all(files.map(file => readFile(new URL(`./${file}`, import.meta.url), "utf8")));
  const prototype = contents.join("\n");

  assert.doesNotMatch(prototype, /80\s*\/\s*20|80\s*%[^\n]{0,40}20\s*%|Conseil 80\s*\/\s*20/i);
  assert.doesNotMatch(prototype, /ratio-advice|ratioVitality|ratioPleasure|ratio-advice-msg/i);
  for (const profile of NUTRITION_PROFILES) assert.match(prototype, new RegExp(`profile-${profile}`));
  assert.match(prototype, /Profils des recettes planifiées/);
});
