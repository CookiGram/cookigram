"""MMR stdlib : diversification minimale du top-k (gate 3, #508).

Selection : argmax l * sim(q, d) - (1 - l) * max_{s in S} sim(d, s).
`score` (similarite requete-doc, ex. cosinus Qdrant) sert de pertinence,
`vector` sert a la diversite. Deterministe. Zero dependance.
"""

from __future__ import annotations

import math


def cosine(a: list[float], b: list[float]) -> float:
    n = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)) or 1.0
    return sum(x * y for x, y in zip(a, b)) / n


def mmr_select(query_vec: list[float], candidates: list[dict], top_k: int = 3,
               lambda_: float = 0.5) -> list[dict]:
    """candidates: [{id, score, vector, ...}]. Retourne top_k diversifies."""
    remaining = list(candidates)
    selected: list[dict] = []
    while remaining and len(selected) < top_k:
        best, best_val = None, None
        for c in remaining:
            div = max((cosine(c["vector"], s["vector"]) for s in selected),
                      default=0.0)
            val = lambda_ * c["score"] - (1 - lambda_) * div
            if best_val is None or val > best_val:
                best, best_val = c, val
        out = dict(best)
        out["mmr_score"] = round(best_val, 4)
        selected.append(out)
        remaining = [c for c in remaining if c["id"] != best["id"]]
    return selected
