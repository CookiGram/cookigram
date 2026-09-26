import test from "node:test";
import assert from "node:assert/strict";

import {
  AVAILABILITY_STORAGE_KEY,
  isIngredientAvailable,
  setIngredientAvailable,
  toggleIngredientAvailable,
  setRecipeIngredientsAvailable,
  migrateLegacyAvailability,
  parseQuantity,
  formatQuantity,
  areQuantitiesCompatible,
  consolidateShopping,
  normalizeIngredientKey,
} from "../static/selection/ingredient-availability.js";

const createMockStorage = (initial = {}) => {
  const store = new Map(Object.entries(initial));
  return {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
    clear: () => store.clear(),
    key: (i) => Array.from(store.keys())[i] || null,
    get length() {
      return store.size;
    },
    _raw: store,
  };
};

test("normalisation canonique de clé d'ingrédient", () => {
  assert.equal(normalizeIngredientKey("Oignons"), "oignons");
  assert.equal(normalizeIngredientKey("Morue salée"), "morue-salee");
  assert.equal(normalizeIngredientKey("farine-de-ble"), "farine-de-ble");
  assert.equal(normalizeIngredientKey("  Huile d'olive extra-vierge!  "), "huile-d-olive-extra-vierge");
});

test("portée par recette : déjà_disponible est un besoin de recette et non un stock global (STOCK-015, STOCK-018)", () => {
  const storage = createMockStorage();

  // Recette A et Recette B ont toutes deux besoin d'oignons
  assert.equal(isIngredientAvailable("recette-a", "oignon", "main", storage), false);
  assert.equal(isIngredientAvailable("recette-b", "oignon", "main", storage), false);

  // Marquer l'oignon comme déjà disponible pour la recette A UNIQUEMENT
  setIngredientAvailable("recette-a", "oignon", true, "main", storage);

  // Vérifier : A est disponible, mais B reste non disponible !
  assert.equal(isIngredientAvailable("recette-a", "oignon", "main", storage), true);
  assert.equal(isIngredientAvailable("recette-b", "oignon", "main", storage), false);

  // Vérifier le miroir pour la fiche recette A
  const mirrorA = JSON.parse(storage.getItem("cookigram:recette-a:main:checked") || "[]");
  assert.ok(mirrorA.includes("oignon"));

  // Vérifier que la fiche recette B n'est pas polluée
  const mirrorB = storage.getItem("cookigram:recette-b:main:checked");
  assert.equal(mirrorB, null);
});

test("quantités compatibles : agrégation compacte et exclusion des besoins déjà disponibles (SHOP-002, STOCK-016, STOCK-019)", () => {
  const storage = createMockStorage();

  const selectedRecipes = [
    {
      slug: "recette-a",
      title: "Recette A",
      shopping: {
        aisles: {
          "Fruits & Légumes": [
            { slug: "oignon", name: "Oignons", quantity: "2 pièces", aisle: "Fruits & Légumes" },
          ],
        },
      },
    },
    {
      slug: "recette-b",
      title: "Recette B",
      shopping: {
        aisles: {
          "Fruits & Légumes": [
            { slug: "oignon", name: "Oignons", quantity: "1 pièce", aisle: "Fruits & Légumes" },
          ],
        },
      },
    },
  ];

  // 1. Initialement : 2 + 1 = 3 pièces à acheter
  let list = consolidateShopping(selectedRecipes, storage);
  assert.equal(list.length, 1);
  assert.equal(list[0].name, "Oignons");
  assert.equal(list[0].parentStatus, "empty");
  assert.equal(list[0].compactLabel, "3 pièces");
  assert.equal(list[0].buckets[0].totalAmountToBuy, 3);

  // 2. Recette A cochée "déjà disponible" -> A ne contribue plus -> courses = 1 pièce (exemple normatif du 25/09/2026)
  setIngredientAvailable("recette-a", "oignon", true, "main", storage);

  list = consolidateShopping(selectedRecipes, storage);
  assert.equal(list.length, 1);
  assert.equal(list[0].parentStatus, "partial");
  // Le total affiché est le total restant à acheter (1 pièce), pas 2/3 ni 2+1 !
  assert.equal(list[0].compactLabel, "1 pièce");
  assert.equal(list[0].buckets[0].totalAmountToBuy, 1);
  assert.equal(list[0].buckets[0].totalAmountInitial, 3);

  // 3. Recette B également cochée -> tous disponibles -> statut complete
  setIngredientAvailable("recette-b", "oignon", true, "main", storage);

  list = consolidateShopping(selectedRecipes, storage);
  assert.equal(list.length, 1);
  assert.equal(list[0].parentStatus, "complete");
  assert.equal(list[0].buckets[0].totalAmountToBuy, 0);
  assert.equal(list[0].compactLabel, "3 pièces"); // label initial barré en statut complet
});

