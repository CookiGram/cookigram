"""Politique d'abstention minimale et explicable (gate 3, #508).

Regle : ABSTAIN si s1 < tau (pertinence absolue insuffisante)
         ou si marge (s1 - s2) < delta (indecision entre candidats).
Sinon ANSWER. Fonction pure -> testable sans Qdrant.
tau=0.40 / delta=0.03 calibres POST-HOC sur le jeu etiquete du gate 3
(piège N2 : marge 0.014) : FIGES pour le holdout gate 4 (dev_freeze.json),
aucun retuning apres lecture du holdout.
"""

from __future__ import annotations

TAU = 0.40
DELTA = 0.03
# GAMMA fige APRES calibrage dev (calibrate_gamma.py) : le dev montre
# AUCUN seuil separant (grappes reponse {D1:0.587, H2:0.733} vs pieges
# {N2:0.706, N4:0.824} imbriquees, meilleur 2/4 = hasard).
# GAMMA=0.70 fige pour tester l'hypothese negative sur holdout, pas pour gagner.
GAMMA = 0.70


def mean_intersim(vectors: list[list[float]]) -> float:
    """Similarite cosinus moyenne par paire (corroboration du top-k)."""
    import math
    if len(vectors) < 2:
        return 1.0
    sims = []
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            a, b = vectors[i], vectors[j]
            n = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
            sims.append(sum(x * y for x, y in zip(a, b)) / (n or 1.0))
    return sum(sims) / len(sims)


def decide_cluster(top_scores: list[float], top_vectors: list[list[float]],
                   tau: float = TAU, delta: float = DELTA,
                   gamma: float | None = GAMMA) -> tuple[str, str]:
    """Regle cluster-aware : la marge ne fait abstenir que si les candidats
    se contredisent (inter-sim < gamma). Des candidats groupes (inter-sim
    haute) se corroborent -> ANSWER. gamma calibre sur dev uniquement."""
    if gamma is None:
        raise ValueError("gamma non calibre (voir calibrate_gamma.py)")
    if not top_scores:
        return ("abstain", "aucun candidat")
    s1 = top_scores[0]
    if s1 < tau:
        return ("abstain", f"s1={s1:.3f} < tau={tau}")
    margin = s1 - (top_scores[1] if len(top_scores) > 1 else 0.0)
    if margin >= delta:
        return ("answer", f"s1={s1:.3f} marge={margin:.3f}")
    inter = mean_intersim(top_vectors[:3])
    if inter >= gamma:
        return ("answer", f"grappe corroborante inter={inter:.3f}>=gamma={gamma}")
    return ("abstain", f"vraie indecision inter={inter:.3f}<gamma={gamma}")


def decide(top_scores: list[float], tau: float = TAU,
           delta: float = DELTA) -> tuple[str, str]:
    if not top_scores:
        return ("abstain", "aucun candidat")
    s1 = top_scores[0]
    if s1 < tau:
        return ("abstain", f"s1={s1:.3f} < tau={tau}")
    margin = s1 - (top_scores[1] if len(top_scores) > 1 else 0.0)
    if margin < delta:
        return ("abstain", f"marge={margin:.3f} < delta={delta}")
    return ("answer", f"s1={s1:.3f} marge={margin:.3f}")
