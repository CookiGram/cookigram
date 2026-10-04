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
  "barbecue",
  "plancha",
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
  barbecue: "Barbecue",
  plancha: "Plancha",
  stovetop: "Plaques & Poêles",
});

// Capability families have value-sensitive matching. Legacy `true` means the
// user owns an unspecified model and remains a wildcard for compatibility.
export const EQUIPMENT_CAPABILITIES = Object.freeze({
  barbecue: Object.freeze(["charcoal_kettle", "gas_grill"]),
  sous_vide: Object.freeze(["standard", "anova_precision_cooker"]),
});
export const EQUIPMENT_CAPABILITY_LABELS = Object.freeze({
  charcoal_kettle: "Kettle charbon",
  gas_grill: "Grill à gaz",
  standard: "Standard",
  anova_precision_cooker: "Thermoplongeur Anova",
});

const CAPABILITY_FAMILY_BY_VALUE = Object.freeze(Object.fromEntries(
  Object.entries(EQUIPMENT_CAPABILITIES).flatMap(([family, values]) =>
    values.filter((value) => value !== "standard").map((value) => [value, family])),
));

// Fuel requirements are recipe metadata, never food ingredients or appliances.
export const COOKING_FUEL_TYPES = Object.freeze({
  charcoal: Object.freeze(["briquettes"]),
  smoking_wood: Object.freeze(["oak"]),
});

// Pressure-cooker capabilities (§4): one generic family capability plus
// per-model refinements. `generic` means "owns a pressure cooker, model
// unknown" (e.g. migrated legacy profiles); it covers `standard` recipes.
const PRESSURE_CAPS_ORDER = ["generic", "standard", "instant_pot", "cookeo"];

// Per-model refinement models (the selectable opt-ins owned by Lane C).
export const PRESSURE_COOKER_MODELS = Object.freeze(["standard", "instant_pot", "cookeo"]);

// Secondary refinement labels (§9: brands live in refinements, never primary).
export const PRESSURE_COOKER_MODEL_LABELS = Object.freeze({
  standard: "Traditionnel",
  instant_pot: "Instant Pot",
  cookeo: "Cookeo",
});

