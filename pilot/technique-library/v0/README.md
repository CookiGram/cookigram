# Pilot #656 — réutiliser le « Comment ? » d'une action

**Statut : expérimental, non validé et non connecté au build.**

## Objet

Tester la proposition « un savoir-faire réutilisable peut être référencé par plusieurs recettes » sans modifier les recettes, le pilote Why/How #541, le contrat public ni Core.

Le fichier `techniques.yaml` contient **un seul** exemple : `thermomix.scrape-bowl-walls`, relié aux sous-étapes « Racler les parois avec la #spatule{}. » des recettes `sauce-bolognaise-rapide` et `tzatziki-grec`.

Les références sont des **témoins documentaires** basés sur la version consultée des recettes ; elles ne constituent **pas** un mécanisme de recherche automatique et n'ont ni garantie de stabilité ni index atomique contractuel. La résolution future devra utiliser des identifiants stables et vérifier les variantes finales, les ingrédients/matériels et le texte courant avant affichage.

## Correction de frontière : action syntaxique → micro-recette CookiGram

**Décision de conception proposée (14 novembre 2026)** : l'action appartient d'abord à la **syntaxe de la recette** ; l'application résout éventuellement une **micro-recette pédagogique « Comment ? »** en fonction de cette action, de l'ingrédient et du matériel.

La syntaxe officielle de Gram accepte un marqueur d'action optionnel en début d'étape, par exemple :

```gram
[Émincer] l'@oignon{1}.
```

Source : https://gram-lang.org/docs/reference/syntax/document-structure/ — *Action verbs*. Le marqueur porte le **verbe de l'action**, pas la méthode détaillée. Ne pas créer un verbe syntaxique distinct pour `émincer-oignon` et `émincer-ail`.

**Attention à l'état de CookiGram** : dans notre dialecte de production, `[Hacher le soffritto]` nomme actuellement une *macro-phase* et chaque `- ...` est une sous-étape atomique. Il n'existe **pas encore** de marqueur d'action Gram officiel distinct pour chaque sous-étape dans notre parser. C'est une frontière à étudier avant tout rattachement automatique ; ce pilote n'introduit aucune nouvelle syntaxe.

Exemples conceptuels de résolution côté **application**, pas des éléments de grammaire :

| Action syntaxique | Ingrédient / matériel contextualisé | Micro-recette « Comment ? » choisie |
| --- | --- | --- |
| `Émincer` | oignon + couteau | `how.emincer-oignon-couteau` |
| `Émincer` | ail + couteau | `how.emincer-ail-couteau` |
| `Émincer` | ingrédient compatible sans spécialisation | `how.emincer-generique` si revue et réellement appropriée |
| `Racler` | bol Thermomix + spatule | `how.racler-parois-thermomix` |
| `Ajouter` | sel | aucun, sauf besoin pédagogique explicite |

Ces IDs sont des **illustrations conceptuelles**, pas des identifiants stabilisés ni un contenu publié. Les noms des techniques ne doivent pas polluer le langage Gram.

### Trois identités et une aide effective

