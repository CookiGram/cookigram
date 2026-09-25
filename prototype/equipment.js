/**
 * Equipment model v2 — Lane C (issue #495).
 * Pure profile/matching/filtering helpers for the prototype.
 * Contract: docs/equipment-contract-495.md (Lane B). No recipe changes here.
 */

export const CANONICAL_KEYS = Object.freeze([
  "air_fryer",
  "stand_mixer",
  "rice_cooker",
  "pizza_oven",
  "pressure_cooker",
  "four",
  "blender",
  "immersion_blender",
  "food_processor",
  "microwave",
  "slow_cooker",
  "thermomix",
  "sous_vide",
  "stovetop",
]);

const CANONICAL_SET = new Set(CANONICAL_KEYS);

// Read aliases accepted on read, normalized to canonical (§4, §5, §7).
export const READ_ALIASES = Object.freeze({
  oven: "four",
  instant_pot: "pressure_cooker",
  cookeo: "pressure_cooker",
});

// Generic French UI labels, no brands (§1, §9). `thermomix` keeps its
// established family name; it is the only brand-derived primary label.
export const EQUIPMENT_LABELS = Object.freeze({
  air_fryer: "Air Fryer",
  stand_mixer: "Robot pâtissier",
  rice_cooker: "Rice cooker",
  pizza_oven: "Four à pizza",
  pressure_cooker: "Autocuiseur / Multicuiseur",
  four: "Four",
  blender: "Blender",
  immersion_blender: "Mixeur plongeant",
  food_processor: "Robot multifonction",
  microwave: "Micro-ondes",
  slow_cooker: "Mijoteuse",
  thermomix: "Thermomix",
  sous_vide: "Sous-vide",
  stovetop: "Plaques & Poêles",
});

// Utensils that stay in `required_equipment` and must never block (§8).
// Compared accent-insensitive (see normalizeToken).
const UTENSILS_OUT = new Set(
  [
    "casserole", "faitout", "cocotte", "cocotte en fonte", "poele", "sauteuse",
    "wok", "passoire", "saladier", "fouet", "spatule", "mandoline", "rape",
    "moules", "plaques", "pierre", "pelle", "pierre a pizza", "pelle a pizza",
    "balance", "thermometre", "couteaux",
  ].map(normalizeToken),
);

export function normalizeToken(value) {
  return String(value ?? "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

export function normalizeEquipmentKey(key) {
  const token = normalizeToken(key).replace(/-/g, "_");
  if (CANONICAL_SET.has(token)) return token;
  const aliased = READ_ALIASES[token];
  return aliased ?? token;
}

export function isKnownEquipmentKey(key) {
  const token = normalizeToken(key).replace(/-/g, "_");
  return CANONICAL_SET.has(token) || token in READ_ALIASES;
}

export function isUtensilToken(value) {
  return UTENSILS_OUT.has(normalizeToken(value));
}

export const DEFAULT_USER_EQUIPMENT = Object.freeze({
  stovetop: true,
  four: true,
  thermomix: false,
  sous_vide: false,
  pressure_cooker: false,
  air_fryer: false,
  stand_mixer: false,
  rice_cooker: false,
  pizza_oven: false,
  blender: false,
  immersion_blender: false,
  food_processor: false,
  microwave: false,
  slow_cooker: false,
});

// Tolerant migration of stored profiles: oven → four, legacy
// instant_pot/cookeo keys fold into pressure_cooker, new families default
// to false, stovetop stays locked on. Never throws on unexpected input.
export function migrateUserEquipment(saved) {
  const merged = { ...DEFAULT_USER_EQUIPMENT };
  if (!saved || typeof saved !== "object") return { ...merged };
  for (const [rawKey, value] of Object.entries(saved)) {
    const canonical = normalizeEquipmentKey(rawKey);
    if (!CANONICAL_SET.has(canonical)) continue;
    merged[canonical] = Boolean(value) || merged[canonical];
  }
  merged.stovetop = true;
  return merged;
}

function normalizedOwnership(userEquipment) {
  const owned = new Set();
  if (!userEquipment || typeof userEquipment !== "object") return owned;
  for (const [rawKey, value] of Object.entries(userEquipment)) {
    if (!value) continue;
    const canonical = normalizeEquipmentKey(rawKey);
    if (CANONICAL_SET.has(canonical)) owned.add(canonical);
  }
  return owned;
}

// Filter predicate: which canonical appliance keys of `recipe` are missing
// from `userEquipment`? Both recipe and profile use the key-presence shape
// (`requiredEquipment: [...]` / `{key: boolean}`).
// - `oven` reads as `four`; legacy `instant_pot`/`cookeo` read as
//   `pressure_cooker` (retrocompat, §7);
// - `blender` + `immersion_blender` combine with OR: owning either device
//   satisfies a recipe listing both (§6);
// - `pizza_oven`: family ownership satisfies any model requirement (§2);
// - utensil tokens never block (§8);
// - unknown appliance keys fail closed: reported missing, never ignored (§7).
export function getMissingEquipment(recipe, userEquipment) {
  const required = recipe?.requiredEquipment;
  if (!Array.isArray(required) || required.length === 0) return [];
  const owned = normalizedOwnership(userEquipment);

  const canonicalRequired = [];
  for (const raw of required) {
    const canonical = normalizeEquipmentKey(raw);
    if (CANONICAL_SET.has(canonical)) {
      if (!canonicalRequired.includes(canonical)) canonicalRequired.push(canonical);
    } else if (isUtensilToken(raw)) {
      continue;
    } else {
      if (!canonicalRequired.includes(String(raw))) canonicalRequired.push(String(raw));
    }
  }

  // Blender disjunction: either device satisfies a both-listed recipe.
  if (canonicalRequired.includes("blender") && canonicalRequired.includes("immersion_blender")) {
    if (owned.has("blender") || owned.has("immersion_blender")) {
      return canonicalRequired.filter((key) => key !== "blender" && key !== "immersion_blender" && !owned.has(key));
    }
    return canonicalRequired.filter((key) => key !== "blender" && key !== "immersion_blender").filter((key) => !owned.has(key)).concat("blender");
  }

  return canonicalRequired.filter((key) => !owned.has(key));
}

export function isRecipeCompatible(recipe, userEquipment) {
  return getMissingEquipment(recipe, userEquipment).length === 0;
}
