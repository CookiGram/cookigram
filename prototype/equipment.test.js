import test from "node:test";
import assert from "node:assert/strict";
import {
  CANONICAL_KEYS,
  DEFAULT_USER_EQUIPMENT,
  EQUIPMENT_LABELS,
  getMissingEquipment,
  isRecipeCompatible,
  isKnownEquipmentKey,
  migrateUserEquipment,
  normalizeEquipmentKey,
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
  assert.equal(folded.pressure_cooker, true);
  assert.deepEqual(migrateUserEquipment(null), { ...DEFAULT_USER_EQUIPMENT });
});

test("clés historiques conservées", () => {
  for (const key of ["thermomix", "sous_vide", "stovetop", "four"]) {
    assert.ok(isKnownEquipmentKey(key), key);
  }
  assert.ok(isRecipeCompatible({ requiredEquipment: ["thermomix", "four"] }, { thermomix: true, four: true }));
  assert.ok(!isRecipeCompatible({ requiredEquipment: ["thermomix", "four"] }, { four: true }));
});
