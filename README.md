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

## Vocabulaire officiel CookiGram

CookiGram assume une identité culinaire française dans son vocabulaire produit. L’objectif n’est pas de laisser toute l’interface en français, mais de conserver quelques concepts de marque reconnaissables tout en traduisant normalement ce qui sert à accomplir une tâche.

> **French culinary identity, locally understandable UX.**

### Modèle produit

- **Cuisine** : une instance CookiGram configurée et déployée. Une Cuisine possède sa propre identité visuelle, ses choix éditoriaux et peut réunir plusieurs Livres de recettes.
- **Grand Chef** : la personne qui configure, maintient et donne sa personnalité à une Cuisine. C’est un rôle éditorial, pas un compte ou un rôle d’autorisation imposé par l’application.
- **Livre de recettes** : une source ou collection cohérente de recettes rattachée à une Cuisine. Une même Cuisine peut avoir plusieurs Livres.
- **Catalogue** : la vue agrégée des recettes proposées par une Cuisine à partir de ses Livres.
- **Panier** : la sélection courante de recettes retenues par l’utilisateur ; c’est le concept derrière `Ma sélection`. **Panier est un terme CookiGram assumé**, y compris dans un contexte international, car son sens est renforcé par une représentation visuelle explicite.
- **Planificateur** : la fonction qui organise les recettes dans le temps. Son libellé d’interface peut évoluer ou être localisé sans changer le concept.
- **Menu** : le résultat de cette organisation temporelle, plutôt que le nom de l’outil lui-même.
- **Courses** : la fonction qui prépare les besoins d’achat à partir de tout ou partie du Panier. Le libellé est descriptif et peut être localisé ; il ne constitue pas un terme de marque à préserver à tout prix.
- **Thème** : l’ambiance visuelle d’une Cuisine. Les thèmes disponibles et leurs noms appartiennent à la Cuisine et sont définis par son Grand Chef ; ils ne constituent pas un vocabulaire global imposé par Core.

### Règle d’internationalisation

Les termes de marque suivants sont destinés à pouvoir rester en français dans toutes les langues : **Cuisine**, **Grand Chef**, **Panier** et **Menu**.

Les termes descriptifs comme **Livre de recettes**, **Catalogue**, **Planificateur**, **Courses** ou **Thème** peuvent être traduits lorsque cela améliore la compréhension locale.

Les actions et messages opérationnels doivent être localisés normalement : ajouter, retirer, réinitialiser, planifier, préparer une liste, états accessibles, aide, erreurs, confirmations, etc.

Un terme français ne doit pas être conservé uniquement pour le style s’il oblige l’utilisateur à apprendre une mécanique. S’il devient difficile à comprendre dans le parcours normal, il doit être renommé, traduit ou remplacé. **Panier fait volontairement exception à cette prudence** parce que l’interface le rend visuel et immédiatement contextualisé.

Ce vocabulaire décrit le modèle mental de CookiGram. Il ne crée pas à lui seul de nouvelle abstraction technique, de permission, de compte ou de chantier d’architecture.

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

## Roadmap interne

Cette roadmap donne une direction au produit ; elle ne remplace ni les issues ni les décisions prises à partir des retours d’usage. Plus l’horizon est lointain, moins les éléments ci-dessous constituent des engagements.

Le principe reste constant : **valider un usage réel avant d’élargir le produit**. CookiGram doit rester Git-first, static-first, sans compte obligatoire, sans backend central requis et sans télémétrie nécessaire à son fonctionnement.

### Court terme — réussir le PoC et ouvrir le pilot

