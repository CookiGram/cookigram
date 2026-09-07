# Contribuer à CookiGram 🍳

Merci de contribuer au carnet de recettes public CookiGram. Ce dépôt accueille le contenu culinaire ; le moteur de génération et l’application sont maintenus séparément dans [`PierreCsn/cookigram-core`](https://github.com/PierreCsn/cookigram-core), un dépôt privé.

## Ce qui est dans le périmètre

Les changements attendus ici concernent les recettes `.gram`, [`.gram/ingredients.yaml`](.gram/ingredients.yaml), [`.gram/ingredient-provenance.yaml`](.gram/ingredient-provenance.yaml), les illustrations, les prompts et la documentation éditoriale. Ne modifiez pas le moteur, le build ou le code applicatif dans ce dépôt.

## Ajouter ou corriger une recette

1. Créez ou modifiez `recipes/<slug>.gram`.
2. Résolvez chaque `@ingrédient{quantité}` dans [`.gram/ingredients.yaml`](.gram/ingredients.yaml). Pour toute nouvelle donnée nutritionnelle ou physique, ajoutez sa source dans [`.gram/ingredient-provenance.yaml`](.gram/ingredient-provenance.yaml).
3. Respectez la structure Gram : phases `[Action]`, puces atomiques `- `, quantités mesurables, réglages appareil explicites et critère sensoriel de fin.
4. Ajoutez ou mettez à jour l’image dans `static/images/` et le prompt dans `image-prompts/` si nécessaire. Les chemins sont relatifs à la racine du dépôt.

## Contrôles locaux réellement disponibles

Depuis la racine du dépôt :

```bash
python -c "import yaml, glob; [yaml.safe_load(open(f, encoding='utf-8')) for f in glob.glob('.gram/*.yaml')]"
python scripts/audit-recipe-images.py --check
python scripts/lint-public-content.py --check --warn-only --json
```

Le second contrôle échoue lorsqu’un prompt déclare une image placeholder, une image absente ou un prompt absent. Le linter SEO/content et ses règles sont décrits dans [`docs/PUBLIC-CONTENT-LINT.md`](docs/PUBLIC-CONTENT-LINT.md). Le validateur Gram complet et le build ne sont pas installés ici : ils appartiennent à `cookigram-core` et sont exécutés par la CI lorsque le secret du moteur est disponible. Les PR publiques sans ce secret passent par le contrôle YAML, l’audit des images et le linter public.

Ne lancez pas et ne documentez pas ici `cookigram check`, `python -m generator...`, `npm`, `pytest` ou `ruff` comme commandes locales : ces outils ne sont pas présents dans ce dépôt de contenu.

## Images

Utilisez un nom en kebab-case dérivé du slug. Une image finale est placée dans `static/images/<slug>.<ext>`, et son prompt dans `image-prompts/<slug>.md`. Pour le style et les métadonnées, consultez [`generate-recipe-image`](.agents/skills/generate-recipe-image/SKILL.md).

## Contributions assistées par agent

Pour importer une recette depuis le Web, commencez par le formulaire [`recipe_request.md`](.github/ISSUE_TEMPLATE/recipe_request.md), puis suivez [`import-recipe-gram`](.agents/skills/import-recipe-gram/SKILL.md). Conservez l’URL et l’auteur de la source, et signalez toute incertitude qui affecte la préparation.

## Pull request

Décrivez le contenu modifié, les sources utilisées et les contrôles exécutés. Une PR doit rester limitée au contenu et à la documentation de ce dépôt. La CI et, après succès, le workflow [GitHub Pages](.github/workflows/pages.yml) gèrent la validation complète et la publication.
