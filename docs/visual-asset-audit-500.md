# Audit de couverture visuelle post-vagues (#500)

Snapshot du 26 septembre 2026 sur `origin/main` (`656f2f0`). Les préconditions
sont réunies : #491, #492, #493 et #495 sont fermées. Le détail complet et
diffable, avec recettes, cibles de resolver, statuts et recommandations, est
dans [`visual-asset-audit-500.json`](visual-asset-audit-500.json).

## Synthèse

| Domaine | Univers mesuré | DEDICATED | ALIAS | Fallback | MISSING | REVIEW |
|---|---:|---:|---:|---:|---:|---:|
| Ingrédients utilisés | 371 slugs canoniques sur 379 | 147 | 50 | 40 acceptables | 0 | 134 |
| Outils et ustensiles | 259 libellés distincts observés | 16 | 112 | 94 sans mapping (🍳) | 31 cibles de mapping sans fichier | 6 |
| Appliances | 14 familles canoniques du contrat #495, dont 8 utilisées | 1 | 0 | 4 sans mapping | 6 | 3 |

Pour les ingrédients, 134 entrées sont classées `REVIEW` après contrôle
sémantique : 116 résolvent techniquement par `CATEGORY_FALLBACK` et 18 par un
alias vers un asset trop générique ou inadéquat. Les chemins réels restent
dans `resolution_status` ; chaque revue a un motif. Les 40 autres fallbacks
sont de meilleurs candidats à un fallback de catégorie assumé.

Pour les outils, le décompte porte sur les libellés bruts vus dans les étapes et
`required_equipment`, pas sur 259 objets différents. Six libellés dont le Core
retourne un alias existant sont signalés `REVIEW` car l’objet montré diffère
(par exemple passoire → panier vapeur). La normalisation Core actuelle ne
ramène pas encore tout le vocabulaire aux familles canoniques. Le JSON conserve
chaque libellé et ses recettes.

Les recettes ajoutées par les vagues apportent ces premiers usages canoniques
au corpus :

| Vague | Recettes ajoutées | Slugs nouvellement utilisés | Slugs ajoutés au catalogue |
|---|---:|---:|---:|
| #491 | 10 | 25 | 26 |
| #492 | 24 | 19 | 19 |
| #493 | 36 | 22 | 20 |

L’attribution compare chaque merge à son premier parent, parse les variantes
avec le Core épinglé et résout les mentions avec le `ingredients.yaml` de
chaque commit. Les listes complètes de recettes et slugs sont dans
`wave_attribution` du JSON.

Les 123 recettes Thermomix, 22 Four et 7 Sous-vide incluent les variantes qui
déclarent explicitement ces appareils. Le test miroir #495 compte 112
Thermomix, 21 Four et 6 Sous-vide dans sa lecture bloc uniquement. Le YAML
réel contient 122 déclarations Thermomix de base : 10 sont en forme inline
(`appliances: {thermomix: [...]}`) et sont omises par cette regex ; une
variante ajoute une recette Thermomix supplémentaire. L’inventaire JSON garde
les formes et valeurs brutes ainsi que les décomptes base/variante.

## Priorités

### P0 — représentation trompeuse ou élément nécessaire

- **Beurre** : `beurre-doux` (62 recettes) et `beurre-demi-sel` (5) affichent
  `produit-laitier.svg`. `beurre.svg` existe mais reste orphelin. Recommandation
  : mapper les deux variantes vers cet asset tout en conservant leur distinction
  dans le texte.
- **Pâte à pizza** : 20 recettes utilisent le fallback `pain-de-mie.svg`.
- **Avocat** (9), **mayonnaise** (9), **nori** (8), **patate douce** (3) :
  fallbacks vers pomme, épices ou oignon. Prévoir des assets adaptés après
  arbitrage.
- **Four** : 55 recettes ont un libellé qui cible `four.webp`, absent. Le template
  produit alors une URL d’image qui casse, pas le fallback 🍳.
- **Sous-vide** : le tag `thermoplongeur` est utilisé dans 22 recettes et son
  fichier manque ; les sacs sous-vide (16 recettes) et la machine sous-vide
  (4) n’ont aucun mapping.
- **Air Fryer** : 15 recettes. « panier air fryer » cible `air-fryer.webp`, absent.
- **Pizza** : pelle (20), pierre réfractaire (20) et grille (21) n’ont pas de
  mapping exploitable.
- **Plaques de cuisson** : 10 recettes ont un libellé qui cible
  `plaque-cuisson.webp`, absent.

### P1 — plusieurs recettes ou alias trompeur

- **Autocuiseur** : `cookeo.webp`, `instant-pot.webp` et `multicuiseur.webp`
  sont absents ; les clés canoniques fusionnées `pressure_cooker` couvrent 8
  recettes. Garder une famille générique et mapper les variantes, sans exiger
  un visuel par marque.
- **Robot pâtissier** (7 recettes) et **robot multifonction** : l’alias large
  `robot` réutilise `thermomix.webp`, représentation trompeuse.
- **Passoire/chinois/écumoire** : `passoire` est assimilée à `panier-vapeur`,
  tandis que chinois et écumoire tombent sur 🍳. Canoniser les formulations
  avant de décider d’un asset de famille.
- Ingrédients à examiner ensuite : `riz-sushi` (16, icône riz générique),
  `yaourt-grec` (9), `thon` (8), `mirin` (4), `menthe-fraiche` (4),
  `pate-de-tamarin` (4) et `sauce-nuoc-mam` (4).

### Orphelins et nettoyage

