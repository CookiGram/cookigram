# #656 — propositions initiales d'actions et techniques « Comment ? »

**Inventaire de travail non normatif**, dérivé de deux recettes actuelles :
`recipes/sauce-bolognaise-rapide.gram` et `recipes/tzatziki-grec.gram`.
Aucune action ci-dessous n'est ajoutée au langage Gram ou à un catalogue de techniques approuvé.

## Deux identités distinctes

- **Action culinaire** : opération exécutée et validée individuellement par le cuisinier ; la doctrine d'atomicité v2 (#499) reste l'autorité. Une action exécutée a besoin d'une identité stable par occurrence.
- **Technique « Comment ? »** : méthode pédagogique partageable référencée par zéro, une ou plusieurs occurrences d'actions. Son identité est réutilisable entre recettes.

Les `[Verbe]` de Gram sont des étiquettes optionnelles de méthode, **pas un dictionnaire fermé de techniques**. Nos identifiants proposés ci-dessous sont internes/expérimentaux ; ils ne changent pas la syntaxe des recettes. Ne pas assimiler les 16 catégories de visuels `cooking_actions.py` à des techniques pédagogiques suffisamment précises.

## Catalogue de propositions, à prioriser et valider

| Action candidate (ID provisoire) | Exemples constatés dans le corpus pilote | Technique « Comment ? » potentielle | Priorité |
| --- | --- | --- | --- |
| `scrape-bowl-walls` | « Racler les parois avec la #spatule{}. » — bolognaise et tzatziki | `thermomix.scrape-bowl-walls` (témoin créé) | P0 |
| `blend` | « Mixer ~{5 s} à vitesse 5. » — bolognaise et tzatziki | `thermomix.blend`, sans inventer des réglages différents | P1 |
| `cut-into-pieces` | « Couper les légumes en morceaux. » et « Couper le @concombre{} en tronçons… » | `knife.cut-into-pieces` avec sous-type/contextualisation | P1 |
| `peel` | « Éplucher… » — bolognaise | `knife.peel-vegetable` (si matériel déterminé et conseil pertinent) | P1 |
| `turbo-pulse` | « Donner une impulsion turbo de ~{1 s}. » — tzatziki | `thermomix.turbo-pulse` ; revue par modèle requise | P1 |
| `drain-by-resting` | « Laisser dégorger ~{30 min}… » — tzatziki | `vegetable.drain-by-salting` ; distinguer attente passive et geste | P1 |
| `squeeze-out-water` | « Presser le concombre pour en extraire l'eau. » — tzatziki | `vegetable.squeeze-out-water` | P1 |
| `transfer` | « Transvaser dans une passoire. » — tzatziki | Conseil technique seulement s'il apporte une valeur réelle | P2 |
| `stir` | « Mélanger à la spatule pour décoller le fond… » — bolognaise | `spatula.stir-and-scrape` : à distinguer de `scrape-bowl-walls` | P2 |
| `add-ingredient` | « Ajouter le @yaourt grec… », « Ajouter le @poivre… » — tzatziki | **Pas de « Comment ? » générique par défaut** : conseil souvent inutile | À exclure du pilote |

Les propositions P1/P2 ne sont **pas** des textes culinaires prêts à publier. Ne pas transformer des réglages Thermomix spécifiques à la recette en conseils universels.

## Questions à résoudre avant le code

1. Doit-on conserver le verbe affiché dans la recette, mais résoudre séparément un `action_kind` et un `technique_id` contextualisé ?
2. Comment attribuer un identifiant stable à chaque **sous-étape atomique**, aujourd'hui souvent identifiée par un index dans une macro-étape ?
3. Quelles correspondances peuvent être déterministes et quelles actions doivent rester sans aide si la technique est ambiguë ?
4. Comment gérer les variantes (Thermomix/cocotte) et le niveau de compétence sans dupliquer la technique ?
5. Quel jeu de tests empêche les conseils génériques d'introduire des durées, vitesses, quantités, instructions de sécurité ou gestes non présents dans la recette ?

## Séquence d'exécution recommandée

1. Valider manuellement les **actions proposées**, identifier le premier vocabulaire utile et rejeter les intitulés trop larges.
2. Revoir la seule fiche `thermomix.scrape-bowl-walls` : exactitude, sécurité, provenance, formulation.
3. Éprouver un resolver fail-closed sur les deux occurrences, **sur fixtures uniquement** ; aucun mapping par simple mot-clé ou par illustration.
4. Comparer clic/toucher/clavier et aperçu au survol à l'UX actuelle #541 ; conserver les deux boutons du footer tant que le changement n'a pas été validé.
5. Décider ensuite si un format optionnel doit être normé dans Contract et si les `[Action]` de Gram sont un point d'interopérabilité.

**Gates** : #541 (pilote), #499 (atomicité), #318 (Catalog/Contract/Core), #391 (illustrations/instance), #642 (audit technique read-only). Aucun merge ni déploiement sur la seule base de cette proposition.