test("quantités incompatibles : côte à côte, contrôles indépendants et tri-state parent (SHOP-003, SHOP-004)", () => {
  const storage = createMockStorage();

  const selectedRecipes = [
    {
      slug: "salade-a",
      title: "Salade A",
      shopping: {
        aisles: {
          "Fruits & Légumes": [
            { slug: "oignon", name: "Oignons", quantity: "2 pièces", aisle: "Fruits & Légumes" },
          ],
        },
      },
    },
    {
      slug: "sauce-b",
      title: "Sauce B",
      shopping: {
        aisles: {
          "Fruits & Légumes": [
            { slug: "oignon", name: "Oignons", quantity: "150 g", aisle: "Fruits & Légumes" },
          ],
        },
      },
    },
  ];

  // 1. Initialement : 2 pièces + 150 g -> statut empty
  let list = consolidateShopping(selectedRecipes, storage);
  assert.equal(list.length, 1);
  const oignons = list[0];
  assert.equal(oignons.isSingleBucket, false);
  assert.equal(oignons.parentStatus, "empty");
  assert.equal(oignons.buckets.length, 2);
  assert.equal(oignons.compactLabel, "2 pièces + 150 g");

  // 2. L'utilisateur coche "2 pièces" (besoin de salade-a)
  setIngredientAvailable("salade-a", "oignon", true, "main", storage);

  list = consolidateShopping(selectedRecipes, storage);
  assert.equal(list[0].parentStatus, "partial");
  assert.equal(list[0].buckets[0].isComplete, true); // bucket 2 pièces
  assert.equal(list[0].buckets[1].isComplete, false); // bucket 150 g

  // 3. L'utilisateur coche "150 g" (besoin de sauce-b)
  setIngredientAvailable("sauce-b", "oignon", true, "main", storage);

  list = consolidateShopping(selectedRecipes, storage);
  assert.equal(list[0].parentStatus, "complete");
  assert.equal(list[0].buckets[0].isComplete, true);
  assert.equal(list[0].buckets[1].isComplete, true);

  // 4. Action globale : démarquer tous les besoins (simulation clic parent quand complet)
  setIngredientAvailable("salade-a", "oignon", false, "main", storage);
  setIngredientAvailable("sauce-b", "oignon", false, "main", storage);

  list = consolidateShopping(selectedRecipes, storage);
  assert.equal(list[0].parentStatus, "empty");
});

test("clic parent couvre tous les sous-besoins incompatibles", () => {
  const storage = createMockStorage();

  const selectedRecipes = [
    {
      slug: "recette-1",
      title: "Recette 1",
      shopping: {
        aisles: {
          Épicerie: [{ slug: "sucre", name: "Sucre", quantity: "2 c. à soupe", aisle: "Épicerie" }],
        },
      },
    },
    {
      slug: "recette-2",
      title: "Recette 2",
      shopping: {
        aisles: {
          Épicerie: [{ slug: "sucre", name: "Sucre", quantity: "150 g", aisle: "Épicerie" }],
        },
      },
    },
  ];

  let list = consolidateShopping(selectedRecipes, storage);
  assert.equal(list[0].parentStatus, "empty");

  // Marquer tous les besoins du groupe comme disponibles
  const group = list[0];
  group.needs.forEach((need) => {
    setIngredientAvailable(need.recipeSlug, need.itemSlug, true, need.variantId, storage);
  });

  list = consolidateShopping(selectedRecipes, storage);
  assert.equal(list[0].parentStatus, "complete");
  assert.ok(isIngredientAvailable("recette-1", "sucre", "main", storage));
  assert.ok(isIngredientAvailable("recette-2", "sucre", "main", storage));
});

test("migration déterministe depuis les anciens stockages (STOCK-013)", () => {
  const storage = createMockStorage({
    // Ancien stockage recette checked
    "cookigram:tarte-pommes:main:checked": JSON.stringify(["pomme", "farine"]),
    // Ancien stockage variante
    "cookigram:poulet-roti:air_fryer:shopping-checked": JSON.stringify(["paprika"]),
    // Ancien shopping-eval (false = déjà disponible)
    "cookigram:ratatouille:shopping-eval": JSON.stringify({
      oignon: false, // déjà disponible !
      aubergine: true, // à acheter
    }),
    // Ancienne liste consolidée
    "cookigram:selection-shopping:v2": JSON.stringify({
      "carotte|mass": true,
    }),
  });

  const selectedRecipes = [
    { slug: "soupe-legumes", title: "Soupe Légumes", variantId: "main" },
  ];

  migrateLegacyAvailability(storage, selectedRecipes);

  // Vérifications
  assert.equal(isIngredientAvailable("tarte-pommes", "pomme", "main", storage), true);
  assert.equal(isIngredientAvailable("tarte-pommes", "farine", "main", storage), true);
  assert.equal(isIngredientAvailable("poulet-roti", "paprika", "air_fryer", storage), true);
  assert.equal(isIngredientAvailable("ratatouille", "oignon", "main", storage), true);
  assert.equal(isIngredientAvailable("ratatouille", "aubergine", "main", storage), false);
  // carotte migrée pour la recette sélectionnée
  assert.equal(isIngredientAvailable("soupe-legumes", "carotte", "main", storage), true);
});

