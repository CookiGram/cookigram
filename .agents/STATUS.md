# CookiGram — État d'Exécution & Registre Vivant

> **Note aux agents :** Consultez ce fichier en priorité au démarrage. Il remplace la relecture de dizaines de fichiers de documentation et vous donne l'état exact du projet en moins de 500 tokens.

---

## 🚦 Tâches en cours (Claims actifs)

* **Aucun claim actif.** Le backlog est disponible pour le Jalon 3.

---

## 🏆 Jalons de Maturité Produit (Kitchen OS)

* **✅ Jalon 1 — Recipe OS (Livré)** : Fiches canoniques `.gram`, moteur nutritionnel CIQUAL, portions dynamiques, 100% hors-ligne.
* **✅ Jalon 2 — Cooking Copilot & Mise en Place (Livré — v2.0.0-stable)** : 
  - Étape 0 « Mise en place du plan de travail » avec checklist tactile des découpes et sortie du matériel (#80 / #81)
  - Minuteurs persistants absolus (wall-clock) avec Web Audio et vibrations (#78 / #79)
  - Sticky active timer bar et temps restant estimé en direct (#67 / #78)
  - Cases à cocher d'incorporation par étape
  - Synthèse et reconnaissance vocale mains-libres (« Lancer la cuisson », « Suivant », « Minuteur »)
  - Rendu responsive mobile/tablette sans défilement parasite
* **🔶 Jalon 3 — Kitchen Scheduler (Prochain cap prioritaire — Epic #51)** :
  - **Issue #91** : Typologie d'effort (actif humain vs passif machine) & élasticité thermique.
  - **Issue #92** : Ergonomie du « Live Cooking Feed » multi-tâches en Mode Cuisine.
  - **Issue #93** : Verrous d'équipements exclusifs & micro-étapes de transition de lavage.
  - **Issue #94** : Stratégie Dual-Engine (Python OR-Tools au build vs Micro-Solveur JS natif PWA client).
  - **Issue #95** : « Le Panier du Menu » (Sélection multi-recettes, courses consolidées & audit matériel).
  - **Issue #98** : Moteur d'accords sensoriels & équilibre macro-nutritionnel de menu (« Smart Pairing »).
  - **Issue #99** : Cuisson sous-vide & basse température (Thermodynamique & Tables Baldwin).
* **🎨 Améliorations UX, Design & Imports Transverses** :
  - **Issue #101** : Clarification de la redondance du matériel (suppression du doublon sur fiche recette).
  - **Issue #103** : Support et conversion des mesures américaines et impériales (cups, oz, lbs, °F, sticks).

---

## ✅ Dernières Livraisons Clôturées

* **Issue #102 / PR #104** : Simplification sobre des mentions d'illustration (« Illustration originale CookiGram ») et documentation de la séparation stricte entre provenance technique et attribution publique — *Fusionné dans `main`*.
* **PR #89** : Pack 2 d'icônes d'ustensiles (planche, plat à gratin, thermomix, moule, panier vapeur, économe) et `required_equipment` renseigné sur 123 des 199 recettes (couverture partielle) — *Fusionné dans `main`*.
* **Issue #80 / PR #81** : Étape 0 « Mise en place du plan de travail » en Mode Cuisine — *Fusionné dans `main`*.
* **Issue #78 / PR #79** : Persistance de la progression en Mode Cuisine (minuteurs wall-clock, sticky bar contextuelle, cases à cocher ingrédients) — *Fusionné dans `main`*.
* **PR #76** : Import de 2 nouvelles recettes desserts (Cheesecake japonais & Flan aux œufs) — *Fusionné dans `main`*.
* **Issue #67 / PR #77** : Affichage du temps restant estimé dans le header du Mode Cuisine — *Fusionné dans `main`*.
* **Issue #68** : Explicitation pédagogique de l'évaporation sans projection au panier cuisson — *Fusionné dans `main`*.

---

## 🛑 Règles d'Or Développeurs

1. **Claim obligatoire** dans `.agents/claims.json` avant toute ligne de code.
2. **Interdiction d'inventer des fonctionnalités** sans issue portant le label `potential-dev-work`.
3. **Tests ciblés pendant le dev** (`node --test tests/<mon_test>.test.mjs static/meal-planner/planner-state.test.js`). Ne lancer la suite globale qu'avant le push final.
4. **Commit & push systématique** avec working tree 100% propre.
