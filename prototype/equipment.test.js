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
  togglePressureCookerFamily,
  EQUIPMENT_STATES,
  DEFAULT_EQUIPMENT_PREFERENCES,
  cycleEquipmentState,
  getEquipmentStateFeedback,
  migrateEquipmentPreferences,
  getRecipeVariants,
  isVariantAdmissible,
  getAdmissibleVariants,
  isRecipeAdmissible,
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
  assert.deepEqual(getMissingEquipment({ requiredEquipment: ["pressure_cooker"] }, { pressure_cooker: true }), []);
  assert.deepEqual(getMissingEquipment({ requiredEquipment: ["pressure_cooker"] }, { pressure_cooker: ["cookeo"] }), []);
  assert.ok(!isRecipeCompatible({ requiredEquipment: ["pressure_cooker"] }, { four: true }));
});

test("exigences legacy : spécificité du modèle préservée, tests croisés", () => {
  const legacy = (key) => ({ requiredEquipment: [key] });
  // Instant Pot requis : seul un Instant Pot satisfait, jamais un Cookeo ni le générique.
  assert.deepEqual(getMissingEquipment(legacy("instant_pot"), { pressure_cooker: ["instant_pot"] }), []);
  assert.deepEqual(getMissingEquipment(legacy("instant_pot"), { pressure_cooker: ["cookeo"] }), ["pressure_cooker"]);
  assert.deepEqual(getMissingEquipment(legacy("instant_pot"), { pressure_cooker: true }), ["pressure_cooker"]);
  assert.deepEqual(getMissingEquipment(legacy("instant_pot"), { pressure_cooker: ["generic"] }), ["pressure_cooker"]);
  assert.ok(!isRecipeCompatible(legacy("instant_pot"), { pressure_cooker: ["cookeo"] }));
  // Cookeo requis : symétrique, jamais un Instant Pot ni le générique.
  assert.deepEqual(getMissingEquipment(legacy("cookeo"), { pressure_cooker: ["cookeo"] }), []);
  assert.deepEqual(getMissingEquipment(legacy("cookeo"), { pressure_cooker: ["instant_pot"] }), ["pressure_cooker"]);
  assert.deepEqual(getMissingEquipment(legacy("cookeo"), { pressure_cooker: true }), ["pressure_cooker"]);
  assert.ok(!isRecipeCompatible(legacy("cookeo"), { pressure_cooker: ["instant_pot"] }));
  // Forme objet sans valeurs : même lecture que la clé legacy nue.
  assert.deepEqual(
    getMissingEquipment({ requiredEquipment: [{ key: "cookeo" }] }, { pressure_cooker: ["instant_pot"] }),
    ["pressure_cooker"],
  );
  assert.deepEqual(
    getMissingEquipment({ requiredEquipment: [{ key: "instant_pot" }] }, { pressure_cooker: ["instant_pot"] }),
    [],
  );
  // Forme canonique sans valeurs : exigence générique de famille, tout modèle suffit.
  assert.deepEqual(getMissingEquipment({ requiredEquipment: ["pressure_cooker"] }, { pressure_cooker: ["cookeo"] }), []);
  assert.deepEqual(
    getMissingEquipment({ requiredEquipment: [{ key: "pressure_cooker" }] }, { pressure_cooker: ["instant_pot"] }),
    [],
  );
});

