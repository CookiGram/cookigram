"""Politique d'abstention minimale et explicable (gate 3, #508).

Regle : ABSTAIN si s1 < tau (pertinence absolue insuffisante)
         ou si marge (s1 - s2) < delta (indecision entre candidats).
Sinon ANSWER. Fonction pure -> testable sans Qdrant.
tau=0.40 / delta=0.03 calibres POST-HOC sur le jeu etiquete du gate 3
(piège N2 : marge 0.014) : a revalider sur holdout avant tout usage reel.
"""

from __future__ import annotations

TAU = 0.40
DELTA = 0.03


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
