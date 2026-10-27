# Issue #541 — cadrage de l’enrichissement des étapes

État au 27 octobre 2026. Ce document couvre l’audit et la proposition de pilote ;
il ne modifie aucune recette `.gram` et ne vaut ni validation de schéma Core,
ni GO de généralisation.

## Résumé du préflight initial (27 octobre 2026)

- La source de vérité éditoriale est la recette `.gram` du dépôt public. Ses
  quantités, durées, températures, équipements et variantes doivent rester
  intacts pour ce pilote.
- Le moteur, le parseur complet, la génération de préparation et le Mode Cuisine
  vivent dans `cookigram-core`, dépôt privé absent des worktrees voisins
  disponibles ici. Les surfaces UI, les formats d’état de préparation et les
  hooks de navigation/timers ne sont donc pas vérifiables dans cet audit.
- Le choix UX des deux commandes facultatives a été confirmé dans le commentaire
  Human Owner de l’issue #541. Le même fil autorise le pilote, avec les recettes
  et conditions données ci-dessous.
- **STOP pilote initial** : `recipes/tzatziki-grec.gram` était inclus dans un
  claim #499 R2 et la PR #615. La réconciliation fraîche du 27 octobre 2026
  confirme que la PR #615 est fusionnée et qu’aucune PR ouverte #499 n’est
  détectée ; ce motif de collision est levé.
- Aucun claim #541 n’apparaissait au préflight initial.

## Réconciliation fraîche (27 octobre 2026)

`git fetch origin main` a confirmé `origin/main` au commit
`747182d0e932ad12fd3ca1edbded83be6e80d50c`, identique au HEAD local. La PR
[#615](https://github.com/CookiGram/cookigram/pull/615) est `MERGED` (25 octobre
2026) et les recherches de PR ouvertes liées à #499 ne renvoient aucun résultat.
Les trois sources pilotes sont présentes et inchangées depuis le snapshot de ce
cadrage :

```text
osso-buco-milanaise     1c9d1717496ae49eaa39350e2d2504413a16c02596dcf60d9e4d2ff0a669deba
tzatziki-grec           d473b3f1217427ed91971e4f9dab8b3123210acf1388e9b98910a8324e5f21cb
sauce-bolognaise-rapide dc7e3062645b31f704caa48b3c05a3d02408b26e6dada451209ddd0204f6f5f6
```

À cette date, le label d’approbation n’était pas encore posé et aucun claim #541
n’existait ; ce blocage a été levé par la reprise du travail ci-dessous.

## Pilote borné préparé (27 octobre 2026)

À la demande de reprise, #541 porte maintenant `potential-dev-work`. Le claim
#541 a été ajouté dans `.agents/claims.json`, avec le périmètre sidecar et ce
document ; `499-r2` est laissé inchangé malgré son statut `pr_open` périmé. La
PR #615 reste fusionnée. La PR #621 ouverte sur #499 porte sur une autre recette
et ne recoupe pas le périmètre du pilote.

Le sidecar [`pilot/step-enrichment/v0/pilot-541.yaml`](../pilot/step-enrichment/v0/pilot-541.yaml)
contient quatre propositions `Pourquoi ?` / `Comment ?` : deux variantes de
`simmer-veal` pour osso-buco (Thermomix et Instant Pot), et deux étapes de
`sauce-bolognaise-rapide` (faire revenir, mijoter). Les étapes d’origine restent
la source d’instructions : aucun remplacement principal n’est fourni. La
variante cocotte de l’osso-buco est explicitement exclue du pilote, car sa
description annonce 2 h de mijotage et son étape de remplacement 1 h 45. Les
revues indépendantes culinaire/provenance et UX/contrat sont PASS. Les entrées
restent `proposed`; l’acceptation produit reste `pending`.

Le sidecar est expérimental et aucun chargeur/UI Core ne le consomme dans ce
dépôt. La réversibilité consiste à supprimer/désactiver le fichier ; le parcours
actuel n’est donc pas affecté. La recette source de chaque aide est épinglée par
révision Git et SHA-256 de l’intégralité du fichier `.gram`. Tout changement de
hash invalide toutes les aides de cette recette. Le rattachement est uniformément
`step_ref`, combiné à `variant_id`. Les `.gram` doivent rester byte-à-byte
identiques.

Contrôles passés avant PR : chargement YAML du sidecar, validation des clés et
références de recette/variante/étape, comparaison des hashes aux sources, absence
de mutation des `.gram`, puis `git diff --check`. Les contrôles applicatifs des
boutons, timers, cases à cocher, variantes et navigation nécessitent Core et ne
sont pas satisfaits par le seul sidecar ; aucun raccordement Core/UI n’est inclus.

## Audit du corpus pilote

