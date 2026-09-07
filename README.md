# CookiGram 🍳

[![CI](https://github.com/CookiGram/cookigram/actions/workflows/ci.yml/badge.svg)](https://github.com/CookiGram/cookigram/actions/workflows/ci.yml)
[![Deploy GitHub Pages](https://github.com/CookiGram/cookigram/actions/workflows/pages.yml/badge.svg)](https://github.com/CookiGram/cookigram/actions/workflows/pages.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Gram Language](https://img.shields.io/badge/Gram-Gram%20Language-orange.svg)](https://gram-lang.org)

> Carnet de recettes Gram, pensé pour une exécution claire sur le plan de travail.

🌐 **Site publié :** [cookigram.github.io/cookigram](https://cookigram.github.io/cookigram/)<br>
🇬🇧 **English:** [README.en.md](README.en.md) · 🤝 **Contribuer :** [CONTRIBUTING.md](CONTRIBUTING.md)

## Ce dépôt

`CookiGram/cookigram` est le dépôt public de contenu de CookiGram. Il rassemble :

- les recettes structurées dans [`recipes/`](recipes/) au format [Gram](https://gram-lang.org/) ;
- la base d’ingrédients et ses sources dans [`.gram/`](.gram/) ;
- les illustrations publiées dans [`static/images/`](static/images/) ;
- les prompts et métadonnées de génération dans [`image-prompts/`](image-prompts/) ;
- les règles et compétences éditoriales dans [`AGENTS.md`](AGENTS.md) et [`.agents/`](.agents/).

La recette et ses sources sont la référence. Une contribution peut améliorer la formulation ou la structuration, mais ne doit pas inventer de quantité, de durée, de compatibilité appareil ou de provenance.

## Frontière avec le moteur privé

Le moteur de génération, le parseur et validateur complet Gram, le site statique/PWA, ainsi que les tests applicatifs résident dans [`CookiGram/cookigram-core`](https://github.com/CookiGram/cookigram-core), un dépôt privé.

Ce dépôt ne contient donc pas le code du moteur et ne se construit pas seul. Le fichier [`.core-version`](.core-version) épingle le commit du moteur utilisé par l’intégration continue et le déploiement. Il ne constitue pas une dépendance à installer depuis ce dépôt.

## Validation disponible

La CI adapte son niveau de contrôle à l’accès au moteur :

- avec le secret Core, elle installe le commit épinglé, exécute `recipe_check` sur le corpus et construit le site ;
- pour une PR publique ou un fork sans secret, elle valide la syntaxe YAML de [`.gram/`](.gram/) et contrôle les couples image/prompt avec [`scripts/audit-recipe-images.py`](scripts/audit-recipe-images.py) ;
- le déploiement GitHub Pages utilise le moteur privé et ne s’exécute qu’après une CI réussie.

Les contrôles publics peuvent être lancés depuis la racine du dépôt :

```bash
python -c "import yaml, glob; [yaml.safe_load(open(f, encoding='utf-8')) for f in glob.glob('.gram/*.yaml')]"
python scripts/audit-recipe-images.py --check
python scripts/lint-public-content.py --check --warn-only --json
```

Le validateur complet `python -m generator.recipe_check`, le build et les tests Python/JavaScript ne sont pas disponibles dans ce dépôt ; ils nécessitent une installation de `cookigram-core` autorisée. Ne pas documenter de couverture ou de commande `npm`, `pytest`, `ruff` ou `generator` comme prérequis local ici.

## Format d’une recette

Une recette `.gram` comporte un frontmatter YAML et des actions culinaires structurées. Les ingrédients utilisés doivent être annotés et résolus dans [`.gram/ingredients.yaml`](.gram/ingredients.yaml) ; toute nouvelle donnée nutritionnelle ou physique doit être sourcée dans [`.gram/ingredient-provenance.yaml`](.gram/ingredient-provenance.yaml).

```gram
---
title: Poulet rôti au citron
portions: 4
prep_time: 15 min
total_time: 1 h 05 min
spiciness: 0
description: Poulet doré, jus court au citron et ail confit, servi avec une peau bien croustillante.
tags: [poulet, four, familial]
source: https://example.com/poulet-citron
author: Nom de l’auteur
---

[Préparer]
- Frotter le @poulet{1,5 kg} avec le @gros sel{1 c. à soupe} et le @thym frais{4 brins}.

[Rôtir]
- Enfourner sur une #plaque{} à ^{200 C} pendant ~{50 min}, jusqu’à peau bien dorée.
```

Règles essentielles : étapes lisibles et atomiques, un geste ou réglage par puce, quantités mesurables, checkpoints sensoriels et compatibilité appareil explicitement vérifiée. Le [profil Gram](https://gram-lang.org/docs/) et les consignes détaillées d’import sont dans [`import-recipe-gram`](.agents/skills/import-recipe-gram/SKILL.md).

## Images et licences

Chaque recette publiée peut référencer une image sous `static/images/` et, pour une illustration générée, un prompt correspondant sous `image-prompts/`. Les crédits et conditions d’utilisation sont conservés dans le frontmatter de la recette. Consultez [`generate-recipe-image`](.agents/skills/generate-recipe-image/SKILL.md) avant de remplacer une illustration.

## Documents associés

- [Charte](CHARTER.md) · [Principes produit](PRODUCT_PRINCIPLES.md)
- [Guide de contribution](CONTRIBUTING.md)
- [Demandes d’import de recette](.github/ISSUE_TEMPLATE/recipe_request.md)
- [CI](.github/workflows/ci.yml) · [Déploiement Pages](.github/workflows/pages.yml)

## Licence

Le dépôt est distribué sous [licence MIT](LICENSE). Les recettes, images et sources externes peuvent avoir des conditions supplémentaires indiquées dans leurs métadonnées.
