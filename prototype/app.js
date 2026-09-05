/**
 * CookiGram Kitchen OS — Prototype « Ma Semaine » v3
 * Nutrition Plaisir & Santé (80/20) + Vie Réelle + Semaine Dynamique Glissante + Persistance LocalStorage
 */

import { moveMeal, normalizePortions, recipeMeal, removeMeal, setMeal } from "./planner-state.js";

const STORAGE_KEY = "cookigram:meal-plan:v3";

// DATA: RECIPES CORPUS
const RECIPES = {
  "porc-au-caramel": {
    id: "porc-au-caramel",
    title: "Porc au caramel vietnamien",
    profile: "pleasure",
    timeTotal: "45 min",
    timeActive: "20 min",
    appliance: "Cocotte",
    requiredEquipment: ["stovetop"],
    dishes: "1 cocotte, 1 planche",
    category: "mijoté",
    description: "Échine fondante laquée au caramel ambré, gingembre frais et sauce nuoc-mâm.",
    plants: ["Gingembre", "Ail", "Oignon", "Poivre noir", "Coriandre"],
    ingredients: [
      { name: "Échine de porc", qty: "600 g", aisle: "Boucherie & Poissonnerie" },
      { name: "Gingembre frais", qty: "30 g", aisle: "Primeur" },
      { name: "Ail", qty: "3 gousses", aisle: "Primeur" },
      { name: "Oignon jaune", qty: "1 pièce", aisle: "Primeur" },
      { name: "Sucre roux", qty: "50 g", aisle: "Épicerie & Sec" },
      { name: "Sauce nuoc-mâm", qty: "30 ml", aisle: "Épicerie & Sec" },
      { name: "Riz jasmin", qty: "250 g", aisle: "Épicerie & Sec" }
    ]
  },
  "pommes-anna": {
    id: "pommes-anna",
    title: "Pommes Anna dorées au four",
    profile: "pleasure",
    timeTotal: "55 min",
    timeActive: "15 min",
    appliance: "Four",
    requiredEquipment: ["oven"],
    dishes: "1 poêle allant au four",
    category: "mijoté",
    description: "Lamelles croustillantes et cœur fondant au beurre noisette clarifié.",
    plants: ["Pomme de terre", "Thym", "Poivre"],
    ingredients: [
      { name: "Pommes de terre Charlotte", qty: "800 g", aisle: "Primeur" },
      { name: "Beurre doux", qty: "100 g", aisle: "Frais & Crèmerie" },
      { name: "Thym frais", qty: "2 branches", aisle: "Primeur" }
    ]
  },
  "barbacoa-boeuf-effiloche": {
    id: "barbacoa-boeuf-effiloche",
    title: "Barbacoa de bœuf effiloché",
    profile: "pleasure",
    timeTotal: "1 h 15 min",
    timeActive: "15 min",
    appliance: "Cocotte minute",
    requiredEquipment: ["pressure_cooker"],
    dishes: "1 cocotte",
    category: "monde",
    description: "Paleron confit et effiloché aux épices fumées, chipotle et jus de lime.",
    plants: ["Ail", "Oignon rouge", "Piment chipotle", "Cumin", "Origan", "Citron vert", "Coriandre"],
    ingredients: [
      { name: "Paleron de bœuf", qty: "800 g", aisle: "Boucherie & Poissonnerie" },
      { name: "Oignons rouges", qty: "2 pièces", aisle: "Primeur" },
      { name: "Ail", qty: "4 gousses", aisle: "Primeur" },
      { name: "Citrons verts", qty: "2 pièces", aisle: "Primeur" },
      { name: "Cumin moulu", qty: "1 c.à.c", aisle: "Épicerie & Sec" },
      { name: "Tortillas de maïs", qty: "8 pièces", aisle: "Épicerie & Sec" }
    ]
  },
  "tantanmen-ramen-epice": {
    id: "tantanmen-ramen-epice",
    title: "Tantanmen ramen épicé au sésame",
    profile: "pleasure",
    timeTotal: "35 min",
    timeActive: "20 min",
    appliance: "Casserole & Poêle",
    requiredEquipment: ["stovetop"],
    dishes: "1 casserole, 1 poêle",
    category: "monde",
    description: "Bouillon crémeux au sésame blanc grillé, porc haché sauté au piment doux.",
    plants: ["Sésame blanc", "Ail", "Gingembre", "Cébette", "Chou pak choï", "Piment"],
    ingredients: [
      { name: "Nouilles ramen fraîches", qty: "300 g", aisle: "Frais & Crèmerie" },
      { name: "Porc haché", qty: "300 g", aisle: "Boucherie & Poissonnerie" },
      { name: "Pâte de sésame (tahini)", qty: "4 c.à.s", aisle: "Épicerie & Sec" },
      { name: "Chou pak choï", qty: "2 pièces", aisle: "Primeur" },
      { name: "Cébettes", qty: "1 botte", aisle: "Primeur" }
    ]
  },
  "butter-chicken": {
    id: "butter-chicken",
    title: "Butter Chicken velouté",
    profile: "pleasure",
    timeTotal: "40 min",
    timeActive: "15 min",
    appliance: "Poêle haute",
    requiredEquipment: ["stovetop"],
    dishes: "1 sauteuse",
    category: "monde",
    description: "Poulet mariné au yaourt et sauce onctueuse tomate-fenugrec à la crème.",
    plants: ["Tomate", "Ail", "Gingembre", "Garam masala", "Fenugrec", "Coriandre"],
    ingredients: [
      { name: "Blancs de poulet", qty: "500 g", aisle: "Boucherie & Poissonnerie" },
      { name: "Coulis de tomate", qty: "400 g", aisle: "Épicerie & Sec" },
      { name: "Crème fraîche épaisse", qty: "150 ml", aisle: "Frais & Crèmerie" },
      { name: "Beurre doux", qty: "40 g", aisle: "Frais & Crèmerie" }
    ]
  },
  "brioche-butchy": {
    id: "brioche-butchy",
    title: "Brioche Butchy ultra moelleuse",
    profile: "pleasure",
    timeTotal: "45 min (+ pousse)",
    timeActive: "20 min",
    appliance: "Four",
    requiredEquipment: ["oven"],
    dishes: "1 moule à gâteau",
    category: "douceur",
    description: "Mie filante incomparable sans beurre, montée à la crème fraîche épaisse.",
    plants: ["Blé", "Vanille"],
    ingredients: [
      { name: "Farine T45", qty: "500 g", aisle: "Épicerie & Sec" },
      { name: "Crème fraîche épaisse", qty: "200 g", aisle: "Frais & Crèmerie" },
      { name: "Œufs bio", qty: "2 pièces", aisle: "Frais & Crèmerie" },
      { name: "Sucre blond", qty: "60 g", aisle: "Épicerie & Sec" }
    ]
  },
  "focaccia-thermomix": {
    id: "focaccia-thermomix",
    title: "Focaccia romarin & tomates cerises (Thermomix)",
    profile: "pleasure",
    timeTotal: "45 min (+ pousse)",
    timeActive: "10 min",
    appliance: "Thermomix & Four",
    requiredEquipment: ["thermomix", "oven"],
    dishes: "Bol Thermomix, 1 plaque four",
    category: "douceur",
    description: "Pâte pétrie au robot TM, dorée au four à l'huile d'olive et gros sel.",
    plants: ["Blé", "Romarin", "Tomates cerises", "Olive"],
    ingredients: [
      { name: "Farine T55", qty: "500 g", aisle: "Épicerie & Sec" },
      { name: "Levure boulangère", qty: "1 sachet", aisle: "Frais & Crèmerie" },
      { name: "Huile d'olive vierge extra", qty: "50 ml", aisle: "Épicerie & Sec" },
      { name: "Romarin frais", qty: "2 branches", aisle: "Primeur" }
    ]
  },

  // VITALITY (Semaine fraîche, digeste, riche en végétaux)
  "colin-alaska-tomate-estragon": {
    id: "colin-alaska-tomate-estragon",
    title: "Colin d'Alaska tomate & estragon",
    profile: "vitality",
    timeTotal: "20 min",
    timeActive: "10 min",
    appliance: "Poêle",
    requiredEquipment: ["stovetop"],
    dishes: "1 poêle, 1 planche",
    freshnessNote: "Poisson frais : à consommer sous 48h (J1-J2)",
    description: "Dos de colin nacré nappé d'une concassée minute de tomates et feuilles d'estragon.",
    plants: ["Tomate", "Estragon", "Ail", "Échalote", "Huile d'olive"],
    shortEveningAlternative: {
      title: "⚡ Colin express poêlé au citron & câpres",
      timeTotal: "12 min",
      timeActive: "5 min",
      note: "Saisie directe 4 min par face, déglacée au jus de citron frais. Même poisson, zéro vaisselle supplémentaire."
    },
    ingredients: [
      { name: "Dos de colin d'Alaska frais", qty: "400 g", aisle: "Boucherie & Poissonnerie" },
      { name: "Tomates mûres", qty: "4 pièces", aisle: "Primeur" },
      { name: "Estragon frais", qty: "1 petit bouquet", aisle: "Primeur" },
      { name: "Échalotes", qty: "2 pièces", aisle: "Primeur" },
      { name: "Ail", qty: "2 gousses", aisle: "Primeur" }
    ]
  },
  "salade-de-pois-chiches": {
    id: "salade-de-pois-chiches",
    title: "Salade croquante de pois chiches & herbes",
    profile: "vitality",
    timeTotal: "15 min",
    timeActive: "15 min",
    appliance: "Sans cuisson",
    requiredEquipment: ["stovetop"],
    dishes: "1 saladier",
    freshnessNote: "Végétaux croquants (J1-J3)",
    description: "Pois chiches rincés, concombre croquant, tomates cerises, persil plat et vinaigrette au citron.",
    plants: ["Pois chiches", "Concombre", "Tomates cerises", "Persil plat", "Citron", "Oignon rouge"],
    shortEveningAlternative: {
      title: "⚡ Salade minute pois chiches & feta",
      timeTotal: "8 min",
      timeActive: "8 min",
      note: "Assemblage direct en bol avec un filet d'huile d'olive et jus de citron. Prêt en 8 minutes chrono."
    },
    ingredients: [
      { name: "Pois chiches bio (bocal)", qty: "400 g", aisle: "Épicerie & Sec" },
      { name: "Concombre", qty: "1 pièce", aisle: "Primeur" },
      { name: "Tomates cerises", qty: "250 g", aisle: "Primeur" },
      { name: "Persil plat frais", qty: "1/2 botte", aisle: "Primeur" },
      { name: "Citron jaune bio", qty: "2 pièces", aisle: "Primeur" }
    ]
  },
  "dhal-lentilles-corail-coco": {
    id: "dhal-lentilles-corail-coco",
    title: "Dhal de lentilles corail & épinards coco",
    profile: "vitality",
    timeTotal: "25 min",
    timeActive: "10 min",
    appliance: "Casserole",
    requiredEquipment: ["stovetop"],
    dishes: "1 casserole",
    freshnessNote: "Légumineuse sèche & conservation longue",
    description: "Lentilles fondantes mijotées au curcuma, lait de coco léger et jeunes pousses d'épinards fraîches.",
    plants: ["Lentilles corail", "Épinards", "Curcuma", "Gingembre", "Ail", "Oignon", "Lait de coco", "Coriandre"],
    shortEveningAlternative: {
      title: "⚡ Dhal express aux lentilles précuites",
      timeTotal: "12 min",
      timeActive: "6 min",
      note: "Réchauffage des lentilles du batch-prep avec lait de coco et pousses d'épinards tombées à la minute."
    },
    ingredients: [
      { name: "Lentilles corail", qty: "250 g", aisle: "Épicerie & Sec" },
      { name: "Pousses d'épinards fraîches", qty: "200 g", aisle: "Primeur" },
      { name: "Lait de coco léger", qty: "200 ml", aisle: "Épicerie & Sec" },
      { name: "Gingembre frais", qty: "20 g", aisle: "Primeur" },
      { name: "Curcuma moulu", qty: "1 c.à.c", aisle: "Épicerie & Sec" }
    ]
  },
  "shakshuka-feta-oeufs": {
    id: "shakshuka-feta-oeufs",
    title: "Shakshuka aux poivrons, tomates & feta",
    profile: "vitality",
    timeTotal: "20 min",
    timeActive: "10 min",
    appliance: "Poêle avec couvercle",
    requiredEquipment: ["stovetop"],
    dishes: "1 poêle",
    freshnessNote: "Œufs bio & poivrons robustes (J4-J6)",
    description: "Fondue épicée de poivrons et tomates au cumin, œufs pochés au cœur coulant et feta émiettée.",
    plants: ["Poivron rouge", "Poivron jaune", "Tomate", "Oignon", "Ail", "Cumin", "Paprika", "Persil"],
    shortEveningAlternative: {
      title: "⚡ Shakshuka minute 15 min",
      timeTotal: "15 min",
      timeActive: "7 min",
      note: "Utilisation du couvercle pour pocher les œufs en 4 minutes à feu vif."
    },
    ingredients: [
      { name: "Poivrons (rouge et jaune)", qty: "2 pièces", aisle: "Primeur" },
      { name: "Tomates concassées", qty: "400 g", aisle: "Épicerie & Sec" },
      { name: "Œufs bio", qty: "4 pièces", aisle: "Frais & Crèmerie" },
      { name: "Feta AOP", qty: "100 g", aisle: "Frais & Crèmerie" },
      { name: "Cumin moulu", qty: "1 c.à.c", aisle: "Épicerie & Sec" }
    ]
  },
  "veloute-potiron-cannelle": {
    id: "veloute-potiron-cannelle",
    title: "Velouté de potiron, carottes & cannelle",
    profile: "vitality",
    timeTotal: "25 min",
    timeActive: "8 min",
    appliance: "Casserole ou Thermomix",
    requiredEquipment: ["stovetop"],
    dishes: "1 casserole ou bol robot",
    freshnessNote: "Légumes racines longue conservation (J6-J7)",
    description: "Soupe onctueuse et réconfortante, relevée d'une pointe de cannelle et de graines de courge grillées.",
    plants: ["Potiron / Butternut", "Carotte", "Oignon", "Cannelle", "Graines de courge"],
    shortEveningAlternative: {
      title: "⚡ Velouté express dés coupés fin",
      timeTotal: "16 min",
      timeActive: "6 min",
      note: "Découpe en petits dés de 1 cm pour une cuisson express en 10 minutes."
    },
    ingredients: [
      { name: "Courge butternut ou potiron", qty: "600 g", aisle: "Primeur" },
      { name: "Carottes", qty: "2 pièces", aisle: "Primeur" },
      { name: "Oignon jaune", qty: "1 pièce", aisle: "Primeur" },
      { name: "Cannelle moulue", qty: "1/2 c.à.c", aisle: "Épicerie & Sec" },
      { name: "Graines de courge", qty: "30 g", aisle: "Épicerie & Sec" }
    ]
  },

  // BALANCED (Équilibré complet, réconfortant)
  "blanquette-de-poulet": {
    id: "blanquette-de-poulet",
    title: "Blanquette de poulet aux champignons",
    profile: "balanced",
    timeTotal: "35 min",
    timeActive: "15 min",
    appliance: "Cocotte",
    requiredEquipment: ["stovetop"],
    dishes: "1 cocotte",
    freshnessNote: "Volaille fraîche à cuire d'ici J3-J4",
    description: "Morceaux de poulet tendres mijotés avec carottes fondantes, champignons de Paris et sauce veloutée légère.",
    plants: ["Carotte", "Champignons de Paris", "Poireau", "Oignon", "Ail", "Thym", "Laurier"],
    shortEveningAlternative: {
      title: "⚡ Sauté de poulet express aux champignons",
      timeTotal: "18 min",
      timeActive: "10 min",
      note: "Poêlée vive des émincés de poulet et champignons, sauce montée au yaourt sans réduction longue."
    },
    ingredients: [
      { name: "Blancs de poulet fermier", qty: "500 g", aisle: "Boucherie & Poissonnerie" },
      { name: "Champignons de Paris", qty: "250 g", aisle: "Primeur" },
      { name: "Carottes", qty: "3 pièces", aisle: "Primeur" },
      { name: "Poireau", qty: "1 pièce", aisle: "Primeur" },
      { name: "Crème fraîche liquide", qty: "100 ml", aisle: "Frais & Crèmerie" }
    ]
  },
  "risotto-petits-pois-jambon": {
    id: "risotto-petits-pois-jambon",
    title: "Risotto aux petits pois & parmesan",
    profile: "balanced",
    timeTotal: "30 min",
    timeActive: "15 min",
    appliance: "Casserole",
    requiredEquipment: ["stovetop"],
    dishes: "1 casserole",
    freshnessNote: "Épicerie & surgelé d'appoint",
    description: "Riz crémeux arborio lié au parmesan affiné, petits pois croquants et éclats de jambon de Parme.",
    plants: ["Riz arborio", "Petits pois", "Échalote", "Ail"],
    shortEveningAlternative: {
      title: "⚡ Risotto minute façon orzo",
      timeTotal: "15 min",
      timeActive: "10 min",
      note: "Cuisson rapide façon one-pot."
    },
    ingredients: [
      { name: "Riz arborio", qty: "250 g", aisle: "Épicerie & Sec" },
      { name: "Petits pois (frais ou surgelés)", qty: "200 g", aisle: "Primeur" },
      { name: "Parmesan AOP", qty: "60 g", aisle: "Frais & Crèmerie" },
      { name: "Chiffonnade de jambon cru", qty: "4 tranches", aisle: "Boucherie & Poissonnerie" }
    ]
  },
  "supreme-poulet-sous-vide": {
    id: "supreme-poulet-sous-vide",
    title: "Suprême de poulet ultra-fondant sous-vide (64°C)",
    profile: "vitality",
    timeTotal: "1 h 30 min",
    timeActive: "10 min",
    appliance: "Thermoplongeur sous-vide",
    requiredEquipment: ["sous_vide"],
    dishes: "Bain sous-vide, 1 poêle",
    freshnessNote: "Volaille fermière sous-vide haute précision",
    description: "Cuisson basse température d'une tendreté absolue, relevée au thym et jus de citron.",
    plants: ["Poulet", "Thym", "Citron", "Ail"],
    shortEveningAlternative: {
      title: "⚡ Aiguillettes express poêlées",
      timeTotal: "10 min",
      timeActive: "8 min",
      note: "Saisie vive à la poêle."
    },
    ingredients: [
      { name: "Suprêmes de poulet fermier", qty: "500 g", aisle: "Boucherie & Poissonnerie" },
      { name: "Thym frais", qty: "3 branches", aisle: "Primeur" },
      { name: "Citron jaune", qty: "1 pièce", aisle: "Primeur" }
    ]
  }
};

