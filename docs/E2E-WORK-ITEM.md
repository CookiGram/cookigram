# Gabarit work-item durable E2E

> Ancre : écart **E3** de [`CATALOGUE-CONTRACT-CORE.md`](CATALOGUE-CONTRACT-CORE.md) —
> l'E2E de PR tourne sur **fixtures**, le catalogue officiel reste réservé au
> workflow de compatibilité (déclenchement manuel / périodique / après release
> ou changement de contrat). Ce gabarit ne prescrit ni registres de preuve, ni
> version de moteur, ni workflow CI, ni outillage d'écriture, ni contenu de
> recette : il décrit seulement comment formuler, valider et reprendre un
> travail E2E durable.

## 1. `id`

* Format : `e2e-<domaine>-<objet>` (domaine : `parcours`, `compat`, `smoke` …).
* Règles : minuscules, tirets, sans date ni nom d'auteur ; un travail = un `id`.
* L'`id` est repris tel quel dans la branche (`slice/<id>`), le titre de PR et
  la section reprise (§ 5).

Exemple : `e2e-parcours-recherche-fixture`.

## 2. `objectif`

* Une phrase : parcours couvert + résultat observable pour l'utilisateur.
* Critères d'acceptation (2 à 5), chacun vérifiable sans connaître
  l'implémentation :
  * Donner l'état de départ (page / entrée) et l'état d'arrivée attendu.
  * Préciser ce qui ne doit **pas** changer (non-régression explicite).
* Hors périmètre : lister ce que le work-item ne couvre pas (autres parcours,
  autres jeux de données, compatibilité catalogue officiel).

Exemple :

> Vérifier que la recherche par slug aboutit à la fiche attendue.
> Acceptation : (1) saisir un slug présent dans les fixtures affiche la fiche ;
> (2) un slug inconnu affiche l'état vide ; (3) le reste du parcours catalogue
> reste inchangé. Hors périmètre : compatibilité avec le catalogue officiel.

## 3. `fixtures`

* Principe d'ancrage E3 : les specs E2E de PR n'utilisent que des contenus
  génériques ou des slugs déjà présents dans les fixtures ; tout slug cité
  doit exister dans le jeu de fixtures au moment de la PR.
* Chaque work-item déclare son jeu minimal :
  * `jeu` : nom du jeu de fixtures utilisé ;
  * `slugs` : liste exacte des slugs / comptes exploités ;
  * `écarts` : ce que les fixtures ne couvrent pas et qui relève donc du
    workflow de compatibilité (catalogue officiel), pas de la PR.
* Si une fixture manque, le work-item est bloqué : ajouter la fixture d'abord,
  dans un travail séparé, puis reprendre (§ 5).

Exemple :

```yaml
jeu: fixtures E2E de PR
slugs: [<slug-fixture-1>, <slug-fixture-2>]
comptes: [> 0]
ecarts: [rendu sur catalogue officiel complet -> workflow de compatibilite]
```

## 4. `validation`

* Ordre : (1) specs E2E sur fixtures en local ; (2) mêmes specs en CI de PR ;
  (3) compatibilité catalogue officiel uniquement via le workflow dédié, jamais
  comme gate de PR.
* Chaque critère d'acceptation du § 2 mappe à au moins une assertion E2E
  nommée ; noter les assertions instables (flaky) avec leur preuve de
  relance (2 passages verts consécutifs).
* Échec : consigner la sortie minimale (spec, étape, attendu / observé) et
  classer — `fixture-manquante`, `spec-instable`, `regression-parcours`,
  `hors-perimetre-compatibilite` — avant toute correction.

## 5. `reprise`

* État à consigner pour le prochain agent : `id`, ref de branche, dernier
  point vert (spec / étape), point de blocage et sa classe (§ 4).
* Reprise en 3 commandes : se placer sur la branche, rejouer le jeu minimal
  du § 3, puis continuer à partir du point de blocage — sans réinventer le
  périmètre ni élargir aux écarts déclarés.
* Modèle de note de reprise :

```text
id: <e2e-...>
branche: slice/<id> @ <sha>
vert: <spec + etape>
blocage: <classe> — <fait observe>
suite: <prochaine action unique>
```

## Anti-périmètre (rappel de la slice)

Ce gabarit ne touche pas : registres de preuve et réconciliation, versions et
provenance du moteur, workflows CI / déploiement, outillage d'écriture, jeux
de recettes du catalogue, gratins. Un work-item E2E qui exige l'un de ces
sujets est découpé : le sujet externe fait l'objet d'un travail séparé.
