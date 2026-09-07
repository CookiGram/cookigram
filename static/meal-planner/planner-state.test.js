import test from "node:test";
import assert from "node:assert/strict";
import { addPlacement, loadPlanning, removePlacement } from "./planner-state.js";

test("planning is a projection over selected recipes and persists locally", () => {
  const placements = addPlacement({}, "porc-au-caramel", "2026-09-10", "Dîner");
  assert.deepEqual(placements["porc-au-caramel"], { slug: "porc-au-caramel", date: "2026-09-10", moment: "Dîner" });
  assert.deepEqual(removePlacement(placements, "porc-au-caramel"), {});
  const storage = { value: '{}', getItem() { return this.value; }, setItem(_, value) { this.value = value; } };
  assert.deepEqual(loadPlanning(storage), {});
});