// EQUIPMENT DEFINITIONS & HELPERS
const EQUIPMENT_LABELS = {
  stovetop: "Plaques & Poêles",
  oven: "Four",
  thermomix: "Thermomix",
  sous_vide: "Sous-vide",
  pressure_cooker: "Cocotte minute"
};

function getMissingEquipment(recipe, userEquipment = (state && state.userEquipment)) {
  if (!recipe || !recipe.requiredEquipment || !userEquipment) return [];
  return recipe.requiredEquipment.filter(eq => !userEquipment[eq]);
}

// HELPERS FOR DATES
const DAY_NAMES_FR = ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"];
const MONTH_NAMES_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];

function formatDayLabel(date, isToday = false) {
  const dayName = DAY_NAMES_FR[date.getDay()];
  const dayNum = date.getDate();
  const monthName = MONTH_NAMES_FR[date.getMonth()];
  return `${dayName} ${dayNum} ${monthName}${isToday ? " (Aujourd'hui)" : ""}`;
}

// INITIAL STATE FACTORY
function createDefaultState(startDate = new Date()) {
  const weekPlan = [];
  // Default freshness rotation across 7 days relative to shopping day:
  const defaultDinnerRecipes = [
    "colin-alaska-tomate-estragon", // J1 : poisson frais
    "salade-de-pois-chiches",      // J2 : légumineuses crues croquantes
    "dhal-lentilles-corail-coco",   // J3 : réconfort dhal
    "blanquette-de-poulet",         // J4 : mijoté volaille
    "shakshuka-feta-oeufs",         // J5 : shakshuka express
    "porc-au-caramel",              // J6 : kiff week-end
    "veloute-potiron-cannelle"      // J7 : velouté anti-gaspi
  ];

  const defaultLunchSlots = [
    { type: "eating_out", customTitle: "Cantine / Resto travail", icon: "🍽️" },
    { type: "leftovers", customTitle: "Restes Colin & riz (Lunchbox)", icon: "🍱" },
    { type: "eating_out", customTitle: "Déjeuner extérieur", icon: "🍽️" },
    { type: "leftovers", customTitle: "Restes Dhal réchauffé", icon: "🍱" },
    { type: "eating_out", customTitle: "Cantine / Collègues", icon: "🍽️" },
    { type: "free", customTitle: "Toast avocat & œuf marché", icon: "✍️" },
    { type: "eating_out", customTitle: "Repas de famille dominical", icon: "🍽️" }
  ];

  for (let i = 0; i < 7; i++) {
    const d = new Date(startDate);
    d.setDate(d.getDate() + i);
    weekPlan.push({
      dateStr: d.toISOString(),
      dateLabel: `J${i + 1}`,
      dayName: formatDayLabel(d, i === 0),
      isToday: i === 0,
      lunch: defaultLunchSlots[i],
      dinner: recipeMeal(defaultDinnerRecipes[i], 2, defaultDinnerRecipes[i] === "porc-au-caramel" ? "✨" : "🍳")
    });
  }

  return {
    currentStep: 1,
    startShoppingDate: startDate.toISOString(),
    userEquipment: {
      stovetop: true,
      oven: true,
      thermomix: false,
      sous_vide: false,
      pressure_cooker: false
    },
    selectedKiffIds: ["porc-au-caramel"],
    selectedKiffSlots: {
      "porc-au-caramel": { dayIndex: 5, period: "dinner" }
    },
    shortEveningActive: false,
    activeSlotEditing: null,
    isMobileView: true,
    checkedShoppingItems: [],
    weekPlan: weekPlan
  };
}

