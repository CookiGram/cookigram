# Work-item 391-lot-ui-icons — mapping du pack d'icônes UI

Statut : BLOCKED (contrat Core manquant).

## Objectif

Permettre à l'instance de choisir son pack d'icônes UI mappé sur les
slots sémantiques Core (cf. #391 : pack graphique et mapping côté instance).

## Blocage

Preuve fraîche : aucun mécanisme `icons/ui`, `ui_pack` ou `icon_pack`
dans `generator/*.py` ni `templates/*.html` de Core ; les icônes UI
sont codées dans les templates/JS Core sans slot référençable.

## Suite

Décision Core requise (slots + validation de config d'instance).
Ne pas toucher au Core depuis ce dépôt. Rouvrir après contrat Core.
