/** Minimal local planning state. Selection remains date-free and authoritative for candidates. */
export const MOMENTS = ["Midi", "Soir"];
export const addPlacement = (placements, slug, date, moment) => ({ ...placements, [slug]: { slug, date, moment } });
export const removePlacement = (placements, slug) => { const next = { ...placements }; delete next[slug]; return next; };
export const movePlacement = (placements, slug, date, moment) => addPlacement(placements, slug, date, moment);
export const loadPlanning = (storage = globalThis.localStorage) => {
  try {
    const value = JSON.parse(storage.getItem("cookigram:meal-planning:v1") || "{}");
    if (!value || typeof value !== "object") return {};
    return Object.fromEntries(Object.entries(value).map(([slug, placement]) => [slug, { ...placement, moment: placement.moment === "Déjeuner" ? "Midi" : placement.moment === "Dîner" ? "Soir" : placement.moment }]));
  } catch { return {}; }
};
export const savePlanning = (planning, storage = globalThis.localStorage) => storage.setItem("cookigram:meal-planning:v1", JSON.stringify(planning));