// LOAD OR INIT STATE FROM LOCALSTORAGE
let state;
function loadState() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed && Array.isArray(parsed.weekPlan) && parsed.weekPlan.length === 7) {
        state = parsed;
        state.weekPlan.forEach(day => ["lunch", "dinner"].forEach(period => {
          if (day[period]?.type === "recipe") day[period].portions = normalizePortions(day[period].portions);
        }));
        if (!state.userEquipment) {
          state.userEquipment = {
            stovetop: true,
            oven: true,
            thermomix: false,
            sous_vide: false,
            pressure_cooker: false
          };
        }
        return;
      }
    }
  } catch (e) {
    console.warn("Storage load error", e);
  }
  state = createDefaultState(new Date());
}

function saveState() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (e) {
    console.warn("Storage save error", e);
  }
}

// DOM ELEMENTS
const el = {
  tabs: document.querySelectorAll(".step-tab"),
  views: {
    1: document.getElementById("view-step-1"),
    2: document.getElementById("view-step-2"),
    3: document.getElementById("view-step-3")
  },
  selectStartDay: document.getElementById("select-start-day"),
  equipmentChips: document.getElementById("equipment-chips"),
  kiffCardsContainer: document.getElementById("kiff-cards-container"),
  selectedKiffsCount: document.getElementById("selected-kiffs-count"),
  filterChips: document.querySelectorAll(".filter-chips .chip"),
  btnGenerateWeek: document.getElementById("btn-generate-week"),

  weekTitleHeading: document.getElementById("week-title-heading"),
  weekSubtitleRange: document.getElementById("week-subtitle-range"),
  heroTodayCard: document.getElementById("hero-today-card"),
  weekDaysContainer: document.getElementById("week-days-container"),
  toggleBatchPrep: document.getElementById("toggle-batch-prep"),
  batchPrepContent: document.getElementById("batch-prep-content"),
  btnBackToKiffs: document.getElementById("btn-back-to-kiffs"),
  btnGoToBasket: document.getElementById("btn-go-to-basket"),

  weekStatsCallout: document.getElementById("week-stats-callout"),
  gardenCount: document.getElementById("garden-count"),
  gardenCheerMsg: document.getElementById("garden-cheer-msg"),
  ratioVitalityLabel: document.getElementById("ratio-vitality-label"),
  ratioPleasureLabel: document.getElementById("ratio-pleasure-label"),
  ratioVitalityBar: document.getElementById("ratio-vitality-bar"),
  ratioPleasureBar: document.getElementById("ratio-pleasure-bar"),
  ratioAdviceMsg: document.getElementById("ratio-advice-msg"),
  gardenPlantsGrid: document.getElementById("garden-plants-grid"),
  shoppingAislesContainer: document.getElementById("shopping-aisles-container"),
  btnCopyShopping: document.getElementById("btn-copy-shopping"),
  btnRegenerateMenu: document.getElementById("btn-regenerate-menu"),
  btnBackToWeek: document.getElementById("btn-back-to-week"),

  swapModal: document.getElementById("swap-modal"),
  btnCloseModal: document.getElementById("btn-close-modal"),
  modalSlotTitle: document.getElementById("modal-slot-title"),
  modalSlotSub: document.getElementById("modal-slot-sub"),
  modalBtnEatingOut: document.getElementById("modal-btn-eating-out"),
  modalBtnLeftovers: document.getElementById("modal-btn-leftovers"),
  customRecipeInput: document.getElementById("custom-recipe-input"),
  btnApplyCustomRecipe: document.getElementById("btn-apply-custom-recipe"),
  modalRecipesList: document.getElementById("modal-recipes-list"),
  modalMoveTarget: document.getElementById("modal-move-target"),
  mealPortions: document.getElementById("meal-portions"),
  btnDeleteMeal: document.getElementById("btn-delete-meal"),
  btnMoveMeal: document.getElementById("btn-move-meal"),

  btnResetPlan: document.getElementById("btn-reset-plan"),
  toggleViewBtn: document.getElementById("toggle-view-btn"),
  mobileFrame: document.getElementById("mobile-frame"),
  toast: document.getElementById("toast-notification")
};