// Utensils that stay in `required_equipment` and must never block (§8).
// Compared accent-insensitive (see normalizeToken).
const UTENSILS_OUT = new Set(
  [
    "casserole", "faitout", "cocotte", "cocotte en fonte", "poele", "sauteuse",
    "wok", "passoire", "saladier", "fouet", "spatule", "mandoline", "rape",
    "moules", "plaques", "pierre", "pelle", "pierre a pizza", "pelle a pizza",
    "balance", "thermometre", "couteaux", "grille de saisie en fonte",
    "grille en fonte", "anneau a charbon", "anneau a briquettes",
    "diffuseur", "diffuseur thermique", "deflecteur thermique", "separateurs a charbon",
    "cheminee d'allumage", "cheminee d allumage", "cheminee d'allumage pour charbon",
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

function normalizePressureCap(value) {
  const token = normalizeToken(value).replace(/-/g, "_");
  if (token === "instant_pot_6qt") return "instant_pot";
  return PRESSURE_CAPS_ORDER.includes(token) ? token : null;
}

// Normalize a user-side pressure_cooker value to an ordered capability list.
// Accepts legacy booleans (`true` = family owned, model unknown → generic),
// a single capability string, or an array. Unknown tokens are dropped.
export function normalizePressureCookerCaps(value) {
  if (value === undefined || value === null || value === false) return [];
  if (value === true) return ["generic"];
  if (!Array.isArray(value)) {
    if (typeof value === "string") {
      const cap = normalizePressureCap(value);
      return cap ? [cap] : [];
    }
    return value ? ["generic"] : [];
  }
  const caps = [];
  for (const item of value) {
    if (typeof item !== "string") continue;
    const cap = normalizePressureCap(item);
    if (cap && !caps.includes(cap)) caps.push(cap);
  }
  return PRESSURE_CAPS_ORDER.filter((cap) => caps.includes(cap));
}

// Toggle one capability in a user-side pressure_cooker value. Returns an
// ordered capability array, or `false` when nothing remains selected.
export function togglePressureCookerCap(value, cap) {
  const wanted = typeof cap === "string" ? normalizePressureCap(cap) : null;
  if (!wanted) return normalizePressureCookerCaps(value);
  const caps = normalizePressureCookerCaps(value);
  const next = caps.includes(wanted) ? caps.filter((c) => c !== wanted) : [...caps, wanted];
  const ordered = PRESSURE_CAPS_ORDER.filter((c) => next.includes(c));
  return ordered.length ? ordered : false;
}

// Family switch: owning any capability clears the whole family, owning none
// selects the generic capability. The parent chip therefore always reflects
// and toggles family ownership, never contradicting active refinements.
export function togglePressureCookerFamily(value) {
  return normalizePressureCookerCaps(value).length ? false : ["generic"];
}

// Union of pressure_cooker capabilities owned by a profile, folding legacy
// `instant_pot` / `cookeo` keys into model capabilities (§4, §7).
export function pressureCapsOf(userEquipment) {
  if (!userEquipment || typeof userEquipment !== "object") return [];
  const caps = [];
  const push = (cap) => {
    if (cap && !caps.includes(cap)) caps.push(cap);
  };
  for (const [rawKey, value] of Object.entries(userEquipment)) {
    if (!value) continue;
    const token = normalizeToken(rawKey).replace(/-/g, "_");
    if (token === "instant_pot") {
      push("instant_pot");
      continue;
    }
    if (token === "cookeo") {
      push("cookeo");
      continue;
    }
    if (token !== "pressure_cooker") continue;
    for (const cap of normalizePressureCookerCaps(value)) push(cap);
  }
  return PRESSURE_CAPS_ORDER.filter((cap) => caps.includes(cap));
}

export const DEFAULT_USER_EQUIPMENT = Object.freeze({
  stovetop: true,
  four: true,
  thermomix: false,
  sous_vide: false,
  barbecue: false,
  plancha: false,
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

function migratePressureValue(canonicalRaw, aliasValues) {
  const caps = [];
  const push = (cap) => {
    if (cap && !caps.includes(cap)) caps.push(cap);
  };
  if (canonicalRaw !== undefined) {
    for (const cap of normalizePressureCookerCaps(canonicalRaw)) push(cap);
  }
  for (const { alias, value } of aliasValues) {
    if (!value) continue;
    if (alias === "instant_pot") push("instant_pot");
    else if (alias === "cookeo") push("cookeo");
  }
  const ordered = PRESSURE_CAPS_ORDER.filter((cap) => caps.includes(cap));
  return ordered.length ? ordered : false;
}

function normalizeCapabilityValue(value, family) {
  const values = EQUIPMENT_CAPABILITIES[family];
  if (!values) return [];
  if (value === true) return ["generic"];
  if (value === undefined || value === null || value === false) return [];
  const raw = Array.isArray(value) ? value : [value];
  const normalized = [];
  for (const item of raw) {
    if (typeof item !== "string") continue;
    const token = normalizeToken(item).replace(/-/g, "_");
    if ((values.includes(token) || token === "generic") && !normalized.includes(token)) normalized.push(token);
  }
  return normalized;
}

export function addEquipmentCapability(value, family, capability) {
  const current = normalizeCapabilityValue(value, family);
  if (!EQUIPMENT_CAPABILITIES[family]?.includes(capability)) return current;
  if (current.includes("generic")) return [capability];
  return current.includes(capability) ? current : [...current, capability];
}

export function removeEquipmentCapability(value, family, capability) {
  const current = normalizeCapabilityValue(value, family);
  if (!EQUIPMENT_CAPABILITIES[family]?.includes(capability)) return current.length ? current : false;
  const next = current.filter((item) => item !== capability);
  return next.length ? next : false;
}

export function toggleEquipmentCapability(value, family, capability) {
  return normalizeCapabilityValue(value, family).includes(capability)
    ? removeEquipmentCapability(value, family, capability)
    : addEquipmentCapability(value, family, capability);
}

export function normalizeFuelRequirements(value) {
  if (value === undefined || value === null) return {};
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new TypeError("fuel_requirements must be a dictionary");
  }
  const normalized = {};
  for (const [rawType, rawValues] of Object.entries(value)) {
    const type = normalizeToken(rawType).replace(/-/g, "_");
    const allowed = COOKING_FUEL_TYPES[type];
    if (!allowed) throw new TypeError(`unknown fuel requirement: ${rawType}`);
    const values = Array.isArray(rawValues) ? rawValues : [rawValues];
    const mapped = values.map((item) => normalizeToken(item).replace(/-/g, "_").trim());
    if (!mapped.length || mapped.some((item) => !allowed.includes(item))) {
      throw new TypeError(`invalid ${type} fuel requirement`);
    }
    normalized[type] = [...new Set(mapped)];
  }
  return normalized;
}

function capabilityRequirementSatisfied(family, values, userValue) {
  const owned = normalizeCapabilityValue(userValue, family);
  if (!owned.length) return false;
  if (!values || values.length === 0) return true;
  const wanted = values.map(normalizeRequirementValue);
  if (owned.includes("generic")) return true;
  if (wanted.includes("standard") && owned.some((cap) => cap !== "generic")) return true;
  return wanted.some((cap) => owned.includes(cap));
}

// Tolerant migration of stored profiles. Presence-based: an explicitly stored
// value always wins over its default, so an explicit `false` (e.g. oven off)
// survives the oven → four normalization. Canonical spelling wins over a
// read alias when both are stored. Legacy `instant_pot` / `cookeo` keys fold
// into pressure_cooker model capabilities, a legacy `true` family flag maps
// to the generic capability (model unknown), new families default to off and
// stovetop stays locked on. Never throws on unexpected input.
export function migrateUserEquipment(saved) {
  const merged = { ...DEFAULT_USER_EQUIPMENT };
  if (!saved || typeof saved !== "object" || Array.isArray(saved)) return { ...merged };
  const byCanonical = new Map();
  for (const [rawKey, rawValue] of Object.entries(saved)) {
    const token = normalizeToken(rawKey).replace(/-/g, "_");
    const canonical = CANONICAL_SET.has(token) ? token : READ_ALIASES[token];
    if (!canonical) continue;
    let entry = byCanonical.get(canonical);
    if (!entry) {
      entry = { canonicalRaw: undefined, aliases: [] };
      byCanonical.set(canonical, entry);
    }
    if (token === canonical) entry.canonicalRaw = rawValue;
    else entry.aliases.push({ alias: token, value: Boolean(rawValue) });
  }
  for (const [canonical, entry] of byCanonical) {
    if (canonical === "pressure_cooker") {
      merged.pressure_cooker = migratePressureValue(entry.canonicalRaw, entry.aliases);
    } else if (EQUIPMENT_CAPABILITIES[canonical]) {
      merged[canonical] = normalizeCapabilityValue(entry.canonicalRaw, canonical);
    } else if (entry.canonicalRaw !== undefined) {
      merged[canonical] = Boolean(entry.canonicalRaw);
    } else {
      merged[canonical] = entry.aliases.some((alias) => alias.value);
    }
  }
  merged.stovetop = true;
  return merged;
}

function normalizedOwnership(userEquipment) {
  const owned = new Set();
  if (!userEquipment || typeof userEquipment !== "object") return owned;
  for (const [rawKey, value] of Object.entries(userEquipment)) {
    const canonical = normalizeEquipmentKey(rawKey);
    if (!CANONICAL_SET.has(canonical)) continue;
    if (EQUIPMENT_CAPABILITIES[canonical]) {
      if (normalizeCapabilityValue(value, canonical).length) owned.add(canonical);
      continue;
    }
    if (!value) continue;
    if (canonical === "pressure_cooker") continue; // capability-based, see pressureCapsOf
    owned.add(canonical);
  }
  if (pressureCapsOf(userEquipment).length > 0) owned.add("pressure_cooker");
  return owned;
}

function normalizeRequirementValue(value) {
  const token = normalizeToken(value).replace(/-/g, "_");
  if (token === "instant_pot_6qt") return "instant_pot";
  return token;
}

// A valued pressure_cooker requirement is satisfied by capability
// intersection; the generic family capability covers `standard` recipes (§4).
function isPressureSatisfied(values, caps) {
  if (caps.length === 0) return false;
  if (!values || values.length === 0) return true;
  const effective = new Set(caps);
  if (effective.has("generic")) effective.add("standard");
  return values.some((value) => effective.has(value));
}

function requirementsFromAppliances(appliances) {
  if (!appliances || typeof appliances !== "object" || Array.isArray(appliances)) return [];
  return Object.entries(appliances).map(([key, values]) => ({
    key,
    values: Array.isArray(values) ? values : null,
  }));
}

// Parse recipe requirement items into canonical keys and values
export function parseRecipeRequirements(required) {
  if (!Array.isArray(required) || required.length === 0) return [];
  const keyed = [];
  const pushKeyed = (key, values) => {
    if (!keyed.some((entry) => entry.key === key)) keyed.push({ key, values });
  };
  const aliasModel = (token) => (token === "instant_pot" || token === "cookeo" ? token : null);
  for (const raw of required) {
    if (raw && typeof raw === "object" && !Array.isArray(raw)) {
      const token = normalizeToken(raw.key).replace(/-/g, "_");
      const canonical = CANONICAL_SET.has(token) ? token : READ_ALIASES[token];
      const values = Array.isArray(raw.values)
        ? raw.values.map(normalizeRequirementValue).filter(Boolean)
        : null;
      if (canonical === "pressure_cooker" && !values && token !== "pressure_cooker") {
        pushKeyed(canonical, [aliasModel(token)]);
        continue;
      }
      if (canonical && CANONICAL_SET.has(canonical)) pushKeyed(canonical, values);
      else if (isUtensilToken(raw.key)) continue;
      else pushKeyed(String(raw.key), values);
      continue;
    }
    const token = normalizeToken(raw).replace(/-/g, "_");
    const canonical = CANONICAL_SET.has(token) ? token : READ_ALIASES[token];
    if (canonical === "pressure_cooker" && token !== "pressure_cooker") {
      pushKeyed(canonical, [token]);
      continue;
    }
    if (canonical && CANONICAL_SET.has(canonical)) pushKeyed(canonical, null);
    else if (isUtensilToken(raw)) continue;
    else pushKeyed(String(raw), null);
  }
  return keyed;
}

// Filter predicate: which canonical appliance keys of `recipe` are missing
// from `userEquipment`? Recipes use the key-presence shape
// (`requiredEquipment: [...]`) with optional valued entries
// (`{key, values}`), or the equivalent `appliances` map. Profiles use
// `{key: boolean}` plus capability arrays for pressure_cooker, barbecue, and
// sous_vide.
// - `oven` reads as `four`; legacy `instant_pot`/`cookeo` read as
//   `pressure_cooker` (retrocompat, §7);
// - `blender` + `immersion_blender` combine with OR: owning either device
//   satisfies a recipe listing both (§6);
// - `pizza_oven`: family ownership satisfies any model requirement (§2);
// - utensil tokens never block (§8);
// - unknown appliance keys fail closed: reported missing, never ignored (§7).
export function getMissingEquipment(recipe, userEquipment) {
  const required = Array.isArray(recipe?.requiredEquipment)
    ? recipe.requiredEquipment
    : requirementsFromAppliances(recipe?.appliances);
  const keyed = parseRecipeRequirements(required);
  if (keyed.length === 0) return [];
  const owned = normalizedOwnership(userEquipment);
  const pressureCaps = pressureCapsOf(userEquipment);

  const wantsBlender = keyed.some((entry) => entry.key === "blender");
  const wantsImmersion = keyed.some((entry) => entry.key === "immersion_blender");
  const blenderSatisfied =
    wantsBlender && wantsImmersion && (owned.has("blender") || owned.has("immersion_blender"));

  const missing = [];
  for (const { key, values } of keyed) {
    if (key === "blender" || key === "immersion_blender") {
      if (blenderSatisfied || owned.has(key)) continue;
      if (!missing.includes("blender")) missing.push("blender");
      continue;
    }
    if (key === "pressure_cooker") {
      if (!isPressureSatisfied(values, pressureCaps)) missing.push(key);
      continue;
    }
    if (EQUIPMENT_CAPABILITIES[key]) {
      if (!capabilityRequirementSatisfied(key, values, userEquipment?.[key])) missing.push(key);
      continue;
    }
    if (CANONICAL_SET.has(key)) {
      if (!owned.has(key)) missing.push(key);
      continue;
    }
    missing.push(key);
  }
  return missing;
}

export function isRecipeCompatible(recipe, userEquipment) {
  return getMissingEquipment(recipe, userEquipment).length === 0;
}

// --- Tri-state equipment preferences model (#506) ---

export const EQUIPMENT_STATES = Object.freeze({
  NEUTRAL: "neutral",
  SELECTED: "selected",
  EXCLUDE: "exclude",
});

export const DEFAULT_EQUIPMENT_PREFERENCES = Object.freeze({
  stovetop: "neutral",
  four: "neutral",
  thermomix: "neutral",
  sous_vide: "neutral",
  barbecue: "neutral",
  plancha: "neutral",
  pressure_cooker: "neutral",
  air_fryer: "neutral",
  stand_mixer: "neutral",
  rice_cooker: "neutral",
  pizza_oven: "neutral",
  blender: "neutral",
  immersion_blender: "neutral",
  food_processor: "neutral",
  microwave: "neutral",
  slow_cooker: "neutral",
});

// Exact cycle: neutral -> selected -> exclude -> neutral (#506)
export function cycleEquipmentState(currentState) {
  if (currentState === EQUIPMENT_STATES.SELECTED) return EQUIPMENT_STATES.EXCLUDE;
  if (currentState === EQUIPMENT_STATES.EXCLUDE) return EQUIPMENT_STATES.NEUTRAL;
  return EQUIPMENT_STATES.SELECTED;
}

// Shorter/clean feedback labels for notifications & feedback
export const EQUIPMENT_FEEDBACK_LABELS = Object.freeze({
  ...EQUIPMENT_LABELS,
  pressure_cooker: "Autocuiseur",
  instant_pot: "Instant Pot",
  cookeo: "Cookeo",
});

// Accessible feedback messages conforme #506
export function getEquipmentStateFeedback(equipKey, state) {
  const label = EQUIPMENT_CAPABILITY_LABELS[equipKey] || EQUIPMENT_FEEDBACK_LABELS[equipKey] || EQUIPMENT_LABELS[equipKey] || equipKey;
  switch (state) {
    case EQUIPMENT_STATES.SELECTED:
      return `${label} sélectionné`;
    case EQUIPMENT_STATES.EXCLUDE:
      return `${label} exclu`;
    case EQUIPMENT_STATES.NEUTRAL:
    default:
      return `Préférence ${label} supprimée`;
  }
}

// Tolerant migration for tri-state preferences
export function migrateEquipmentPreferences(saved) {
  const result = { ...DEFAULT_EQUIPMENT_PREFERENCES };
  if (!saved || typeof saved !== "object" || Array.isArray(saved)) return result;

  for (const [rawKey, rawValue] of Object.entries(saved)) {
    const token = normalizeToken(rawKey).replace(/-/g, "_");
    const canonical = CANONICAL_SET.has(token) ? token : READ_ALIASES[token];
    const capabilityFamily = CAPABILITY_FAMILY_BY_VALUE[token];
    if (capabilityFamily) {
      if ([EQUIPMENT_STATES.NEUTRAL, EQUIPMENT_STATES.SELECTED, EQUIPMENT_STATES.EXCLUDE].includes(rawValue)) {
        result[token] = rawValue;
      } else if (rawValue === true || (Array.isArray(rawValue) && rawValue.length)) {
        result[token] = EQUIPMENT_STATES.SELECTED;
      }
      continue;
    }
    if (!canonical) continue;

    // Already a valid tri-state value
    if (
      rawValue === EQUIPMENT_STATES.NEUTRAL ||
      rawValue === EQUIPMENT_STATES.SELECTED ||
      rawValue === EQUIPMENT_STATES.EXCLUDE
    ) {
      result[canonical] = rawValue;
      continue;
    }

    // Tolerant conversion from legacy boolean format:
    if (rawValue === true || (Array.isArray(rawValue) && rawValue.length > 0)) {
      if (canonical !== "stovetop") {
        result[canonical] = EQUIPMENT_STATES.SELECTED;
      }
    } else if (rawValue === false && (token === "four" || token === "oven")) {
      result.four = EQUIPMENT_STATES.EXCLUDE;
    }
  }
  return result;
}

// Extract variants from recipe: multi-variant or single default variant
export function getRecipeVariants(recipe) {
  if (Array.isArray(recipe?.variants) && recipe.variants.length > 0) {
    return recipe.variants.map((v, idx) => ({
      id: v.id || `variant-${idx}`,
      name: v.name || `Variante ${idx + 1}`,
      description: v.description || "",
      requiredEquipment: v.requiredEquipment || (v.appliances ? requirementsFromAppliances(v.appliances) : (recipe.requiredEquipment || [])),
      appliances: v.appliances || null,
      timeTotal: v.timeTotal || recipe.timeTotal,
      default: Boolean(v.default),
    }));
  }
  return [
    {
      id: "default",
      name: "Standard",
      description: recipe?.description || "",
      requiredEquipment: Array.isArray(recipe?.requiredEquipment)
        ? recipe.requiredEquipment
        : requirementsFromAppliances(recipe?.appliances),
      appliances: recipe?.appliances || null,
      timeTotal: recipe?.timeTotal,
      default: true,
    },
  ];
}

// Evaluates whether a single variant is admissible according to tri-state preferences (#506)
export function isVariantAdmissible(variant, preferences) {
  const prefs = preferences || DEFAULT_EQUIPMENT_PREFERENCES;
  const required = variant?.requiredEquipment || (variant?.appliances ? Object.keys(variant.appliances) : []);
  const keyed = parseRecipeRequirements(required);

  const excludedKeys = new Set();
  const selectedKeys = new Set();
  const selectedCapabilities = new Set();

  for (const [key, state] of Object.entries(prefs)) {
    const canonical = normalizeEquipmentKey(key);
    if (CAPABILITY_FAMILY_BY_VALUE[canonical]) {
      if (state === EQUIPMENT_STATES.SELECTED) selectedCapabilities.add(canonical);
      continue;
    }
    if (!CANONICAL_SET.has(canonical)) continue;
    if (state === EQUIPMENT_STATES.EXCLUDE) excludedKeys.add(canonical);
    else if (state === EQUIPMENT_STATES.SELECTED) selectedKeys.add(canonical);
  }

  const isExcluded = (key, values) => {
    if (excludedKeys.has(key)) return true;
    if (EQUIPMENT_CAPABILITIES[key]) {
      const alternatives = values?.length ? values : EQUIPMENT_CAPABILITIES[key];
      return alternatives.every((value) => prefs[value] === EQUIPMENT_STATES.EXCLUDE);
    }
    if (key === "pressure_cooker" && values && values.length > 0) {
      return values.some((val) => prefs[val] === EQUIPMENT_STATES.EXCLUDE);
    }
    return false;
  };

  const isSelected = (key, values) => {
    if (selectedKeys.has(key)) return true;
    if (EQUIPMENT_CAPABILITIES[key]) {
      const alternatives = values?.length ? values : EQUIPMENT_CAPABILITIES[key];
      return alternatives.some((value) => prefs[value] === EQUIPMENT_STATES.SELECTED);
    }
    if (key === "pressure_cooker" && values && values.length > 0) {
      return values.some((val) => prefs[val] === EQUIPMENT_STATES.SELECTED);
    }
    return false;
  };

  // Blender / immersion_blender disjunction:
  const wantsBlender = keyed.some((e) => e.key === "blender");
  const wantsImmersion = keyed.some((e) => e.key === "immersion_blender");
  const isBlenderDisjunction = wantsBlender && wantsImmersion;

  // 1. Exclude filter: if variant requires any excluded equipment, it is rejected.
  for (const { key, values } of keyed) {
    if (isBlenderDisjunction && (key === "blender" || key === "immersion_blender")) {
      if (isExcluded("blender") && isExcluded("immersion_blender")) {
        return false;
      }
      continue;
    }
    if (isExcluded(key, values)) {
      return false;
    }
  }

  // 2. Selected filter (OR combination):
  // If no equipment is selected, any non-excluded variant is admissible.
  if (selectedKeys.size === 0 && selectedCapabilities.size === 0) {
    return true;
  }

  // If positive filters exist, variant must require at least one selected appliance
  for (const { key, values } of keyed) {
    if (isBlenderDisjunction && (key === "blender" || key === "immersion_blender")) {
      if (isSelected("blender") || isSelected("immersion_blender")) {
        return true;
      }
      continue;
    }
    if (isSelected(key, values)) {
      return true;
    }
  }

  return false;
}

// Return all admissible variants for a recipe given preferences
export function getAdmissibleVariants(recipe, preferences) {
  const variants = getRecipeVariants(recipe);
  return variants.filter((v) => isVariantAdmissible(v, preferences));
}

// A recipe is admissible if at least one variant is admissible (#506)
export function isRecipeAdmissible(recipe, preferences) {
  return getAdmissibleVariants(recipe, preferences).length > 0;
}
