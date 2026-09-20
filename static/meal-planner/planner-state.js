/** Minimal local planning state. Selection remains date-free and authoritative for candidates. */
export const MOMENTS = ["Midi", "Soir"];
export const addPlacement = (placements, slug, date, moment) => ({ ...placements, [slug]: { slug, date, moment } });
export const removePlacement = (placements, slug) => { const next = { ...placements }; delete next[slug]; return next; };
export const movePlacement = (placements, slug, date, moment) => addPlacement(placements, slug, date, moment);
/** Start of the local day (midnight), immune to UTC shifts: the planner window always starts "today" for the user. */
export const startOfLocalDay = (value = new Date()) => { const date = new Date(value); date.setHours(0, 0, 0, 0); return date; };
/** Local `YYYY-MM-DD` computed from calendar parts (never via `toISOString`, which can shift the day across timezones). */
export const toLocalISODate = (value = new Date()) => {
  const date = new Date(value);
  const pad = part => String(part).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
};
/** Initial planner window: always today (J -> J+6 sliding window, issue #388). A persisted week is never restored as entry point. */
export const resolveInitialWeekStart = (now = new Date()) => startOfLocalDay(now);
export const loadPlanning = (storage = globalThis.localStorage) => {
  try {
    const value = JSON.parse(storage.getItem("cookigram:meal-planning:v1") || "{}");
    if (!value || typeof value !== "object") return {};
    return Object.fromEntries(Object.entries(value).map(([slug, placement]) => [slug, { ...placement, moment: placement.moment === "Déjeuner" ? "Midi" : placement.moment === "Dîner" ? "Soir" : placement.moment }]));
  } catch { return {}; }
};
export const savePlanning = (planning, storage = globalThis.localStorage) => storage.setItem("cookigram:meal-planning:v1", JSON.stringify(planning));
