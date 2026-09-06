# CookiGram 🍳

[![CI](https://github.com/CookiGram/cookigram/actions/workflows/ci.yml/badge.svg)](https://github.com/CookiGram/cookigram/actions/workflows/ci.yml)
[![Deploy GitHub Pages](https://github.com/CookiGram/cookigram/actions/workflows/pages.yml/badge.svg)](https://github.com/CookiGram/cookigram/actions/workflows/pages.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Gram Language](https://img.shields.io/badge/Gram-Gram%20Language-orange.svg)](https://gram-lang.org)

> A structured Gram recipe notebook designed for real cooking at the counter.

🌐 **Published site:** [cookigram.github.io/cookigram](https://cookigram.github.io/cookigram/)<br>
🇫🇷 **Français:** [README.md](README.md) · 🤝 **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)

## This repository

`PierreCsn/cookigram` is CookiGram’s public content repository. It contains:

- structured [Gram](https://gram-lang.org/) recipes in [`recipes/`](recipes/);
- the ingredient database and provenance in [`.gram/`](.gram/);
- published illustrations in [`static/images/`](static/images/);
- generation prompts and metadata in [`image-prompts/`](image-prompts/);
- editorial rules and agent skills in [`AGENTS.md`](AGENTS.md) and [`.agents/`](.agents/).

Recipes and their sources are the authority. Contributions may improve wording or structure, but must not silently invent quantities, timings, appliance compatibility, or provenance.

## Boundary with the private engine

The generation engine, full Gram parser and validator, static site/PWA, and application test suites live in [`CookiGram/cookigram-core`](https://github.com/CookiGram/cookigram-core), a private repository.

This repository therefore does not contain the engine code and cannot be built standalone. [`.core-version`](.core-version) pins the engine commit used by CI and deployment; it is not a package to install from this repository.

## Available validation

CI selects the available level of validation:

- with the Core secret, it installs the pinned commit, runs `recipe_check` over the corpus, and builds the site;
- for a public pull request or fork without the secret, it validates YAML syntax in [`.gram/`](.gram/) and checks image/prompt pairs with [`scripts/audit-recipe-images.py`](scripts/audit-recipe-images.py);
- GitHub Pages deployment uses the private engine and runs only after successful CI.

The public checks can be run from the repository root:

```bash
python -c "import yaml, glob; [yaml.safe_load(open(f, encoding='utf-8')) for f in glob.glob('.gram/*.yaml')]"
python scripts/audit-recipe-images.py --check
python scripts/lint-public-content.py --mode blocking --format json
```

The full `python -m generator.recipe_check` validator, build, and Python/JavaScript test suites are not present in this repository; they require an authorized installation of `cookigram-core`. Do not treat `npm`, `pytest`, `ruff`, or `generator` commands as local prerequisites here.

## Recipe format

A `.gram` recipe combines YAML frontmatter with structured cooking actions. Every used ingredient must resolve in [`.gram/ingredients.yaml`](.gram/ingredients.yaml); new nutritional or physical data must be sourced in [`.gram/ingredient-provenance.yaml`](.gram/ingredient-provenance.yaml).

```gram
---
title: Lemon roast chicken
portions: 4
prep_time: 15 min
total_time: 1 h 05 min
spiciness: 0
description: Golden chicken with a short lemon and garlic jus and crisp, deeply browned skin.
tags: [chicken, oven, family]
source: https://example.com/lemon-chicken
author: Recipe author
---

[Prepare]
- Rub @chicken{1.5 kg} with @coarse salt{1 tbsp} and @fresh thyme{4 sprigs}.

[Roast]
- Roast on a #sheet pan{} at ^{200 C} for ~{50 min}, until the skin is deeply golden.
```

Keep phases readable and atomic: one gesture or setting per bullet, measurable quantities, observable doneness cues, and explicitly verified appliance compatibility. See the [Gram documentation](https://gram-lang.org/docs/) and [`import-recipe-gram`](.agents/skills/import-recipe-gram/SKILL.md) for detailed import guidance.

## Images and licensing

Recipes may reference an image under `static/images/` and, for generated artwork, a matching prompt under `image-prompts/`. Credits and terms are kept in the recipe frontmatter. Read [`generate-recipe-image`](.agents/skills/generate-recipe-image/SKILL.md) before replacing artwork.

## Related documents

- [Charter](CHARTER.md) · [Product principles](PRODUCT_PRINCIPLES.md)
- [Contribution guide](CONTRIBUTING.md)
- [Recipe import requests](.github/ISSUE_TEMPLATE/recipe_request.md)
- [CI](.github/workflows/ci.yml) · [Pages deployment](.github/workflows/pages.yml)

## License

This repository is released under the [MIT License](LICENSE). Recipes, images, and external sources may have additional terms recorded in their metadata.