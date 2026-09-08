/** Minimal local planning state. Selection remains date-free and authoritative for candidates. */
export const MOMENTS = ["Déjeuner", "Dîner"];
export const addPlacement = (placements, slug, date, moment) => ({ ...placements, [slug]: { slug, date, moment } });
export const removePlacement = (placements, slug) => { const next = { ...placements }; delete next[slug]; return next; };
export const loadPlanning = (storage = globalThis.localStorage) => {
  try { const value = JSON.parse(storage.getItem("cookigram:meal-planning:v1") || "{}"); return value && typeof value === "object" ? value : {}; } catch { return {}; }
};
export const savePlanning = (planning, storage = globalThis.localStorage) => storage.setItem("cookigram:meal-planning:v1", JSON.stringify(planning));