L’objectif immédiat est de rendre CookiGram suffisamment cohérent pour être confié à quelques utilisateurs sans accompagnement constant. Le gate de référence est [#267 — PoC testeurs / READY FOR PILOT](https://github.com/CookiGram/cookigram/issues/267).

Priorités :

- amener les quatre surfaces principales au seuil **READY FOR PILOT** : Catalogue, fiche recette, Planificateur et Courses ;
- terminer la convergence UX de l’accueil : recherche, filtres, tris, sélection et lisibilité desktop/mobile ;
- terminer le polish du Planificateur sans ajouter de sophistication non nécessaire ;
- rendre Courses suffisamment fiable pour une utilisation réelle, notamment sur mobile ;
- conserver une navigation, des thèmes et des états interactifs cohérents entre toutes les pages ;
- faire produire à Core un builder Linux x86_64 versionné, publiquement récupérable et vérifiable ;
- faire construire et déployer ce dépôt avec exactement le même builder que celui destiné aux utilisateurs ;
- permettre à un fork ou à une Cuisine indépendante de déployer son propre GitHub Pages sans accès ni secret vers `cookigram-core` ;
- documenter le parcours minimal puis le faire tester par les premiers utilisateurs externes.

**Garde-fou :** jusqu’au pilot, toute nouvelle fonctionnalité qui n’aide pas directement cette validation doit normalement attendre.

### Moyen terme — consolider le modèle après le pilot

Une fois le PoC validé, l’objectif devient de transformer le parcours démontré en modèle reproductible et maintenable, sans perdre la simplicité qui fait partie du produit.

Sujets probables :

- traiter en priorité les frictions observées chez les testeurs plutôt que les améliorations imaginées en interne ;
- stabiliser le contrat du builder autour d’une transformation simple `sources -> _site/`, avec releases explicites et compatibilité maîtrisée ;
- simplifier la création d’une nouvelle Cuisine : dépôt modèle, configuration minimale et documentation de déploiement ;
- clarifier encore la séparation entre moteur, application générée et contenu afin qu’un dépôt de recettes tiers puisse rester maître de ses données ;
- faire mûrir le modèle Cuisine / Livres / Catalogue lorsque des cas d’usage réels nécessitent plusieurs sources de recettes ;
- continuer à améliorer recherche, tris, thèmes, accessibilité, PWA et usages mobile/offline à partir des retours réels ;
- renforcer les workflows éditoriaux : import, validation Gram, provenance, images et qualité du corpus ;
- durcir la stabilité des builds, des migrations de données locales et des tests de non-régression ;
- expérimenter un premier adaptateur GitLab ou Gitea seulement lorsqu’un besoin concret justifie de sortir du chemin GitHub-first.

À cet horizon, l’absence de compte CookiGram et de collecte d’usage centralisée reste un choix produit à préserver, pas une lacune à corriger par défaut.

### Long terme — sujets d’exploration

Ces sujets décrivent des directions possibles. Ils ne doivent pas influencer prématurément l’architecture du PoC ou du produit à court terme.

- portabilité complète vers plusieurs forges et scénarios auto-hébergés ;
- builders locaux et cibles supplémentaires : macOS, Windows, ARM et environnements sans GitHub Actions ;
- séparation encore plus libre entre une Cuisine, ses Livres et l’application qui les rend, afin de faciliter les écosystèmes de dépôts tiers ;
- planification culinaire plus riche : menus plus longs, calendrier et coordination de préparation lorsque l’usage le justifie ;
- nutrition, inventaire/garde-manger, substitutions et autres données culinaires enrichies, uniquement lorsque leurs sources et règles de calcul sont suffisamment fiables ;
- assistance à l’exécution en cuisine : ordonnancement des tâches, appareils, parallélisation et éventuel Kitchen Scheduler ;
- intégrations optionnelles avec calendriers, assistants domestiques ou autres surfaces de consultation en cuisine ;
- liens entre recettes et production de contenu, notamment les workflows vidéo ;
- circulation et partage de Livres de recettes entre Cuisines sans imposer de plateforme centrale CookiGram.

### Principes qui ne sont pas dans la roadmap

La croissance de CookiGram ne doit pas supposer qu’il faudra un SaaS central, des comptes utilisateurs, du multi-tenant ou du tracking comportemental. Git et les fichiers restent des fondations du modèle, et la sortie statique doit rester suffisamment simple pour pouvoir être servie ailleurs que sur l’infrastructure choisie pour le premier PoC.

Une fonctionnalité lointaine ne doit pas créer de dette architecturale aujourd’hui : **on généralise après avoir appris, pas avant**.

## Documents associés

- [Charte](CHARTER.md) · [Principes produit](PRODUCT_PRINCIPLES.md)
- [Guide de contribution](CONTRIBUTING.md)
- [Demandes d’import de recette](.github/ISSUE_TEMPLATE/recipe_request.md)
- [CI](.github/workflows/ci.yml) · [Déploiement Pages](.github/workflows/pages.yml)

## Licence

Le dépôt est distribué sous [licence MIT](LICENSE). Les recettes, images et sources externes peuvent avoir des conditions supplémentaires indiquées dans leurs métadonnées.
