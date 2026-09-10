import { getRecipeSelection, toggleRecipeSelection } from "../assets/js/modules/recipe-selection.js";
const list = document.querySelector("[data-selection-list]");
const empty = document.querySelector("[data-selection-empty]");
const storageKey = "cookigram:recipe-selection";
const write = items => localStorage.setItem(storageKey, JSON.stringify(items));
const esc = value => String(value ?? "").replace(/[&<>\"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c]));
const render = () => {
  const items = getRecipeSelection();
  list.innerHTML = items.map((item, index) => `<article class="selection-row"><a href="../recipes/${encodeURIComponent(item.slug)}/">${esc(item.title || item.slug)}</a><div class="selection-row-actions"><button type="button" class="selection-reorder" data-move="up" data-index="${index}" ${index === 0 ? "disabled" : ""} aria-label="Monter ${esc(item.title || item.slug)}">↑</button><button type="button" class="selection-reorder" data-move="down" data-index="${index}" ${index === items.length - 1 ? "disabled" : ""} aria-label="Descendre ${esc(item.title || item.slug)}">↓</button><button type="button" class="selection-remove" data-remove="${esc(item.slug)}">Retirer</button></div></article>`).join("");
  empty.hidden = items.length > 0;
  list.querySelectorAll("[data-remove]").forEach(button => button.addEventListener("click", () => { toggleRecipeSelection(button.dataset.remove); render(); }));
  list.querySelectorAll("[data-move]").forEach(button => button.addEventListener("click", () => { const next = [...getRecipeSelection()]; const index = Number(button.dataset.index); const target = button.dataset.move === "up" ? index - 1 : index + 1; if (target < 0 || target >= next.length) return; [next[index], next[target]] = [next[target], next[index]]; write(next); render(); list.querySelector(`[data-index="${target}"]`)?.focus(); }));
  document.dispatchEvent(new CustomEvent("cookigram:selection-change"));
};
render();

const shoppingSection = document.querySelector("[data-selection-shopping]");
const shoppingList = document.querySelector("[data-shopping-list]");
const shoppingLoading = document.querySelector("[data-shopping-loading]");
const plannerLink = document.querySelector(".selection-planner-link");
const shoppingStateKey = "cookigram:selection-shopping:v2";
let recipes = [];
const readShoppingState = () => { try { const value = JSON.parse(localStorage.getItem(shoppingStateKey) || "{}"); return value && typeof value === "object" ? value : {}; } catch { return {}; } };
const saveShoppingState = value => localStorage.setItem(shoppingStateKey, JSON.stringify(value));
const fraction = value => { const [a, b] = String(value).split("/").map(Number); return b ? a / b : Number(value); };
const parseQuantity = raw => {
  const match = String(raw || "").trim().match(/^([\d./]+)\s*(.*)$/);
  if (!match) return null;
  const amount = fraction(match[1]);
  if (!Number.isFinite(amount)) return null;
  const unit = match[2].trim().toLowerCase();
  const family = /^(kg|g|mg)$/.test(unit) ? "mass" : /^(l|dl|cl|ml)$/.test(unit) ? "volume" : /^(pièce|pièces|piece|pieces|unité|unités)$/.test(unit) ? "piece" : /c\.\s*à\s*(café|soupe)/.test(unit) ? "spoon" : null;
  if (!family) return null;
  const factors = { kg: 1000, g: 1, mg: .001, l: 1000, dl: 100, cl: 10, ml: 1, "c. à soupe": 15, "c. à café": 5 };
  return { amount: amount * (factors[unit] || 1), family, unit };
};
const formatQuantity = (total, family, unit) => {
  const units = family === "mass" ? ["kg", 1000] : family === "volume" ? ["l", 1000] : family === "spoon" ? ["ml", 1] : [unit, 1];
  const value = total / units[1];
  return `${Number.isInteger(value) ? value : Number(value.toFixed(2))} ${units[0]}`;
};
const itemKey = item => item.parsed ? `${item.slug}|${item.parsed.family}` : `${item.slug}|review|${item.quantity}`;
const legacyItemKey = item => `${item.slug}|${item.parsed?.family || "review"}|${item.parsed?.unit || item.quantity}`;
const isShoppingChecked = (item, state) => Boolean(state[itemKey(item)] || state[legacyItemKey(item)]);
const normalizeIngredientName = value => String(value || "").trim().toLocaleLowerCase("fr-FR").normalize("NFD").replace(/[\u0300-\u036f]/g, "");
const recipeShoppingChoice = (recipe, item) => {
  try {
    const saved = JSON.parse(localStorage.getItem(`cookigram:${recipe.slug}:shopping-eval`) || "null");
    if (saved && typeof saved === "object" && item.slug in saved) return saved[item.slug] !== false;

    const checked = JSON.parse(localStorage.getItem(`cookigram:${recipe.slug}:main:checked`) || "[]");
    if (!Array.isArray(checked)) return true;
    const ingredientName = normalizeIngredientName(item.name);
    return !checked.some(value => normalizeIngredientName(value) === ingredientName);
  } catch { return true; }
};
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
const consolidate = selected => {
  const groups = new Map();
  selected.forEach(recipe => {
    const entries = [...(recipe.shopping?.aisles ? Object.entries(recipe.shopping.aisles).flatMap(([aisle, items]) => items.map(item => ({ ...item, aisle }))) : []), ...(recipe.shopping?.staples || []).map(item => ({ ...item, aisle: "Fond de placard" }))].filter(item => recipeShoppingChoice(recipe, item));
    entries.forEach(item => {
      const parsed = parseQuantity(item.quantity);
      const key = itemKey({ ...item, parsed });
      const group = groups.get(key) || { ...item, aisle: normalizeAisle(item.aisle), recipes: [], parsed, total: 0, review: !parsed };
      if (parsed) group.total += parsed.amount;
      group.recipes.push(recipe.title);
      groups.set(key, group);
    });
  });
  const order = ["Fruits & légumes", "Boucherie & volailles", "Poissonnerie", "Crèmerie & œufs", "Épicerie", "Condiments & épices", "Fond de placard", "À vérifier"];
  return [...groups.values()].sort((a, b) => (order.indexOf(a.aisle) - order.indexOf(b.aisle)) || a.name.localeCompare(b.name, "fr"));
};
const selectedRecipes = () => getRecipeSelection().map(item => recipes.find(recipe => recipe.slug === item.slug)).filter(Boolean);
const shoppingItemsToBuy = () => consolidate(selectedRecipes()).filter(item => !isShoppingChecked(item, readShoppingState()));
const renderShopping = () => {
  if (!shoppingList) return;
  const items = consolidate(selectedRecipes());
  const state = readShoppingState();
  shoppingSection.hidden = getRecipeSelection().length === 0;
  if (plannerLink) plannerLink.hidden = items.length === 0;
  const grouped = items.reduce((groups, item) => { const group = groups.find(entry => entry.aisle === item.aisle); if (group) group.items.push(item); else groups.push({ aisle: item.aisle, items: [item] }); return groups; }, []);
  shoppingList.innerHTML = items.length ? grouped.map(group => `<section class="shopping-group" data-aisle="${esc(group.aisle)}"><h3>${esc(group.aisle)}</h3><ul class="shopping-group-items">${group.items.map(item => {
    const qty = item.parsed ? formatQuantity(item.total, item.parsed.family, item.parsed.unit) : `À vérifier · ${item.quantity || "quantité non précisée"}`;
    const key = itemKey(item);
    const checked = isShoppingChecked(item, state);
    return `<li class="shopping-item${item.review ? " shopping-item--review" : ""}${checked ? " shopping-item--available" : ""}"><label><input type="checkbox" data-shopping-item="${esc(key)}" aria-label="${checked ? "Déjà disponible" : "À acheter"} : ${esc(item.name)}" ${checked ? "checked" : ""}>${item.icon ? `<img class="shopping-item-icon" src="../assets/${esc(item.icon)}" alt="" aria-hidden="true" loading="lazy">` : ""}<span><strong>${esc(item.name)}</strong><small>${esc(qty)} · ${esc(item.recipes.join(", "))}</small></span>${item.review ? `<span class="shopping-review-icon" role="img" title="À vérifier" aria-label="À vérifier">⌕</span>` : ""}</label></li>`;
  }).join("")}</ul></section>`).join("") : `<p class="shopping-empty">Ajoutez des recettes à Ma sélection pour préparer une liste.</p>`;
  shoppingList.querySelectorAll("[data-shopping-item]").forEach(cb => cb.addEventListener("change", () => { const next = readShoppingState(); next[cb.dataset.shoppingItem] = cb.checked; saveShoppingState(next); const row = cb.closest(".shopping-item"); row?.classList.toggle("shopping-item--available", cb.checked); const name = row?.querySelector("strong")?.textContent || "l’ingrédient"; cb.setAttribute("aria-label", `${cb.checked ? "Déjà disponible" : "À acheter"} : ${name}`); }));
};
document.addEventListener("cookigram:selection-change", renderShopping);
fetch("../recipes.json").then(response => response.json()).then(data => { recipes = Array.isArray(data) ? data : data.recipes || []; if (shoppingLoading) shoppingLoading.hidden = true; renderShopping(); }).catch(() => { if (shoppingLoading) shoppingLoading.textContent = "La liste consolidée est temporairement indisponible."; });
const shoppingText = () => shoppingItemsToBuy().map(item => `${item.name} : ${item.parsed ? formatQuantity(item.total, item.parsed.family, item.parsed.unit) : `À vérifier · ${item.quantity || "quantité non précisée"}`}`).join("\n");
const copyShopping = async () => { const text = shoppingText(); try { await navigator.clipboard.writeText(text); } catch { const area = document.createElement("textarea"); area.value = text; document.body.append(area); area.select(); document.execCommand("copy"); area.remove(); } };
document.querySelector("[data-copy-shopping]")?.addEventListener("click", async () => { await copyShopping(); });
document.querySelector("[data-share-shopping]")?.addEventListener("click", async () => { const text = shoppingText(); if (navigator.share) await navigator.share({ title: "Courses · Ma sélection", text }); else await copyShopping(); });
document.querySelector("[data-export-shopping]")?.addEventListener("click", () => { const blob = new Blob([shoppingText()], { type: "text/plain;charset=utf-8" }); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "courses-cookigram.txt"; link.click(); URL.revokeObjectURL(link.href); });
renderShopping();
