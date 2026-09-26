import { addPlacement, loadPlanning, MOMENTS, removePlacement, savePlanning } from "./planner-state.js";
import { resolveInitialWeekStart, startOfLocalDay, toLocalISODate } from "./planner-state.js";
import { buildCalendarExport } from "./calendar-export.js";
import { formatPleasureShare, formatWeekCoverage, isNutritionProfile, NUTRITION_PROFILE_LABELS, summarizeWeekProfiles } from "./planner-nutrition.js";
import { summarizeDayNutrition } from "./planner-nutrition.js";

const SELECTION_KEY = "cookigram:recipe-selection";
const WEEK_KEY = "cookigram:meal-planning-week:v1";
const focusSlug = new URLSearchParams(window.location.search).get("recipe");
const DAYS_FROM_SUNDAY = ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"];
const esc = value => String(value ?? "").replace(/[&<>\"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c]));
const readSelection = () => { try { const value = JSON.parse(localStorage.getItem(SELECTION_KEY) || "[]"); return Array.isArray(value) ? value.filter(item => item?.slug) : []; } catch { return []; } };
const iso = date => toLocalISODate(date);
const formatRange = dates => `${dates[0].toLocaleDateString("fr-FR", { day: "numeric", month: "long" })} – ${dates[6].toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" })}`;

let selection = readSelection();
let planning = loadPlanning();
let weekStart = resolveInitialWeekStart();
let weekPinned = false;
let catalog = new Map();
let selectedSlug = null;
let ignoreClickSlug = null;
let feedbackTimer = null;

const nativeDragEnabled = () => !window.matchMedia("(pointer: coarse)").matches;
const draggableAttribute = () => nativeDragEnabled() ? ' draggable="true"' : '';

const dates = () => Array.from({ length: 7 }, (_, index) => { const date = new Date(weekStart); date.setDate(weekStart.getDate() + index); return iso(date); });
const dayLabel = index => { const date = new Date(`${dates()[index]}T12:00:00`); return { day: DAYS_FROM_SUNDAY[date.getDay()], date: date.toLocaleDateString("fr-FR", { day: "numeric", month: "short" }) }; };
const persist = () => { savePlanning(planning); localStorage.setItem(WEEK_KEY, iso(weekStart)); };
const refreshWindowForToday = () => {
  if (weekPinned) return false;
  const today = startOfLocalDay(new Date());
  if (iso(today) === iso(weekStart)) return false;
  weekStart = today;
  persist();
  return true;
};
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
const selectForPlacement = slug => {
  if (!unplanned().some(item => item.slug === slug)) return;
  selectedSlug = slug;
  render();
};

const renderUnplannedRecipe = item => {
  const active = item.slug === selectedSlug;
  const title = recipeTitle(item);
  return `<article class="planner-recipe planner-recipe-unplaced${active ? " planner-recipe-selected" : ""}"${draggableAttribute()} tabindex="0" role="button" aria-pressed="${active}" aria-label="Sélectionner ${esc(title)} pour le placement" title="${esc(title)}" data-planner-recipe="${esc(item.slug)}" data-select-planner="${esc(item.slug)}">
    <span class="planner-recipe-thumb" aria-hidden="true">${recipeImage(item)}</span>
    <span class="planner-recipe-title">${esc(title)}</span>
    <button type="button" class="planner-selection-remove" data-remove-selection="${esc(item.slug)}" aria-label="Retirer ${esc(title)} de Ma sélection" title="Retirer de Ma sélection">×</button>
  </article>`;
};

const renderPlacedRecipe = item => {
  const title = recipeTitle(item);
  return `<article class="planner-recipe planner-recipe-placed"${draggableAttribute()} tabindex="0" role="button" aria-label="Remettre ${esc(title)} dans À placer" title="${esc(title)} — cliquer pour remettre dans À placer" data-planner-recipe="${esc(item.slug)}" data-unplan-card="${esc(item.slug)}">
    <span class="planner-recipe-thumb" aria-hidden="true">${recipeImage(item)}</span>
    <span class="planner-recipe-overlay" aria-hidden="true"><strong>${esc(title)}</strong><span>↩ À placer</span></span>
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
const formatCalories = value => new Intl.NumberFormat("fr-FR").format(value);
const NUTRITION_FACET_HASH = profile => `#nutrition-${profile}`;
const plannedItemsForWeek = datesForWeek => datesForWeek.flatMap(date => MOMENTS.flatMap(moment => slotItems(date, moment)));
const EXPECTED_WEEK_MEALS = datesForWeek => datesForWeek.length * MOMENTS.length;
const renderWeekProfiles = datesForWeek => {
  const summary = summarizeWeekProfiles(plannedItemsForWeek(datesForWeek), recipeFor, EXPECTED_WEEK_MEALS(datesForWeek));
  const share = summary.pleasureShare === null
    ? "Aucun repas classé cette semaine."
    : `${formatPleasureShare(summary.pleasureShare)} · Repère : environ 20 % plaisir`;
  const rows = ["vitality", "balanced", "pleasure"].map(profile => {
    const label = NUTRITION_PROFILE_LABELS[profile];
    return `<li><a href="../${NUTRITION_FACET_HASH(profile)}" data-nutrition-week-filter="${profile}" aria-label="Choisir une recette ${label} pour la semaine" title="Choisir une recette ${label}"><span>${label}</span> <strong>${summary[profile]}</strong></a></li>`;
  }).join("");
  return `<section class="planner-panel planner-week-profiles" aria-labelledby="week-profiles-title"><h2 id="week-profiles-title">Repère nutrition de la semaine</h2><p class="nutrition-week-range">${esc(formatRange(datesForWeek.map(date => new Date(`${date}T12:00:00`))))}</p><ul class="nutrition-week-counts">${rows}</ul><p class="nutrition-week-share">${esc(share)}</p><p class="nutrition-week-coverage">${esc(formatWeekCoverage(summary.planned, summary.expected))}</p></section>`;
};
const renderDayNutrition = date => {
  const summary = summarizeDayNutrition(
    MOMENTS.map(moment => ({ moment, items: slotItems(date, moment) })),
    recipeFor,
  );
  if (!summary) return "";
  const details = summary.entries
    .map(entry => `<li><span>${esc(entry.moment)} · ${esc(entry.title)}</span><strong>${formatCalories(entry.calories)} kcal</strong></li>`)
    .join("");
  return `<details class="planner-day-nutrition"><summary aria-label="Environ ${formatCalories(summary.total)} kilocalories par portion">≈ ${formatCalories(summary.total)} kcal</summary><div class="planner-day-nutrition-detail"><span>Estimation par portion</span><ul>${details}</ul></div></details>`;
};

const render = () => {
  refreshWindowForToday();
  selection = readSelection();
  const pending = unplanned();
  if (selectedSlug && !pending.some(item => item.slug === selectedSlug)) selectedSlug = null;
  const datesForWeek = dates();
  document.querySelector("#planner-empty").hidden = selection.length > 0;
  document.querySelector("#planner-content").hidden = selection.length === 0;
  document.querySelector("#planner-week-title").textContent = formatRange(datesForWeek.map(date => new Date(`${date}T12:00:00`)));
  document.querySelector("#planner-week-profiles").innerHTML = renderWeekProfiles(datesForWeek);
  document.querySelector("#planner-selection").innerHTML = pending.map(renderUnplannedRecipe).join("");
  const unplacedPanel = document.querySelector(".planner-unplaced");
  unplacedPanel.hidden = pending.length === 0;
  document.querySelector("#planner-all-placed").hidden = pending.length > 0;
  document.querySelector(".planner-board-shell").classList.toggle("planner-board-shell-full", pending.length === 0);
  const today = iso(new Date());
  document.querySelector("#planner-week").innerHTML = datesForWeek.map((date, index) => {
    const label = dayLabel(index);
    return `<section class="planner-day${date === today ? " planner-day-current" : ""}" aria-labelledby="day-${date}"><h3 id="day-${date}"><span class="planner-day-name">${label.day}</span><span class="planner-day-date">${label.date}</span>${date === today ? "<span class=\"planner-today\">Aujourd’hui</span>" : ""}</h3>${MOMENTS.map(moment => renderSlot(date, moment)).join("")}${renderDayNutrition(date)}</section>`;
  }).join("");
  bindEvents();
  if (focusSlug) document.querySelector(`[data-planner-recipe="${CSS.escape(focusSlug)}"]`)?.scrollIntoView({ block: "center" });
};

const activateUnplanned = card => {
  if (ignoreClickSlug === card.dataset.selectPlanner) { ignoreClickSlug = null; return; }
  selectForPlacement(card.dataset.selectPlanner);
};
const activatePlaced = card => {
  if (ignoreClickSlug === card.dataset.unplanCard) { ignoreClickSlug = null; return; }
  unplan(card.dataset.unplanCard);
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
  document.querySelectorAll("[data-unplan-card]").forEach(card => {
    card.addEventListener("click", () => activatePlaced(card));
    card.addEventListener("keydown", event => {
      if (event.target !== card) return;
      if (event.key === "Enter" || event.key === " ") { event.preventDefault(); activatePlaced(card); }
    });
  });
  document.querySelectorAll("[data-planner-recipe]").forEach(card => {
    card.addEventListener("dragstart", event => {
      event.dataTransfer.setData("text/plain", card.dataset.plannerRecipe);
      event.dataTransfer.effectAllowed = "move";
      card.classList.add("planner-recipe-dragging");
    });
    card.addEventListener("dragend", () => {
      const slug = card.dataset.plannerRecipe;
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
document.querySelector("[data-week-prev]").addEventListener("click", () => { weekStart.setDate(weekStart.getDate() - 7); weekPinned = true; persist(); render(); });
document.querySelector("[data-week-next]").addEventListener("click", () => { weekStart.setDate(weekStart.getDate() + 7); weekPinned = true; persist(); render(); });
document.querySelector("[data-week-today]").addEventListener("click", () => { weekStart = resolveInitialWeekStart(); weekPinned = false; persist(); render(); });
document.addEventListener("visibilitychange", () => { if (!document.hidden && refreshWindowForToday()) render(); });
window.addEventListener("focus", () => { if (refreshWindowForToday()) render(); });
fetch("../recipes.json").then(response => response.json()).then(data => { const recipes = Array.isArray(data) ? data : data.recipes || []; catalog = new Map(recipes.filter(recipe => recipe?.slug).map(recipe => [recipe.slug, recipe])); render(); }).catch(() => {});
render();
