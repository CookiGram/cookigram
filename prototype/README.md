# Meal Planner prototype — issue #160

## Conservé et corrigé

- Conservé : la semaine glissante de 7 jours, les créneaux midi/soir, la vie réelle (dehors, restes, recette libre), la sélection d’équipement et la persistance locale déjà présentes.
- Corrigé : les 7 jours sont lisibles sans ouvrir chaque carte ; la modification depuis le repas héroïque cible bien le jour courant ; une recette peut maintenant être ajoutée, remplacée, déplacée ou supprimée depuis la même interaction.
- Ajouté : un nombre de portions par recette, avec migration tolérante des anciens états localStorage (valeur par défaut : 2).

## Frontière Shopping Planner

`planner-state.js` expose `toShoppingPlannerInput(weekPlan)`, une représentation plate des 14 créneaux : jour, date, moment, type, `recipeId` et portions. Le prototype ne résout pas les ingrédients et ne fait aucune agrégation ; un futur Shopping Planner pourra consommer cette sortie et appliquer ses propres règles.

Les métadonnées Meal Composition (`completeness`, `role`, `needs`, `benefits_from`) ne sont ni redéfinies ni exigées ici. Une recette sans ces métadonnées reste planifiable.

## Besoins métier remontés

- Le produit devra préciser si déplacer un repas sur un créneau occupé doit échanger les repas (choix actuel) ou refuser l’action.
- Le produit devra préciser le cas des portions variables selon le repas et la gestion d’un nombre de personnes différent pour une recette déjà planifiée.
- Le contrat entre `recipeId`, portions et le futur Shopping Planner devra être stabilisé quand Meal Composition sera finalisé.

Test local ciblé : `node --test prototype/planner-state.test.js`.
