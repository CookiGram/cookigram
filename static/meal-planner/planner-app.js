import { addPlacement, loadPlanning, MOMENTS, removePlacement, savePlanning } from "./planner-state.js";
import { buildCalendarExport } from "./calendar-export.js";

const SELECTION_KEY = "cookigram:recipe-selection";
const WEEK_KEY = "cookigram:meal-planning-week:v1";
const focusSlug = new URLSearchParams(window.location.search).get("recipe");
const DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"];
const esc = value => String(value ?? "").replace(/[&<>\"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c]));
const readSelection = () => { try { const value = JSON.parse(localStorage.getItem(SELECTION_KEY) || "[]"); return Array.isArray(value) ? value.filter(item => item?.slug) : []; } catch { return []; } };
const monday = value => { const date = new Date(value); const day = date.getDay() || 7; date.setHours(12, 0, 0, 0); date.setDate(date.getDate() - day + 1); return date; };
const iso = date => date.toISOString().slice(0, 10);
const readWeek = () => { const stored = localStorage.getItem(WEEK_KEY); return stored ? monday(stored) : monday(new Date()); };
const formatRange = dates => `${dates[0].toLocaleDateString("fr-FR", { day: "numeric", month: "long" })} – ${dates[6].toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" })}`;

let selection = readSelection();
let planning = loadPlanning();
let weekStart = readWeek();
let catalog = new Map();
let selectedSlug = null;
let draggingSlug = null;
let ignoreClickSlug = null;
let feedbackTimer = null;

const dates = () => Array.from({ length: 7 }, (_, index) => { const date = new Date(weekStart); date.setDate(weekStart.getDate() + index); return iso(date); });
const dayLabel = index => { const date = new Date(`${dates()[index]}T12:00:00`); return { day: DAYS[index], date: date.toLocaleDateString("fr-FR", { day: "numeric", month: "short" }) }; };
const persist = () => { savePlanning(planning); localStorage.setItem(WEEK_KEY, iso(weekStart)); };
const unplanned = () => selection.filter(item => !planning[item.slug]?.date);
const recipeFor = item => catalog.get(item.slug) || item;
const recipeTitle = item => recipeFor(item).title || item.title || item.slug;
const itemForSlug = slug => selection.find(item => item.slug === slug) || { slug };
const slotItems = (date, moment) => selection.filter(item => planning[item.slug]?.date === date && planning[item.slug]?.moment === moment).sort((a, b) => (planning[a.slug]?.order ?? selection.indexOf(a)) - (planning[b.slug]?.order ?? selection.indexOf(b)));
const recipeImage = item => {
  const image = recipeFor(item).image;
  return image ? `<img src="../assets/${esc(image)}" alt="" loading="lazy">` : `<span aria-hidden="true">${esc(recipeTitle(item).slice(0, 2).toUpperCase())}</span>`;
};
const place = (slug, date, moment) => {
  if (!slug || !date || !moment) return;
  const order = slotItems(date, moment).length;
  planning = addPlacement(planning, slug, date, moment);
  planning[slug].order = order;
  if (selectedSlug === slug) selectedSlug = null;
  persist();
  render();
};
const unplan = slug => {
  planning = removePlacement(planning, slug);
  persist();
  render();
};
const removeFromSelection = slug => {
  const next = readSelection().filter(item => item.slug !== slug);
  localStorage.setItem(SELECTION_KEY, JSON.stringify(next));
  if (selectedSlug === slug) selectedSlug = null;
  document.dispatchEvent(new CustomEvent("cookigram:selection-change"));
  render();
};
const reorder = (slug, direction) => {
  const placement = planning[slug];
  if (!placement?.date || !placement?.moment) return;
  const items = slotItems(placement.date, placement.moment);
  const index = items.findIndex(item => item.slug === slug);
  const target = index + direction;
  if (index < 0 || target < 0 || target >= items.length) return;
  const next = { ...planning };
  const first = items[index].slug;
  const second = items[target].slug;
  const firstOrder = next[first].order ?? index;
  next[first] = { ...next[first], order: next[second].order ?? target };
  next[second] = { ...next[second], order: firstOrder };
  planning = next;
  persist();
  render();
};
const selectForPlacement = slug => {
  if (!unplanned().some(item => item.slug === slug)) return;
  selectedSlug = slug;
  render();
};

const renderUnplannedRecipe = item => {
  const active = item.slug === selectedSlug;
  const title = recipeTitle(item);
  return `<article class="planner-recipe planner-recipe-unplaced${active ? " planner-recipe-selected" : ""}" draggable="true" tabindex="0" role="button" aria-pressed="${active}" aria-label="Sélectionner ${esc(title)} pour le placement" title="${esc(title)}" data-planner-recipe="${esc(item.slug)}" data-select-planner="${esc(item.slug)}">
    <span class="planner-recipe-thumb" aria-hidden="true">${recipeImage(item)}</span>
    <span class="planner-recipe-title">${esc(title)}</span>
    <button type="button" class="planner-selection-remove" data-remove-selection="${esc(item.slug)}" aria-label="Retirer ${esc(title)} de Ma sélection" title="Retirer de Ma sélection">×</button>
  </article>`;
};

const renderPlacedRecipe = item => {
  const title = recipeTitle(item);
  const placement = planning[item.slug];
  const peers = slotItems(placement.date, placement.moment);
  const index = peers.findIndex(peer => peer.slug === item.slug);
  return `<article class="planner-recipe planner-recipe-placed" draggable="true" tabindex="0" aria-label="${esc(title)}" title="${esc(title)}" data-planner-recipe="${esc(item.slug)}">
    <span class="planner-recipe-thumb" aria-hidden="true">${recipeImage(item)}</span>
    <span class="planner-recipe-overlay" aria-hidden="true"><strong>${esc(title)}</strong></span>
    <span class="planner-recipe-actions"><button type="button" class="planner-order" data-reorder="up" data-recipe="${esc(item.slug)}" aria-label="Monter ${esc(title)}" ${index === 0 ? "disabled" : ""}>↑</button><button type="button" class="planner-order" data-reorder="down" data-recipe="${esc(item.slug)}" aria-label="Descendre ${esc(title)}" ${index === peers.length - 1 ? "disabled" : ""}>↓</button><button type="button" class="planner-unplan" data-unplan="${esc(item.slug)}" aria-label="Remettre ${esc(title)} dans À placer" title="Remettre dans À placer">×</button></span>
  </article>`;
};

const renderSlot = (date, moment) => {
  const items = slotItems(date, moment);
  const selected = selectedSlug ? recipeTitle(itemForSlug(selectedSlug)) : null;
  const label = selected ? `Placer ${selected} dans ${moment} du ${date}` : `${moment} du ${date}. Sélectionnez une recette dans À placer pour la placer ici`;
  return `<div class="planner-slot${selectedSlug ? " planner-slot-ready" : ""}" data-slot-date="${date}" data-slot-moment="${moment}" tabindex="0" role="button" aria-label="${esc(label)}">
    <div class="planner-slot-heading"><span>${moment}</span></div>
    <div class="planner-slot-items">${items.length ? items.map(renderPlacedRecipe).join("") : `<span class="planner-slot-empty" aria-hidden="true"></span>`}</div>
  </div>`;
};

const render = () => {
  selection = readSelection();
  const pending = unplanned();
  if (selectedSlug && !pending.some(item => item.slug === selectedSlug)) selectedSlug = null;
  const datesForWeek = dates();
  document.querySelector("#planner-empty").hidden = selection.length > 0;
  document.querySelector("#planner-content").hidden = selection.length === 0;
  document.querySelector("#planner-week-title").textContent = formatRange(datesForWeek.map(date => new Date(`${date}T12:00:00`)));
  document.querySelector("#planner-selection").innerHTML = pending.map(renderUnplannedRecipe).join("");
  const unplacedPanel = document.querySelector(".planner-unplaced");
  unplacedPanel.hidden = pending.length === 0;
  document.querySelector("#planner-all-placed").hidden = pending.length > 0;
  document.querySelector(".planner-board-shell").classList.toggle("planner-board-shell-full", pending.length === 0);
  const today = iso(new Date());
  document.querySelector("#planner-week").innerHTML = datesForWeek.map((date, index) => {
    const label = dayLabel(index);
    return `<section class="planner-day${date === today ? " planner-day-current" : ""}" aria-labelledby="day-${date}"><h3 id="day-${date}"><span class="planner-day-name">${label.day}</span><span class="planner-day-date">${label.date}</span>${date === today ? "<span class=\"planner-today\">Aujourd’hui</span>" : ""}</h3>${MOMENTS.map(moment => renderSlot(date, moment)).join("")}</section>`;
  }).join("");
  bindEvents();
  if (focusSlug) document.querySelector(`[data-planner-recipe="${CSS.escape(focusSlug)}"]`)?.scrollIntoView({ block: "center" });
};

const activateUnplanned = card => {
  if (ignoreClickSlug === card.dataset.selectPlanner) return;
  selectForPlacement(card.dataset.selectPlanner);
};
const activateSlot = slot => {
  if (!selectedSlug) return;
  place(selectedSlug, slot.dataset.slotDate, slot.dataset.slotMoment);
};

const bindEvents = () => {
  document.querySelectorAll("[data-select-planner]").forEach(card => {
    card.addEventListener("click", () => activateUnplanned(card));
    card.addEventListener("keydown", event => {
      if (event.target !== card) return;
      if (event.key === "Enter" || event.key === " ") { event.preventDefault(); activateUnplanned(card); }
    });
  });
  document.querySelectorAll("[data-remove-selection]").forEach(button => button.addEventListener("click", event => { event.preventDefault(); event.stopPropagation(); removeFromSelection(button.dataset.removeSelection); }));
  document.querySelectorAll("[data-unplan]").forEach(button => button.addEventListener("click", event => { event.stopPropagation(); unplan(button.dataset.unplan); }));
  document.querySelectorAll("[data-reorder]").forEach(button => button.addEventListener("click", event => { event.stopPropagation(); reorder(button.dataset.recipe, button.dataset.reorder === "up" ? -1 : 1); }));
  document.querySelectorAll("[data-planner-recipe]").forEach(card => {
    card.addEventListener("dragstart", event => {
      draggingSlug = card.dataset.plannerRecipe;
      event.dataTransfer.setData("text/plain", draggingSlug);
      event.dataTransfer.effectAllowed = "move";
      card.classList.add("planner-recipe-dragging");
    });
    card.addEventListener("dragend", () => {
      const slug = draggingSlug;
      draggingSlug = null;
      ignoreClickSlug = slug;
      card.classList.remove("planner-recipe-dragging");
      window.setTimeout(() => { if (ignoreClickSlug === slug) ignoreClickSlug = null; }, 0);
    });
  });
  document.querySelectorAll("[data-slot-date]").forEach(slot => {
    slot.addEventListener("click", event => {
      if (event.target.closest("[data-planner-recipe]")) return;
      activateSlot(slot);
    });
    slot.addEventListener("dragover", event => { event.preventDefault(); slot.classList.add("planner-slot-over"); });
    slot.addEventListener("dragleave", () => slot.classList.remove("planner-slot-over"));
    slot.addEventListener("drop", event => {
      event.preventDefault();
      slot.classList.remove("planner-slot-over");
      const slug = event.dataTransfer.getData("text/plain");
      place(slug, slot.dataset.slotDate, slot.dataset.slotMoment);
    });
    slot.addEventListener("keydown", event => {
      if (event.target !== slot) return;
      if ((event.key === "Enter" || event.key === " ") && selectedSlug) { event.preventDefault(); activateSlot(slot); }
    });
  });
};

const showFeedback = message => {
  const feedback = document.querySelector("#planner-feedback");
  const messageNode = document.querySelector("#planner-feedback-message");
  clearTimeout(feedbackTimer);
  messageNode.textContent = message;
  feedback.hidden = false;
  feedbackTimer = window.setTimeout(() => { feedback.hidden = true; }, 8000);
};
const exportCalendar = () => {
  const weekDates = dates();
  try {
    const content = buildCalendarExport({ placements: planning, selection, weekDates, baseUrl: new URL("../", window.location.href) });
    const blob = new Blob([content], { type: "text/calendar;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `cookigram-semaine-${weekDates[0]}.ics`;
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(link.href), 0);
    showFeedback("La photo de cette semaine a été exportée.");
  } catch (error) {
    showFeedback(error.message);
  }
};

document.querySelector("[data-export-calendar]").addEventListener("click", exportCalendar);
document.querySelector("[data-week-prev]").addEventListener("click", () => { weekStart.setDate(weekStart.getDate() - 7); persist(); render(); });
document.querySelector("[data-week-next]").addEventListener("click", () => { weekStart.setDate(weekStart.getDate() + 7); persist(); render(); });
document.querySelector("[data-week-today]").addEventListener("click", () => { weekStart = monday(new Date()); persist(); render(); });
fetch("../recipes.json").then(response => response.json()).then(data => { const recipes = Array.isArray(data) ? data : data.recipes || []; catalog = new Map(recipes.filter(recipe => recipe?.slug).map(recipe => [recipe.slug, recipe])); render(); }).catch(() => {});
render();
