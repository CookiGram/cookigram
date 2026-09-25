import test from "node:test";
import assert from "node:assert/strict";
import {
  CANONICAL_KEYS,
  DEFAULT_USER_EQUIPMENT,
  EQUIPMENT_LABELS,
  PRESSURE_COOKER_MODELS,
  getMissingEquipment,
  isRecipeCompatible,
  isKnownEquipmentKey,
  migrateUserEquipment,
  normalizeEquipmentKey,
  normalizePressureCookerCaps,
  pressureCapsOf,
  togglePressureCookerCap,
} from "./equipment.js";

const FULL = Object.fromEntries(CANONICAL_KEYS.map((key) => [key, true]));

test("familles canoniques exposées avec libellés génériques sans marques", () => {
  for (const key of [
    "air_fryer", "stand_mixer", "rice_cooker", "pizza_oven", "pressure_cooker",
    "four", "blender", "immersion_blender", "food_processor", "microwave", "slow_cooker",
  ]) {
    assert.ok(CANONICAL_KEYS.includes(key), key);
    assert.ok(EQUIPMENT_LABELS[key], `label manquant: ${key}`);
  }
  const brands = ["ooni", "koda", "cookeo", "instant pot", "instant_pot", "anova", "moulinex", "magimix"];
  for (const [key, label] of Object.entries(EQUIPMENT_LABELS)) {
    if (key === "thermomix") continue;
    for (const token of brands) {
      assert.ok(!label.toLowerCase().includes(token), `${key}: marque dans le libellé (${label})`);
    }
  }
});

test("alias oven → four (rétrocompatibilité)", () => {
  assert.equal(normalizeEquipmentKey("oven"), "four");
  assert.ok(isKnownEquipmentKey("oven"));
  assert.deepEqual(getMissingEquipment({ requiredEquipment: ["oven"] }, { four: true }), []);
  assert.deepEqual(getMissingEquipment({ requiredEquipment: ["four"] }, { oven: true }), []);
  assert.deepEqual(getMissingEquipment({ requiredEquipment: ["oven"] }, FULL), []);
});

test("matching générique pizza_oven", () => {
  assert.deepEqual(getMissingEquipment({ requiredEquipment: ["pizza_oven"] }, { pizza_oven: true }), []);
  assert.deepEqual(getMissingEquipment({ requiredEquipment: ["pizza_oven"] }, FULL), []);
  assert.ok(!isRecipeCompatible({ requiredEquipment: ["pizza_oven"] }, { four: true }));
});

test("sémantique OR blender / immersion_blender", () => {
  const both = { requiredEquipment: ["blender", "immersion_blender"] };
  assert.deepEqual(getMissingEquipment(both, { blender: true }), []);
  assert.deepEqual(getMissingEquipment(both, { immersion_blender: true }), []);
  assert.ok(isRecipeCompatible(both, { blender: true }));
  assert.ok(isRecipeCompatible(both, { immersion_blender: true }));
  assert.ok(!isRecipeCompatible(both, { stovetop: true }));
});

test("famille hiérarchique pressure_cooker sans faux blocage", () => {
  assert.equal(normalizeEquipmentKey("instant_pot"), "pressure_cooker");
  assert.equal(normalizeEquipmentKey("cookeo"), "pressure_cooker");
  assert.deepEqual(getMissingEquipment({ requiredEquipment: ["instant_pot"] }, { pressure_cooker: true }), []);
  assert.deepEqual(getMissingEquipment({ requiredEquipment: ["cookeo"] }, { pressure_cooker: true }), []);
  assert.deepEqual(getMissingEquipment({ requiredEquipment: ["pressure_cooker"] }, { pressure_cooker: true }), []);
  assert.ok(!isRecipeCompatible({ requiredEquipment: ["pressure_cooker"] }, { four: true }));
});

test("ustensiles ordinaires ne bloquent jamais", () => {
  const utensils = {
    requiredEquipment: ["casserole", "poêle", "fouet", "balance", "thermomètre", "couteaux"],
  };
  assert.deepEqual(getMissingEquipment(utensils, { stovetop: true }), []);
  assert.ok(isRecipeCompatible(utensils, DEFAULT_USER_EQUIPMENT));
  assert.deepEqual(getMissingEquipment({ requiredEquipment: [] }, DEFAULT_USER_EQUIPMENT), []);
  assert.deepEqual(getMissingEquipment({}, DEFAULT_USER_EQUIPMENT), []);
});

test("clés inconnues en échec fermé (signalées, jamais ignorées)", () => {
  assert.deepEqual(getMissingEquipment({ requiredEquipment: ["barbecue"] }, FULL), ["barbecue"]);
  assert.ok(!isRecipeCompatible({ requiredEquipment: ["barbecue"] }, FULL));
});

test("migration tolérante du profil stocké", () => {
  assert.deepEqual(migrateUserEquipment({ oven: true }), { ...DEFAULT_USER_EQUIPMENT });
  const migrated = migrateUserEquipment({ oven: false, four: true, thermomix: true, stovetop: false });
  assert.equal(migrated.four, true);
  assert.equal(migrated.thermomix, true);
  assert.equal(migrated.stovetop, true);
  assert.equal(migrated.pizza_oven, false);
  const folded = migrateUserEquipment({ instant_pot: true });
  assert.deepEqual(folded.pressure_cooker, ["instant_pot"]);
  assert.deepEqual(migrateUserEquipment(null), { ...DEFAULT_USER_EQUIPMENT });
});

