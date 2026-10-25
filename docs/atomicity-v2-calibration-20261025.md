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

## Convergence Core vérifiée (correction du préflight)

Au moment de la lecture GitHub, `.core-version` sur `main` de CookiGram référence `5c91478a355a7ea6637433783e8f9f700f60ce3b`. Les merge commits des cinq PR ont été comparés individuellement au pin actuel à l'aide de GitHub compare. #340 (`887c0443`), #343 (`a952a6c0`), #345 (`f970d6da`), #352 (`7d4433b2`) et #353 (`dce1223c`) sont **tous des ancêtres** de `5c91478a355a7ea6637433783e8f9f700f60ce3b` (statut `ahead`, `behind_by=0` depuis chacun des commits de fusion vers le pin). Le pin contient donc déjà ces changements Atomic. **Aucune mise à jour du pin n'est nécessaire à cette fin.** Reste à exécuter/qualifier le strict gate et le build effectif sur cette version.

## Critères restant à satisfaire avant cinq vagues

1. Qualifier la revue des quinze recettes ci-dessous en ajoutant les numéros de ligne, le résultat du gate (non exécuté) et la décision indépendante de chaque cas limite.
2. Exécuter les gates et le build sur le Core déjà épinglé par le dépôt public (install/build/gates et rendu Cook Mode).
3. Revérifier claims opérationnels, PR ouvertes et ownership exact/hiérarchique, en particulier les lots 1–5, avant mutation.
4. Faire valider les cas limites de découpage, en distinguant incorporation d'ingrédients et une seule opération de cuisson/mélange.
5. Qualification indépendante des PR recettes. **Aucun merge automatique.**

Statut : **PARTIAL / NOT PASS**. Ce document ne prétend pas lever le gate #499.

## Neuf recettes supplémentaires examinées sur main (15 fichiers au total)

| Fichier | Témoin observé | Revue sémantique préliminaire |
|---|---|---|
| `arepas-poulet-avocat.gram` | Mettre eau, carotte, pomme de terre, poireau, coriandre, cube et huile dans le bol | Plusieurs incorporations indépendantes : scinder, sans modifier la cuisson du poulet |
| `banh-bao-porc.gram` | Ajouter farine, levure chimique et huile ; farce porc + vinaigre + sauce huître + sel + poivre | Ajouts composites : scinder ; conserver opération de mélange séparée |
| `guacamole-classique.gram` | Ajouter oignon, piment et ail ; puis avocat, jus de citron et sel | Deux séquences d'incorporation à atomiser |
| `houmous-classique.gram` | Ajouter pois chiches et huile de sésame ; huile d'olive et citron ; sel, paprika et piment | Trois ajouts composites ; texture finale liée au mixage |
| `pate-a-crepes.gram` | Mettre lait, farine, œufs et sel dans la cuve | Quatre gestes d'incorporation indépendants |
| `sauce-bechamel.gram` | Ajouter lait, sel, poivre et noix de muscade | Quatre ajouts indépendants ; préserver cuisson et repère « nappe la cuillère » |
| `air-fryer-crevettes-ail-citron.gram` | Mélanger les crevettes avec huile, ail, paprika, sel ; secouer à mi-cuisson | Découper les ingrédients de l'enrobage sans changer le geste de mélange ; évaluer le secouage comme action indépendante |
| `one-pot-poulet-riz-legumes.gram` | Mélanger paprika, coriandre, ail et huile ; verser bouillon et ajouter riz, poireaux, origan et laurier | Plusieurs préparations et ajouts distincts ; préserver enchaînement et paramètres de cuisson |
| `chili-con-carne.gram` | Mettre poivrons, oignon, ail ensemble ; ajouter huile, viande, cumin, paprika | Ajouts multi-ingrédients ; distinguer incorporation et programme machine |

Ces 15 fichiers constituent maintenant **une revue qualitative initiale**, pas 15 validations du strict gate. Le résultat réel du linter, les lignes et une qualification indépendante restent **NOT RUN / NOT PASS**. Les cas composites ci-dessus sont observés dans le texte GitHub ; ne pas assimiler l'examen lexical à un verdict automatique.
