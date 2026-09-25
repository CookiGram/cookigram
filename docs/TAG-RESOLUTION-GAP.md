# Écart doctrine / implémentation — résolution des tags ingrédients

> Note enregistrée séparément du chantier #493, pour correction ultérieure.
> Ne pas traiter dans le scope #493.

## Constat (vérifié 2026-09-25, chantier #493)

- La doctrine (skill `import-recipe-gram`) annonce qu'un ingrédient de recette
  « resolves through a key, `name`, or alias ».
- L'implémentation (`generator/schema.py`, `get_known_ingredient_names`)
  n'accepte que `name` et `aliases` (comparaison `casefold`, sensible aux
  traits d'union et aux accents). La **clé n'est jamais acceptée**.

## Effet observé

34 tags `@clé-avec-traits-d-union` rédigés pour #493 ont été rejetés par le
vrai gate Core (`ingredient ... is missing from .gram/ingredients.yaml`)
alors qu'ils correspondaient exactement à des clés existantes
(ex. `@bouquet-garni`, `@clou-de-girofle`, `@sucre-roux`).
Correction appliquée dans #493 : réécriture vers les formes nom/alias
(ex. `@bouquet garni`, `@sucre roux`).

## Correction candidate (hors scope #493)

Au choix :
1. aligner le checker sur la doctrine (accepter aussi les clés), ou
2. aligner la doctrine sur le checker (`nom|alias` uniquement), ou
3. ajouter les alias à traits d'union manquants (travail de fond, risque de
   doublons — même prudence que la réconciliation #492).

Décision et implémentation : à trancher hors #493 (propriété Core + skill).