test("compatibilité d'unités (areQuantitiesCompatible)", () => {
  const g100 = parseQuantity("100 g");
  const kg1 = parseQuantity("1 kg");
  const ml200 = parseQuantity("200 ml");
  const cl50 = parseQuantity("50 cl");
  const cs2 = parseQuantity("2 c. à soupe");
  const p3 = parseQuantity("3 pièces");
  const p1 = parseQuantity("1");
  const gousse2 = parseQuantity("2 gousses");

  assert.equal(areQuantitiesCompatible(g100, kg1), true);
  assert.equal(areQuantitiesCompatible(ml200, cl50), true);
  assert.equal(areQuantitiesCompatible(ml200, cs2), true); // cuillères assimilées volume ml
  assert.equal(areQuantitiesCompatible(p3, p1), true);

  assert.equal(areQuantitiesCompatible(g100, ml200), false); // masse vs volume
  assert.equal(areQuantitiesCompatible(g100, p3), false); // masse vs pièce
  assert.equal(areQuantitiesCompatible(p3, gousse2), false); // pièce vs gousse
});

test("propagation bidirectionnelle : fiche -> courses et courses -> fiche (STOCK-010, STOCK-011)", () => {
  const storage = createMockStorage();

  const selectedRecipes = [
    {
      slug: "acras-de-morue",
      title: "Acras de morue",
      shopping: {
        aisles: {
          Poissonnerie: [{ slug: "morue-salee", name: "Morue salée", quantity: "300 g", aisle: "Poissonnerie" }],
        },
      },
    },
  ];

  // 1. Action depuis la fiche recette : simulation écriture fiche recette
  storage.setItem("cookigram:acras-de-morue:main:checked", JSON.stringify(["morue-salee"]));

  // Vérifier côté courses : morue-salee est immédiatement reconnue comme déjà disponible
  assert.equal(isIngredientAvailable("acras-de-morue", "morue-salee", "main", storage), true);
  let list = consolidateShopping(selectedRecipes, storage);
  assert.equal(list[0].parentStatus, "complete");

  // 2. Action inverse depuis les courses : démarquer la morue
  setIngredientAvailable("acras-de-morue", "morue-salee", false, "main", storage);

  // Vérifier côté fiche recette : la clé miroir est mise à jour (vide)
  assert.equal(isIngredientAvailable("acras-de-morue", "morue-salee", "main", storage), false);
  const mirror = JSON.parse(storage.getItem("cookigram:acras-de-morue:main:checked") || "[]");
  assert.equal(mirror.includes("morue-salee"), false);

  list = consolidateShopping(selectedRecipes, storage);
  assert.equal(list[0].parentStatus, "empty");

  // 3. Action depuis les courses : marquer la morue
  setIngredientAvailable("acras-de-morue", "morue-salee", true, "main", storage);
  const updatedMirror = JSON.parse(storage.getItem("cookigram:acras-de-morue:main:checked") || "[]");
  assert.ok(updatedMirror.includes("morue-salee"));
});

test("persistance déterministe après reload simulé", () => {
  const storage = createMockStorage();

  setIngredientAvailable("pizza-margherita", "mozzarella", true, "main", storage);
  setIngredientAvailable("pizza-margherita", "basilic", true, "main", storage);

  // Simulation d'un nouveau reload : relecture brute du storage
  const rawData = storage.getItem(AVAILABILITY_STORAGE_KEY);
  assert.ok(rawData);
  const newStorage = createMockStorage({ [AVAILABILITY_STORAGE_KEY]: rawData });

  assert.equal(isIngredientAvailable("pizza-margherita", "mozzarella", "main", newStorage), true);
  assert.equal(isIngredientAvailable("pizza-margherita", "basilic", "main", newStorage), true);
  assert.equal(isIngredientAvailable("pizza-margherita", "farine", "main", newStorage), false);
});

test("absence de stock quantitatif partiel à l'intérieur d'un besoin de recette", () => {
  const storage = createMockStorage();

  // Une recette demande 300 g de farine. L'utilisateur coche "déjà disponible".
  // L'état est binaire pour ce besoin : true ou false, jamais { quantityHeld: 150 }.
  setIngredientAvailable("crepes", "farine", true, "main", storage);
  assert.strictEqual(typeof isIngredientAvailable("crepes", "farine", "main", storage), "boolean");

  const state = JSON.parse(storage.getItem(AVAILABILITY_STORAGE_KEY) || "{}");
  assert.strictEqual(state["crepes:main"]["farine"], true);
});