- **Action syntaxique** : le marqueur de méthode/verb de Gram (quand réellement disponible dans l'AST) ; le texte de la recette conserve l'ingrédient, les quantités, les réglages et l'ordre. Une normalisation des synonymes, si nécessaire, relève d'un adapter CookiGram.
- **Occurrence atomique** : action exécutée dans une recette/variante/phase précise, avec son identité stable pour la progression (#499). Elle ne se confond ni avec le verbe syntaxique ni avec l'aide.
- **Micro-recette pédagogique** : contenu applicatif versionné expliquant la réalisation d'un geste générique ou spécialisé pour un ingrédient/outil ; réutilisable dans plusieurs recettes. Elle peut contenir plusieurs gestes explicatifs, exemples ou visuels, **sans injecter de nouvelles actions obligatoires, durées, ingrédients ou dépendances dans la recette principale**.

Le résultat de la résolution est **0..1 « Comment ? » par occurrence atomique**. Une même micro-recette peut être réutilisée dans de nombreuses occurrences compatibles. Le « Pourquoi ? » reste plutôt lié au contexte de la recette.

Ce mécanisme n'est **pas** le `@use` de Gram : `@use` importe une préparation réelle dans la recette et sa planification ; nos micro-recettes sont des **aides pédagogiques facultatives**, sans effet sur la planification.

### Propagation et contrôle d'impact

L'application peut sélectionner automatiquement une micro-recette approuvée d'après l'action syntaxique, puis l'ingrédient/objet concerné, le matériel, la variante et d'éventuelles préconditions. Une action présente dans 40 recettes peut ainsi recevoir une aide partagée sans éditer 40 fichiers `.gram`.

Le resolver doit être **déterministe et fail-closed** : même verbe n'implique pas même geste, un matériel non reconnu ou un contexte ambigu entraîne l'absence d'aide, pas un conseil incorrect. Ne pas déduire une micro-recette de `visual_action` seul ou d'une recherche par sous-chaîne.

Lors d'une modification de micro-recette partagée, produire la **liste des recettes, variantes et occurrences concernées**, détecter les exceptions et requalifier le conseil avant publication. La propagation est effective au prochain build (ou chargement, selon l'architecture future), jamais en réécrivant silencieusement les recettes.

**Le fichier `techniques.yaml` existant reste un témoin documentaire « Racler les parois »**, à deux occurrences liées manuellement. Il ne démontre **ni** la présence effective de marqueurs syntaxiques sur ces atomes dans CookiGram **ni** la propagation automatique. Son schéma et son nom ne sont pas normatifs ; une éventuelle migration vers un format `microrecipes` fera l'objet d'un changement séparé et qualifié.

## Sélection proposée pour une future implémentation

1. Priorité à l'aide `how` recette + variante explicitement revue (pilote #541), si présente et applicable à l'action atomique affichée.
2. Sinon, micro-recette **spécialisée** approuvée : action + ingrédient/objet + équipement + contexte compatibles.
3. Sinon, micro-recette **générique** approuvée pour cette action, si elle reste pertinente pour cet ingrédient et ce matériel.
4. Sinon, aucune aide. Ne pas hériter d'une autre variante, d'un matériel voisin ou d'une action homonyme.

Le contenu `how_candidate` n'est **pas approuvé** ; `reviewed_how: null` signifie absence d'aide publiable. Les champs `review.culinary` et `review.appliance_safety` sont `pending`. Une revue culinaire et des sources suffisantes sont nécessaires avant toute adoption, surtout pour un geste lié à un appareil.

## UX à tester, non décidée

Sur ordinateur, un survol pourrait offrir un bref aperçu, mais **le clic doit être possible** ; sur mobile, toucher ; au clavier, focus + activation. Conserver les aides facultatives sans bouton inutile lorsque le contenu est absent. Ne pas remplacer d'office les deux commandes « Pourquoi / Comment » du pilote #541. Toute interaction doit préserver minuteurs, cases à cocher, navigation et TTS.

## Ownership

- **Catalogue / instance** : bibliothèque de micro-recettes pédagogiques, provenance, spécialisations et éventuels médias.
- **Contract** : seulement un schéma optionnel stable *si* la fonctionnalité est adoptée ; aucune extension requise dans cette expérience.
- **Core** : adapter entre la syntaxe/parsing des actions et les occurrences atomiques, résolution contextuelle, présentation avec feature flag, fixtures et tests ; PR ultérieure distincte.
- **Gram** : propriétaire de la syntaxe du marqueur d'action `[Verbe]` dans le langage officiel ; aucune bibliothèque de micro-recettes à imposer upstream.

## Non-objectifs / gates

Aucun fichier `.gram`, sidecar `pilot/step-enrichment/v0/pilot-541.yaml`, code de génération, écran de Cook Mode ni configuration CI ne change. Ne pas modifier les audits read-only #640–#644 et éviter d'interférer avec l'atomicité #499.

Avant une implémentation : revue culinaire, décision Human Owner, validation de l'identité atomique, contrôle du découplage #318, qualification sur les deux recettes et test de non-régression du pilote existant.

Références : [#541](https://github.com/CookiGram/cookigram/issues/541), [#499](https://github.com/CookiGram/cookigram/issues/499), [#642](https://github.com/CookiGram/cookigram/issues/642), [#656](https://github.com/CookiGram/cookigram/issues/656).
