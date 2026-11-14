# #656 — propositions initiales d'actions et techniques « Comment ? »

**Inventaire de travail non normatif**, dérivé de deux recettes actuelles :
`recipes/sauce-bolognaise-rapide.gram` et `recipes/tzatziki-grec.gram`.
Aucune action ci-dessous n'est ajoutée au langage Gram ou à un catalogue de techniques approuvé.

## Modèle corrigé : action syntaxique et micro-recette d'application

Les actions sont des **marqueurs syntaxiques** de la recette (dans Gram officiel : un verbe optionnel `[Émincer]` en début d'étape). La distinction entre `Émincer` + oignon et `Émincer` + ail relève de **CookiGram**, et non de deux nouveaux verbes du langage.

Dans CookiGram aujourd'hui, les crochets nomment nos **macro-phases** et les sous-étapes `- ...` ne portent pas encore individuellement ce marqueur syntaxique. Il faut étudier un adapter/une évolution de parsing compatible avant la résolution automatique, sans injecter de syntaxe improvisée dans le catalogue.

- **Action syntaxique** : méthode/verb reconnu dans la recette ; le nom est indépendant de l'ingrédient.
- **Occurrence atomique** : instance exécutable et validable dans une recette/variante donnée (#499).
- **Micro-recette `Comment ?`** : guide pédagogique facultatif, potentiellement multi-gestes, résolu côté application par `action + ingrédient + équipement + contexte`; ne modifie jamais le déroulé ni le scheduler.

**Exemple** : `Émincer` + `oignon` → micro-recette « Émincer un oignon » ; `Émincer` + `ail` → micro-recette « Émincer de l'ail ». L'action reste `Émincer` dans les deux cas.

Le vocabulaire ci-dessous est un **inventaire de verbes candidats à qualifier**, dont les IDs en anglais ne sont que des clés internes d'exploration. Il ne faut pas confondre les familles de visuels `cooking_actions.py` avec des actions syntaxiques ni avec la bibliothèque de guides.

## Propositions de marqueurs d'action, à prioriser et valider

| Verbe d'action suggéré (clé exploratoire) | Exemples constatés dans le corpus pilote | Micro-recette « Comment ? » potentielle côté application | Priorité |
| --- | --- | --- | --- |
| Racler (`scrape-bowl-walls`) | « Racler les parois avec la #spatule{}. » — bolognaise et tzatziki | `thermomix.scrape-bowl-walls` (témoin créé) | P0 |
| Mixer (`blend`) | « Mixer ~{5 s} à vitesse 5. » — bolognaise et tzatziki | `thermomix.blend`, sans inventer des réglages différents | P1 |
| Couper (`cut-into-pieces`) | « Couper les légumes en morceaux. » et « Couper le @concombre{} en tronçons… » | `knife.cut-into-pieces` avec sous-type/contextualisation | P1 |
| Éplucher (`peel`) | « Éplucher… » — bolognaise | `knife.peel-vegetable` (si matériel déterminé et conseil pertinent) | P1 |
| Pulser (`turbo-pulse`) | « Donner une impulsion turbo de ~{1 s}. » — tzatziki | `thermomix.turbo-pulse` ; revue par modèle requise | P1 |
| Dégorger (`drain-by-resting`) | « Laisser dégorger ~{30 min}… » — tzatziki | `vegetable.drain-by-salting` ; distinguer attente passive et geste | P1 |
| Presser (`squeeze-out-water`) | « Presser le concombre pour en extraire l'eau. » — tzatziki | `vegetable.squeeze-out-water` | P1 |
| Transvaser (`transfer`) | « Transvaser dans une passoire. » — tzatziki | Conseil technique seulement s'il apporte une valeur réelle | P2 |
| Mélanger (`stir`) | « Mélanger à la spatule pour décoller le fond… » — bolognaise | `spatula.stir-and-scrape` : à distinguer de `scrape-bowl-walls` | P2 |
| Ajouter (`add-ingredient`) | « Ajouter le @yaourt grec… », « Ajouter le @poivre… » — tzatziki | **Pas de « Comment ? » générique par défaut** : conseil souvent inutile | À exclure du pilote |

Les propositions P1/P2 ne sont **pas** des textes culinaires prêts à publier. Ne pas transformer des réglages Thermomix spécifiques à la recette en conseils universels.

## Questions à résoudre avant le code

1. Comment exposer le marqueur d'action syntaxique **par sous-étape atomique**, sans confondre les crochets des phases CookiGram avec les marqueurs Gram officiels ?
2. Comment attribuer un identifiant stable à chaque **sous-étape atomique**, aujourd'hui souvent identifiée par un index dans une macro-étape ?
3. Quelles associations `action + ingrédient + équipement` sont sûres et déterministes, et lesquelles doivent rester sans micro-recette si le contexte est ambigu ?
4. Comment gérer les variantes (Thermomix/cocotte) et le niveau de compétence sans dupliquer la technique ?
5. Quel jeu de tests empêche les conseils génériques d'introduire des durées, vitesses, quantités, instructions de sécurité ou gestes non présents dans la recette ?

## Séquence d'exécution recommandée

1. Valider manuellement les **verbes d'action proposés**, puis vérifier le lien effectif avec chaque atome de nos recettes avant tout mapping automatique.
2. Revoir la fiche candidate `thermomix.scrape-bowl-walls` comme micro-recette potentielle (documentation `techniques.yaml` encore non normative) : exactitude, sécurité, provenance, formulation.
3. Éprouver un resolver fail-closed `action syntaxique → contexte ingrédient/matériel → micro-recette`, **sur fixtures uniquement** ; aucun mapping par simple mot-clé ou par illustration.
4. Comparer clic/toucher/clavier et aperçu au survol à l'UX actuelle #541 ; conserver les deux boutons du footer tant que le changement n'a pas été validé.
5. Décider ensuite si un format optionnel doit être normé dans Contract et si les `[Action]` de Gram sont un point d'interopérabilité.

**Gates** : #541 (pilote), #499 (atomicité), #318 (Catalog/Contract/Core), #391 (illustrations/instance), #642 (audit technique read-only). Aucun merge ni déploiement sur la seule base de cette proposition.
