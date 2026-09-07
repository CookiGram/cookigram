import { RECIPES } from "./app.js";
import {
  addIntention, buildShoppingAssessment, createMealIntention, removeIntention,
  projectWeek, updateIntention
} from "./planner-state.js";

const STORAGE_KEY = "cookigram:meal-plan:intentions:v1";
const esc = value => String(value ?? "").replace(/[&<>\"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
const today = () => new Date().toISOString().slice(0, 10);
let state = { intentions: [], kitchenFacts: {} };
let selectedIds = new Set();

function load() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    if (saved && Array.isArray(saved.intentions)) state = { ...state, ...saved };
  } catch (error) { console.warn("Planner storage ignored", error); }
}
function save() { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
function notify(message) { const toast = document.getElementById("toast-notification"); toast.textContent = message; toast.classList.add("show"); setTimeout(() => toast.classList.remove("show"), 2400); }
function recipeCard(recipe) {
  return `<article class="kiff-card intent-recipe-card"><div class="kiff-card-top"><strong>${esc(recipe.title)}</strong><span class="badge">${esc(recipe.timeTotal || "CookiGram")}</span></div><p class="kiff-card-desc">${esc(recipe.description || "")}</p><button class="btn-small primary" data-add-recipe="${esc(recipe.id)}">Ajouter à mes intentions</button></article>`;
}
function renderRecipes(filter = "") {
  const needle = filter.trim().toLowerCase();
  const recipes = Object.values(RECIPES).filter(recipe => !needle || `${recipe.title} ${recipe.description}`.toLowerCase().includes(needle));
  document.getElementById("recipe-catalog").innerHTML = recipes.map(recipeCard).join("") || `<p class="empty-state">Aucune recette trouvée.</p>`;
  document.querySelectorAll("[data-add-recipe]").forEach(button => button.addEventListener("click", () => {
    const recipe = RECIPES[button.dataset.addRecipe];
    state.intentions = addIntention(state.intentions, { type: "recipe", recipeId: recipe.id, title: recipe.title });
    save(); render(); notify("Intention ajoutée, datez-la quand vous voulez.");
  }));
}
function intentionEditor(intent) {
  const recipe = RECIPES[intent.recipeId];
  return `<article class="intent-card"><div><strong>${esc(intent.title)}</strong>${recipe ? `<a class="recipe-link" href="../recipes/${esc(recipe.id)}.html">Ouvrir la recette ↗</a>` : `<span class="badge">Idée libre</span>`}</div><div class="intent-controls"><label>Date <input type="date" data-date="${esc(intent.id)}" value="${esc(intent.date || "")}"></label><label>Horizon <select data-horizon="${esc(intent.id)}"><option value="" ${!intent.horizon ? "selected" : ""}>Sans date</option><option value="this_week" ${intent.horizon === "this_week" ? "selected" : ""}>Cette semaine</option></select></label><label>Moment <select data-moment="${esc(intent.id)}"><option value="">Quand ?</option>${["lunch","dinner"].map(v => `<option value="${v}" ${intent.moment === v ? "selected" : ""}>${v === "lunch" ? "Déjeuner" : "Dîner"}</option>`).join("")}</select></label><label>Portions <input type="number" min="1" data-portions="${esc(intent.id)}" value="${esc(intent.portions || "")}" placeholder="recette"></label><button class="btn-small danger" data-remove="${esc(intent.id)}">Retirer</button></div></article>`;
}
function renderIntentions() {
  document.getElementById("intentions-count").textContent = `${state.intentions.length} intention${state.intentions.length > 1 ? "s" : ""}`;
  document.getElementById("intentions-list").innerHTML = state.intentions.length ? state.intentions.map(intentionEditor).join("") : `<p class="empty-state">Votre liste est vide. Commencez par une recette ou une idée libre.</p>`;
  document.querySelectorAll("[data-date]").forEach(input => input.addEventListener("change", () => mutate(input.dataset.date, { date: input.value || null })));
  document.querySelectorAll("[data-moment]").forEach(input => input.addEventListener("change", () => mutate(input.dataset.moment, { moment: input.value || null })));
  document.querySelectorAll("[data-horizon]").forEach(input => input.addEventListener("change", () => mutate(input.dataset.horizon, { horizon: input.value || null })));
  document.querySelectorAll("[data-portions]").forEach(input => input.addEventListener("change", () => mutate(input.dataset.portions, { portions: input.value || null })));
  document.querySelectorAll("[data-remove]").forEach(button => button.addEventListener("click", () => { state.intentions = removeIntention(state.intentions, button.dataset.remove); selectedIds.delete(button.dataset.remove); save(); render(); }));
}
function mutate(id, changes) { state.intentions = updateIntention(state.intentions, id, changes); save(); render(); }
function renderWeek() {
  const dated = projectWeek(state.intentions).sort((a, b) => a.date.localeCompare(b.date));
  document.getElementById("week-projection").innerHTML = dated.length ? dated.map(intent => `<article class="week-day-card"><div><strong>${esc(intent.date)}</strong><span>${esc(intent.moment || "Moment libre")}</span></div><p>${esc(intent.title)}</p><button class="btn-small" data-clear-date="${esc(intent.id)}">Retirer de la semaine</button></article>`).join("") : `<p class="empty-state">Aucune intention datée : votre semaine reste ouverte.</p>`;
  document.getElementById("undated-intentions").innerHTML = state.intentions.filter(i => !i.date).map(i => `<span class="badge">${esc(i.title)}</span>`).join(" ") || "";
  document.querySelectorAll("[data-clear-date]").forEach(button => button.addEventListener("click", () => mutate(button.dataset.clearDate, { date: null })));
}
function selectedIngredients() {
  const names = new Map();
  for (const intent of state.intentions.filter(i => selectedIds.has(i.id))) for (const ingredient of RECIPES[intent.recipeId]?.ingredients || []) names.set(ingredient.name.toLowerCase(), ingredient);
  return names;
}
function factRow(ingredient) {
  const key = ingredient.name.toLowerCase();
  const fact = state.kitchenFacts[key] || {};
  return `<div class="kitchen-fact"><strong>${esc(ingredient.name)}</strong><select data-fact-status="${esc(key)}"><option value="unknown" ${!fact.status ? "selected" : ""}>Je ne sais pas</option><option value="absent" ${fact.status === "absent" ? "selected" : ""}>Je ne l’ai pas</option><option value="present" ${fact.status === "present" ? "selected" : ""}>Je pense l’avoir</option></select><input data-fact-qty="${esc(key)}" placeholder="quantité exacte (optionnel)" value="${esc(fact.quantity || "")}"><select data-fact-certainty="${esc(key)}"><option value="unknown" ${!fact.certainty || fact.certainty === "unknown" ? "selected" : ""}>inconnue</option><option value="approximate" ${fact.certainty === "approximate" ? "selected" : ""}>approximative</option><option value="exact" ${fact.certainty === "exact" ? "selected" : ""}>exacte</option></select></div>`;
}
function resultList(title, items) {
  const rows = items.map(item => `<li><strong>${esc(item.name)}</strong> — ${esc(item.qty)}${item.reason ? ` <span class="badge">${esc(item.reason)}</span>` : ""}</li>`).join("");
  return `<div class="shopping-result"><h3>${title}</h3>${rows ? `<ul>${rows}</ul>` : `<p class="empty-state">Rien pour l’instant.</p>`}</div>`;
}
function renderShopping() {
  document.getElementById("shopping-selection").innerHTML = `<h3>Intentions pour cette course</h3>${state.intentions.map(i => `<label class="shopping-intent"><input type="checkbox" data-select="${esc(i.id)}" ${selectedIds.has(i.id) ? "checked" : ""}> ${esc(i.title)}</label>`).join("") || `<p class="empty-state">Ajoutez d’abord une intention.</p>`}`;
  document.querySelectorAll("[data-select]").forEach(input => input.addEventListener("change", () => { input.checked ? selectedIds.add(input.dataset.select) : selectedIds.delete(input.dataset.select); renderShopping(); }));
  const ingredients = selectedIngredients();
  const factRows = [...ingredients.values()].map(factRow).join("");
  document.getElementById("kitchen-facts").innerHTML = `<h3>J’ai… <small>(déclaratif, jamais un inventaire)</small></h3>${factRows || `<p class="empty-state">Sélectionnez une intention avec recette pour déclarer ce que vous avez.</p>`}`;
  document.querySelectorAll("[data-fact-status],[data-fact-qty],[data-fact-certainty]").forEach(input => input.addEventListener("change", () => { const key = input.dataset.factStatus || input.dataset.factQty || input.dataset.factCertainty; const fact = state.kitchenFacts[key] || {}; if (input.dataset.factStatus) fact.status = input.value; if (input.dataset.factQty) fact.quantity = input.value; if (input.dataset.factCertainty) fact.certainty = input.value; state.kitchenFacts[key] = fact; save(); renderShopping(); }));
  const assessment = buildShoppingAssessment(state.intentions, RECIPES, state.kitchenFacts, [...selectedIds]);
  document.getElementById("shopping-result").innerHTML = resultList("À acheter", assessment.toBuy) + resultList("À vérifier", assessment.toVerify) + resultList("Déjà couvert", assessment.covered);
}
function show(view) { document.querySelectorAll(".step-tab").forEach(t => t.classList.toggle("active", t.dataset.view === view)); document.querySelectorAll(".step-view").forEach(v => v.classList.toggle("active", v.id === `view-${view}`)); }
function render() { renderIntentions(); renderWeek(); renderShopping(); }
load();
document.getElementById("recipe-search").addEventListener("input", e => renderRecipes(e.target.value));
document.getElementById("btn-add-free").addEventListener("click", () => { const title = prompt("Quelle idée de repas garder ?"); if (!title?.trim()) return; state.intentions = addIntention(state.intentions, createMealIntention({ type: "free", title })); save(); render(); });
document.querySelectorAll("[data-view]").forEach(tab => tab.addEventListener("click", () => show(tab.dataset.view)));
document.getElementById("btn-reset-plan").addEventListener("click", () => { if (confirm("Effacer les intentions de ce Planner ?")) { state = { intentions: [], kitchenFacts: {} }; selectedIds.clear(); save(); render(); } });
renderRecipes(); render();
