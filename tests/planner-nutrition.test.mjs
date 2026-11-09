import assert from "node:assert/strict";
import test from "node:test";

import { summarizeDayNutrition } from "../static/meal-planner/planner-nutrition.js";

const catalog = new Map([
  ["main", { slug: "main", title: "Plat principal", nutrition: { calories: 420 } }],
  ["side", { slug: "side", title: "Accompagnement", nutrition: { calories: 180 } }],
]);

test("daily nutrition sums planned recipes per portion and keeps the detail", () => {
  const summary = summarizeDayNutrition(
    [
      { moment: "Midi", items: [{ slug: "main" }] },
      { moment: "Soir", items: [{ slug: "side" }] },
    ],
    item => catalog.get(item.slug),
  );

  assert.deepEqual(summary, {
    total: 600,
    entries: [
      { moment: "Midi", title: "Plat principal", calories: 420 },
      { moment: "Soir", title: "Accompagnement", calories: 180 },
    ],
  });
});

test("daily nutrition stays hidden when one planned recipe has no reliable value", () => {
  const summary = summarizeDayNutrition(
    [{ moment: "Midi", items: [{ slug: "main" }, { slug: "unknown" }] }],
    item => catalog.get(item.slug),
  );

  assert.equal(summary, null);
});

test("daily nutrition rejects empty and non-numeric calorie values", async t => {
  for (const calories of [null, "", "   ", true, false, [], [180], {}, -1, Infinity, -Infinity, NaN, "not numeric", "Infinity"]) {
    await t.test(`rejects ${String(calories)}`, () => {
      const summary = summarizeDayNutrition(
        [{ moment: "Midi", items: [{ slug: "main" }, { slug: "invalid" }] }],
        item => item.slug === "invalid"
          ? { title: "Valeur invalide", nutrition: { calories } }
          : catalog.get(item.slug),
      );

      assert.equal(summary, null, `calories=${String(calories)} must not produce a partial daily estimate`);
    });
  }
});

test("daily nutrition preserves numeric zero and numeric-string compatibility", () => {
  const summary = summarizeDayNutrition(
    [{ moment: "Midi", items: [{ slug: "zero" }, { slug: "string" }] }],
    item => item.slug === "zero"
      ? { title: "Zéro", nutrition: { calories: 0 } }
      : { title: "Valeur historique", nutrition: { calories: "180" } },
  );

  assert.deepEqual(summary, {
    total: 180,
    entries: [
      { moment: "Midi", title: "Zéro", calories: 0 },
      { moment: "Midi", title: "Valeur historique", calories: 180 },
    ],
  });
});
