import assert from "node:assert/strict";
import test from "node:test";
import { buildCalendarExport } from "../static/meal-planner/calendar-export.js";

const input = {
  baseUrl: "https://cookigram.github.io/cookigram/",
  weekDates: ["2026-09-07", "2026-09-08", "2026-09-09"],
  selection: [
    { slug: "porc-au-caramel", title: "Porc au caramel" },
    { slug: "riz-blanc", title: "Riz blanc" },
  ],
  placements: {
    "porc-au-caramel": { slug: "porc-au-caramel", date: "2026-09-08", moment: "Soir" },
    "riz-blanc": { slug: "riz-blanc", date: "2026-09-09", moment: "Midi" },
  },
  exportedAt: new Date("2026-09-07T10:00:00Z"),
};

test("exports one all-day event per placement with an honest meal moment", () => {
  const ics = buildCalendarExport(input);
  assert.equal((ics.match(/BEGIN:VEVENT/g) || []).length, 2);
  assert.match(ics, /DTSTART;VALUE=DATE:20260908/);
  assert.match(ics, /SUMMARY:Soir — Porc au caramel/);
  assert.match(ics, /DESCRIPTION:Recette CookiGram .*créneau : Soir/);
  assert.match(ics, /URL:https:\/\/cookigram\.github\.io\/cookigram\/recipes\/porc-au-caramel\//);
  assert.match(ics, /DTEND;VALUE=DATE:20260909/);
});

test("exports only the displayed week and keeps UID stable across snapshots", () => {
  const later = buildCalendarExport({ ...input, exportedAt: new Date("2026-09-08T10:00:00Z") });
  const uid = input.selection.map(recipe => `${recipe.slug}-2026-09-0${recipe.slug === "porc-au-caramel" ? "8" : "9"}`);
  assert.match(later, new RegExp(`UID:${uid[0]}-soir@cookigram`));
  assert.doesNotMatch(later, /DTSTART;VALUE=DATE:20260910/);
  assert.match(later, /DTSTAMP:20260908T100000Z/);
});

test("rejects a visible placement that would produce a misleading event", () => {
  assert.throws(() => buildCalendarExport({
    ...input,
    placements: { ...input.placements, "porc-au-caramel": { ...input.placements["porc-au-caramel"], moment: "Quand je veux" } },
  }), /ne peuvent pas être exportés/);
});
