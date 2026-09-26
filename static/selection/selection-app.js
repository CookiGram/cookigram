import { getRecipeSelection, toggleRecipeSelection } from "../assets/js/modules/recipe-selection.js";
import {
  consolidateShopping,
  setIngredientAvailable,
  isIngredientAvailable,
  migrateLegacyAvailability,
  normalizeIngredientName,
} from "./ingredient-availability.js";

const list = document.querySelector("[data-selection-list]");
const empty = document.querySelector("[data-selection-empty]");
const esc = value => String(value ?? "").replace(/[&<>\"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c]));

const render = () => {
  const items = getRecipeSelection();
  list.innerHTML = items.map(item => `<article class="selection-row"><a href="../recipes/${encodeURIComponent(item.slug)}/">${esc(item.title || item.slug)}</a><div class="selection-row-actions"><button type="button" class="selection-remove" data-remove="${esc(item.slug)}" aria-label="Retirer ${esc(item.title || item.slug)} de Ma sélection" title="Retirer de Ma sélection">×</button></div></article>`).join("");
  empty.hidden = items.length > 0;
  list.querySelectorAll("[data-remove]").forEach(button => button.addEventListener("click", () => { toggleRecipeSelection(button.dataset.remove); render(); }));
  document.dispatchEvent(new CustomEvent("cookigram:selection-change"));
};
render();

const shoppingSection = document.querySelector("[data-selection-shopping]");
const shoppingList = document.querySelector("[data-shopping-list]");
const shoppingLoading = document.querySelector("[data-shopping-loading]");
const plannerLink = document.querySelector(".selection-planner-link");
let recipes = [];

const normalizeAisle = aisle => ({
  "Fruits & Légumes": "Fruits & légumes",
  "Boucherie & Volailles": "Boucherie & volailles",
  "Frais & Crèmerie": "Crèmerie & œufs",
  "Condiments & Épices": "Condiments & épices",
  "Épicerie & Féculents": "Épicerie",
  "Boissons & Vins": "Épicerie",
  "Fond de placard": "Fond de placard",
  "Fruits à coque et graines": "Épicerie",
  "Produits laitiers et matières grasses": "Crèmerie & œufs",
  "Boucherie et volaille": "Boucherie & volailles",
  "Épicerie sucrée": "Épicerie",
  "Conserves et bocaux": "Épicerie",
  "Pâtes et céréales": "Épicerie",
}[aisle] || "À vérifier");

const selectedRecipes = () => getRecipeSelection().map(item => recipes.find(recipe => recipe.slug === item.slug)).filter(Boolean);

export const recipeShoppingChoice = (recipe, item) => {
  // Rétrocompatibilité : vérifie si l'ingrédient de cette recette est déjà disponible
  return !isIngredientAvailable(recipe.slug, item.slug || item.name, recipe.variantId || "main");
};

const shoppingItemsToBuy = () => {
  const allItems = consolidateShopping(selectedRecipes(), localStorage);
  return allItems.filter(item => item.parentStatus !== "complete").map(item => {
    if (item.isSingleBucket) {
      return { name: item.name, textQty: item.buckets[0].displayRemaining || item.compactLabel };
    }
    const remainingBuckets = item.buckets.filter(b => !b.isComplete);
    return { name: item.name, textQty: remainingBuckets.map(b => b.displayRemaining).join(" + ") };
  });
};

const renderShopping = () => {
  if (!shoppingList) return;
  const selected = selectedRecipes();
  shoppingSection.hidden = getRecipeSelection().length === 0;

  const rawItems = consolidateShopping(selected, localStorage);
  const items = rawItems.map(item => ({ ...item, aisle: normalizeAisle(item.aisle) }));

  if (plannerLink) plannerLink.hidden = items.length === 0;

  const order = ["Fruits & légumes", "Boucherie & volailles", "Poissonnerie", "Crèmerie & œufs", "Épicerie", "Condiments & épices", "Fond de placard", "À vérifier"];
  items.sort((a, b) => (order.indexOf(a.aisle) - order.indexOf(b.aisle)) || a.name.localeCompare(b.name, "fr"));

  const grouped = items.reduce((groups, item) => {
    const group = groups.find(entry => entry.aisle === item.aisle);
    if (group) group.items.push(item);
    else groups.push({ aisle: item.aisle, items: [item] });
    return groups;
  }, []);

  shoppingList.innerHTML = items.length ? grouped.map(group => `<section class="shopping-group" data-aisle="${esc(group.aisle)}"><h3>${esc(group.aisle)}</h3><ul class="shopping-group-items">${group.items.map(item => {
    const isComplete = item.parentStatus === "complete";
    const isPartial = item.parentStatus === "partial";
    const statusClass = isComplete ? " shopping-item--available" : isPartial ? " shopping-item--partial" : "";

    const ariaLabel = isComplete
      ? `Déjà disponible : ${esc(item.name)}`
      : isPartial
      ? `Partiellement disponible : ${esc(item.name)}`
      : `À acheter : ${esc(item.name)}`;

    if (item.isSingleBucket) {
      const displayQty = isComplete ? item.buckets[0].displayInitial : item.buckets[0].displayRemaining;
      return `<li class="shopping-item${statusClass}" data-ingredient-row="${esc(item.key)}"><label><input type="checkbox" data-shopping-item="${esc(item.key)}" aria-label="${ariaLabel}" ${isComplete ? "checked" : ""}>${item.icon ? `<img class="shopping-item-icon" src="../assets/${esc(item.icon)}" alt="" aria-hidden="true" loading="lazy">` : `<span class="shopping-item-icon" aria-hidden="true"></span>`}<span class="shopping-item-copy"><strong>${esc(item.name)}</strong><small>${esc(displayQty)} · ${esc(item.recipes.join(", "))}</small></span></label></li>`;
    }

    // Incompatibles : contrôles indépendants + parent tri-state
    return `<li class="shopping-item${statusClass}" data-ingredient-row="${esc(item.key)}"><div class="shopping-item-incompatible-wrap"><label><input type="checkbox" data-shopping-item="${esc(item.key)}" data-parent-tristate="true" aria-label="${ariaLabel}" ${isComplete ? "checked" : ""}>${item.icon ? `<img class="shopping-item-icon" src="../assets/${esc(item.icon)}" alt="" aria-hidden="true" loading="lazy">` : `<span class="shopping-item-icon" aria-hidden="true"></span>`}<span class="shopping-item-copy"><strong>${esc(item.name)}</strong><span class="shopping-subquantities">${item.buckets.map((b, idx) => `<button type="button" class="quantity-chip${b.isComplete ? " is-available" : ""}" role="checkbox" aria-checked="${b.isComplete}" data-ingredient-key="${esc(item.key)}" data-bucket-idx="${idx}" aria-label="${b.isComplete ? "Déjà disponible" : "À acheter"} : ${esc(b.displayInitial)} (${esc(item.name)})" title="${b.isComplete ? "Marqué déjà disponible — cliquer pour réinclure" : "Cliquer pour marquer déjà disponible"}">${esc(b.displayInitial)}</button>`).join('<span class="quantity-separator" aria-hidden="true">+</span>')}</span><small class="shopping-item-recipes">${esc(item.recipes.join(", "))}</small></span></label></div></li>`;
  }).join("")}</ul></section>`).join("") : `<p class="shopping-empty">Ajoutez des recettes à Ma sélection pour préparer une liste.</p>`;

  // Configurer les états indéterminés des cases à cocher parentes
  items.forEach(item => {
    if (!item.isSingleBucket && item.parentStatus === "partial") {
      const row = shoppingList.querySelector(`[data-ingredient-row="${item.key}"]`);
      const cb = row?.querySelector('[data-parent-tristate="true"]');
      if (cb) {
        cb.indeterminate = true;
        cb.setAttribute("aria-checked", "mixed");
      }
    }
  });

  // Écouteur sur les cases à cocher principales
  shoppingList.querySelectorAll("[data-shopping-item]").forEach(cb => {
    cb.addEventListener("change", () => {
      const key = cb.dataset.shoppingItem;
      const targetItem = items.find(i => i.key === key);
      if (!targetItem) return;

      if (targetItem.isSingleBucket) {
        targetItem.needs.forEach(need => {
          setIngredientAvailable(need.recipeSlug, need.itemSlug, cb.checked, need.variantId);
        });
      } else {
        // Quantités incompatibles : cliquer sur le parent couvre tous les sous-besoins
        // Si c'était partiel ou vide -> marquer tout disponible. Si c'était complet -> tout démarquer.
        const shouldBeAvailable = targetItem.parentStatus !== "complete";
        targetItem.needs.forEach(need => {
          setIngredientAvailable(need.recipeSlug, need.itemSlug, shouldBeAvailable, need.variantId);
        });
      }
      renderShopping();
    });
  });

  // Écouteur sur les chips de quantités incompatibles
  shoppingList.querySelectorAll(".quantity-chip").forEach(chip => {
    chip.addEventListener("click", e => {
      e.preventDefault();
      e.stopPropagation();
      const key = chip.dataset.ingredientKey;
      const bucketIdx = Number(chip.dataset.bucketIdx);
      const targetItem = items.find(i => i.key === key);
      if (!targetItem || !targetItem.buckets[bucketIdx]) return;

      const bucket = targetItem.buckets[bucketIdx];
      const nextAvailable = !bucket.isComplete;
      bucket.needs.forEach(need => {
        setIngredientAvailable(need.recipeSlug, need.itemSlug, nextAvailable, need.variantId);
      });
      renderShopping();
    });
  });
};

document.addEventListener("cookigram:selection-change", renderShopping);
document.addEventListener("cookigram:availability-change", renderShopping);
window.addEventListener("storage", e => {
  if (e.key === "cookigram:recipe-selection" || e.key?.startsWith("cookigram:")) {
    renderShopping();
  }
});

fetch("../recipes.json")
  .then(response => response.json())
  .then(data => {
    recipes = Array.isArray(data) ? data : data.recipes || [];
    migrateLegacyAvailability(localStorage, selectedRecipes());
    if (shoppingLoading) shoppingLoading.hidden = true;
    renderShopping();
  })
  .catch(() => {
    if (shoppingLoading) shoppingLoading.textContent = "La liste consolidée est temporairement indisponible.";
  });

const shoppingText = () => shoppingItemsToBuy().map(item => `${item.name} : ${item.textQty || "quantité non précisée"}`).join("\n");

const copyShopping = async () => {
  const text = shoppingText();
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const area = document.createElement("textarea");
    area.value = text;
    document.body.append(area);
    area.select();
    document.execCommand("copy");
    area.remove();
  }
};

document.querySelector("[data-copy-shopping]")?.addEventListener("click", async () => { await copyShopping(); });
document.querySelector("[data-share-shopping]")?.addEventListener("click", async () => {
  const text = shoppingText();
  if (navigator.share) await navigator.share({ title: "Courses · Ma sélection", text });
  else await copyShopping();
});
document.querySelector("[data-export-shopping]")?.addEventListener("click", () => {
  const blob = new Blob([shoppingText()], { type: "text/plain;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "courses-cookigram.txt";
  link.click();
  URL.revokeObjectURL(link.href);
});

renderShopping();
