# Cycle 510 — amendement politique (POLICY CALIBRATION DEV uniquement)

Statut : **amendement pré-enregistré avant toute mesure de politique**.
Complète `method-freeze.md` (inchangé) sans le réécrire. Autorisation
Human Owner : POLICY CALIBRATION DEV uniquement. Ne couvre ni le
holdout (construction, lecture, mesure), ni aucun changement
retrieval (corpus, embeddings, chunking, top_k, filtres), ni aucun
nouveau run retrieval des 13 positifs déjà mesurés.

## 1. Pourquoi des négatifs sont nécessaires

La politique d'abstention est inobservable sur les 13 positifs seuls :
chaque item a `expected=answer`, donc la branche `abstain` de
`decision_correct` (`retrieval_metrics.py`, L36-49) n'est jamais
exercée et la préférence d'abstention n'est pas mesurable. Sans
négatif, tout point permissif (répondre toujours) maximise
trivialement le score et `tau`/`delta` ne sont pas identifiables.
Des items `expected=abstain` sont donc requis AVANT toute sélection
de point, exactement comme le précédent c2b (`~23 answer +
traps/OOD`, `c2b_method_freeze.json`, `procedure_next`).

## 2. Construction des négatifs DEV sans consommer la réserve

8 négatifs (`dev_negatives.json`) : 6 hors-domaine lointain (OOD) et
2 pièges quasi-domaine. Garanties, chacune testée :

- **Zéro slot consommé** : un négatif n'a ni ancre, ni chemin, ni
  section, ni preuve. Structurellement, il ne peut intersecter ni les
  13 slots dev ni les 12 slots de réserve (test : aucune clé
  `anchor`/`path`/`section`/`slot` dans les items).
- **Zéro ancre/gold #508** : scan verbatim des 75 ancres
  `forbidden_508.json` sur les champs des négatifs (test).
- **Zéro information du futur holdout** : aucun gold holdout n'existe
  (aucun fichier holdout, `holdout_created=false`) ; les négatifs ne
  référencent aucune section de réserve, qu'ils ignorent.
- **Inrépondabilité vérifiée** : chaque négatif porte des
  `absent_terms` — termes distinctifs que toute réponse correcte
  contiendrait — vérifiés absents (casefold) des 4 documents du
  corpus fermé (test par relecture exhaustive). Les OOD portent sur
  des sujets sans rapport (géographie, cuisine concrète, art,
  biologie, crypto, médecine) ; les pièges portent sur des faits
  plausibles mais jamais énoncés (budget des illustrations, réunion
  de synchronisation des agents).

## 3. Nombre et identité exacte

Exactement 8 négatifs, `510-neg-001` à `510-neg-008`
(6 `ood`, 2 `trap`), tous `expected=abstain`, définis dans
`dev_negatives.json` (requête, rationale, `absent_terms`,
`proposition_key`). Aucun ajout/retrait sans nouvel amendement.

## 4. Définition d'un négatif et résultat attendu

Un négatif est une requête sans réponse dans le corpus fermé :
`golds=[]`, retrieval `None` (`retrieval_scores`, L15-23). Résultat
attendu à tout point `(tau, delta)` : verdict `abstain`. Item
correct ssi `abstain` (`decision_correct`, branche abstain).
Les positifs gardent `expected=answer` (13 items avec preuve).

## 5. Grille finie et déterministe

Reprise méthode c2b (`cycle2b/c2b_calibrate.py`, L38-39), qui est une
définition de grille, pas un résultat :

- `taus = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]` (7) ;
- `deltas = [0.01, 0.02, 0.03, 0.05]` (4) ;
- 28 configurations, sérialisées dans `policy_preregistration.json`.

## 6. Sémantique exacte de tau, delta, abstention

`policy.decide(scores, tau, delta)` (`policy.py`, L58-68), repris tel
quel (fonction pure, testable sans Qdrant) :

- aucun score → `abstain` (`aucun candidat`) ;
- `s1 < tau` → `abstain` (pertinence absolue insuffisante) ;
- marge `s1 - s2 < delta` (avec `s2 = 0.0` si un seul hit) →
  `abstain` (indécision entre candidats) ;
- sinon → `answer`.

`tau` = pertinence absolue minimale du meilleur candidat ;
`delta` = marge d'indécision minimale entre les deux meilleurs.
Les défauts du module (`TAU=0.40`, `DELTA=0.03`, calibrés post-hoc
au gate 3) NE SONT PAS utilisés : chaque point de grille est évalué
explicitement. Pas de règle cluster/gamma (hors précédent c2b :
c2b n'utilise que `decide`).

## 7. Métriques sur positifs et négatifs

Par item et par point : `decision_correct` stricte et indulgente
(`retrieval_metrics.py`, L25-49), avec `retrieval_ok_*` sur le
recall section-level. Agrégats `mean()` : `decision_lenient`
global (21 items), `decision_lenient_pos` (13), `decision_lenient_neg`
(8), `decision_strict` global (diagnostic, NON sélectif).
Grille complète enregistrée sur `dense_fact` (28 cellules) ET
`dense_sec` (28 cellules). `lexical` reste retrieval-only sans
politique (précédent c2b : grille sur bras denses seuls ;
`c2b_calibrate.py`, L117-131, `grid_on(dense_fact|dense_sec)`).

Entrées gelées : positifs = lignes de `510_calibration.json`
(scores denses + recall, AUCUNE re-mesure retrieval des positifs) ;
négatifs = UNE mesure retrieval unique (3 bras, paramètres gelés
inchangés, corpora reconstruits et vérifiés aux SHA gelés
`1c55730fe6de78e9` / `07eae33590c88b5a`). La grille est ensuite
purement computationnelle sur les scores.

## 8. Règle de sélection finale (ordre total, avant mesure)

Reprise méthode c2b (`c2b_calibrate.py`, L134-135 et texte de règle
L155-163) :

1. maximiser `decision_lenient` global sur le bras `dense_fact` ;
2. égalité → `tau` supérieur (préférence abstention) ;
3. égalité → `delta` supérieur (préférence abstention).

Les 28 paires `(tau, delta)` sont uniques : l'ordre est total, aucune
décision discrétionnaire post-observation. Configuration transmise =
`(tau, delta, decision_lenient_fact)` + `dense_sec` au même point
(secondaire, reporté) + `lexical` brut. Cellules holdout futures
`A2=sec+politique` / `B2=fact+politique` définies mais NON exécutées
(gate distinct, interdit ici).

**Bras primaire et non-rétroactivité.** `fact` reste primaire si et
seulement si le précédent c2b le désigne : c'est le cas
(« Bras primaire : dense-fact+politique », `c2b_calibrate.py`,
L155-163), précédent documenté avant toute mesure #510. Aucune
comparaison inter-bras data-dépendante n'est autorisée : les rôles
sont fixés par précédent et les résultats DEV ne changent ni
protocole ni rôles. Preuve de non-cherry-picking : `fact` est le
bras le plus faible en succès DEV (0.308 contre 0.692) et reste
néanmoins primaire. Aucune règle alternative favorisant `lex` ou
`sec` n'est introduite.
