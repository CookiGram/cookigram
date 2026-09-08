import test from "node:test";
import assert from "node:assert/strict";
import { addPlacement, loadPlanning, movePlacement, removePlacement } from "./planner-state.js";

test("planning is a projection over selected recipes and persists locally", () => {
  const placements = addPlacement({}, "porc-au-caramel", "2026-09-10", "Soir");
  assert.deepEqual(placements["porc-au-caramel"], { slug: "porc-au-caramel", date: "2026-09-10", moment: "Soir" });
  assert.deepEqual(removePlacement(placements, "porc-au-caramel"), {});
  const storage = { value: '{}', getItem() { return this.value; }, setItem(_, value) { this.value = value; } };
  assert.deepEqual(loadPlanning(storage), {});
});

test("a placement can move without affecting the selection", () => {
  const placements = addPlacement({}, "curry", "2026-09-10", "Soir");
  assert.deepEqual(movePlacement(placements, "curry", "2026-09-12", "Midi")["curry"], { slug: "curry", date: "2026-09-12", moment: "Midi" });
});

test("legacy meal moments remain visible after the Midi/Soir migration", () => {
  const storage = { value: JSON.stringify({ curry: { slug: "curry", date: "2026-09-10", moment: "Dîner" } }), getItem() { return this.value; } };
  assert.equal(loadPlanning(storage).curry.moment, "Soir");
});
