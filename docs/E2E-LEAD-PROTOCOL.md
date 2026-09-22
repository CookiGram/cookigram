# Protocole Lead / workers E2E

Protocole de bout en bout pour un run Lead + workers : découpage du travail,
coordination via GitHub, règle d'écriture unique sur D2.

## 1. Portée et ancrage

- Ancre : **D2**. Ce document décrit le protocole ; D2 reste l'ancre de
  référence du run (périmètre, décisions, état d'avancement).
- Les slices **s2** et **s4** sont en **lecture seule** pour ce protocole :
  il les cite comme dépendances/contrats mais ne les modifie pas.
- Périmètre d'écriture de cette slice : **ce fichier uniquement**
  (`docs/E2E-LEAD-PROTOCOL.md`). Ne touche ni à `claims/`, ni au builder,
  ni à la CI (`.github/workflows/`), ni à un quelconque writer, ni à
  `recipes/*` (périmètre réservé, cf. PR #427 en cours sur le catalogue).

## 2. Rôles

| Rôle | Responsabilités | Interdits |
| --- | --- | --- |
| Lead | Découpe en slices, assigne les lanes, tient D2 à jour, qualifie les PR (checks), décide merge / reprise | Ne merge jamais une PR à checks rouges ; ne réécrit pas l'historique |
| Worker | Implémente **sa** slice sur **sa** branche, pousse, ouvre sa PR, exécute ses validations | Ne touche jamais aux lanes Herdr d'autrui ; ne modifie jamais D2 directement |

## 3. Règle d'écriture unique sur D2 : pas de second writer

- **Un seul writer sur D2 : le Lead.** Les workers ne proposent des
  évolutions de D2 que via leur PR de slice (commentaire ou section
  dédiée) ; seul le Lead les reporte dans D2.
- Conséquence : deux workers ne se synchronisent jamais en s'écrivant
  mutuellement dans D2. Toute coordination passe par GitHub (issue / PR /
  review), jamais par une écriture concurrente dans le document ancre.
- En cas de conflit apparent sur D2 (deux PR proposant des évolutions
  divergentes), le Lead tranche, reporte une seule version, et notifie les
  workers concernés sur leurs PR.

## 4. Découpage (slicing)

1. Le Lead découpe le run en slices **disjointes en fichiers** : chaque
   slice liste exhaustivement ses fichiers ; un fichier appartient à au
   plus une slice.
2. Chaque slice définit : nom, objectif, fichiers (périmètre exclusif),
   validations à exécuter, base (`origin/main` après `fetch`).
3. Base commune : chaque worker part de `origin/main` à jour
   (`git fetch origin` + branche nouvelle depuis `origin/main`).
4. Fichier nouveau vs. existant : une slice peut créer un fichier nouveau
   (cas de ce protocole) ; elle ne doit alors chevaucher aucun fichier des
   autres slices du même run.

## 5. Coordination via GitHub

- **Lane par worker** : une branche par slice, nommée explicitement
  (ex. `docs/e2e-lead-protocol`, `slice/...`). Ne jamais pusher sur la
  branche d'autrui.
- **Herdr lanes** : si le run utilise des lanes Herdr, chacun reste sur la
  sienne ; on ne touche jamais aux lanes Herdr d'autrui.
- **PR par slice** : une PR par branche (`gh pr create`), avec dans la
  description : périmètre (fichiers), validations observées, écart éventuel.
- **Qualification** : le Lead suit `gh pr checks` par PR. Une PR n'est
  présentée au merge que si ses checks requis sont verts.
- **NE MERGE JAMAIS (worker)** : aucun worker ne merge, ni sa PR ni celle
  d'autrui. Le merge — lorsqu'il est autorisé par le run — relève d'une
  décision explicite distincte du présent protocole.
- **Reprise possible** : chaque PR/lane doit permettre la reprise par un
  tiers : nom de branche + ref (SHA) + état CI + validations observées.

## 6. Cycle E2E d'un run

1. Lead : `git fetch origin`, découpe, publie D2 (état initial), assigne.
2. Workers : branche nouvelle depuis `origin/main`, implémentation dans le
   périmètre exclusif, exécution des validations de la slice.
3. Workers : `commit` + `push` + PR via `gh` (si `open_pr`), sans merge.
4. Lead : revue + `gh pr checks`, report des décisions dans D2 (writer
   unique), demande de reprise si rouge.
5. Clôture : D2 fige l'état final (PR, branches, refs, états CI).

## 7. Validations de cette slice (observables)

- [ ] `git status --short` ne montre que `docs/E2E-LEAD-PROTOCOL.md`
  (fichier nouveau, disjoint des 2 autres slices du run).
- [ ] Aucune modification sous `claims/`, aucun builder, aucun fichier
  sous `.github/workflows/`, aucun writer, rien sous `recipes/*`.
- [ ] `git diff --stat origin/main...HEAD` ne liste que ce fichier.
- [ ] PR ouverte via `gh`, checks suivis via `gh pr checks`, **sans merge**.

## 8. Reprise

- Branche : `docs/e2e-lead-protocol` (depuis `origin/main`).
- Ref et état CI : voir la PR et `gh pr checks` (le Lead y reporte
  l'état final dans D2).
