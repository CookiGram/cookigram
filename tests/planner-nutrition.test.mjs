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