// INIT
function init() {
  loadState();
  bindEquipmentChips();
  populateStartDayOptions();
  bindNavigation();
  renderKiffList("all");
  renderStep2();
  renderStep3();
  setupViewToggle();

  // Hash routing
  function checkHash() {
    const hash = window.location.hash;
    if (hash === "#step2") goToStep(2);
    else if (hash === "#step3") goToStep(3);
    else if (hash === "#step1") goToStep(1);
  }
  window.addEventListener("hashchange", checkHash);
  checkHash();
}

// BIND KITCHEN EQUIPMENT CHIPS
function bindEquipmentChips() {
  const container = document.getElementById("equipment-chips");
  if (!container) return;
  const chips = container.querySelectorAll(".equip-chip");

  chips.forEach(chip => {
    const equip = chip.dataset.equip;
    if (state.userEquipment && state.userEquipment[equip]) {
      chip.classList.add("active");
    } else {
      chip.classList.remove("active");
    }

    chip.addEventListener("click", () => {
      if (chip.classList.contains("locked")) {
        showToast("🍳 Les plaques et poêles sont la base indispensable de toute cuisine !");
        return;
      }
      const isNowActive = !state.userEquipment[equip];
      state.userEquipment[equip] = isNowActive;
      chip.classList.toggle("active", isNowActive);
      saveState();

      const label = EQUIPMENT_LABELS[equip] || equip;
      if (isNowActive) {
        showToast(`✓ ${label} activé : les recettes correspondantes sont débloquées !`);
      } else {
        showToast(`✕ ${label} désactivé : les recettes nécessitant ce matériel sont signalées.`);
      }

      renderKiffList(document.querySelector(".filter-chips .chip.active")?.dataset.filter || "all");
      renderStep2();
      renderStep3();
    });
  });
}

// POPULATE DYNAMIC SHOPPING DAY SELECTOR
function populateStartDayOptions() {
  el.selectStartDay.innerHTML = "";
  const now = new Date();

  // Offer options from today up to 6 days ahead
  for (let i = 0; i < 7; i++) {
    const optDate = new Date(now);
    optDate.setDate(now.getDate() + i);
    const opt = document.createElement("option");
    opt.value = i;
    const prefix = i === 0 ? "Aujourd'hui" : (i === 1 ? "Demain" : DAY_NAMES_FR[optDate.getDay()]);
    opt.textContent = `${prefix} (${optDate.getDate()} ${MONTH_NAMES_FR[optDate.getMonth()]})`;
    el.selectStartDay.appendChild(opt);
  }

  el.selectStartDay.addEventListener("change", (e) => {
    const offset = parseInt(e.target.value);
    const newStart = new Date();
    newStart.setDate(newStart.getDate() + offset);
    recomputeWeekDates(newStart);
    saveState();
    renderStep2();
    renderStep3();
    showToast(`Planning calé à partir de ${el.selectStartDay.options[el.selectStartDay.selectedIndex].text}`);
  });
}

function recomputeWeekDates(startDate) {
  state.startShoppingDate = startDate.toISOString();
  state.weekPlan.forEach((day, idx) => {
    const d = new Date(startDate);
    d.setDate(d.getDate() + idx);
    day.dateStr = d.toISOString();
    day.dayName = formatDayLabel(d, idx === 0);
    day.isToday = idx === 0;
  });
}

// STEP NAVIGATION
function goToStep(stepNumber) {
  state.currentStep = stepNumber;
  saveState();

  el.tabs.forEach(tab => {
    tab.classList.toggle("active", parseInt(tab.dataset.step) === stepNumber);
  });

  Object.keys(el.views).forEach(k => {
    el.views[k].classList.toggle("active", parseInt(k) === stepNumber);
  });

  window.scrollTo({ top: 0, behavior: "smooth" });

  if (stepNumber === 2) {
    updateWeekPlanFromKiffs();
    renderStep2();
  } else if (stepNumber === 3) {
    renderStep3();
  }
}

