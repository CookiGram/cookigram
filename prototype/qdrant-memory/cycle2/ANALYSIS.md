# Cycle 2 — analyse (dev n=14, holdout n=8, run unique)

Point figé (règle pré-enregistrée) : τ=0.55, δ=0.01, bras primaire
fact+politique (B2). Zéro retuning post-holdout.

## Observations

- Retrieval généralise BIEN sur docs frais : holdout recall@3 0.9
  (sec ET fact), rank-1 fact 1.0 / sec 0.8 / lexical 0.4.
  Dev : fact 0.722 / sec 0.611 / lex 0.722 (rank-1 lex 0.778).
- Les ANCRES restent le goulot : succès holdout 0.2–0.4 malgré
  recall 0.9 (C2-A/C2-D : gold rank-1, chunk-réponse absent du top-3).
  « Bon doc ≠ bon chunk », répliqué (3e fois, 2 chunkings).
- Politique : 3/3 abstentions correctes (s1 max 0.486, confortable
  sous τ=0.55) MAIS 2 sur-abstentions sur retrieval correct
  (C2-C marges 0.004/0.007, C2-D fact 0.001 < δ=0.01).
  Décision indulgente : dev fact 0.786 (11/14) → holdout B2 0.75 (6/8).
- Avantage faits répliqué directionnellement, atténué :
  dev recall 0.722 vs 0.611 (sec) ; holdout rank-1 1.0 vs 0.8,
  recall 0.9 partout dense. Écart c1 (0.7/0.3) non reproduit tel quel.
- Claims (dev C1/C2, nouveauté c2) : dense rec3=0.0 les deux
  (chunk unique noyé) ; lexical trouve C2. Pas d'item claim au
  holdout (trou de couverture assumé, pool épuisé).

## Hypothèses (non démontrées)

- Décalage granularité : le top-3 ramène le bon document mais pas
  le span-réponse, aux deux chunkings → l'injection brute top-k
  plafonne ; piste : rank-then-extract, jamais testée ici.
- marge < δ capte la concentration mono-doc autant que l'indécision
  (C2-C/D : candidats groupés corrects, comme H2/D1 au cycle 1).

## Limites

n=14/8, un run, ancres substring, pas de claim au holdout, pas de
bras MMR/cluster, latences locales, corpus mono-checkout. Le choix
τ=0.55 (haut du plateau dev [0.30,0.55]) n'est validé que par 3
négatifs ; δ=0.01 est au contact (0.007/0.001 vs 0.01).

## Ce que le cycle 2 permet / ne permet pas

- Permet : confirmer que le retrieval dense généralise sur docs
  frais (0.9) ; confirmer l'économie d'abstention (3/3, 8–18 tok) ;
  confirmer que la marge brute sur-abstient ; répliquer
  l'avantage faits (atténué) ; établir que l'ancre, pas le doc,
  borne le succès.
- Ne permet pas : fixer un point opérable (n trop petit, marges au
  contact) ; trancher faits vs sections en général ; qualifier
  l'injection mémoire agent de bout en bout ; aucune décision produit.
