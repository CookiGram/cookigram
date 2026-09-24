# Roadmap CookiGram

> 📌 **Ordre officiel de priorisation produit (Lots 1 à 5)**  
> Arbitrage validé par le Product Owner (@PierreCsn, utilisateur n°1) et le Product Lead.  
> Référence GitHub : Issue épinglée **[#35](https://github.com/PierreCsn/cookigram/issues/35)** et **[`PRODUCT_PRINCIPLES.md`](PRODUCT_PRINCIPLES.md)**.
>
> 1. 🍳 **Lot 1 — UX Cuisine & Ergonomie Mobile (P0/P1)** : #28, #29, #27, #37 (**TERMINÉ**)
> 2. 🔍 **Lot 2 — SEO Critique & Indexation (P1)** : #15, #16, #20 (**TERMINÉ**)
> 3. 📱 **Lot 3 — Ergonomie & Fiche Recette (P1)** : #26, #30, #31, #32, #39, #49 (**TERMINÉ**)
> 4. 🎨 **Lot 4 — SEO Avancé, Design System & Performance (P2)** : #17, #24, #34, #23, #21, #22, #19, #18, #33 (**TERMINÉ**)
> 5. 🧱 **Lot 5 — Dette Technique & Évolution Socle (P3/P4)** : #8 (fait), #1 (en attente)

Dernier audit : 3 septembre 2026.

> Actualisation (24 septembre 2026, #435) : la section « État du projet au
> moment de l'audit » ci-dessous est le snapshot archivé du 3 septembre 2026,
> conservé sans réécriture. État vérifiable à cette date : 199 recettes
> `.gram` dans `recipes/`, 314 entrées dans `.gram/ingredients.yaml`,
> 17 fichiers `tests/test_*.py` plus 4 tests Node via `node --test` (sans
> seuil de couverture), CI sans Ruff/Biome/Playwright (validation via
> `cookigram_contract`, `pytest`, `node --test`, audit images et lint
> contenu), `static/app.js` et `static/sw.js` supprimés (JS éclaté par
> fonctionnalité dans `static/meal-planner/`, `static/selection/` et
> `static/info/`), aucune branche `legacy/codex-pre-gemini` dans ce dépôt.

## État du projet au moment de l'audit (snapshot 3 sept. 2026 — archivé)


- 43 fichiers de recettes `.gram` et 170 entrées dans la base d'ingrédients.
- 100 tests Python collectés dans la CI, avec seuil de couverture configuré à 80 %.
- Ruff, Biome, tests JavaScript et génération complète du site sont contrôlés par la CI.
- Le site est généré et déployé uniquement après validation de la CI.
- La branche principale locale suit désormais l'historique GitHub ; l'ancien
  historique local reste conservé dans `legacy/codex-pre-gemini`.

### État des travaux récents

- [x] Ajouter les icônes d'instruments de cuisine (#56).
- [x] Ajouter les icônes d'ingrédients du lot pilote et résoudre les variantes Gram.
- [x] Ajouter les icônes manquantes eau, poivre, vin blanc et bouquet garni (#71).
- [x] Ajouter les descriptions éditoriales approuvées (#45).
- [x] Corriger les quantités et ingrédients manquants (#43).
- [ ] Finaliser les cas ambigus d'ingrédients répétés (#42).
- [ ] Finaliser l'audit des cinq salades (#63).
- [x] Fusionner les PR #69 et #70 pour clôturer #23, #19, #18 et #33.
- [ ] Valider avec Design / UX l'affichage du temps restant en mode pas à pas (#67).
- [ ] Obtenir l'analyse Recipe Expert sur le panier cuisson à l'étape 3 (#68).
- [ ] Obtenir l'arbitrage du Product Owner sur la compatibilité TM31 à 120 °C (#40).

## P0 — Stabiliser les parcours principaux

- [x] Corriger le redimensionnement des portions dans `static/app.js` :
  initialiser `step` depuis `portionPicker.dataset.step` avant son utilisation.
- [x] Corriger la checklist et la liste de courses : remplacer la variable globale
  implicite `recipeSlug` par une valeur issue de `checklistEl.dataset.recipe` ou
  d'un attribut explicite de la page.
- [x] Vérifier qu'une erreur dans une fonctionnalité n'empêche pas
  l'initialisation des fonctionnalités suivantes (blocs initialisés via
  `initFeature`, gardes `speechSynthesis` fiabilisées).
- [x] Ajouter un test navigateur pour modifier le nombre de portions et vérifier
  le recalcul, les limites min/max et la persistance après rechargement.
- [x] Ajouter un test navigateur pour cocher, restaurer et réinitialiser la liste
  d'ingrédients.
- [x] Ajouter un test navigateur pour ouvrir la fenêtre de courses et copier ou
  partager la sélection.

> Note (2 sept. 2026) : les variables non déclarées `step`, `recipeSlug` et
> `steps` dans `app.js` ont été corrigées ; le mode cuisine ne levait plus de
> `ReferenceError`.

### Critère de sortie P0

- [x] La recherche, les portions, la checklist, les courses et le mode cuisine
  fonctionnent sans erreur JavaScript sur une fiche recette représentative.

## P1 — Mettre en place un vrai filet de sécurité

- [x] Ajouter Playwright, avec une configuration adaptée au site statique.
- [x] Couvrir au minimum les scénarios de bout en bout suivants :
  - [x] recherche et filtres du catalogue ;
  - [x] changement du nombre de portions ;
  - [x] checklist et évaluation des courses ;
  - [x] navigation dans le mode cuisine ;
  - [x] démarrage, pause, reprise et remise à zéro d'un minuteur ;
  - [x] comportement sans les API optionnelles de voix, partage et Wake Lock ;
  - [x] installation et navigation hors ligne de la PWA.
- [x] Ajouter un contrôle de syntaxe JavaScript explicite à la CI
  (`node --check` sur `app.js` et `sw.js`).
- [x] Faire échouer la CI sur les erreurs console non attendues des tests
  navigateur.
- [x] Faire dépendre le déploiement GitHub Pages de la réussite de la CI, ou
  fusionner build, tests et déploiement dans un pipeline ordonné.
- [x] Unifier la validation CI sur Python 3.12 unique (suppression de la matrice multi-versions redondante, compatibilité 3.11 garantie par Ruff et Mypy).
- [x] Remplacer le badge de couverture statique par une mesure générée, ou le
  mettre à jour automatiquement.

### Critère de sortie P1

- [x] Aucun déploiement ne peut avoir lieu si le lint, le build, les validations
  de données ou un parcours utilisateur critique échouent.

## P1 — Formaliser le contrat des recettes

- [x] Définir un schéma canonique pour le frontmatter `.gram`.
- [x] Valider explicitement :
  - [x] le titre, les portions et la présence d'au moins une étape ;
  - [x] les types et valeurs de `tags`, `prep_time` et `total_time` ;
  - [x] la cohérence de `scaling` (`min`, `max`, `step`, raison si désactivé) ;
  - [x] la présence du fichier image déclaré ;
  - [x] la source, l'auteur et les crédits photographiques requis ;
  - [x] l'existence de chaque ingrédient dans la base locale ;
  - [x] les durées, températures et réglages d'appareil pris en charge.
- [x] Produire des erreurs de build précises avec fichier, champ et valeur en
  cause.
- [x] Ajouter des tests de recettes malformées et de métadonnées invalides.
- [x] Rendre tous les chemins de données indépendants du répertoire courant ;
  utiliser une racine de projet ou injecter explicitement les chemins.
- [x] Décider si le parseur MVP accepte les constructions Gram inconnues avec un
  avertissement ou les refuse strictement.

### Critère de sortie du contrat de données

- [x] Une recette incomplète ou incohérente bloque le build avec un diagnostic
  immédiatement exploitable.

## P2 — Fiabiliser les calculs nutritionnels

- [x] Séparer le référentiel nutritionnel, le parsing des quantités, les
  conversions et le calcul par recette.
- [x] Supprimer le fallback silencieux de 10 g pour une quantité inconnue.
- [x] Ne plus traiter tous les millilitres comme des grammes sans densité propre
  à l'ingrédient.
- [x] Stocker dans la base les densités, poids unitaires et conversions utiles
  plutôt que des heuristiques codées en dur.
- [x] Signaler les ingrédients ignorés et les quantités non convertibles.
- [x] Calculer et exposer un taux de couverture nutritionnelle par recette.
- [x] Associer les valeurs affichées à leur source et à leur niveau de confiance
  (`verified`, `estimated`, `manual`, etc.).
- [x] N'afficher un résultat nutritionnel que si son seuil de qualité est atteint,
  ou l'accompagner clairement d'un avertissement.
- [x] Ajouter des tests pour les fractions, densités, unités, comptes, valeurs
  inconnues et mélanges de sources.
- [x] Revoir le libellé « par portion (CIQUAL) » lorsqu'une recette contient des
  estimations ou des données provenant d'une autre source.

### Critère de sortie nutrition

- [x] Chaque valeur affichée est traçable et son degré d'approximation est connu.


## P2 — Rendre la PWA réellement utilisable hors ligne

- [x] Choisir et documenter une stratégie :
  - [x] précharger toutes les recettes et leurs images ; ou
  - [x] proposer un téléchargement hors ligne explicite par recette.
- [x] Inclure `recipes.json` et les pages nécessaires dans la stratégie de cache.
- [x] Ajouter une page de secours lorsqu'une ressource non téléchargée est
  demandée hors ligne.
- [x] Définir les stratégies de cache séparément pour HTML, données, scripts,
  styles et images.
- [x] Vérifier qu'une nouvelle version du service worker met à jour les assets
  sans laisser une interface incohérente.
- [x] Tester l'installation fraîche, la mise à jour et le retour en ligne.
- [x] Tester en CI le mode avion sur une fiche, son image et son mode cuisine.
- [x] Ajuster la promesse « consultable partout, sans connexion » si toutes les
  recettes ne sont pas disponibles après la première installation.

### Critère de sortie PWA

- [x] Une recette déclarée disponible hors ligne reste intégralement utilisable
  en mode avion, image et mode cuisine compris.

## P2 — Réduire la dette frontend

- [x] Découper `static/app.js` en modules par fonctionnalité :
  - [x] thème et installation PWA ;
  - [x] recherche et filtres ;
  - [x] portions et parsing des quantités ;
  - [x] checklist et courses ;
  - [x] partage et export ;
  - [x] mode cuisine et sous-étapes ;
  - [x] minuteurs ;
  - [x] voix, synthèse vocale et Wake Lock.
- [x] Donner à chaque module une fonction d'initialisation indépendante et
  tolérante à l'absence de son HTML.
- [x] Éliminer les dépendances à des variables globales implicites.
- [x] Ajouter des tests unitaires JavaScript pour les fonctions pures, notamment
  le parsing et le redimensionnement des quantités.
- [x] Remettre le CSS source dans un format maintenable ; minifier uniquement lors
  du build si nécessaire.
- [x] Découper le CSS par domaine ou composant sans multiplier inutilement les
  requêtes de production.
- [x] Extraire les fragments de template répétés, notamment les badges et icônes
  Thermomix, dans des macros Jinja.
- [x] Afficher des icônes de matériel nécessaire (robot, Varoma, Cookeo, etc.)
  sur les vignettes des recettes du catalogue, en plus des fiches recette.
- [x] Formaliser l'interface des plugins et éviter de recharger chaque module pour
  chaque recette.

### Critère de sortie frontend

- [x] Chaque fonctionnalité peut être testée et modifiée sans dépendre de l'ordre
  d'exécution d'un script monolithique.

## P3 — Qualité produit et publication

- [ ] Réaliser un audit d'accessibilité clavier et lecteur d'écran.
- [ ] Vérifier le focus et la fermeture de la fenêtre modale de courses.
- [ ] Respecter `prefers-reduced-motion` pour les animations importantes.
- [ ] Tester les parcours critiques sur Chrome Android et Safari iOS.
- [ ] Vérifier la dégradation progressive des API Web non universelles : voix,
  partage, vibration, notifications, Wake Lock et presse-papiers.
- [ ] Définir des budgets de poids pour HTML, JavaScript, CSS et images.
- [x] Ajouter des données structurées Schema.org `Recipe` avec durée, cuisine,
  dates et fil d'Ariane (#19).
- [x] Ajouter les URL canoniques, métadonnées Open Graph et cartes sociales.
- [x] Générer un sitemap et, si utile, un flux des nouvelles recettes.
- [ ] Mesurer Lighthouse dans la CI sans imposer de seuils instables au départ.
- [ ] Documenter une courte procédure de release et de retour arrière.

## P4 — Évolution du socle

- [ ] Étudier le remplacement du parseur MVP par le compilateur Gram officiel.
- [ ] Conserver le modèle canonique interne afin de ne pas coupler templates et
  plugins au compilateur.
- [ ] Construire des tests de compatibilité entre l'ancien adaptateur et le futur
  adaptateur officiel.
- [ ] Versionner l'interface des plugins et documenter leurs entrées/sorties.
- [ ] Automatiser davantage l'import de recettes sans réduire les contrôles de
  provenance, de licence et de scaling.

## Ordre de réalisation recommandé

1. Finaliser l'audit recette #63 et clarifier les cas restants de #42.
2. Faire valider par Design / UX puis traiter la fonctionnalité du temps restant
   en mode pas à pas (#67).
3. Obtenir l'analyse Recipe Expert sur l'usage du panier cuisson à l'étape 3 (#68).
4. Obtenir la décision du Product Owner sur #40.
5. Reprendre ensuite les chantiers P3/P4 et les nouvelles fonctionnalités validées.

## Définition de « terminé » pour une tâche

- [ ] Le comportement est couvert par un test proportionné au risque.
- [ ] Le lint, les tests et le build complet réussissent localement et en CI.
- [ ] La documentation utilisateur ou contributeur est mise à jour si nécessaire.
- [ ] La modification fonctionne sans les API navigateur optionnelles.
- [ ] Aucune donnée nutritionnelle, provenance ou licence n'est inventée ou
  dégradée silencieusement.