function bindNavigation() {
  el.tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      goToStep(parseInt(tab.dataset.step));
    });
  });

  el.btnGenerateWeek.addEventListener("click", () => goToStep(2));
  el.btnBackToKiffs.addEventListener("click", () => goToStep(1));
  el.btnGoToBasket.addEventListener("click", () => goToStep(3));
  el.btnBackToWeek.addEventListener("click", () => goToStep(2));

  // Reset plan for a brand new week
  el.btnResetPlan.addEventListener("click", () => {
    if (confirm("Réinitialiser votre planning et démarrer un nouveau cycle de courses ?")) {
      localStorage.removeItem(STORAGE_KEY);
      state = createDefaultState(new Date());
      saveState();
      populateStartDayOptions();
      goToStep(1);
      renderKiffList("all");
      renderStep2();
      renderStep3();
      showToast("🔄 Nouveau cycle de courses démarré !");
    }
  });

  // Filter chips for Kiffs
  el.filterChips.forEach(chip => {
    chip.addEventListener("click", () => {
      el.filterChips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      renderKiffList(chip.dataset.filter);
    });
  });

  // Batch Prep Toggle
  el.toggleBatchPrep.addEventListener("click", () => {
    const isHidden = el.batchPrepContent.style.display === "none";
    el.batchPrepContent.style.display = isHidden ? "block" : "none";
    el.toggleBatchPrep.textContent = isHidden ? "Masquer" : "Voir";
  });

  // Modal actions
  el.btnCloseModal.addEventListener("click", closeModal);
  el.swapModal.addEventListener("click", (e) => {
    if (e.target === el.swapModal) closeModal();
  });

  el.modalBtnEatingOut.addEventListener("click", () => {
    applySlotAction({ type: "eating_out", customTitle: "Restaurant / Manger dehors", icon: "🍽️" });
  });

  el.modalBtnLeftovers.addEventListener("click", () => {
    applySlotAction({ type: "leftovers", customTitle: "Finir les restes (0 gaspi)", icon: "🍱" });
  });

  el.btnApplyCustomRecipe.addEventListener("click", () => {
    const title = el.customRecipeInput.value.trim();
    if (!title) {
      showToast("Veuillez saisir un nom pour votre recette libre.");
      return;
    }
    applySlotAction({ type: "free", customTitle: title, icon: "✍️" });
  });

  el.btnDeleteMeal.addEventListener("click", () => {
    if (!state.activeSlotEditing) return;
    const { dayIndex, period } = state.activeSlotEditing;
    removeMeal(state.weekPlan, dayIndex, period);
    saveState();
    closeModal();
    renderStep2();
    renderStep3();
    showToast("Créneau supprimé du planning.");
  });

  el.btnMoveMeal.addEventListener("click", () => {
    if (!state.activeSlotEditing) return;
    const [dayIndex, period] = el.modalMoveTarget.value.split(":");
    const from = state.activeSlotEditing;
    moveMeal(state.weekPlan, from.dayIndex, from.period, Number(dayIndex), period);
    saveState();
    closeModal();
    renderStep2();
    renderStep3();
    showToast("Repas déplacé dans la semaine.");
  });

  // Copy shopping list
  el.btnCopyShopping.addEventListener("click", handleCopyShoppingList);

  // Regenerate menu
  el.btnRegenerateMenu.addEventListener("click", () => {
    showToast("🔄 Semaine rééquilibrée avec succès !");
    updateWeekPlanFromKiffs();
    saveState();
    renderStep2();
    renderStep3();
  });
}

// STEP 1: KIFFS SELECTION
function renderKiffList(filterCategory) {
  el.kiffCardsContainer.innerHTML = "";
  const pleasureRecipes = Object.values(RECIPES).filter(r => r.profile === "pleasure");

  pleasureRecipes.forEach(recipe => {
    if (filterCategory !== "all" && recipe.category !== filterCategory) return;

    const isSelected = state.selectedKiffIds.includes(recipe.id);
    const missingEquip = getMissingEquipment(recipe, state.userEquipment);
    const hasMissing = missingEquip.length > 0;

    const card = document.createElement("div");
    card.className = `kiff-card ${isSelected ? "selected" : ""} ${hasMissing ? "incompatible-equip" : ""}`;

    const currentSlot = state.selectedKiffSlots[recipe.id] || { dayIndex: 5, period: "dinner" };
    const slotValue = `${currentSlot.dayIndex}-${currentSlot.period}`;

    // Options relative to the current 7 days
    const slotOptionsHtml = state.weekPlan.map((d, idx) => `
      <option value="${idx}-dinner" ${slotValue === `${idx}-dinner` ? "selected" : ""}>${d.dayName} (Dîner)</option>
      <option value="${idx}-lunch" ${slotValue === `${idx}-lunch` ? "selected" : ""}>${d.dayName} (Déjeuner)</option>
    `).join("");

    let warningBadgeHtml = "";
    if (hasMissing) {
      const names = missingEquip.map(e => EQUIPMENT_LABELS[e] || e).join(", ");
      warningBadgeHtml = `<div class="equip-warning-badge">⚠️ Matériel non configuré : ${names}</div>`;
    }

    card.innerHTML = `
      <div class="kiff-card-top">
        <div class="kiff-card-title">${recipe.title}</div>
        <div class="kiff-select-indicator">${isSelected ? "✓" : ""}</div>
      </div>
      <p class="kiff-card-desc">${recipe.description}</p>
      ${warningBadgeHtml}
      <div class="kiff-card-tags">
        <span class="badge pleasure">✨ Plaisir</span>
        <span class="badge">⏱️ ${recipe.timeTotal}</span>
        <span class="badge">🥘 ${recipe.appliance}</span>
      </div>
      ${isSelected ? `
        <div class="kiff-day-picker" onclick="event.stopPropagation()">
          <span class="day-select-label">Quand le déguster ?</span>
          <select class="day-select-dropdown" data-recipe-id="${recipe.id}">
            ${slotOptionsHtml}
          </select>
        </div>
      ` : ""}
    `;

    card.addEventListener("click", () => {
      if (hasMissing && !isSelected) {
        const names = missingEquip.map(e => EQUIPMENT_LABELS[e] || e).join(", ");
        showToast(`⚠️ Attention : cette recette nécessite "${names}". Activez ce matériel en haut si vous le possédez.`);
      }
      toggleKiffSelection(recipe.id);
    });

    el.kiffCardsContainer.appendChild(card);
  });

  // Dropdown listeners
  document.querySelectorAll(".day-select-dropdown").forEach(dropdown => {
    dropdown.addEventListener("change", (e) => {
      const rid = e.target.dataset.recipeId;
      const [dIdx, period] = e.target.value.split("-");
      state.selectedKiffSlots[rid] = { dayIndex: parseInt(dIdx), period };
      saveState();
    });
  });

  el.selectedKiffsCount.textContent = state.selectedKiffIds.length;
}

function toggleKiffSelection(recipeId) {
  const index = state.selectedKiffIds.indexOf(recipeId);
  if (index > -1) {
    // Libre de retirer tous les kiffs sans blocage
    state.selectedKiffIds.splice(index, 1);
    delete state.selectedKiffSlots[recipeId];
  } else {
    // Libre d'ajouter 1, 2, 3, 4 ou plus sans blocage
    state.selectedKiffIds.push(recipeId);

    // Créneaux festifs recommandés par défaut
    const preferredSlots = [
      { dayIndex: 5, period: "dinner" }, // Samedi Soir
      { dayIndex: 6, period: "lunch" },  // Dimanche Midi
      { dayIndex: 4, period: "dinner" }, // Vendredi Soir
      { dayIndex: 6, period: "dinner" }, // Dimanche Soir
      { dayIndex: 3, period: "dinner" }, // Jeudi Soir
      { dayIndex: 2, period: "dinner" }  // Mercredi Soir
    ];

    const currentAssigned = Object.values(state.selectedKiffSlots);
    const availableSlot = preferredSlots.find(slot =>
      !currentAssigned.some(a => a.dayIndex === slot.dayIndex && a.period === slot.period)
    ) || { dayIndex: 5, period: "dinner" };

    state.selectedKiffSlots[recipeId] = availableSlot;

    // Conseil bienveillant sans blocage
    if (state.selectedKiffIds.length > 2) {
      showToast("✨ Semaine très gourmande ! C'est vous qui décidez de vos plaisirs.");
    }
  }

  saveState();
  renderKiffList(document.querySelector(".filter-chips .chip.active").dataset.filter);
}

// UPDATE WEEK PLAN FROM SELECTED KIFFS
function updateWeekPlanFromKiffs() {
  state.selectedKiffIds.forEach((kiffId, idx) => {
    const slotInfo = state.selectedKiffSlots[kiffId] || (idx === 0 ? { dayIndex: 5, period: "dinner" } : { dayIndex: 6, period: "lunch" });
    if (state.weekPlan[slotInfo.dayIndex]) {
      setMeal(state.weekPlan, slotInfo.dayIndex, slotInfo.period, recipeMeal(kiffId, 2, "✨"));
    }
  });
  saveState();
}