Huit slugs du catalogue ne sont utilisés par aucune recette actuelle ; leur
résolution est dans `unused_ingredients` du JSON. Les SVG ingrédients non
atteints par une occurrence résolue sont `ail-tete.svg`, `beurre.svg`,
`clous-de-girofle.svg` et `jus-de-cuisson-sous-vide.svg`. Les 12 WebP
d’ustensiles sont tous atteints.
`clou-de-girofle.svg` et `clous-de-girofle.svg` sont deux fichiers distincts ;
conserver le singulier utilisé et arbitrer le pluriel. `ail-tete.svg` peut être
un asset de variante pertinent, mais aucune occurrence du corpus courant ne le
résout.

### P2 — revue ciblée et cas rares

Le JSON attribue `P2` aux entrées moins fréquentes dont le fallback ou l’alias
reste acceptable, ainsi qu’aux libellés d’outils utilisés mais sans mapping
spécifique. Les priorités sont portées entrée par entrée (`priority`) : elles
tiennent compte du caractère trompeur et de la compréhension de la recette,
pas seulement du nombre d’usages.

### P3 — assets à arbitrer ou nettoyer

Les candidats P3 sont les 8 ingrédients du catalogue sans usage, les 4 SVG
orphelins ci-dessus et les appliances non déclarées. Vérifier d’abord qu’aucun
consommateur hors corpus ne dépend des fichiers avant de les supprimer ; garder
un asset de variante utile est aussi une issue possible.

### Cohérence du pack avec le profil #391

Les 174 SVG ont été parcourus sur des planches contact et contrôlés par XML.
48 n’ont aucun contour `stroke` explicite ; trois utilisent un `viewBox` 64×64
au lieu de 32×32 (`haricots-blancs`, `paprika-fume`, `tofu-ferme`) ; sept
dépassent trois couleurs de remplissage. Aucun SVG ne dépasse 2 Ko et aucun
fichier ne comporte d’erreur XML. Ce sont des candidats de revue visuelle,
pas des rejets automatiques : la liste par fichier, ses ingrédients et ses
recettes est dans `style_audit.review_candidates` du JSON. Les icônes de
fallback `produit-laitier.svg`, `epices-cajun.svg` et `pain-de-mie.svg` font
partie des fichiers sans contour explicite et sont très utilisées.

## Appliances canoniques

| Famille | Recettes (variantes incluses) | Statut | Résolution actuelle |
|---|---:|---|---|
| Thermomix | 123 | DEDICATED | `thermomix.webp` |
| Four | 22 | MISSING | `four.webp` absent |
| Four à pizza | 20 | MISSING | `four.webp` absent ; alias générique possible |
| Air Fryer | 15 | MISSING | `air-fryer.webp` absent |
| Sous-vide | 7 | FALLBACK | pas de mapping pour la famille ; thermoplongeur séparé |
| Autocuiseur / multicuiseur | 8 | MISSING | `multicuiseur.webp` absent |
| Robot pâtissier | 7 | REVIEW | `thermomix.webp` trompeur |
| Rice cooker | 1 | FALLBACK | aucun mapping |
| Plaques & poêles (stovetop) | 0 | REVIEW | `poele.webp` n’exprime pas toute la famille |
| Blender | 0 | MISSING | `blender.webp` absent |
| Mixeur plongeant | 0 | MISSING | `blender.webp` absent |
| Robot multifonction | 0 | REVIEW | `thermomix.webp` trompeur |
| Micro-ondes | 0 | FALLBACK | aucun mapping |
| Mijoteuse | 0 | FALLBACK | aucun mapping |

## Méthode et surfaces vérifiées

- Catalogue et recettes du commit indiqué ; mentions et variantes lues avec le
  parseur de recettes épinglé dans `.core-version` (`b8f30cef`).
- Ingrédients résolus par `IngredientIconResolver`, avec ses familles et
  fallbacks de catégorie. `DEDICATED` désigne le slug propre, `ALIAS` une
  famille d’icônes, `CATEGORY_FALLBACK` le pictogramme de catégorie, et
  `MISSING` une absence de résolution.
- Outils résolus par `resolve_utensil_icon` du même commit. Un nom qui retourne
  une cible sans fichier est classé `MISSING` ; un `None` est le fallback 🍳.
- Les templates `recipe.html` et `cook.html` ont été inspectés au commit Core
  épinglé pour la fiche, la mise en place et Cook Mode. La fiche réutilise aussi
  les icônes ingrédients dans l’évaluation et la liste de courses. Une cible
  d’outil non nulle est rendue comme `<img>` même si le fichier manque. Les
  ingrédients n’émettent pas d’image si la résolution est vide. Le profil
  matériel du prototype filtre les familles par libellé et emoji ; il n’a pas
  de mapping d’icônes d’appliance distinct.
- Le build UI avec secret Core n’a pas été rejoué dans ce dépôt de contenu ;
  la vérification des templates est une vérification source, pas un test
  navigateur. La planche contact couvre le pack entier, mais ne remplace pas une
  QA de chaque icône à la taille UI. `REVIEW` signale les mappings
  sémantiquement trompeurs ; `style_audit` liste séparément les écarts
  structurels au profil.

Gates publics exécutés : chargement YAML de `.gram/*.yaml` et
`python scripts/audit-recipe-images.py --check` (aucune anomalie).

## Décision de suite

L’inventaire est prêt à être relu. Aucun asset, recette ou contrat Core n’a été
modifié. Après revue, découper la correction en lots ingrédients, outils et
appliances ; les recommandations ligne par ligne et recettes associées sont
dans le JSON.
