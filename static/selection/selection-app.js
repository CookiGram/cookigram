import { getRecipeSelection, toggleRecipeSelection } from "../assets/js/modules/recipe-selection.js";
const list = document.querySelector("[data-selection-list]");
const empty = document.querySelector("[data-selection-empty]");
const render = () => {
  const items = getRecipeSelection();
  list.innerHTML = items.map(item => `<article class="selection-row"><a href="../recipes/${encodeURIComponent(item.slug)}/">${item.title || item.slug}</a><button type="button" class="selection-remove" data-remove="${item.slug}">Retirer</button></article>`).join("");
  empty.hidden = items.length > 0;
  list.querySelectorAll("[data-remove]").forEach(button => button.addEventListener("click", () => { toggleRecipeSelection(button.dataset.remove); render(); }));
};
render();
