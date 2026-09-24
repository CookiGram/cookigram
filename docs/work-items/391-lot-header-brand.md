# Work-item 391-lot-header-brand — nom/logo/header pilotés par l'instance

Statut : BLOCKED (contrat Core manquant).

## Objectif

`og:site_name`, nom du header et chemins d'icônes PWA rendus depuis
`site-config.yaml` au lieu de valeurs codées.

## Blocage

Preuve fraîche : `og:site_name content="CookiGram"` codé dans
`category.html`, `cook.html`, `index.html`, `recipe.html` de Core ;
`base.html` code `assets/icons/icon-*.png/svg` sans utiliser
`branding_logo`/`favicon_url` pourtant calculés par le build.
`site-config.yaml` est lu mais non rendu sur ces surfaces.

## Suite

Slots templates Core requis. Ne pas toucher au Core depuis ce dépôt.
Rouvrir après contrat Core.
