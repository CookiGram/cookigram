/**
 * Unified ingredient availability model between recipe cards and shopping list.
 *
 * Sémantique normative (CookiGram #504 / #507) :
 * - "déjà_disponible" est porté par le besoin ingrédient d'une recette (recipeSlug, variantId, ingredientKey)
 * - Aucune notion de stock d'inventaire global ou de garde-manger quantitatif partiel
 * - Fiche recette et liste de courses sont deux vues du même état métier
 * - Exclusion des besoins déjà disponibles avant agrégation
 * - Agrégation compacte des quantités compatibles (ex: 2 + 1 = 3 ; si 2 dispo -> reste 1)
 * - Maintien côte à côte des quantités incompatibles avec état parent vide / partiel / complet
 */

export const AVAILABILITY_STORAGE_KEY = "cookigram:ingredient-availability:v1";

/**
 * Normalise un nom ou un slug d'ingrédient pour une clé canonique stable.
 */
export const normalizeIngredientKey = (value) => {
  return String(value || "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
};

/**
 * Normalise le nom d'affichage sans diacritiques pour comparaisons tolérantes.
 */
export const normalizeIngredientName = (value) => {
  return String(value || "")
    .trim()
    .toLocaleLowerCase("fr-FR")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
};

/**
 * Clé d'accès à la recette/variante dans le dictionnaire de disponibilité.
 */
export const makeRecipeScopeKey = (recipeSlug, variantId = "main") => {
  return `${recipeSlug}:${variantId || "main"}`;
};

/**
 * Charge l'état canonique complet de disponibilité depuis le stockage.
 */
export const loadAvailability = (storage = globalThis.localStorage) => {
  if (!storage) return {};
  try {
    const raw = storage.getItem(AVAILABILITY_STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
};

/**
 * Sauvegarde l'état canonique complet et synchronise les clés miroir pour les fiches recettes.
 */
export const saveAvailability = (state, storage = globalThis.localStorage) => {
  if (!storage) return;
  try {
    storage.setItem(AVAILABILITY_STORAGE_KEY, JSON.stringify(state));
  } catch {}
};

/**
 * Synchronise les clés de stockage miroir par recette pour compatibilité immédiate avec les fiches.
 */
const syncRecipeMirrors = (recipeSlug, variantId, availableKeys, storage = globalThis.localStorage) => {
  if (!storage) return;
  try {
    const vId = variantId || "main";
    const keysArray = Array.isArray(availableKeys) ? availableKeys : Object.keys(availableKeys).filter((k) => availableKeys[k]);
    storage.setItem(`cookigram:${recipeSlug}:${vId}:shopping-checked`, JSON.stringify(keysArray));
    if (vId === "main") {
      storage.setItem(`cookigram:${recipeSlug}:main:checked`, JSON.stringify(keysArray));
    }
  } catch {}
};

/**
 * Détermine si un ingrédient précis d'une recette/variante est marqué "déjà disponible".
 */
export const isIngredientAvailable = (recipeSlug, ingredientKeyOrName, variantId = "main", storage = globalThis.localStorage) => {
  if (!recipeSlug || !ingredientKeyOrName) return false;
  const canonicalKey = normalizeIngredientKey(ingredientKeyOrName);
  const state = loadAvailability(storage);
  const scopeKey = makeRecipeScopeKey(recipeSlug, variantId);

  // 1. Vérification dans l'état canonique unifié
  if (state[scopeKey] && typeof state[scopeKey] === "object") {
    if (state[scopeKey][canonicalKey] !== undefined) {
      return Boolean(state[scopeKey][canonicalKey]);
    }
  }

  // 2. Fallback de réconciliation immédiate avec les clés locales de recette si non encore migré
  if (storage) {
    try {
      const vId = variantId || "main";
      // shopping-checked (tableau de clés)
      const rawChecked = storage.getItem(`cookigram:${recipeSlug}:${vId}:shopping-checked`) || (vId === "main" ? storage.getItem(`cookigram:${recipeSlug}:main:checked`) : null);
      if (rawChecked) {
        const arr = JSON.parse(rawChecked);
        if (Array.isArray(arr)) {
          const match = arr.some((item) => normalizeIngredientKey(item) === canonicalKey || normalizeIngredientName(item) === normalizeIngredientName(ingredientKeyOrName));
          if (match) return true;
        }
      }

      // shopping-eval (map { slug: boolean }, false = déjà disponible / ne pas acheter)
      const rawEval = storage.getItem(`cookigram:${recipeSlug}:shopping-eval`);
      if (rawEval) {
        const evalMap = JSON.parse(rawEval);
        if (evalMap && typeof evalMap === "object" && canonicalKey in evalMap) {
          return evalMap[canonicalKey] === false;
        }
      }
    } catch {}
  }

  return false;
};

/**
 * Modifie l'état de disponibilité d'un besoin ingrédient d'une recette.
 */
export const setIngredientAvailable = (recipeSlug, ingredientKeyOrName, available, variantId = "main", storage = globalThis.localStorage) => {
  if (!recipeSlug || !ingredientKeyOrName) return;
  const canonicalKey = normalizeIngredientKey(ingredientKeyOrName);
  const scopeKey = makeRecipeScopeKey(recipeSlug, variantId);
  const state = loadAvailability(storage);

  if (!state[scopeKey] || typeof state[scopeKey] !== "object") {
    state[scopeKey] = {};
  }

  if (available) {
    state[scopeKey][canonicalKey] = true;
  } else {
    delete state[scopeKey][canonicalKey];
    if (Object.keys(state[scopeKey]).length === 0) {
      delete state[scopeKey];
    }
  }

  saveAvailability(state, storage);

  // Synchronisation miroir des clés de fiches recettes
  const activeKeys = state[scopeKey] ? Object.keys(state[scopeKey]) : [];
  syncRecipeMirrors(recipeSlug, variantId, activeKeys, storage);

  // Émission d'événement pour réactivité temps réel intra-page
  if (typeof document !== "undefined" && document.dispatchEvent) {
    document.dispatchEvent(
      new CustomEvent("cookigram:availability-change", {
        detail: { recipeSlug, variantId, ingredientKey: canonicalKey, available: Boolean(available) },
      })
    );
  }
};

/**
 * Bascule la disponibilité d'un besoin.
 */
export const toggleIngredientAvailable = (recipeSlug, ingredientKeyOrName, variantId = "main", storage = globalThis.localStorage) => {
  const current = isIngredientAvailable(recipeSlug, ingredientKeyOrName, variantId, storage);
  setIngredientAvailable(recipeSlug, ingredientKeyOrName, !current, variantId, storage);
  return !current;
};

/**
 * Modifie la disponibilité de plusieurs ingrédients d'une recette d'un coup.
 */
export const setRecipeIngredientsAvailable = (recipeSlug, ingredientKeys, available, variantId = "main", storage = globalThis.localStorage) => {
  if (!recipeSlug || !Array.isArray(ingredientKeys)) return;
  const scopeKey = makeRecipeScopeKey(recipeSlug, variantId);
  const state = loadAvailability(storage);

  if (!state[scopeKey] || typeof state[scopeKey] !== "object") {
    state[scopeKey] = {};
  }

  ingredientKeys.forEach((keyOrName) => {
    const canonicalKey = normalizeIngredientKey(keyOrName);
    if (available) {
      state[scopeKey][canonicalKey] = true;
    } else {
      delete state[scopeKey][canonicalKey];
    }
  });

  if (Object.keys(state[scopeKey]).length === 0) {
    delete state[scopeKey];
  }

  saveAvailability(state, storage);

  const activeKeys = state[scopeKey] ? Object.keys(state[scopeKey]) : [];
  syncRecipeMirrors(recipeSlug, variantId, activeKeys, storage);

  if (typeof document !== "undefined" && document.dispatchEvent) {
    document.dispatchEvent(
      new CustomEvent("cookigram:availability-change", {
        detail: { recipeSlug, variantId, available: Boolean(available) },
      })
    );
  }
};

/**
 * Migration déterministe depuis les stockages historiques.
 *
 * Règle de migration :
 * 1. cookigram:<slug>:main:checked et cookigram:<slug>:<variant>:shopping-checked -> importés dans l'état unifié
 * 2. cookigram:<slug>:shopping-eval -> les clés à false (ne pas acheter = dispo) sont importées
 * 3. cookigram:selection-shopping:v2 -> si des items globaux étaient cochés, et que des recettes sélectionnées
 *    sont fournies, leurs besoins correspondants sont marqués disponibles.
 */
export const migrateLegacyAvailability = (storage = globalThis.localStorage, selectedRecipes = []) => {
  if (!storage) return;

  const state = loadAvailability(storage);
  let changed = false;

  try {
    for (let i = 0; i < storage.length; i++) {
      const key = storage.key(i);
      if (!key || !key.startsWith("cookigram:")) continue;

      // 1. Clés checked recette
      const checkedMatch = key.match(/^cookigram:([^:]+):(main|shopping-checked|checked)$/);
      if (checkedMatch) {
        const recipeSlug = checkedMatch[1];
        const scopeKey = makeRecipeScopeKey(recipeSlug, "main");
        const raw = storage.getItem(key);
        try {
          const arr = JSON.parse(raw);
          if (Array.isArray(arr) && arr.length > 0) {
            state[scopeKey] = state[scopeKey] || {};
            arr.forEach((item) => {
              const k = normalizeIngredientKey(item);
              if (k) {
                state[scopeKey][k] = true;
                changed = true;
              }
            });
          }
        } catch {}
      }

      // Clés checked variante: cookigram:<slug>:<variant>:shopping-checked
      const variantCheckedMatch = key.match(/^cookigram:([^:]+):([^:]+):shopping-checked$/);
      if (variantCheckedMatch) {
        const recipeSlug = variantCheckedMatch[1];
        const variantId = variantCheckedMatch[2];
        const scopeKey = makeRecipeScopeKey(recipeSlug, variantId);
        const raw = storage.getItem(key);
        try {
          const arr = JSON.parse(raw);
          if (Array.isArray(arr) && arr.length > 0) {
            state[scopeKey] = state[scopeKey] || {};
            arr.forEach((item) => {
              const k = normalizeIngredientKey(item);
              if (k) {
                state[scopeKey][k] = true;
                changed = true;
              }
            });
          }
        } catch {}
      }

      // 2. Clés shopping-eval: false = déjà disponible
      const evalMatch = key.match(/^cookigram:([^:]+):shopping-eval$/);
      if (evalMatch) {
        const recipeSlug = evalMatch[1];
        const scopeKey = makeRecipeScopeKey(recipeSlug, "main");
        const raw = storage.getItem(key);
        try {
          const evalMap = JSON.parse(raw);
          if (evalMap && typeof evalMap === "object") {
            state[scopeKey] = state[scopeKey] || {};
            Object.entries(evalMap).forEach(([itemSlug, toBuy]) => {
              if (toBuy === false) {
                const k = normalizeIngredientKey(itemSlug);
                if (k) {
                  state[scopeKey][k] = true;
                  changed = true;
                }
              }
            });
          }
        } catch {}
      }
    }

    // 3. Ancienne liste consolidée cookigram:selection-shopping:v2
    if (selectedRecipes && selectedRecipes.length > 0) {
      const rawLegacyShopping = storage.getItem("cookigram:selection-shopping:v2");
      if (rawLegacyShopping) {
        try {
          const legacyMap = JSON.parse(rawLegacyShopping);
          if (legacyMap && typeof legacyMap === "object") {
            Object.entries(legacyMap).forEach(([legacyItemKey, isChecked]) => {
              if (!isChecked) return;
              const [ingSlug] = legacyItemKey.split("|");
              const targetKey = normalizeIngredientKey(ingSlug);
              selectedRecipes.forEach((recipe) => {
                const scopeKey = makeRecipeScopeKey(recipe.slug, recipe.variantId || "main");
                state[scopeKey] = state[scopeKey] || {};
                state[scopeKey][targetKey] = true;
                changed = true;
              });
            });
          }
        } catch {}
      }
    }
  } catch {}

  if (changed) {
    saveAvailability(state, storage);
  }
  return state;
};

// ============================================================================
// Parsing, détection de compatibilité et agrégation des quantités
// ============================================================================

export const parseFraction = (value) => {
  const parts = String(value || "").split("/");
  if (parts.length === 2) {
    const a = Number(parts[0]);
    const b = Number(parts[1]);
    return b ? a / b : Number(value);
  }
  return Number(value);
};

/**
 * Analyse une quantité brute.
 * Familles canoniques : mass (en g), volume (en ml), piece (nombre d'unités).
 */
export const parseQuantity = (raw) => {
  if (raw === null || raw === undefined) return null;
  const str = String(raw).trim();
  if (!str) return null;

  const match = str.match(/^([\d./]+)\s*(.*)$/);
  if (!match) return null;

  const amount = parseFraction(match[1]);
  if (!Number.isFinite(amount) || amount <= 0) return null;

  const rawUnit = match[2].trim().toLowerCase();

  // Masse -> base gramme
  if (/^(kg|g|mg)$/.test(rawUnit)) {
    const factors = { kg: 1000, g: 1, mg: 0.001 };
    return { amount: amount * factors[rawUnit], family: "mass", baseUnit: "g", rawUnit };
  }

  // Volume -> base ml
  if (/^(l|dl|cl|ml)$/.test(rawUnit)) {
    const factors = { l: 1000, dl: 100, cl: 10, ml: 1 };
    return { amount: amount * factors[rawUnit], family: "volume", baseUnit: "ml", rawUnit };
  }

  // Cuillères -> assimilées volume (ml)
  if (/c\.\s*à\s*(café|soupe)/.test(rawUnit)) {
    const isSoupe = /soupe/.test(rawUnit);
    return { amount: amount * (isSoupe ? 15 : 5), family: "spoon", baseUnit: "ml", rawUnit: isSoupe ? "c. à soupe" : "c. à café" };
  }

  // Pièces / unités sans ambiguïté
  if (/^(pièce|pièces|piece|pieces|unité|unités)$/.test(rawUnit) || rawUnit === "") {
    return { amount, family: "piece", baseUnit: "pièce", rawUnit: rawUnit || "pièce" };
  }

  // Unité spécifique identifiable (ex: gousse, gousses, tranche, tranches, brin, brins)
  if (/^(gousse|gousses|tranche|tranches|brin|brins|tige|tiges|feuille|feuilles|pincée|pincées)$/.test(rawUnit)) {
    const singular = rawUnit.replace(/s$/, "");
    return { amount, family: `specific:${singular}`, baseUnit: singular, rawUnit };
  }

  // Autre (qualitatif ou descriptif non réductible)
  return null;
};

/**
 * Formatage lisible d'une quantité totale d'une famille.
 */
export const formatQuantity = (amount, family, baseUnit = "") => {
  if (family === "mass") {
    if (amount >= 1000) {
      const kg = amount / 1000;
      return `${Number.isInteger(kg) ? kg : Number(kg.toFixed(2))} kg`;
    }
    return `${Number.isInteger(amount) ? amount : Number(amount.toFixed(1))} g`;
  }
  if (family === "volume" || family === "spoon") {
    if (amount >= 1000) {
      const l = amount / 1000;
      return `${Number.isInteger(l) ? l : Number(l.toFixed(2))} l`;
    }
    if (amount >= 100 && amount % 10 === 0) {
      return `${amount / 10} cl`;
    }
    return `${Number.isInteger(amount) ? amount : Number(amount.toFixed(1))} ml`;
  }
  if (family === "piece") {
    const count = Number.isInteger(amount) ? amount : Number(amount.toFixed(1));
    return count > 1 ? `${count} pièces` : `${count} pièce`;
  }
  if (family.startsWith("specific:")) {
    const unit = family.slice("specific:".length);
    const count = Number.isInteger(amount) ? amount : Number(amount.toFixed(1));
    return count > 1 ? `${count} ${unit}s` : `${count} ${unit}`;
  }
  return `${amount} ${baseUnit}`.trim();
};

/**
 * Vérifie si deux quantités parsées sont d'unités/familles compatibles.
 */
export const areQuantitiesCompatible = (q1, q2) => {
  if (!q1 || !q2) return false;
  if (q1.family === q2.family) return true;
  // spoon et volume sont compatibles (ml)
  if ((q1.family === "volume" && q2.family === "spoon") || (q1.family === "spoon" && q2.family === "volume")) {
    return true;
  }
  return false;
};

// ============================================================================
// Consolidation du panier / liste de courses
// ============================================================================

/**
 * Calcule les lignes de courses consolidées à partir des recettes sélectionnées
 * et de l'état de disponibilité unifié.
 *
 * @param {Array} selectedRecipes - Recettes sélectionnées avec leurs ingrédients
 * @param {Storage} storage - Instance de stockage (localStorage)
 * @returns {Array} Liste des groupes d'ingrédients canoniques avec état et sous-quantités
 */
export const consolidateShopping = (selectedRecipes, storage = globalThis.localStorage) => {
  const ingredientGroups = new Map();

  selectedRecipes.forEach((recipe) => {
    const recipeSlug = recipe.slug;
    const variantId = recipe.variantId || "main";

    // Extraction des ingrédients shopping
    const entries = [];
    if (recipe.shopping?.aisles) {
      Object.entries(recipe.shopping.aisles).forEach(([aisle, items]) => {
        items.forEach((item) => entries.push({ ...item, aisle }));
      });
    }
    if (recipe.shopping?.staples) {
      recipe.shopping.staples.forEach((item) => {
        entries.push({ ...item, aisle: "Fond de placard" });
      });
    }

    entries.forEach((item) => {
      const ingKey = normalizeIngredientKey(item.slug || item.name);
      const isAvailable = isIngredientAvailable(recipeSlug, ingKey, variantId, storage);
      const parsed = parseQuantity(item.quantity);

      const need = {
        recipeSlug,
        recipeTitle: recipe.title || recipeSlug,
        variantId,
        rawQuantity: item.quantity,
        parsed,
        isAvailable,
        itemSlug: item.slug || ingKey,
        name: item.name,
      };

      let group = ingredientGroups.get(ingKey);
      if (!group) {
        group = {
          key: ingKey,
          slug: item.slug || ingKey,
          name: item.name,
          aisle: item.aisle || "Épicerie",
          icon: item.icon || "",
          needs: [],
        };
        ingredientGroups.set(ingKey, group);
      }
      group.needs.push(need);
    });
  });

  // Pour chaque groupe canonique d'ingrédient, organiser les sous-besoins par compatibilité
  const results = [];

  ingredientGroups.forEach((group) => {
    // Partitionner les besoins en "buckets" compatibles
    const buckets = [];

    group.needs.forEach((need) => {
      let placed = false;
      for (const bucket of buckets) {
        if (need.parsed && bucket.parsed && areQuantitiesCompatible(need.parsed, bucket.parsed)) {
          bucket.needs.push(need);
          placed = true;
          break;
        } else if (!need.parsed && !bucket.parsed && need.rawQuantity === bucket.rawQuantity) {
          bucket.needs.push(need);
          placed = true;
          break;
        }
      }
      if (!placed) {
        buckets.push({
          family: need.parsed?.family || "review",
          parsed: need.parsed,
          rawQuantity: need.rawQuantity,
          needs: [need],
        });
      }
    });

    // Pour chaque bucket : calculer le total initial et le total restant après exclusion des disponibles
    const processedBuckets = buckets.map((bucket) => {
      const allNeeds = bucket.needs;
      const toBuyNeeds = allNeeds.filter((n) => !n.isAvailable);
      const isComplete = toBuyNeeds.length === 0;
      const isPartial = toBuyNeeds.length > 0 && toBuyNeeds.length < allNeeds.length;
      const isEmpty = toBuyNeeds.length === allNeeds.length;

      let totalAmountToBuy = 0;
      let totalAmountInitial = 0;
      let displayRemaining = "";
      let displayInitial = "";

      if (bucket.parsed) {
        allNeeds.forEach((n) => {
          if (n.parsed) totalAmountInitial += n.parsed.amount;
        });
        toBuyNeeds.forEach((n) => {
          if (n.parsed) totalAmountToBuy += n.parsed.amount;
        });

        const family = bucket.parsed.family;
        const unit = bucket.parsed.baseUnit;
        displayRemaining = formatQuantity(totalAmountToBuy, family, unit);
        displayInitial = formatQuantity(totalAmountInitial, family, unit);
      } else {
        displayRemaining = toBuyNeeds.length > 0 ? bucket.rawQuantity : "";
        displayInitial = bucket.rawQuantity;
      }

      return {
        ...bucket,
        allNeeds,
        toBuyNeeds,
        isComplete,
        isPartial,
        isEmpty,
        totalAmountToBuy,
        totalAmountInitial,
        displayRemaining,
        displayInitial,
      };
    });

    // Déterminer si le groupe est mono-compatible ou multi-incompatible
    const isSingleBucket = processedBuckets.length === 1;

    // Statut global du parent
    const totalNeedsCount = group.needs.length;
    const availableNeedsCount = group.needs.filter((n) => n.isAvailable).length;

    const parentStatus =
      availableNeedsCount === 0
        ? "empty"
        : availableNeedsCount === totalNeedsCount
        ? "complete"
        : "partial";

    // Libellé restant pour la vue principale
    let compactLabel = "";
    if (isSingleBucket) {
      const b = processedBuckets[0];
      compactLabel = parentStatus === "complete" ? b.displayInitial : b.displayRemaining;
    } else {
      // Incompatibles : afficher les quantités côte à côte
      // "2 pièces + 150 g"
      compactLabel = processedBuckets.map((b) => b.displayInitial).join(" + ");
    }

    results.push({
      key: group.key,
      slug: group.slug,
      name: group.name,
      aisle: group.aisle,
      icon: group.icon,
      isSingleBucket,
      parentStatus, // "empty" | "partial" | "complete"
      buckets: processedBuckets,
      compactLabel,
      needs: group.needs,
      recipes: [...new Set(group.needs.map((n) => n.recipeTitle))],
    });
  });

  return results;
};
