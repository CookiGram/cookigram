import assert from "node:assert/strict";
import test from "node:test";

process.env.TZ = "Europe/Paris";

const RealDate = Date;
const SUNDAY = new RealDate(2026, 8, 20, 10, 0, 0);

const useMockDate = fixed => {
  class MockDate extends RealDate {
    constructor(...args) {
      super(...(args.length ? args : [fixed.getTime()]));
    }
    static now() {
      return fixed.getTime();
    }
  }
  globalThis.Date = MockDate;
};
const restoreDate = () => {
  globalThis.Date = RealDate;
};

const createStorage = (initial = {}) => {
  const store = new Map(Object.entries(initial));
  return {
    getItem: key => (store.has(key) ? store.get(key) : null),
    setItem: (key, value) => store.set(key, String(value)),
    removeItem: key => store.delete(key),
    clear: () => store.clear(),
  };
};

const setupDom = storage => {
  const elements = new Map();
  const element = () => ({
    hidden: false,
    textContent: "",
    innerHTML: "",
    dataset: {},
    classList: { toggle() {}, add() {}, remove() {}, contains: () => false },
    addEventListener: () => {},
    scrollIntoView: () => {},
  });
  const handlerMap = new Map();
  const button = selector => ({
    addEventListener: (type, fn) => handlerMap.set(selector, fn),
  });
  globalThis.window = {
    location: { search: "" },
    matchMedia: () => ({ matches: false }),
    setTimeout: () => 0,
    clearTimeout: () => {},
    addEventListener: (type, fn) => handlerMap.set(`window:${type}`, fn),
    localStorage: storage,
  };
  globalThis.localStorage = storage;
  globalThis.document = {
    hidden: false,
    querySelector: selector => {
      if (selector === "[data-export-calendar]" || selector === "[data-week-prev]" || selector === "[data-week-next]" || selector === "[data-week-today]") {
        if (!elements.has(selector)) elements.set(selector, button(selector));
        return elements.get(selector);
      }
      if (!elements.has(selector)) elements.set(selector, element());
      return elements.get(selector);
    },
    querySelectorAll: () => [],
    addEventListener: (type, fn) => handlerMap.set(`document:${type}`, fn),
    createElement: () => element(),
    dispatchEvent: () => true,
  };
  globalThis.CSS = { escape: value => String(value) };
  globalThis.fetch = async () => ({ json: async () => [] });
  return { elements, handlerMap };
};

const dayNames = html => [...html.matchAll(/<span class="planner-day-name">([^<]+)<\/span>/g)].map(match => match[1]);
const dayIds = html => [...html.matchAll(/id="day-([^"]+)"/g)].map(match => match[1]);

test("planner opens on a sliding today window even on a Sunday with a stale stored week", async () => {
  const storage = createStorage({ "cookigram:meal-planning-week:v1": "2026-09-14" });
  useMockDate(SUNDAY);
  const { elements, handlerMap } = setupDom(storage);
  try {
    await import("../static/meal-planner/planner-app.js");
    await new Promise(resolve => setImmediate(resolve));
    const html = elements.get("#planner-week").innerHTML;
    assert.deepEqual(dayNames(html), ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]);
    assert.deepEqual(dayIds(html)[0], "2026-09-20");
    assert.deepEqual(dayIds(html)[6], "2026-09-26");
    assert.match(html, /id="day-2026-09-20"/);
    assert.doesNotMatch(html, /2026-09-14/);
    assert.equal((html.match(/planner-today/g) || []).length, 1);

    const clickToday = handlerMap.get("[data-week-today]");
    const clickNext = handlerMap.get("[data-week-next]");
    assert.equal(typeof clickNext, "function");
    clickNext();
    const moved = dayIds(elements.get("#planner-week").innerHTML);
    assert.deepEqual(moved[0], "2026-09-27");
    assert.equal(typeof clickToday, "function");
    clickToday();
    const back = dayIds(elements.get("#planner-week").innerHTML);
    assert.deepEqual(back[0], "2026-09-20");
    assert.deepEqual(back[6], "2026-09-26");
  } finally {
    restoreDate();
    delete globalThis.window;
    delete globalThis.document;
    delete globalThis.localStorage;
    delete globalThis.CSS;
    delete globalThis.fetch;
  }
});
