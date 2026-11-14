# Pilot #656 — réutiliser le « Comment ? » d'une action

**Statut : expérimental, non validé et non connecté au build.**

## Objet

Tester la proposition « un savoir-faire réutilisable peut être référencé par plusieurs recettes » sans modifier les recettes, le pilote Why/How #541, le contrat public ni Core.

Le fichier `techniques.yaml` contient **un seul** exemple : `thermomix.scrape-bowl-walls`, relié aux sous-étapes « Racler les parois avec la #spatule{}. » des recettes `sauce-bolognaise-rapide` et `tzatziki-grec`.

Les références sont des **témoins documentaires** basés sur la version consultée des recettes ; elles ne constituent **pas** un mécanisme de recherche automatique et n'ont ni garantie de stabilité ni index atomique contractuel. La résolution future devra utiliser des identifiants stables et vérifier les variantes finales, les ingrédients/matériels et le texte courant avant affichage.

## Distinctions sémantiques

- **Quoi** : l'instruction canonique issue de la recette `.gram`.
- **Comment générique** : technique partageable, associée à une action et à un contexte matériel précis ; ne doit jamais remplacer l'instruction.
- **Comment contextuel** : précision approuvée pour une recette/variante précise ; prioritaire sur le générique quand les deux existent.
- **Pourquoi** : justification liée à l'objectif culinaire de l'étape ; demeure principalement spécifique à la recette.

Une famille visuelle de `generator/cooking_actions.py` (par ex. `mix`) est trop large pour identifier avec certitude une technique pédagogique ; **aucun appariement automatique fondé uniquement sur `visual_action`**.

## Sélection proposée pour une future implémentation

1. Priorité à l'aide `how` recette + variante explicitement revue (pilote #541), si présente et applicable à l'action affichée.
2. Sinon, technique générique revue, correspondance exacte ou sémantiquement démontrée avec l'action atomique et son contexte.
3. Sinon, aucune aide. Ne pas hériter d'une autre variante, d'un matériel voisin ou d'une action homonyme.

Le contenu `how_candidate` n'est **pas approuvé** ; `reviewed_how: null` signifie absence d'aide publiable. Les champs `review.culinary` et `review.appliance_safety` sont `pending`. Une revue culinaire et des sources suffisantes sont nécessaires avant toute adoption, surtout pour un geste lié à un appareil.

## UX à tester, non décidée

Sur ordinateur, un survol pourrait offrir un bref aperçu, mais **le clic doit être possible** ; sur mobile, toucher ; au clavier, focus + activation. Conserver les aides facultatives sans bouton inutile lorsque le contenu est absent. Ne pas remplacer d'office les deux commandes « Pourquoi / Comment » du pilote #541. Toute interaction doit préserver minuteurs, cases à cocher, navigation et TTS.

## Ownership

- **Catalogue / instance** : fiches pédagogiques, provenance, contextes et éventuels médias.
- **Contract** : seulement un schéma optionnel stable *si* la fonctionnalité est adoptée ; aucune extension requise dans cette expérience.
- **Core** : résolution/présentation avec feature flag, fixtures et tests, dans une PR ultérieure distincte.
- **Gram** : possible futur point d'interopérabilité pour l'identité des actions, sans migration de syntaxe requise.

## Non-objectifs / gates

Aucun fichier `.gram`, sidecar `pilot/step-enrichment/v0/pilot-541.yaml`, code de génération, écran de Cook Mode ni configuration CI ne change. Ne pas modifier les audits read-only #640–#644 et éviter d'interférer avec l'atomicité #499.

Avant une implémentation : revue culinaire, décision Human Owner, validation de l'identité atomique, contrôle du découplage #318, qualification sur les deux recettes et test de non-régression du pilote existant.

Références : [#541](https://github.com/CookiGram/cookigram/issues/541), [#499](https://github.com/CookiGram/cookigram/issues/499), [#642](https://github.com/CookiGram/cookigram/issues/642), [#656](https://github.com/CookiGram/cookigram/issues/656).
