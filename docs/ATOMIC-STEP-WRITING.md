# Aide-mémoire — écrire des sous-étapes atomiques (gate strict-atomic, #359)

Objet : formuler les puces `- ` des recettes `.gram` pour passer le gate
`Strict atomic check on changed recipes` (job `Build qualified Pages artifact`).
Référence : issue #359. Ne pas confondre avec
[`ATOMIC_ACTION_ILLUSTRATIONS.md`](ATOMIC_ACTION_ILLUSTRATIONS.md), qui traite
des visuels d'instance, pas de la rédaction.

## Règle

1 puce = **1 seul verbe d'action, d'une seule famille** (CUIRE, INCORPORER,
MELANGER, DECOUPER, …), avec ses compléments (quantités `@…{}`, réglages
`^{}`, durées `~{}`, équipement `#…{}`) et, pour les cuissons, l'état d'arrêt
observable conservé sur la puce de cuisson.

Interdits dans une même puce entre deux verbes de familles différentes :
`et`, `puis`, `avant de` (règles `ATOMIC_MULTIPLE_ACTION_VERBS` et
`ATOMIC_SUCCESSION_CONJUNCTION`).

## Catalogue vérifié (lignes passées au gate sur PR mergées)

**CUIRE** : `- Cuire à ^{200 C} ~{35 min}, en les retournant à mi-cuisson.`
(`recipes/air-fryer-ailes-poulet-croustillantes.gram`, #459) ;
`- Faire suer ~{3 min}.` (barbacoa, #453).

**INCORPORER** : `- Verser l'@huile d'olive{15 g, ~1 c. à soupe}.` ;
`- Ajouter les @flocons d'avoine{50 g}.`

**MELANGER** : `- Mélanger jusqu'à homogénéité.`

**DECOUPER** : `- Couper les @patates douces{2 pièces} en bâtonnets de 1/2 cm.`
(#454).

**Réglage / divers** : `- Baisser le feu sous la cocotte.` ;
`- Préchauffer le #four{} à 150°C (chaleur tournante).` ;
`- Réserver dans un #saladier{}.` ; `- Servir.`

## Avant / après types (corrections #359 de la session)

- `- Disposer … et cuire …` → `- Disposer … .` + `- Cuire … .`
- `- Badigeonner …, puis cuire …` → `- Badigeonner … .` + `- Cuire … .`
- `- … avant de servir.` → `- … .` + `- Servir.`
- `- Juste avant de manger, ajouter …` → `- Ajouter … au moment de manger.`
  (préserve l'info de timing sans la conjonction flaggée).

Ne rien inventer : découper à la ponctuation existante, reprendre quantités,
températures, durées et équipements verbatim. Ne corriger que les lignes
flaggées par la CI.

## Limites

Le mapping verbe → famille vit dans Core privé (`cookigram-core`) et n'est
pas vérifiable localement : la CI fait foi. Contrôles locaux avant push :
`python scripts/lint-public-content.py --check`,
`python scripts/audit-recipe-images.py --check`,
`pytest tests/test_public_content_lint.py`.
