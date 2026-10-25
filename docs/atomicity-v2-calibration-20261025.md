# Atomicité v2 — calibration reproductible, état initial (2026-10-25)

Référence : CookiGram/cookigram#499. Ce document consigne des **preuves partielles** à partir des fichiers `recipes/*.gram` lus sur `main` de GitHub. Ce n'est **pas** le rapport final de calibration des 15 recettes et **aucun** strict atomic gate n'a été exécuté ici.

## Règle sémantique à qualifier

Une instruction d'ajout contenant plusieurs ingrédients indépendants doit être scindée, sans toucher aux balises `@ingrédient{quantité}`, à l'ordre, aux durées ni aux paramètres machine. Les consignes portant sur la cuisson d'un mélange restent une opération machine unique lorsque c'est pertinent. Les noms/quantités ne doivent pas être masqués dans le Mode Cuisine.

## Six fichiers relus sur main

| Fichier | Observation vérifiable | Classe |
|---|---|---|
| `porc-aigre-doux-puree.gram` | « Mettre » avec jus de raisin, sauce soja, huile et vinaigre dans une seule puce ; seconde puce ajoutant fécule, porc et oignons | 2 ajouts composites |
| `chutney-mangue-pomme.gram` | 3 puces d'ajouts groupés : huile+moutarde, pomme+mangue, sucre+vinaigre+sel | 3 ajouts composites |
| `aioli-citron-capres.gram` | ail+zeste, câpres+jaunes, moutarde+jus de citron | 3 ajouts composites |
| `risotto-petits-pois-jambon.gram` | eau+cube+petits pois ; sel+poivre ; jambon+ricotta | 3 ajouts composites |
| `air-fryer-ailes-poulet-croustillantes.gram` | mélanger ailes avec huile, sel, poivre et ail dans une puce | 1 candidate, sémantique à arbitrer (enrobage) |
| `pate-a-choux.gram` | porter à ébullition eau, beurre, sel et sucre en une seule commande | cas limite : une seule chauffe sur mélange ; ne pas compter automatiquement comme faux PASS |

Les quatre premiers témoignent d'instructions d'ajout multi-ingrédients ; le cinquième et sixième servent à prévenir une règle automatique trop agressive. Un comptage lexical n'est pas une preuve d'échec du linter. Vérifier les cas particuliers de mélange préalable et les instructions de cuisson.

## Traçabilité des propositions directes

- PR #551 : `porc-aigre-doux-puree.gram` (draft)
- PR #552 : `aioli-citron-capres.gram` (draft)
- PR #553 : `risotto-petits-pois-jambon.gram` (draft)

**Collision connue** : `aioli-citron-capres.gram` figure dans le lot 1 proposé ; l'exclure tant que #552 est ouverte. Le témoin porc aigre-doux est également détenu par #551. Les trois recettes pilotes de #541 restent exclues de la campagne.

## Dépendance Core non levée

Au moment de la lecture GitHub, `.core-version` sur `main` de CookiGram référence `5c91478a355a7ea6637433783e8f9f700f60ce3b`. Les PR Core #340, #343, #345, #352 et #353 sont fermées. **Leur inclusion effective dans un nouveau pin, la reproductibilité du build et le résultat du strict atomic gate ne sont pas encore qualifiés.** Ne pas changer le pin par supposition : préparer un changement séparé, tester et faire qualifier.

## Critères restant à satisfaire avant cinq vagues

1. Compléter la revue de quinze recettes représentatives, en documentant le fichier, la ligne, la version, le résultat du gate et l'arbitrage sémantique.
2. Qualifier le Core effectivement épinglé par le dépôt public (install/build/gates et rendu Cook Mode).
3. Revérifier claims opérationnels, PR ouvertes et ownership exact/hiérarchique, en particulier les lots 1–5, avant mutation.
4. Faire valider les cas limites de découpage, en distinguant incorporation d'ingrédients et une seule opération de cuisson/mélange.
5. Qualification indépendante des PR recettes. **Aucun merge automatique.**

Statut : **PARTIAL / NOT PASS**. Ce document ne prétend pas lever le gate #499.