test("chip parent pressure_cooker : bascule de famille cohérente", () => {
  assert.deepEqual(togglePressureCookerFamily(false), ["generic"]);
  assert.equal(togglePressureCookerFamily(["instant_pot"]), false);
  assert.equal(togglePressureCookerFamily(["generic", "cookeo"]), false);
  assert.equal(togglePressureCookerFamily(true), false);
  // La famille suit les capacités : non vide = détenue, vide = éteinte.
  assert.ok(isRecipeCompatible({ requiredEquipment: ["pressure_cooker"] }, { pressure_cooker: ["instant_pot"] }));
  assert.ok(!isRecipeCompatible({ requiredEquipment: ["pressure_cooker"] }, { pressure_cooker: false }));
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

// --- Tests Modèle Tri-State & Filtrage par Variante (#506) ---

test("tri-state : cycle neutral -> selected -> exclude -> neutral", () => {
  assert.equal(cycleEquipmentState(EQUIPMENT_STATES.NEUTRAL), EQUIPMENT_STATES.SELECTED);
  assert.equal(cycleEquipmentState(EQUIPMENT_STATES.SELECTED), EQUIPMENT_STATES.EXCLUDE);
  assert.equal(cycleEquipmentState(EQUIPMENT_STATES.EXCLUDE), EQUIPMENT_STATES.NEUTRAL);
  // Valeur inconnue ou absente démarre à selected
  assert.equal(cycleEquipmentState(undefined), EQUIPMENT_STATES.SELECTED);
  assert.equal(cycleEquipmentState("unknown"), EQUIPMENT_STATES.SELECTED);
});

test("tri-state : état initial neutral sur les 14 clés canoniques", () => {
  const keys = Object.keys(DEFAULT_EQUIPMENT_PREFERENCES);
  assert.equal(keys.length, 14);
  for (const key of CANONICAL_KEYS) {
    assert.equal(DEFAULT_EQUIPMENT_PREFERENCES[key], EQUIPMENT_STATES.NEUTRAL, `${key} n'est pas neutral`);
  }
  // En état initial neutre, aucune recette n'est filtrée
  const recipeWithReqs = { requiredEquipment: ["four", "thermomix"] };
  assert.ok(isRecipeAdmissible(recipeWithReqs, DEFAULT_EQUIPMENT_PREFERENCES));
});

test("tri-state : messages de feedback conformes à l'accessibilité", () => {
  assert.equal(getEquipmentStateFeedback("thermomix", EQUIPMENT_STATES.SELECTED), "Thermomix sélectionné");
  assert.equal(getEquipmentStateFeedback("four", EQUIPMENT_STATES.EXCLUDE), "Four exclu");
  assert.equal(getEquipmentStateFeedback("air_fryer", EQUIPMENT_STATES.NEUTRAL), "Préférence Air Fryer supprimée");
  assert.equal(getEquipmentStateFeedback("pressure_cooker", EQUIPMENT_STATES.SELECTED), "Autocuiseur sélectionné");
});

test("tri-state : persistance et migration tolérante de profil legacy", () => {
  // Profil null ou vide
  const def = migrateEquipmentPreferences(null);
  assert.deepEqual(def, DEFAULT_EQUIPMENT_PREFERENCES);

  // Profil legacy booléen (four=false -> exclude, thermomix=true -> selected)
  const legacy1 = migrateEquipmentPreferences({ oven: false, thermomix: true, stovetop: true });
  assert.equal(legacy1.four, EQUIPMENT_STATES.EXCLUDE);
  assert.equal(legacy1.thermomix, EQUIPMENT_STATES.SELECTED);
  // stovetop n'est jamais basculé en selected lors de la migration automatique
  assert.equal(legacy1.stovetop, EQUIPMENT_STATES.NEUTRAL);

  // Profil avec tableau de capacités (pressure_cooker: ['instant_pot'])
  const legacy2 = migrateEquipmentPreferences({ instant_pot: true, air_fryer: true });
  assert.equal(legacy2.pressure_cooker, EQUIPMENT_STATES.SELECTED);
  assert.equal(legacy2.air_fryer, EQUIPMENT_STATES.SELECTED);

  // Profil tri-state déjà valide préservé
  const triState = migrateEquipmentPreferences({
    four: EQUIPMENT_STATES.EXCLUDE,
    thermomix: EQUIPMENT_STATES.SELECTED,
    air_fryer: EQUIPMENT_STATES.NEUTRAL,
  });
  assert.equal(triState.four, EQUIPMENT_STATES.EXCLUDE);
  assert.equal(triState.thermomix, EQUIPMENT_STATES.SELECTED);
  assert.equal(triState.air_fryer, EQUIPMENT_STATES.NEUTRAL);
});

test("tri-state : combinaison OR de plusieurs équipements sélectionnés", () => {
  const prefs = {
    ...DEFAULT_EQUIPMENT_PREFERENCES,
    thermomix: EQUIPMENT_STATES.SELECTED,
    air_fryer: EQUIPMENT_STATES.SELECTED,
  };

  // Une recette nécessitant thermomix doit être admissible
  assert.ok(isRecipeAdmissible({ requiredEquipment: ["thermomix"] }, prefs));
  // Une recette nécessitant air_fryer doit être admissible
  assert.ok(isRecipeAdmissible({ requiredEquipment: ["air_fryer"] }, prefs));
  // Une recette nécessitant four (non sélectionné) ne doit PAS être admissible
  assert.ok(!isRecipeAdmissible({ requiredEquipment: ["four"] }, prefs));
  // Une recette nécessitant stovetop (non sélectionné) ne doit PAS être admissible
  assert.ok(!isRecipeAdmissible({ requiredEquipment: ["stovetop"] }, prefs));
});

test("tri-state : exclusion stricte d'un équipement", () => {
  const prefs = {
    ...DEFAULT_EQUIPMENT_PREFERENCES,
    four: EQUIPMENT_STATES.EXCLUDE,
  };

  // Recette avec four est rejetée
  assert.ok(!isRecipeAdmissible({ requiredEquipment: ["four"] }, prefs));
  // Recette sans four (ex. stovetop) est acceptée (pas de sélection positive active)
  assert.ok(isRecipeAdmissible({ requiredEquipment: ["stovetop"] }, prefs));
  assert.ok(isRecipeAdmissible({ requiredEquipment: ["thermomix"] }, prefs));
});

test("tri-state : combinaison sélection + exclusion simultanées", () => {
  const prefs = {
    ...DEFAULT_EQUIPMENT_PREFERENCES,
    thermomix: EQUIPMENT_STATES.SELECTED,
    four: EQUIPMENT_STATES.EXCLUDE,
  };

  // Thermomix seul : admissible
  assert.ok(isRecipeAdmissible({ requiredEquipment: ["thermomix"] }, prefs));
  // Thermomix ET Four : rejeté car le Four est exclu (exclusion prioritaire)
  assert.ok(!isRecipeAdmissible({ requiredEquipment: ["thermomix", "four"] }, prefs));
  // Four seul : rejeté
  assert.ok(!isRecipeAdmissible({ requiredEquipment: ["four"] }, prefs));
  // Stovetop seul : rejeté car thermomix est sélectionné (filtre positif non satisfait)
  assert.ok(!isRecipeAdmissible({ requiredEquipment: ["stovetop"] }, prefs));
});

test("tri-state : recette mono-variante", () => {
  const mono = { id: "pommes-anna", requiredEquipment: ["four"] };

  // Neutre
  assert.ok(isRecipeAdmissible(mono, DEFAULT_EQUIPMENT_PREFERENCES));

  // Four sélectionné
  const prefsSelected = { ...DEFAULT_EQUIPMENT_PREFERENCES, four: EQUIPMENT_STATES.SELECTED };
  assert.ok(isRecipeAdmissible(mono, prefsSelected));

  // Four exclu
  const prefsExcluded = { ...DEFAULT_EQUIPMENT_PREFERENCES, four: EQUIPMENT_STATES.EXCLUDE };
  assert.ok(!isRecipeAdmissible(mono, prefsExcluded));
});

test("tri-state : recette multi-variante partiellement exclue (reste visible)", () => {
  // Structure identique à la recette carbonnade-flamande du catalogue CookiGram
  const carbonnade = {
    id: "carbonnade-flamande",
    title: "Carbonnade flamande à la bière brune & pain d'épices",
    requiredEquipment: ["thermomix"],
    variants: [
      {
        id: "thermomix",
        name: "Thermomix (Mijotage doux régulé)",
        default: true,
        requiredEquipment: ["thermomix"],
      },
      {
        id: "instant-pot",
        name: "Instant Pot (Haute Pression Express)",
        requiredEquipment: [{ key: "pressure_cooker", values: ["instant_pot"] }],
      },
      {
        id: "cocotte-fonte",
        name: "Cocotte en fonte traditionnelle (Sans robot)",
        requiredEquipment: ["stovetop"],
      },
    ],
  };

  // Exclure thermomix : la recette reste admissible via instant-pot et cocotte-fonte
  const prefsExThermomix = { ...DEFAULT_EQUIPMENT_PREFERENCES, thermomix: EQUIPMENT_STATES.EXCLUDE };
  assert.ok(isRecipeAdmissible(carbonnade, prefsExThermomix));
  const admissible1 = getAdmissibleVariants(carbonnade, prefsExThermomix);
  assert.equal(admissible1.length, 2);
  assert.deepEqual(admissible1.map((v) => v.id), ["instant-pot", "cocotte-fonte"]);

  // Exclure thermomix ET pressure_cooker : la recette reste admissible via cocotte-fonte (stovetop)
  const prefsExTwo = {
    ...DEFAULT_EQUIPMENT_PREFERENCES,
    thermomix: EQUIPMENT_STATES.EXCLUDE,
    pressure_cooker: EQUIPMENT_STATES.EXCLUDE,
  };
  assert.ok(isRecipeAdmissible(carbonnade, prefsExTwo));
  const admissible2 = getAdmissibleVariants(carbonnade, prefsExTwo);
  assert.equal(admissible2.length, 1);
  assert.equal(admissible2[0].id, "cocotte-fonte");
});

test("tri-state : recette multi-variante totalement exclue (masquée)", () => {
  const carbonnade = {
    id: "carbonnade-flamande",
    title: "Carbonnade flamande à la bière brune & pain d'épices",
    requiredEquipment: ["thermomix"],
    variants: [
      {
        id: "thermomix",
        name: "Thermomix (Mijotage doux régulé)",
        requiredEquipment: ["thermomix"],
      },
      {
        id: "instant-pot",
        name: "Instant Pot (Haute Pression Express)",
        requiredEquipment: [{ key: "pressure_cooker", values: ["instant_pot"] }],
      },
      {
        id: "cocotte-fonte",
        name: "Cocotte en fonte traditionnelle (Sans robot)",
        requiredEquipment: ["stovetop"],
      },
    ],
  };

  // Exclure les 3 équipements : thermomix, pressure_cooker, stovetop
  const prefsExAll = {
    ...DEFAULT_EQUIPMENT_PREFERENCES,
    thermomix: EQUIPMENT_STATES.EXCLUDE,
    pressure_cooker: EQUIPMENT_STATES.EXCLUDE,
    stovetop: EQUIPMENT_STATES.EXCLUDE,
  };
  assert.ok(!isRecipeAdmissible(carbonnade, prefsExAll));
  assert.deepEqual(getAdmissibleVariants(carbonnade, prefsExAll), []);
});

test("tri-state : disjonction blender / immersion_blender (OR)", () => {
  const soup = {
    id: "soupe",
    requiredEquipment: ["blender", "immersion_blender"],
  };

  // Exclure seulement blender : admissible car le mixeur plongeant est utilisable
  const prefsExBlender = {
    ...DEFAULT_EQUIPMENT_PREFERENCES,
    blender: EQUIPMENT_STATES.EXCLUDE,
  };
  assert.ok(isRecipeAdmissible(soup, prefsExBlender));

  // Exclure seulement mixeur plongeant : admissible car le blender est utilisable
  const prefsExImmersion = {
    ...DEFAULT_EQUIPMENT_PREFERENCES,
    immersion_blender: EQUIPMENT_STATES.EXCLUDE,
  };
  assert.ok(isRecipeAdmissible(soup, prefsExImmersion));

  // Exclure les deux : non admissible
  const prefsExBoth = {
    ...DEFAULT_EQUIPMENT_PREFERENCES,
    blender: EQUIPMENT_STATES.EXCLUDE,
    immersion_blender: EQUIPMENT_STATES.EXCLUDE,
  };
  assert.ok(!isRecipeAdmissible(soup, prefsExBoth));

  // Sélectionner blender : admissible (satisfait le filtre positif)
  const prefsSelBlender = {
    ...DEFAULT_EQUIPMENT_PREFERENCES,
    blender: EQUIPMENT_STATES.SELECTED,
  };
  assert.ok(isRecipeAdmissible(soup, prefsSelBlender));
});

test("tri-state : règle de non-rétroactivité (arbitrage PO 25/09/2026)", () => {
  // Une recette exclue par préférences de matériel
  const prefs = {
    ...DEFAULT_EQUIPMENT_PREFERENCES,
    four: EQUIPMENT_STATES.EXCLUDE,
  };
  const recipe = { id: "pommes-anna", requiredEquipment: ["four"] };
  assert.ok(!isRecipeAdmissible(recipe, prefs), "La recette doit être inadmissible sous ces préférences");

  // Règle de non-rétroactivité pour la sélection de repas :
  // Si le repas est déjà présent dans les kiffs sélectionnés, il ne doit PAS être supprimé silencieusement
  const selectedKiffIds = ["pommes-anna"];
  const isSelected = selectedKiffIds.includes(recipe.id);
  const isAdmissible = isRecipeAdmissible(recipe, prefs);

  // Le prédicat de visibilité préserve le repas sélectionné :
  const shouldKeepVisible = isAdmissible || isSelected;
  assert.ok(shouldKeepVisible, "Le repas planifié doit rester visible malgré l'incompatibilité");
  // Mais son statut d'incompatibilité est détectable pour affichage d'un badge d'alerte :
  assert.equal(isAdmissible, false);
});