// STEP 2: RENDER WEEK & HERO CARD
function renderStep2() {
  const firstDay = state.weekPlan[0].dayName.replace(" (Aujourd'hui)", "");
  const lastDay = state.weekPlan[6].dayName.replace(" (Aujourd'hui)", "");
  el.weekSubtitleRange.textContent = `Du ${firstDay} au ${lastDay}. Fraîcheur ordonnancée depuis vos courses.`;

  renderHeroCard();
  renderWeekTimeline();
}

function renderHeroCard() {
  const today = state.weekPlan.find(d => d.isToday) || state.weekPlan[0];
  const todayIndex = state.weekPlan.indexOf(today);
  const dinnerSlot = today.dinner;

  if (dinnerSlot.type === "recipe") {
    const recipe = RECIPES[dinnerSlot.recipeId] || RECIPES["colin-alaska-tomate-estragon"];
    const isShort = state.shortEveningActive && recipe.shortEveningAlternative;

    const displayTitle = isShort ? recipe.shortEveningAlternative.title : recipe.title;
    const displayTimeTotal = isShort ? recipe.shortEveningAlternative.timeTotal : recipe.timeTotal;
    const displayTimeActive = isShort ? recipe.shortEveningAlternative.timeActive : recipe.timeActive;
    const displayDishes = isShort ? "1 poêle seulement" : recipe.dishes;

    el.heroTodayCard.innerHTML = `
      <div class="hero-card">
        <div class="hero-top-badge-row">
          <span class="hero-moment-tag">🍃 Repas de ce soir • ${recipe.profile === "vitality" ? "Vitalité" : "Équilibré"}</span>
          <span class="hero-freshness-pill">À consommer J1-J2</span>
        </div>

        <h1 class="hero-title">${displayTitle}</h1>

        <div class="hero-metrics-bar">
          <div class="metric-item">
            <span class="metric-label">Temps total</span>
            <span class="metric-value">⏱️ ${displayTimeTotal}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Effort actif</span>
            <span class="metric-value">⚡ ${displayTimeActive}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Vaisselle</span>
            <span class="metric-value">🍽️ ${displayDishes}</span>
          </div>
        </div>

        <!-- Mode Soirée Courte (< 20 min) Button -->
        <div class="short-evening-toggle-box ${state.shortEveningActive ? "active" : ""}" id="btn-toggle-short-evening">
          <div class="short-evening-info">
            <span class="short-evening-title">⚡ Mode Soirée Courte (&lt; 20 min)</span>
            <span class="short-evening-sub">${state.shortEveningActive ? "Activé : version express avec les mêmes ingrédients !" : "Rentré tard ou fatigué ? Simplifier sans racheter."}</span>
          </div>
          <div class="switch-pill"></div>
        </div>

        ${isShort ? `
          <div class="short-mode-explanation">
            <strong>Astuce express :</strong> ${recipe.shortEveningAlternative.note}
          </div>
        ` : ""}

        <div class="hero-buttons-row">
          <button class="btn primary flex-grow" id="btn-start-cooking">
            <span>🍳 Cuisiner (Mode Cuisine)</span>
          </button>
          <button class="btn secondary" id="btn-hero-swap" title="Modifier ce créneau">
            <span>🔄 Modifier</span>
          </button>
        </div>

        <!-- Real life quick switches on Hero card -->
        <div style="margin-top: 12px; display: flex; gap: 8px; justify-content: center;">
          <button class="btn-small" id="btn-hero-quick-eatout">🍽️ Ce soir on mange dehors !</button>
          <button class="btn-small" id="btn-hero-quick-leftovers">🍱 Ce soir c'est restes !</button>
        </div>
      </div>
    `;

    document.getElementById("btn-toggle-short-evening").addEventListener("click", () => {
      state.shortEveningActive = !state.shortEveningActive;
      saveState();
      renderHeroCard();
      showToast(state.shortEveningActive ? "⚡ Mode Soirée Courte activé !" : "Mode classique restauré.");
    });

    document.getElementById("btn-start-cooking").addEventListener("click", () => {
      showToast("🚀 Lancement du Mode Cuisine lisible à 1 mètre...");
    });

    document.getElementById("btn-hero-swap").addEventListener("click", () => {
      openSlotModal(todayIndex, "dinner");
    });

    document.getElementById("btn-hero-quick-eatout").addEventListener("click", () => {
      today.dinner = { type: "eating_out", customTitle: "Restaurant / Manger dehors", icon: "🍽️" };
      saveState();
      renderStep2();
      renderStep3();
      showToast("🍽️ Ce soir c'est resto ! 0 ingrédient à acheter pour ce soir.");
    });

    document.getElementById("btn-hero-quick-leftovers").addEventListener("click", () => {
      today.dinner = { type: "leftovers", customTitle: "Finir les restes du frigo", icon: "🍱" };
      saveState();
      renderStep2();
      renderStep3();
      showToast("🍱 Ce soir on vide le frigo ! Zéro déchet.");
    });

  } else {
    // Hero when eating out or leftovers
    const title = dinnerSlot.customTitle || "Repas libre";
    const badgeLabel = dinnerSlot.type === "eating_out" ? "🍽️ Sortie Restaurant / Cantine" : (dinnerSlot.type === "leftovers" ? "🍱 Finir les restes" : "✍️ Recette libre");

    el.heroTodayCard.innerHTML = `
      <div class="hero-card">
        <div class="hero-top-badge-row">
          <span class="badge ${dinnerSlot.type}">${badgeLabel}</span>
          <span class="hero-freshness-pill">0 course nécessaire</span>
        </div>

        <h1 class="hero-title">${title}</h1>
        <p class="subtitle" style="margin-bottom: 16px;">
          ${dinnerSlot.type === "eating_out" ? "Soirée libre à l'extérieur : aucun temps de préparation ni vaisselle à faire !" : "Réchauffage express : vous valorisez les restes déjà cuisinés."}
        </p>

        <div class="hero-buttons-row">
          <button class="btn secondary full-width" id="btn-hero-revert-recipe">
            <span>🔄 Re-choisir une recette à cuisiner</span>
          </button>
        </div>
      </div>
    `;

    document.getElementById("btn-hero-revert-recipe").addEventListener("click", () => {
      openSlotModal(todayIndex, "dinner");
    });
  }
}

function renderWeekTimeline() {
  el.weekDaysContainer.innerHTML = "";

  state.weekPlan.forEach((day, dayIndex) => {
    const card = document.createElement("div");
    card.className = `day-card ${day.isToday ? "active-day" : ""}`;

    card.innerHTML = `
      <div class="day-card-header">
        <div class="day-left-meta">
          <div class="day-index-circle">${day.dateLabel}</div>
          <div class="day-title-block">
            <span class="day-name-label">${day.dayName}</span>
            <span class="day-recipe-name">${getSlotDisplayShort(day.dinner)}</span>
          </div>
        </div>
        <div class="day-right-meta">
          <span class="badge ${getSlotBadgeClass(day.dinner)}">${getSlotBadgeLabel(day.dinner)}</span>
          <span class="day-chevron">▼</span>
        </div>
      </div>

      <div class="day-card-body" style="display: block;">
        <div class="day-slots-container">
          <!-- Midi (Déjeuner) -->
          <div class="meal-slot-row" onclick="openSlotModal(${dayIndex}, 'lunch')">
            <div class="slot-left">
              <span class="slot-period-tag">Midi</span>
              <span class="slot-title">${getSlotDisplayTitle(day.lunch)}</span>
            </div>
            <div class="slot-right">
              <span class="badge ${getSlotBadgeClass(day.lunch)}">${getSlotBadgeLabel(day.lunch)}</span>
              <span class="btn-small">Modifier</span>
            </div>
          </div>

          <!-- Soir (Dîner) -->
          <div class="meal-slot-row" onclick="openSlotModal(${dayIndex}, 'dinner')">
            <div class="slot-left">
              <span class="slot-period-tag">Soir</span>
              <span class="slot-title">${getSlotDisplayTitle(day.dinner)}</span>
            </div>
            <div class="slot-right">
              <span class="badge ${getSlotBadgeClass(day.dinner)}">${getSlotBadgeLabel(day.dinner)}</span>
              <span class="btn-small">Modifier</span>
            </div>
          </div>
        </div>
      </div>
    `;

    const header = card.querySelector(".day-card-header");
    const body = card.querySelector(".day-card-body");

    header.addEventListener("click", () => {
      const isExpanded = body.style.display !== "none";
      body.style.display = isExpanded ? "none" : "block";
      card.classList.toggle("expanded", !isExpanded);
    });

    el.weekDaysContainer.appendChild(card);
  });
}

