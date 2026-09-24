# Work-item 391-lot-typography — enveloppe typographique d'instance

Statut : BLOCKED (contrat Core manquant + outillage E2E côté Core).

## Objectif

Familles typographiques choisies par l'instance dans l'enveloppe
autorisée par Core (cf. tableau #391), sans toucher lisibilité/contraste.

## Blocage

Preuve fraîche : aucune enveloppe `font-family` dans
`generator/instance.py` ni `templates/base.html` de Core ; les specs
E2E vivent dans Core (`e2e/`), pas dans ce dépôt.

## Suite

Décision Core requise (enveloppe + validation). Rouvrir après contrat.
