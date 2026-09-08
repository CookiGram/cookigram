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
};
render();