function getSlotDisplayShort(slot) {
  if (!slot) return "Non planifié";
  if (slot.type === "recipe") {
    const r = RECIPES[slot.recipeId];
    return r ? r.title : "Recette CookiGram";
  }
  return slot.customTitle || "Repas libre";
}

function getSlotDisplayTitle(slot) {
  if (!slot) return "—";
  if (slot.type === "recipe") {
    const r = RECIPES[slot.recipeId];
    return r ? `${r.title} (⏱️ ${r.timeTotal})` : "Recette";
  }
  return `${slot.icon || ""} ${slot.customTitle || "Repas libre"}`;
}

function getSlotBadgeClass(slot) {
  if (!slot) return "";
  if (slot.type === "recipe") {
    const r = RECIPES[slot.recipeId];
    return r ? r.profile : "vitality";
  }
  return slot.type;
}

function getSlotBadgeLabel(slot) {
  if (!slot) return "";
  if (slot.type === "recipe") {
    const r = RECIPES[slot.recipeId];
    if (!r) return "Recette";
    return r.profile === "pleasure" ? "✨ Plaisir" : (r.profile === "vitality" ? "🍃 Vitalité" : "⚖️ Équilibré");
  }
  if (slot.type === "eating_out") return "🍽️ Dehors";
  if (slot.type === "leftovers") return "🍱 Restes";
  if (slot.type === "free") return "✍️ Libre";
  return "Autre";
}

// SLOT EDIT MODAL
window.openSlotModal = function(dayIndex, period) {
  state.activeSlotEditing = { dayIndex, period };
  const day = state.weekPlan[dayIndex];
  const periodLabel = period === "lunch" ? "Déjeuner (Midi)" : "Dîner (Soir)";

  el.modalSlotTitle.textContent = `${day.dayName} — ${periodLabel}`;
  el.customRecipeInput.value = "";
  const currentMeal = day[period];
  el.mealPortions.value = currentMeal?.type === "recipe" ? normalizePortions(currentMeal.portions) : 2;
  el.modalMoveTarget.innerHTML = state.weekPlan.flatMap((candidateDay, candidateIndex) => ["lunch", "dinner"].map(candidatePeriod => {
    const selected = candidateIndex === dayIndex && candidatePeriod === period ? " selected" : "";
    const label = candidatePeriod === "lunch" ? "Midi" : "Soir";
    return `<option value="${candidateIndex}:${candidatePeriod}"${selected}>${candidateDay.dayName} — ${label}</option>`;
  })).join("");

  el.modalRecipesList.innerHTML = "";
  Object.values(RECIPES).forEach(recipe => {
    const missingEquip = getMissingEquipment(recipe, state.userEquipment);
    const hasMissing = missingEquip.length > 0;

    const item = document.createElement("div");
    item.className = "modal-recipe-item";

    let warningTag = "";
    if (hasMissing) {
      const missingNames = missingEquip.map(e => EQUIPMENT_LABELS[e] || e).join(", ");
      warningTag = `<span style="font-size: 11px; color: #b45309; background: #fef3c7; padding: 2px 6px; border-radius: 4px; margin-left: 6px; font-weight: 700;">⚠️ ${missingNames} requis</span>`;
    }

    item.innerHTML = `
      <div>
        <div style="font-weight: 700; font-size: 15px;">${recipe.title} ${warningTag}</div>
        <div style="font-size: 12px; color: #57534e;">⏱️ ${recipe.timeTotal} • ${recipe.appliance} • ${recipe.dishes}</div>
      </div>
      <span class="badge ${recipe.profile}">${recipe.profile === "pleasure" ? "Plaisir" : "Vitalité"}</span>
    `;

    item.addEventListener("click", () => {
      if (hasMissing) {
        const missingNames = missingEquip.map(e => EQUIPMENT_LABELS[e] || e).join(", ");
        showToast(`⚠️ Matériel requis : ${missingNames}. Pensez à l'activer dans votre équipement !`);
      }
      applySlotAction(recipeMeal(recipe.id, el.mealPortions.value, recipe.profile === "pleasure" ? "✨" : "🍳"));
    });

    el.modalRecipesList.appendChild(item);
  });

  el.swapModal.style.display = "flex";
};

function closeModal() {
  el.swapModal.style.display = "none";
  state.activeSlotEditing = null;
}

function applySlotAction(slotData) {
  if (!state.activeSlotEditing) return;
  const { dayIndex, period } = state.activeSlotEditing;

  if (slotData.type === "recipe") slotData.portions = normalizePortions(slotData.portions);
  setMeal(state.weekPlan, dayIndex, period, slotData);
  saveState();
  closeModal();

  renderStep2();
  renderStep3();
  showToast(`Créneau mis à jour : ${slotData.customTitle || (RECIPES[slotData.recipeId]?.title)}`);
}

// STEP 3: GARDEN OF 30 PLANTS & CONSOLIDATED SHOPPING
function renderStep3() {
  renderWeekStats();
  renderMicrobiomeGarden();
  renderShoppingBasket();
}

function renderWeekStats() {
  let homeCookedCount = 0;
  let eatingOutCount = 0;
  let leftoversCount = 0;
  let freeCount = 0;

  state.weekPlan.forEach(day => {
    [day.lunch, day.dinner].forEach(slot => {
      if (!slot) return;
      if (slot.type === "recipe") homeCookedCount++;
      else if (slot.type === "eating_out") eatingOutCount++;
      else if (slot.type === "leftovers") leftoversCount++;
      else if (slot.type === "free") freeCount++;
    });
  });

  el.weekStatsCallout.innerHTML = `
    <strong>14 créneaux planifiés sur mesure :</strong><br>
    🍳 <strong>${homeCookedCount} repas cuisinés CookiGram</strong> (ingrédients comptés au gramme près)<br>
    🍽️ <strong>${eatingOutCount} repas à l'extérieur</strong> (aucun achat engagé)<br>
    🍱 <strong>${leftoversCount} repas sur restes</strong> (zéro gaspi / lunchboxes prévues)<br>
    ✍️ <strong>${freeCount} recette(s) libre(s)</strong> hors catalogue.
  `;
}

