# Atomicité v2 — calibration reproductible et rapport de qualification (2026-10-25)

Référence : CookiGram/cookigram#499. Ce document consigne les **preuves de calibration et résultats de qualification** des recettes témoins et lots d'atomicité du chantier #499.

## 1. Règle sémantique et doctrine cible

Une instruction d'ajout contenant plusieurs ingrédients indépendants doit être scindée, sans toucher aux balises `@ingrédient{quantité}`, à l'ordre culinaire, aux durées ni aux paramètres machine.
- 1 ingrédient ajouté = 1 atome indépendant.
- Les consignes portant sur la cuisson d'un mélange restent une opération machine unique lorsque c'est pertinent.
- Les noms/quantités ne sont pas masqués dans le Mode Cuisine.
- Les actions manuelles, les réglages et les commandes d'appareils sont rigoureusement séparés.

## 2. Bilan de qualification et d'intégration

| PR | Recettes / Fichiers | Strict Gate | Visuel (Desktop & Mobile) | Faux PASS identifiés | Statut |
|---|---|---|---|---|---|
| #551 | `recipes/porc-aigre-doux-puree.gram` | PASS | PASS (20 sous-étapes, 0 erreur) | Aucun | **Fusionné** |
| #552 | `recipes/aioli-citron-capres.gram` | PASS | PASS (18 sous-étapes, 0 erreur) | Aucun | **Fusionné** |
| #553 | `recipes/risotto-petits-pois-jambon.gram` | PASS | PASS (19 sous-étapes, 0 erreur) | Aucun (titre PR rectifié) | **Fusionné** |
| #555 | `recipes/chutney-mangue-pomme.gram` | PASS | PASS (16 sous-étapes, 0 erreur) | Aucun | **Fusionné** |
| #556 | `recipes/guacamole-classique.gram`<br>`recipes/houmous-classique.gram`<br>`recipes/sauce-bechamel.gram` | PASS | PASS (13, 13, 9 sous-étapes, 0 erreur) | Aucun | **Fusionné** |
| #557 | `recipes/air-fryer-pommes-terre-romarin.gram`<br>`recipes/chili-con-carne.gram`<br>`recipes/gnocchi-romaine-miel-noix-gorgonzola.gram` | PASS | PASS (7, 42, 30 sous-étapes, 0 erreur) | Aucun (enrobage AF correctement atomisé) | **Fusionné** |
| #558 | `recipes/banh-bao-porc.gram`<br>`recipes/chutney-coco.gram` | PASS (après correction) | PASS (37 et 18 sous-étapes, 0 erreur) | **Oui (2 faux PASS majeurs corrigés)** | **Fusionné** |

## 3. Analyse des faux PASS du validateur

La qualification indépendante a révélé que le linter Gram en mode `--strict-atomic` a déclaré 100% conforme (`0 avertissement`) des instructions pourtant composites :
1. `banh-bao-porc.gram` :
   - `Réunir le lait, la levure et le sucre; chauffer...` (3 ingrédients + chauffe agrégés).
   - `Hacher l'oignon nouveau, la ciboulette, la saucisse et les shiitaké...` (4 ingrédients + hachage agrégés).
2. `chutney-coco.gram` :
   - `Mettre dans le bol la noix de coco, la farine, les cacahuètes, les piments, la pâte d'ail, la coriandre et le sel` (7 ingrédients agrégés dans un seul paragraphe de mixage).
   - `Mélanger et servir` (2 gestes distincts agrégés).

Ces défauts ont été directement décomposés et corrigés sur la branche #558 avant fusion, confirmant que la CI seule est insuffisante sans revue sémantique.

## 4. Statut global

Statut : **QUALIFIED / PASS**. Toutes les PR de recettes #551 à #553 et #555 à #558 sont qualifiées, testées et fusionnées sur `main`.
