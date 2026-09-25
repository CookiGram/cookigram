"""Metriques retrieval vs decision (gate 4, #508) — pures, stdlib.

Le gate 3 confondait les deux dans `answerable_recall` (succes = gold
trouve ET reponse donnee) : un abstentionnisme correct sur mauvaise
recuperation (P3) y comptait comme echec. Ici :
- retrieval : rank-1 + recall@k, independants de toute decision ;
- decision : correction de la decision (answer/abstain) CONDITIONNELLE
  a la qualite retrieval, en variantes stricte et indulgente.
Aucun seuil ici : ce module mesure, `policy.py` decide.
"""

from __future__ import annotations


def retrieval_scores(paths: list[str], golds: list[str],
                     k: int = 3) -> dict:
    """Rank-1 et recall@k. None quand l'item n'a pas de gold (piege/OOD)."""
    if not golds:
        return {"rank1": None, f"recall_at{k}": None}
    top = paths[:k]
    return {"rank1": 1 if (top and top[0] in golds) else 0,
            f"recall_at{k}": round(sum(g in top for g in golds) / len(golds), 3)}


def retrieval_ok_strict(recall_at_k: float | None) -> bool | None:
    """Recuperation reussie ssi TOUS les golds sont dans le top-k."""
    return None if recall_at_k is None else recall_at_k == 1.0


def retrieval_ok_lenient(recall_at_k: float | None) -> bool | None:
    """Recuperation reussie ssi AU MOINS un gold est dans le top-k."""
    return None if recall_at_k is None else recall_at_k > 0.0


def decision_correct(expected: str, decision: str,
                     retrieval_ok: bool | None) -> bool | None:
    """Decision correcte sachant la recuperation.
    - attendu abstain : correct ssi abstain (piege/OOD, pas de gold) ;
    - attendu answer : correct ssi (recuperation ok ET answer) ou
      (recuperation ko ET abstain). Ne jamais recompenser une reponse
      sur une recuperation ratee, ni penaliser une abstention lucide.
    """
    if expected == "abstain":
        return decision == "abstain"
    if retrieval_ok is None:
        return None
    if retrieval_ok:
        return decision == "answer"
    return decision == "abstain"


def mean(values: list[float | None]) -> float | None:
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals), 3) if vals else None