function renderMicrobiomeGarden() {
  const plantSet = new Set();
  const plantToRecipeMap = {};

  state.weekPlan.forEach(day => {
    [day.lunch, day.dinner].forEach(slot => {
      if (slot && slot.type === "recipe") {
        const recipe = RECIPES[slot.recipeId];
        if (recipe && recipe.plants) {
          recipe.plants.forEach(plant => {
            plantSet.add(plant);
            if (!plantToRecipeMap[plant]) plantToRecipeMap[plant] = [];
            if (!plantToRecipeMap[plant].includes(recipe.title)) {
              plantToRecipeMap[plant].push(recipe.title);
            }
          });
        }
      }
    });
  });

  const totalPlants = plantSet.size;
  el.gardenCount.textContent = totalPlants;

  if (totalPlants >= 25) {
    el.gardenCheerMsg.textContent = "🎉 Diversité végétale remarquable ! Votre microbiote est comblé.";
  } else if (totalPlants >= 20) {
    el.gardenCheerMsg.textContent = "🌱 Très bonne diversité végétale ! Vos défenses naturelles sont stimulées.";
  } else {
    el.gardenCheerMsg.textContent = "🍃 Bon équilibre de départ, ajoutez quelques herbes ou aromates frais !";
  }

  el.gardenPlantsGrid.innerHTML = "";
  Array.from(plantSet).sort().forEach(plant => {
    const tag = document.createElement("div");
    tag.className = "plant-tag";
    tag.innerHTML = `<span>🌿</span> <span>${plant}</span>`;
    tag.title = `Présent dans : ${plantToRecipeMap[plant].join(", ")}`;

    tag.addEventListener("click", () => {
      tag.classList.toggle("highlighted");
      showToast(`${plant} : présent dans ${plantToRecipeMap[plant].join(" & ")}`);
    });

    el.gardenPlantsGrid.appendChild(tag);
  });

  // Calcul dynamique du ratio 80/20 comme CONSEIL bienveillant (non bloquant)
  let pleasureSlots = 0;
  let vitalitySlots = 0;

  state.weekPlan.forEach(day => {
    [day.lunch, day.dinner].forEach(slot => {
      if (slot) {
        if (slot.type === "recipe") {
          const r = RECIPES[slot.recipeId];
          if (r && r.profile === "pleasure") {
            pleasureSlots++;
          } else {
            vitalitySlots++;
          }
        } else if (slot.type === "eating_out") {
          pleasureSlots++;
        } else {
          vitalitySlots++;
        }
      }
    });
  });

  const totalEvaluated = (pleasureSlots + vitalitySlots) || 14;
  const pleasurePercent = Math.round((pleasureSlots / totalEvaluated) * 100);
  const vitalityPercent = 100 - pleasurePercent;

  if (el.ratioVitalityLabel) el.ratioVitalityLabel.textContent = `🍃 ${vitalityPercent}% Vitalité & Équilibre (${vitalitySlots} repas)`;
  if (el.ratioPleasureLabel) el.ratioPleasureLabel.textContent = `✨ ${pleasurePercent}% Plaisir & Kiffs (${pleasureSlots} repas)`;
  if (el.ratioVitalityBar) el.ratioVitalityBar.style.width = `${vitalityPercent}%`;
  if (el.ratioPleasureBar) el.ratioPleasureBar.style.width = `${pleasurePercent}%`;

  if (el.ratioAdviceMsg) {
    if (vitalityPercent >= 70 && vitalityPercent <= 85) {
      el.ratioAdviceMsg.innerHTML = `💡 <strong>Conseil 80/20 :</strong> Super équilibre atteint ! Un socle d'énergie léger et digeste avec de vrais moments de fête sans culpabilité.`;
    } else if (vitalityPercent > 85) {
      el.ratioAdviceMsg.innerHTML = `💡 <strong>Conseil 80/20 :</strong> Semaine très légère et épurée. Vous avez toute la marge pour glisser un plat plaisir si l'envie vous prend !`;
    } else {
      el.ratioAdviceMsg.innerHTML = `💡 <strong>Conseil 80/20 :</strong> Semaine très généreuse et festive ! Astuce : accompagnez simplement vos repas d'une salade fraîche ou de légumes croquants.`;
    }
  }
}

function renderShoppingBasket() {
  const aisles = {
    "Primeur": [],
    "Boucherie & Poissonnerie": [],
    "Épicerie & Sec": [],
    "Frais & Crèmerie": []
  };

  const ingredientOccurrences = {};

  state.weekPlan.forEach(day => {
    [day.lunch, day.dinner].forEach(slot => {
      if (slot && slot.type === "recipe") {
        const recipe = RECIPES[slot.recipeId];
        if (recipe) {
          recipe.ingredients.forEach(ing => {
            ingredientOccurrences[ing.name] = (ingredientOccurrences[ing.name] || 0) + 1;
          });
        }
      }
    });
  });

  const addedToAisle = {};

  state.weekPlan.forEach(day => {
    [day.lunch, day.dinner].forEach(slot => {
      if (slot && slot.type === "recipe") {
        const recipe = RECIPES[slot.recipeId];
        if (recipe) {
          recipe.ingredients.forEach(ing => {
            const aisleName = ing.aisle || "Épicerie & Sec";
            if (!aisles[aisleName]) aisles[aisleName] = [];

            const key = ing.name;
            if (!addedToAisle[key]) {
              addedToAisle[key] = true;
              aisles[aisleName].push({
                name: ing.name,
                qty: ing.qty,
                sharedCount: ingredientOccurrences[key] || 1
              });
            }
          });
        }
      }
    });
  });

  el.shoppingAislesContainer.innerHTML = "";

  const aisleIcons = {
    "Primeur": "🥕",
    "Boucherie & Poissonnerie": "🐟",
    "Épicerie & Sec": "🥫",
    "Frais & Crèmerie": "🧈"
  };

  if (!state.checkedShoppingItems) state.checkedShoppingItems = [];

  Object.keys(aisles).forEach(aisleName => {
    const items = aisles[aisleName];
    if (items.length === 0) return;

    const block = document.createElement("div");
    block.className = "aisle-block";

    block.innerHTML = `
      <div class="aisle-title">
        <span>${aisleIcons[aisleName] || "📦"}</span>
        <span>${aisleName}</span>
      </div>
      <ul class="aisle-items">
        ${items.map(item => {
          const isChecked = state.checkedShoppingItems.includes(item.name);
          return `
            <li class="shopping-item-row ${isChecked ? "checked" : ""}">
              <label class="item-left">
                <input type="checkbox" class="shopping-checkbox" data-item-name="${item.name}" ${isChecked ? "checked" : ""}>
                <span class="item-name">${item.name}</span>
              </label>
              <div class="item-right">
                ${item.sharedCount > 1 ? `<span class="item-shared-badge">🤝 Partagé (${item.sharedCount})</span>` : ""}
                <span class="item-qty">${item.qty}</span>
              </div>
            </li>
          `;
        }).join("")}
      </ul>
    `;

    // Checkbox strikethrough interaction with LOCALSTORAGE PERSISTENCE
    block.querySelectorAll(".shopping-item-row").forEach(row => {
      const cb = row.querySelector(".shopping-checkbox");
      cb.addEventListener("change", () => {
        const itemName = cb.dataset.itemName;
        row.classList.toggle("checked", cb.checked);
        if (cb.checked) {
          if (!state.checkedShoppingItems.includes(itemName)) state.checkedShoppingItems.push(itemName);
        } else {
          state.checkedShoppingItems = state.checkedShoppingItems.filter(n => n !== itemName);
        }
        saveState();
      });
    });

    el.shoppingAislesContainer.appendChild(block);
  });
}

function handleCopyShoppingList() {
  let text = "🛒 CookiGram — Liste de courses consolidée (Vie Réelle)\n";
  text += "====================================================\n\n";

  const aisles = el.shoppingAislesContainer.querySelectorAll(".aisle-block");
  aisles.forEach(aisle => {
    const title = aisle.querySelector(".aisle-title").textContent.trim();
    text += `### ${title}\n`;
    aisle.querySelectorAll(".shopping-item-row").forEach(row => {
      const name = row.querySelector(".item-name").textContent.trim();
      const qty = row.querySelector(".item-qty").textContent.trim();
      const isDone = row.querySelector(".shopping-checkbox").checked;
      text += `- [${isDone ? "x" : " "}] ${name} (${qty})\n`;
    });
    text += "\n";
  });

  navigator.clipboard.writeText(text).then(() => {
    showToast("📋 Liste copiée dans le presse-papier !");
  }).catch(() => {
    showToast("Erreur lors de la copie");
  });
}

// VIEWPORT TOGGLE
function setupViewToggle() {
  el.toggleViewBtn.addEventListener("click", () => {
    state.isMobileView = !state.isMobileView;
    el.mobileFrame.classList.toggle("full-width", !state.isMobileView);
    el.toggleViewBtn.querySelector(".label").textContent = state.isMobileView ? "Mobile" : "Plein Écran";
    el.toggleViewBtn.querySelector(".icon").textContent = state.isMobileView ? "📱" : "💻";
    saveState();
  });
}

// TOAST HELPER
function showToast(message) {
  el.toast.textContent = message;
  el.toast.classList.add("show");
  setTimeout(() => {
    el.toast.classList.remove("show");
  }, 2600);
}

// START
window.addEventListener("DOMContentLoaded", init);