| Recette | État observé | Valeur pour le pilote | Points de contrôle |
| --- | --- | --- | --- |
| `osso-buco-milanaise` | IDs de macro-étapes stables (`make-gremolata`, `brown-soffritto`, `simmer-veal`), variante par défaut Thermomix et remplacements `instant-pot` / `cocotte-fonte` | Braiserie longue, technique et variantes substantielles | Les aides doivent suivre les étapes remplacées ; les temps/gestes cocotte et pression restent propres à leur variante. La cuisson Thermomix à 120 °C exclut TM31, mais la recette publiée le liste encore : point hors scope à ne pas retoucher ici. L’URL exacte Cookidoo et l’auteur de la source ne sont pas vérifiés. |
| `tzatziki-grec` | Quatre macro-actions sans identifiants explicites ; Thermomix TM31/TM5/TM6/TM7, sans variante déclarée | Préparation froide, égouttage et texture | Collision #499/#615 levée après merge. Il faut stabiliser la correspondance d’étape sans changer le `.gram`. |
| `sauce-bolognaise-rapide` | Sept macro-actions sans identifiants explicites ; Thermomix TM5/TM6/TM7, sans variante déclarée | Sofritto, cuisson viande, réduction et repères observables déjà présents | Les aides doivent éviter de répéter l’instruction et ne pas créer de réglage supplémentaire. Recette récemment ajoutée depuis #540 : relire sa provenance avant d’écrire des explications culinaires. |

Hashes SHA-256 du snapshot local au cadrage (27 octobre 2026) :

```text
osso-buco-milanaise     1c9d1717496ae49eaa39350e2d2504413a16c02596dcf60d9e4d2ff0a669deba
tzatziki-grec           d473b3f1217427ed91971e4f9dab8b3123210acf1388e9b98910a8324e5f21cb
sauce-bolognaise-rapide dc7e3062645b31f704caa48b3c05a3d02408b26e6dada451209ddd0204f6f5f6
```

Le choix des trois recettes couvre donc deux procédés cuits (dont braisage et
sauce) et une préparation froide, ainsi que plusieurs voies de cuisson sur
l’osso-buco. La présence de variantes techniques rend le test plus informatif
qu’un échantillon de recettes de structure identique.

## Contrat de données proposé (à valider avec Core)

Ne pas ajouter les explications à la recette canonique ni à la définition
partagée des recettes pendant cette expérimentation. Stocker les propositions
dans un artefact de pilote isolé et versionné, joint à une recette et à une
étape résolue. Une représentation possible :

```yaml
schema: cookigram.step-enrichment.v0
recipe: osso-buco-milanaise
source:
  revision: <git-commit>
  source_recipe_sha256: <sha256-du-fichier-gram>
  url_as_recorded: https://cookidoo.fr
  exact_url_status: non_verifiable
  exact_url: null
  recipe_metadata_author: Pierre Cousin
  source_author: null
generation:
  method: assisted-ai
  model: <identifiant-et-version-exacts>
  prompt_revision: <révision>
  generated_at: <date-utc>
review:
  status: proposed # proposed | culinary-reviewed | accepted | rejected
  reviewer: null
steps:
  - step_ref: macro:simmer-veal
    variant_id: thermomix # default explicite; ou instant-pot / cocotte-fonte
    instruction: null # absent ou null = conserver l'instruction .gram
    why: null
    how: null
```

Règles du contrat :

1. Si aucune entrée d’enrichissement n’existe pour une étape, elle n’a pas d’aide.
   Dans une entrée, `instruction`, `why` et `how` restent facultatifs. Une valeur
   non vide de `why` ou `how` rend uniquement sa commande dédiée, repliée par
   défaut. Champ absent et `null` ont le même sens : aucun contenu, aucune
   commande et aucun espace réservé ; ils ne déclenchent pas d’héritage d’une
   autre variante. Une chaîne vide est invalide. `instruction` absent ou `null`
   signifie conserver exactement l’instruction canonique `.gram`, sans override.
2. Une seule forme de rattachement est utilisée partout : `step_ref` est une
   chaîne canonique. Pour les macro-actions nommées, elle vaut
   `macro:<id-gram>` ; quand aucun ID n’existe, elle vaut
   `macro:<ordinal-1-based>:<titre-normalisé>`. `variant_id` est un champ
   distinct et obligatoire. La paire `variant_id + step_ref` identifie l’étape
   résolue ; aucune forme alternative `step_id` n’est utilisée.
3. Chaque recette porte `source_recipe_sha256`, calculé sur les octets complets du
   fichier `.gram`. Tout écart de hash invalide **toutes** les aides attachées à
   cette recette jusqu’à régénération et revue ; aucun fallback par étape, titre,
   ancien texte ou autre variante n’est permis. Cette invalidation complète
   empêche qu’une aide reste attachée après une modification du contexte recette.
4. Les étapes héritées ne reçoivent que des aides génériques si celles-ci restent
   exactes pour toutes les variantes ; toute aide dépendant d’un équipement,
   réglage, temps ou geste propre à une variante doit la cibler explicitement.
   Les remplacements de variante doivent résoudre leurs propres aides et ne pas
   afficher celles de l’étape remplacée.
