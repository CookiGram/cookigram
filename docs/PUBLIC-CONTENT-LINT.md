# Linter public SEO/content

[`scripts/lint-public-content.py`](../scripts/lint-public-content.py) est un contrôle local et CI, déterministe et sans appel réseau. Il lit uniquement le frontmatter des `recipes/*.gram` et produit par défaut un objet JSON stable sur la sortie standard.

## Règles

Les erreurs bloquantes sont : frontmatter absent, fermé incorrectement ou non mapping (`E001`, `E004`), YAML invalide (`E002`), clé YAML dupliquée (`E003`), type ou contenu obligatoire invalide (`E005`, `E006`), et date mal formée (`E007`). Les champs obligatoires minimaux sont `title`, `description` et `tags`.

Les longueurs SEO ne prennent aucune décision éditoriale : elles signalent seulement une recommandation mesurable (`W001` : titre 30–60 caractères ; `W002` : description 70–160 caractères). Elles restent des avertissements même en mode bloquant. Aucun vocabulaire de tags n’est imposé : la règle existante est seulement « liste non vide, chaînes non vides, sans doublon insensible à la casse ».

Les dates dont la clé est `date`, se termine par `_date` ou `_at` (par exemple `image_generation.generated_at`) doivent être ISO 8601. Les dates calendaires `YYYY-MM-DD` du corpus sont acceptées.

## Utilisation et compatibilité fork

Depuis la racine, sans secret Core ni moteur privé :

```bash
python scripts/lint-public-content.py --json
python scripts/lint-public-content.py --check --warn-only --json
```

`--check` retourne le code 1 si une erreur est trouvée et le code 0 sinon ; sans `--check`, le rapport retourne toujours le code 0. `--warn-only` conserve les dépassements de longueur du titre et de la description comme avertissements transitoires, tandis que les doublons de clés YAML et les autres règles restent bloquants. Le JSON contient `version`, `files`, `summary` et une liste `findings` triée par chemin de recette ; chaque finding contient `path`, `line`, `rule`, `level` et `message`.

Le linter est ajouté après le contrat YAML public et l’audit image dans la CI. Ces deux contrôles existants restent inchangés. Comme aucun build ni sortie HTML n’est présent dans ce dépôt de contenu, il ne valide pas de JSON-LD généré : le JSON produit ici est le rapport structuré du linter. La validation des données structurées rendues reste du ressort de `cookigram-core` quand il est disponible.

La CI exécute le mode bloquant sur les forks sans transmettre de secret. Le seuil de longueur est volontairement non bloquant pour ne pas convertir un conseil SEO en réécriture automatique ou en décision éditoriale.
