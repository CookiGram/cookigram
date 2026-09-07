/** Intent-first deterministic Meal Planner operations. */
export const MOMENTS = ["breakfast", "lunch", "dinner", "snack"];

export function normalizePortions(value, fallback = 2) {
  const portions = Number(value);
  return Number.isInteger(portions) && portions > 0 ? portions : fallback;
}

export function createMealIntention(input = {}) {
  const title = String(input.title ?? "").trim();
  if (!title) throw new TypeError("Une intention doit avoir un titre");
  return {
    id: input.id ?? `intent-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    type: input.type === "free" ? "free" : "recipe",
    recipeId: input.recipeId ?? null,
    title,
    date: input.date || null,
    horizon: input.horizon || null,
    moment: MOMENTS.includes(input.moment) ? input.moment : null,
    portions: input.portions == null ? null : normalizePortions(input.portions),
    note: String(input.note ?? "").trim()
  };
}

export function addIntention(intentions, input) { return [...intentions, createMealIntention(input)]; }
export function updateIntention(intentions, id, changes) {
  return intentions.map(intent => intent.id === id ? createMealIntention({ ...intent, ...changes, id }) : intent);
}
export function removeIntention(intentions, id) { return intentions.filter(intent => intent.id !== id); }
export function projectWeek(intentions) { return intentions.filter(intent => Boolean(intent.date)); }
export function selectIntentions(intentions, ids) {
  const selected = new Set(ids);
  return intentions.filter(intent => selected.has(intent.id));
}

function parseQuantity(value) {
  const match = String(value ?? "").trim().match(/^([0-9]+(?:[.,][0-9]+)?|[0-9]+\/[0-9]+)\s*(.*)$/);
  if (!match) return null;
  const amount = match[1].includes("/")
    ? match[1].split("/").map(Number).reduce((a, b) => a / b)
    : Number(match[1].replace(",", "."));
  return Number.isFinite(amount) ? { amount, unit: match[2].trim().toLowerCase() } : null;
}
function formatQuantity(amount, unit) {
  const value = Number.isInteger(amount) ? String(amount) : amount.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
  return `${value} ${unit}`.trim();
}
function assess(ingredient, fact) {
  if (!fact || fact.certainty === "unknown") return "verify";
  if (fact.status === "absent") return "buy";
  if (fact.status !== "present") return "verify";
  if (fact.certainty !== "exact" || !fact.quantity) return "verify";
  const required = parseQuantity(ingredient.qty);
  const available = parseQuantity(fact.quantity);
  if (!required || !available || required.unit !== available.unit) return "verify";
  if (available.amount >= required.amount) return "covered";
  return { kind: "buy", qty: formatQuantity(required.amount - available.amount, required.unit) };
}

/** Selected intentions only; unknown or non-scalable requirements are never invented. */
export function buildShoppingAssessment(intentions, recipes, kitchenFacts = {}, selectedIds = []) {
  const groups = new Map();
  for (const intent of selectIntentions(intentions, selectedIds)) {
    const recipe = intent.type === "recipe" ? recipes[intent.recipeId] : null;
    if (!recipe?.ingredients) continue;
    const baseline = normalizePortions(recipe.portions ?? 2);
    const requested = intent.portions == null ? baseline : normalizePortions(intent.portions);
    for (const ingredient of recipe.ingredients) {
      const key = ingredient.name.trim().toLowerCase();
      const parsed = parseQuantity(ingredient.qty);
      const groupKey = `${key}|${parsed?.unit ?? ingredient.qty}`;
      const item = groups.get(groupKey);
      if (item) { item.assessment = "verify"; continue; }
      const assessment = requested === baseline ? assess(ingredient, kitchenFacts[key]) : "verify";
      groups.set(groupKey, { name: ingredient.name, aisle: ingredient.aisle || "À vérifier", qty: ingredient.qty, intentId: intent.id, assessment });
    }
  }
  const result = { toBuy: [], toVerify: [], covered: [] };
  for (const item of groups.values()) {
    if (item.assessment === "covered") result.covered.push(item);
    else if (item.assessment === "verify") result.toVerify.push({ ...item, reason: "Quantité, unité ou portion à vérifier" });
    else result.toBuy.push({ ...item, qty: typeof item.assessment === "object" ? item.assessment.qty : item.qty });
  }
  return result;
}

// Kept only so the historical module can be parsed by older cached pages; the
// production page no longer uses the slot-based operations below.
export function recipeMeal(recipeId, portions = 2, icon = "🍳") { return { type: "recipe", recipeId, portions: normalizePortions(portions), icon }; }
export function setMeal(plan, dayIndex, period, meal) { if (!plan[dayIndex]) throw new RangeError("Créneau invalide"); plan[dayIndex][period] = meal; }
export function removeMeal(plan, dayIndex, period) { setMeal(plan, dayIndex, period, null); }
export function moveMeal(plan, fromDay, fromPeriod, toDay, toPeriod) {
  const source = plan[fromDay]?.[fromPeriod];
  plan[fromDay][fromPeriod] = plan[toDay][toPeriod];
  plan[toDay][toPeriod] = source;
}
export function getCurrentDinner(plan) { return plan.find(day => day?.isToday)?.dinner ?? plan[0]?.dinner ?? null; }