5. L’instruction principale ne peut changer silencieusement la procédure. Toute
   proposition qui modifie le geste, l’ordre, une quantité, un temps, une
   température, un équipement ou un état de sécurité est rejetée ou renvoyée à
   une révision de recette distincte, sourcée et approuvée.
6. Conserver snapshot Git, hash de source, provenance/auteur d’origine,
   générateur/modèle/version de prompt, statut et identité de revue humaine.
   La suppression/désactivation du sidecar rétablit exactement l’expérience
   originale ; aucune écriture n’est faite dans les `.gram`.
7. Les textes générés sont statiques au moment de préparation/build. Aucun appel
   de modèle ou service réseau ne doit être requis en Mode Cuisine.

Pour `osso-buco-milanaise`, le fichier `.gram` donne seulement `https://cookidoo.fr`
et indique `Pierre Cousin` comme auteur de la fiche locale. La page exacte
Cookidoo n’a pas été confirmée ; le sidecar garde l’URL enregistrée sous
`url_as_recorded`, marque `exact_url_status: non_verifiable` et ne présente pas
l’auteur de la fiche comme auteur confirmé de la source.

Ce schéma est expérimental et reste à valider côté Core ; le format de référence
du pilote est le `step_ref` ci-dessus.

## Parcours et point d’extension minimal à vérifier dans Core

Le rattachement doit s’effectuer après résolution de la variante et génération
des étapes finales, au moment où la préparation est construite. Ainsi les aides
suivent le même graphe d’étapes que l’exécution. L’UI de la carte d’étape peut
alors afficher deux commandes compactes « Pourquoi ? » et « Comment ? », chacune
ouvrant un contenu replié. Une aide absente ne rend rien. Elles ne doivent pas
modifier l’état des cases, le timer, l’avancement, la navigation ou la progression
persistée.

À confirmer dans Core avant toute implémentation : représentation canonique de
variante/étape dans le modèle chargé ; capacité de préparation à transmettre une
annotation auxiliaire ; mode de distribution/chargement d’un sidecar ; sémantique
des étapes remplacées ; rendu desktop/mobile et accessibilité des commandes ;
absence d’effet sur sauvegarde, minuterie et navigation. Si aucun point d’extension
ne permet le rattachement sans changement de contrat global, le pilote doit
rester une démonstration isolée/fixture.

## Choix UX comparés

| Option | Avantage | Coût / risque | Décision pour le pilote |
| --- | --- | --- | --- |
| Deux commandes « Pourquoi ? » et « Comment ? » | Chaque aide répond à une intention précise ; les explications restent courtes et consultables séparément. | Deux affordances par étape lorsqu’elles existent ; nécessite des libellés accessibles et une mise en page compacte. | Préférence confirmée par le Human Owner ; commandes facultatives et repliées. |
| Entrée d’aide unique | Une seule affordance et une surface plus compacte. | Mélange le principe culinaire avec les conseils pratiques ; lecture moins ciblée, contenu potentiellement plus long. | À garder comme comparaison du cadrage, sans remplacer le choix confirmé. |
| Assistant conversationnel en cuisson | Peut répondre à des questions non anticipées. | Réseau, latence, variabilité et sécurité en plein geste ; complexifie timers et navigation. | Exclu : pas de requête IA pendant Cooking. |

## Évaluation et contrôles nécessaires à la reprise

- Relever un snapshot/hash des deux fichiers pilotes avant génération ; vérifier qu’ils
  sont inchangés après le pilote.
- Les revues indépendantes culinaire/provenance et UX/contrat sont PASS pour le
  présent état du sidecar ; toute modification ultérieure de texte ou de
  rattachement nécessite une nouvelle revue.
- Contrôler la correspondance de `step_ref`, des variantes et du hash complet ; couvrir les étapes
  remplacées osso-buco et les étapes héritées dans chaque variante.
- Vérifier aide absente, une seule aide présente et deux aides présentes ; aucun
  bouton ou espace vide pour une aide absente.
- Dans Core, tester manuellement variante, timer, checkbox, navigation et reprise
  de progression avec aides fermées/ouvertes. Les tests applicatifs doivent être
  ajoutés/exécutés dans `cookigram-core`, pas dans le dépôt de contenu.
- Pour le sidecar du pilote, charger le YAML, vérifier le schéma, les références
  et les hashes source, puis confirmer que les fichiers `.gram` restent inchangés.
  Les contrôles du parcours Cooking nécessitent Core.

Mesures de décision : clarté/repères observables, aucune régression culinaire,
spécificité pédagogique, découvrabilité sans distraction, lecture par défaut
inchangée, cohérence des variantes et restauration exacte après désactivation.

## Suite autorisée

L’acceptation produit reste `pending`. Tout raccordement ultérieur devra être
vérifié dans Core comme prototype isolé. La généralisation devra faire l’objet
d’une décision GO / ITERATE / NO-GO séparée. Pas de merge, déploiement ni
migration catalogue dans le cadre de ce document.