test("régression : un false explicite survit à la migration oven → four", () => {
  assert.equal(migrateUserEquipment({ oven: false }).four, false);
  assert.equal(migrateUserEquipment({ four: false }).four, false);
  assert.equal(migrateUserEquipment({ oven: false }).oven, undefined);
  assert.equal(migrateUserEquipment({}).four, true);
  assert.equal(migrateUserEquipment({ thermomix: false }).thermomix, false);
  assert.equal(migrateUserEquipment({ pressure_cooker: false }).pressure_cooker, false);
  // Les deux orthographes stockées : la canonique tranche.
  assert.equal(migrateUserEquipment({ oven: false, four: true }).four, true);
  assert.equal(migrateUserEquipment({ oven: true, four: false }).four, false);
});

test("raffinement pressure_cooker : normalisation des capacités", () => {
  assert.deepEqual(PRESSURE_COOKER_MODELS, ["standard", "instant_pot", "cookeo"]);
  assert.deepEqual(normalizePressureCookerCaps(false), []);
  assert.deepEqual(normalizePressureCookerCaps(true), ["generic"]);
  assert.deepEqual(normalizePressureCookerCaps("instant_pot"), ["instant_pot"]);
  assert.deepEqual(normalizePressureCookerCaps("Cookeo"), ["cookeo"]);
  assert.deepEqual(normalizePressureCookerCaps("instant_pot_6qt"), ["instant_pot"]);
  assert.deepEqual(normalizePressureCookerCaps(["cookeo", "generic"]), ["generic", "cookeo"]);
  assert.deepEqual(normalizePressureCookerCaps(["barbecue"]), []);
  assert.deepEqual(pressureCapsOf({ pressure_cooker: ["instant_pot"] }), ["instant_pot"]);
  assert.deepEqual(pressureCapsOf({ pressure_cooker: true }), ["generic"]);
  assert.deepEqual(pressureCapsOf({ pressure_cooker: [] }), []);
  assert.deepEqual(pressureCapsOf({ instant_pot: true }), ["instant_pot"]);
  assert.deepEqual(pressureCapsOf({ cookeo: true }), ["cookeo"]);
});

test("raffinement pressure_cooker : bascule des capacités", () => {
  assert.deepEqual(togglePressureCookerCap(false, "instant_pot"), ["instant_pot"]);
  assert.deepEqual(togglePressureCookerCap(["instant_pot"], "cookeo"), ["instant_pot", "cookeo"]);
  assert.equal(togglePressureCookerCap(["instant_pot"], "instant_pot"), false);
  assert.deepEqual(togglePressureCookerCap(false, "barbecue"), []);
});

test("raffinement pressure_cooker : matching à capacités (contrat §4)", () => {
  const valued = (values) => ({ requiredEquipment: [{ key: "pressure_cooker", values }] });
  assert.ok(isRecipeCompatible(valued(["instant_pot"]), { pressure_cooker: ["instant_pot"] }));
  assert.ok(!isRecipeCompatible(valued(["cookeo"]), { pressure_cooker: ["instant_pot"] }));
  assert.ok(isRecipeCompatible(valued(["instant_pot", "cookeo"]), { pressure_cooker: ["instant_pot"] }));
  assert.ok(isRecipeCompatible(valued(["instant_pot", "cookeo"]), { pressure_cooker: ["cookeo"] }));
  assert.ok(isRecipeCompatible(valued(["standard"]), { pressure_cooker: ["standard"] }));
  assert.ok(!isRecipeCompatible(valued(["standard"]), { pressure_cooker: ["instant_pot"] }));
  // Le sélecteur générique couvre les recettes traditionnelles, sans modèle précis.
  assert.ok(isRecipeCompatible(valued(["standard"]), { pressure_cooker: ["generic"] }));
  assert.ok(isRecipeCompatible(valued(["standard"]), { pressure_cooker: true }));
  assert.ok(!isRecipeCompatible(valued(["instant_pot"]), { pressure_cooker: ["generic"] }));
  // Recette clé seule : toute famille détenue suffit, éteinte bloque.
  assert.ok(isRecipeCompatible({ requiredEquipment: ["pressure_cooker"] }, { pressure_cooker: ["cookeo"] }));
  assert.ok(!isRecipeCompatible({ requiredEquipment: ["pressure_cooker"] }, { pressure_cooker: false }));
  assert.ok(!isRecipeCompatible({ requiredEquipment: ["pressure_cooker"] }, { four: true }));
});

test("raffinement pressure_cooker : migration des profils stockés", () => {
  assert.deepEqual(migrateUserEquipment({ pressure_cooker: true }).pressure_cooker, ["generic"]);
  assert.equal(migrateUserEquipment({ pressure_cooker: false }).pressure_cooker, false);
  assert.deepEqual(migrateUserEquipment({ cookeo: true }).pressure_cooker, ["cookeo"]);
  assert.deepEqual(migrateUserEquipment({ pressure_cooker: ["instant_pot"] }).pressure_cooker, ["instant_pot"]);
  assert.deepEqual(
    migrateUserEquipment({ pressure_cooker: ["generic"], instant_pot: true }).pressure_cooker,
    ["generic", "instant_pot"],
  );
  assert.equal(migrateUserEquipment({ instant_pot: false }).pressure_cooker, false);
});

test("clés historiques conservées", () => {
  for (const key of ["thermomix", "sous_vide", "stovetop", "four"]) {
    assert.ok(isKnownEquipmentKey(key), key);
  }
  assert.ok(isRecipeCompatible({ requiredEquipment: ["thermomix", "four"] }, { thermomix: true, four: true }));
  assert.ok(!isRecipeCompatible({ requiredEquipment: ["thermomix", "four"] }, { four: true }));
});
