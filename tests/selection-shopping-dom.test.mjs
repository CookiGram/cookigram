import assert from "node:assert/strict";
import test from "node:test";

import {
  consolidateShopping,
  setIngredientAvailable,
  isIngredientAvailable,
  makeRecipeScopeKey,
  AVAILABILITY_STORAGE_KEY,
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

test("cycle DOM / UX complet des quantités incompatibles : vide -> partiel -> complet -> vide", () => {
  const storage = createMockStorage();

  const selectedRecipes = [
    {
      slug: "salade-midi",
      title: "Salade de Midi",
      shopping: {
        aisles: {
          "Fruits & Légumes": [
            { slug: "oignon", name: "Oignons", quantity: "2 pièces", aisle: "Fruits & Légumes" },
          ],
        },
      },
    },
    {
      slug: "soupe-soir",
      title: "Soupe du Soir",
      shopping: {
        aisles: {
          "Fruits & Légumes": [
            { slug: "oignon", name: "Oignons", quantity: "150 g", aisle: "Fruits & Légumes" },
          ],
        },
      },
    },
  ];

  // 1. État initial : vide
  let items = consolidateShopping(selectedRecipes, storage);
  assert.equal(items.length, 1);
  let oignons = items[0];
  assert.equal(oignons.isSingleBucket, false);
  assert.equal(oignons.parentStatus, "empty");
  assert.equal(oignons.buckets[0].isComplete, false);
  assert.equal(oignons.buckets[1].isComplete, false);

  // 2. Clic sur la première quantité incompatible "2 pièces" (salade-midi)
  setIngredientAvailable("salade-midi", "oignon", true, "main", storage);

  items = consolidateShopping(selectedRecipes, storage);
  oignons = items[0];
  // Le parent passe en partiel (indeterminate / mixed)
  assert.equal(oignons.parentStatus, "partial");
  assert.equal(oignons.buckets[0].isComplete, true); // 2 pièces
  assert.equal(oignons.buckets[1].isComplete, false); // 150 g

  // Vérifier la fiche recette correspondante : l'ingrédient est marqué disponible
  assert.equal(isIngredientAvailable("salade-midi", "oignon", "main", storage), true);
  // Mais la fiche soupe-soir reste non disponible
  assert.equal(isIngredientAvailable("soupe-soir", "oignon", "main", storage), false);

  // 3. Clic sur la seconde quantité incompatible "150 g" (soupe-soir)
  setIngredientAvailable("soupe-soir", "oignon", true, "main", storage);

  items = consolidateShopping(selectedRecipes, storage);
  oignons = items[0];
  // Le parent passe en complet
  assert.equal(oignons.parentStatus, "complete");
  assert.equal(oignons.buckets[0].isComplete, true);
  assert.equal(oignons.buckets[1].isComplete, true);

  // 4. Clic sur le parent pour tout démarquer (revient à vide)
  oignons.needs.forEach((n) => setIngredientAvailable(n.recipeSlug, n.itemSlug, false, n.variantId, storage));

  items = consolidateShopping(selectedRecipes, storage);
  oignons = items[0];
  assert.equal(oignons.parentStatus, "empty");
  assert.equal(oignons.buckets[0].isComplete, false);
  assert.equal(oignons.buckets[1].isComplete, false);

  // Les deux fiches recettes sont décochées
  assert.equal(isIngredientAvailable("salade-midi", "oignon", "main", storage), false);
  assert.equal(isIngredientAvailable("soupe-soir", "oignon", "main", storage), false);
});

test("clic parent depuis état partiel couvre tous les sous-besoins", () => {
  const storage = createMockStorage();

  const selectedRecipes = [
    {
      slug: "plat-1",
      title: "Plat 1",
      shopping: {
        aisles: {
          Épicerie: [{ slug: "miel", name: "Miel", quantity: "1 c. à soupe", aisle: "Épicerie" }],
        },
      },
    },
    {
      slug: "plat-2",
      title: "Plat 2",
      shopping: {
        aisles: {
          Épicerie: [{ slug: "miel", name: "Miel", quantity: "200 g", aisle: "Épicerie" }],
        },
      },
    },
  ];

  // Mettre Plat 1 en disponible -> état partiel
  setIngredientAvailable("plat-1", "miel", true, "main", storage);
  let items = consolidateShopping(selectedRecipes, storage);
  assert.equal(items[0].parentStatus, "partial");

  // Clic parent sur état partiel : doit couvrir TOUS les sous-besoins (passer à complete)
  items[0].needs.forEach((n) => setIngredientAvailable(n.recipeSlug, n.itemSlug, true, n.variantId, storage));

  items = consolidateShopping(selectedRecipes, storage);
  assert.equal(items[0].parentStatus, "complete");
  assert.equal(isIngredientAvailable("plat-1", "miel", "main", storage), true);
  assert.equal(isIngredientAvailable("plat-2", "miel", "main", storage), true);
});

test("agrégation compacte des compatibles sans exposition de 2+1 ni 2/3 (règle normative)", () => {
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

  let items = consolidateShopping(selectedRecipes, storage);
  assert.equal(items[0].compactLabel, "3 pièces");
  assert.doesNotMatch(items[0].compactLabel, /2\s*\+\s*1/);
  assert.doesNotMatch(items[0].compactLabel, /2\/3/);

  // Recette A marquée déjà disponible
  setIngredientAvailable("recette-a", "oignon", true, "main", storage);

  items = consolidateShopping(selectedRecipes, storage);
  assert.equal(items[0].compactLabel, "1 pièce");
  assert.doesNotMatch(items[0].compactLabel, /2\s*\+\s*1/);
  assert.doesNotMatch(items[0].compactLabel, /2\/3/);
  assert.doesNotMatch(items[0].compactLabel, /1\/3/);
});
