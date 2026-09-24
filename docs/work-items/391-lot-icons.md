# Work-item 391-lot-icons — couverture du pack d'icônes d'ingrédients

Statut : READY.

## Objectif

Aucun slug de `.gram/ingredients.yaml` sans icône directe ni fallback :
mesure 314 slugs = 148 directs + 165 fallbacks + 1 manquant
(`clous-de-girofle`, catégorie « Épices et condiments » sans fallback Core).

## Acceptation

1. `static/icons/ingredients/clous-de-girofle.svg` original, style pack
   (viewBox 32, outline encre, 2–3 couleurs chaudes, < 2 Ko).
2. Test commis : couverture totale (0 slug sans résolution via
   `IngredientIconResolver` sur `.gram/ingredients.yaml`).
3. `pytest tests` vert ; build instance réel OK.
4. Aucun changement Core, aucune autre icône modifiée.

## Hors périmètre

Pack UI, mapping Core, autres slugs (couverts), refonte du style.

## Dépendances / ownership / collisions

Aucune dépendance. Ownership instance (assets). Pas de PR ouverte ni de
fichier partagé avec un autre lot : seul lot READY, parallélisation N/A.

## Reprise

Branche `feat/391-lot-icons` ; vert = test de couverture + build ;
suite = ouvrir PR non mergée.
