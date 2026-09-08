import { addPlacement, loadPlanning, MOMENTS, removePlacement, savePlanning } from "./planner-state.js";
import { buildCalendarExport } from "./calendar-export.js";

const SELECTION_KEY = "cookigram:recipe-selection";
const WEEK_KEY = "cookigram:meal-planning-week:v1";
const focusSlug = new URLSearchParams(window.location.search).get("recipe");
const DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"];
const esc = value => String(value ?? "").replace(/[&<>\"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c]));
const readSelection = () => { try { const value = JSON.parse(localStorage.getItem(SELECTION_KEY) || "[]"); return Array.isArray(value) ? value.filter(item => item?.slug) : []; } catch { return []; } };
const writeSelection = value => localStorage.setItem(SELECTION_KEY, JSON.stringify(value));
const monday = value => { const date = new Date(value); const day = date.getDay() || 7; date.setHours(12, 0, 0, 0); date.setDate(date.getDate() - day + 1); return date; };
const iso = date => date.toISOString().slice(0, 10);
const readWeek = () => { const stored = localStorage.getItem(WEEK_KEY); return stored ? monday(stored) : monday(new Date()); };
const formatRange = dates => `${dates[0].toLocaleDateString("fr-FR", { day: "numeric", month: "long" })} – ${dates[6].toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" })}`;
let selection = readSelection();
let planning = loadPlanning();
let weekStart = readWeek();
let dialogSlot = null;
let lastBulkRemoval = null;
let feedbackTimer = null;

const dates = () => Array.from({ length: 7 }, (_, index) => { const date = new Date(weekStart); date.setDate(weekStart.getDate() + index); return iso(date); });
const dayLabel = index => { const date = new Date(`${dates()[index]}T12:00:00`); return { day: DAYS[index], date: date.toLocaleDateString("fr-FR", { day: "numeric", month: "short" }) }; };
const isCurrentWeek = () => iso(weekStart) === iso(monday(new Date()));
const persist = () => { savePlanning(planning); localStorage.setItem(WEEK_KEY, iso(weekStart)); };
const unplanned = () => selection.filter(item => !planning[item.slug]?.date);
const place = (slug, date, moment) => { if (!slug || !date || !moment) return; planning = addPlacement(planning, slug, date, moment); persist(); render(); };
const removeFromSelection = slug => { selection = selection.filter(item => item.slug !== slug); writeSelection(selection); planning = removePlacement(planning, slug); persist(); render(); };
const openSlotDialog = (date, moment) => {
  const candidates = unplanned();
  if (!candidates.length) return;
  dialogSlot = { date, moment };
  const select = document.querySelector("#planner-slot-recipe");
  select.innerHTML = candidates.map(item => `<option value="${esc(item.slug)}">${esc(item.title || item.slug)}</option>`).join("");
  const dialog = document.querySelector("#planner-slot-dialog");
  if (typeof dialog.showModal === "function") dialog.showModal(); else if (window.confirm("Placer la première recette non planifiée dans ce créneau ?")) place(candidates[0].slug, date, moment);
};
const renderRecipe = (item, placed) => {
  return `<article class="planner-recipe" draggable="true" data-planner-recipe="${esc(item.slug)}">
    <span class="planner-drag-handle" aria-hidden="true">⠿</span><a href="../recipes/${encodeURIComponent(item.slug)}/">${esc(item.title || item.slug)}</a>
    <div class="planner-recipe-actions">
      ${placed ? `<button type="button" class="btn" data-unplan="${esc(item.slug)}">Retirer du planning</button>` : `<label class="sr-only" for="place-${esc(item.slug)}">Créneau pour ${esc(item.title || item.slug)}</label><select id="place-${esc(item.slug)}" data-assign="${esc(item.slug)}"><option value="">Placer dans…</option>${dates().flatMap((date, index) => MOMENTS.map(moment => `<option value="${date}|${moment}">${DAYS[index]} · ${moment}</option>`)).join("")}</select>`}
      <button type="button" class="btn danger" data-remove-selection="${esc(item.slug)}">Retirer de Ma sélection</button>
    </div>
  </article>`;
};
const renderPlacedRecipe = item => `<article class="planner-recipe planner-recipe-placed" draggable="true" data-planner-recipe="${esc(item.slug)}">
  <span class="planner-drag-handle" aria-hidden="true">⠿</span><a href="../recipes/${encodeURIComponent(item.slug)}/">${esc(item.title || item.slug)}</a>
  <details class="planner-recipe-menu"><summary aria-label="Actions pour ${esc(item.title || item.slug)}">…</summary><div class="planner-recipe-menu-items"><button type="button" class="btn" data-unplan="${esc(item.slug)}">Retirer du planning</button><button type="button" class="btn danger" data-remove-selection="${esc(item.slug)}">Retirer de Ma sélection</button></div></details>
</article>`;
const renderSlot = (date, moment) => {
  const items = selection.filter(item => planning[item.slug]?.date === date && planning[item.slug]?.moment === moment);
  return `<div class="planner-slot" data-slot-date="${date}" data-slot-moment="${moment}" tabindex="0" role="region" aria-label="${moment} du ${date}">
    <div class="planner-slot-heading"><span>${moment}</span><button type="button" class="slot-add" data-slot-add="${date}|${moment}" aria-label="Ajouter une recette au créneau ${moment}">+</button></div>
    <div class="planner-slot-items">${items.length ? items.map(renderPlacedRecipe).join("") : `<span class="planner-slot-empty">Déposer ici</span>`}</div>
  </div>`;
};
const render = () => {
  selection = readSelection();
  const datesForWeek = dates();
  document.querySelector("#planner-empty").hidden = selection.length > 0;
  document.querySelector("#planner-content").hidden = selection.length === 0;
  document.querySelector("#planner-week-title").textContent = `${isCurrentWeek() ? "Cette semaine · " : ""}${formatRange(datesForWeek.map(date => new Date(`${date}T12:00:00`)))}`;
  const pending = unplanned();
  document.querySelector("#planner-selection").innerHTML = pending.map(item => renderRecipe(item, false)).join("");
  document.querySelector("#planner-selection-empty").hidden = pending.length > 0;
  const removeButton = document.querySelector("[data-remove-unplanned]");
  removeButton.hidden = pending.length === 0;
  removeButton.textContent = `Retirer les ${pending.length} non planifiées`;
  const today = iso(new Date());
  document.querySelector("#planner-week").innerHTML = datesForWeek.map((date, index) => { const label = dayLabel(index); return `<section class="planner-day${date === today ? " planner-day-current" : ""}" aria-labelledby="day-${date}"><h3 id="day-${date}"><span class="planner-day-name">${label.day}</span><span class="planner-day-date">${label.date}</span>${date === today ? "<span class=\"planner-today\">Aujourd’hui</span>" : ""}</h3>${MOMENTS.map(moment => renderSlot(date, moment)).join("")}</section>`; }).join("");
  bindEvents();
  if (focusSlug) document.querySelector(`[data-planner-recipe="${CSS.escape(focusSlug)}"]`)?.scrollIntoView({ block: "center" });
};
const bindEvents = () => {
  document.querySelectorAll("[data-assign]").forEach(select => select.addEventListener("change", event => { const [date, moment] = event.target.value.split("|"); if (date && moment) place(event.target.dataset.assign, date, moment); }));
  document.querySelectorAll("[data-unplan]").forEach(button => button.addEventListener("click", () => { planning = removePlacement(planning, button.dataset.unplan); persist(); render(); }));
  document.querySelectorAll("[data-remove-selection]").forEach(button => button.addEventListener("click", () => removeFromSelection(button.dataset.removeSelection)));
  document.querySelectorAll("[data-slot-add]").forEach(button => button.addEventListener("click", () => { const [date, moment] = button.dataset.slotAdd.split("|"); openSlotDialog(date, moment); }));
  document.querySelectorAll("[data-planner-recipe]").forEach(card => {
    card.addEventListener("dragstart", event => { event.dataTransfer.setData("text/plain", card.dataset.plannerRecipe); event.dataTransfer.effectAllowed = "move"; card.classList.add("planner-recipe-dragging"); });
    card.addEventListener("dragend", () => card.classList.remove("planner-recipe-dragging"));
  });
  document.querySelectorAll("[data-slot-date]").forEach(slot => {
    slot.addEventListener("dragover", event => { event.preventDefault(); slot.classList.add("planner-slot-over"); });
    slot.addEventListener("dragleave", () => slot.classList.remove("planner-slot-over"));
    slot.addEventListener("drop", event => { event.preventDefault(); slot.classList.remove("planner-slot-over"); place(event.dataTransfer.getData("text/plain"), slot.dataset.slotDate, slot.dataset.slotMoment); });
    slot.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); openSlotDialog(slot.dataset.slotDate, slot.dataset.slotMoment); } });
  });
  removeButtonHandler();
};
const showFeedback = (message, undo) => { const feedback = document.querySelector("#planner-feedback"); const messageNode = document.querySelector("#planner-feedback-message"); const undoButton = document.querySelector("[data-undo-removal]"); clearTimeout(feedbackTimer); messageNode.textContent = message; undoButton.hidden = !undo; feedback.hidden = false; feedbackTimer = window.setTimeout(() => { feedback.hidden = true; lastBulkRemoval = null; }, 8000); };
const removeButtonHandler = () => {
  document.querySelector("[data-remove-unplanned]").onclick = () => {
    const pending = unplanned(); const count = pending.length;
    if (!count || !window.confirm(`Retirer les ${count} recettes non planifiées de Ma sélection ?`)) return;
    lastBulkRemoval = { selection: [...selection] };
    const plannedSlugs = new Set(selection.filter(item => planning[item.slug]?.date).map(item => item.slug));
    selection = selection.filter(item => plannedSlugs.has(item.slug)); writeSelection(selection); persist(); render(); showFeedback(`${count} recettes retirées de Ma sélection.`, true);
  };
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
    showFeedback("La photo de cette semaine a été exportée.", false);
  } catch (error) {
    showFeedback(error.message, false);
  }
};
document.querySelector("[data-undo-removal]").addEventListener("click", () => { if (!lastBulkRemoval) return; selection = lastBulkRemoval.selection; writeSelection(selection); render(); showFeedback("Les recettes retirées ont été restaurées.", false); lastBulkRemoval = null; });
document.querySelector("[data-export-calendar]").addEventListener("click", exportCalendar);
document.querySelector("[data-week-prev]").addEventListener("click", () => { weekStart.setDate(weekStart.getDate() - 7); persist(); render(); });
document.querySelector("[data-week-next]").addEventListener("click", () => { weekStart.setDate(weekStart.getDate() + 7); persist(); render(); });
document.querySelector("[data-week-today]").addEventListener("click", () => { weekStart = monday(new Date()); persist(); render(); });
document.querySelector("#planner-slot-dialog").addEventListener("close", event => { if (event.target.returnValue === "place" && dialogSlot) { place(document.querySelector("#planner-slot-recipe").value, dialogSlot.date, dialogSlot.moment); } dialogSlot = null; });
render();
