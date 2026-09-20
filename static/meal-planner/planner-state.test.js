import test from "node:test";
import assert from "node:assert/strict";
import { addPlacement, loadPlanning, movePlacement, removePlacement, resolveInitialWeekStart, startOfLocalDay, toLocalISODate } from "./planner-state.js";

process.env.TZ ??= "Europe/Paris";

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

test("the planner window always starts today, whatever the weekday", () => {
  for (const [input, expected] of [
    [new Date(2026, 8, 21, 10, 0), "2026-09-21"],
    [new Date(2026, 8, 23, 18, 45), "2026-09-23"],
    [new Date(2026, 8, 20, 10, 0), "2026-09-20"],
    [new Date(2026, 8, 20, 0, 30), "2026-09-20"],
  ]) {
    assert.equal(toLocalISODate(resolveInitialWeekStart(input)), expected);
  }
});

test("the sliding window covers exactly today plus six days", () => {
  const start = resolveInitialWeekStart(new Date(2026, 8, 20, 10, 0));
  const end = new Date(start);
  end.setDate(end.getDate() + 6);
  assert.equal(toLocalISODate(start), "2026-09-20");
  assert.equal(toLocalISODate(end), "2026-09-26");
});

test("local midnight and ISO formatting never shift the day across timezones", () => {
  const evening = new Date(2026, 8, 20, 23, 30);
  assert.equal(evening.getHours(), 23);
  assert.equal(toLocalISODate(startOfLocalDay(evening)), "2026-09-20");
  const earlyMorning = new Date(2026, 8, 20, 0, 30);
  assert.equal(toLocalISODate(earlyMorning), "2026-09-20");
  const untouched = new Date(2026, 8, 20, 15, 30);
  startOfLocalDay(untouched);
  assert.equal(untouched.getHours(), 15);
});
