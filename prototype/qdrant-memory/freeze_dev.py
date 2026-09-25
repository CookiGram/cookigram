"""Freeze du point de fonctionnement sur DEV (gate 4) — AVANT tout holdout.

Lit UNIQUEMENT les artefacts dev commis (abstention_results.json,
dev_intersim.json optionnel) : aucun contact avec holdout.json.
Recalcule : retrieval (rank-1, recall@3), decision (stricte/indulgente)
pour la politique publiee (tau=0.40, delta=0.03) et le seuil seul,
marges et balayage de sensibilite (arithmetique pure, pas de retuning).
Ecrit dev_freeze.json : le point teste sur holdout est declare ici.
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from policy import DELTA, GAMMA, TAU  # noqa: E402
from retrieval_metrics import (decision_correct, mean,  # noqa: E402
                               retrieval_ok_lenient, retrieval_ok_strict,
                               retrieval_scores)


def main() -> dict:
    ref = json.loads((HERE / "abstention_results.json").read_text())
    rows = ref["items"]
    inter_path = HERE / "dev_intersim.json"
    inter = json.loads(inter_path.read_text()) if inter_path.is_file() else {}

    enriched = []
    for r in rows:
        s = r["scores"]
        margin = s[0] - s[1] if len(s) > 1 else 1.0
        ret = retrieval_scores(r["paths"], r["golds"])
        rec = ret["recall_at3"]
        pol = r["policy"]
        enriched.append({
            "id": r["id"], "expected": r["expected"], "s1": s[0] if s else 0.0,
            "margin": round(margin, 4), **ret,
            "retrieval_ok_strict": retrieval_ok_strict(rec),
            "retrieval_ok_lenient": retrieval_ok_lenient(rec),
            "policy_decision": pol,
            "decision_strict": decision_correct(
                r["expected"], pol, retrieval_ok_strict(rec)),
            "decision_lenient": decision_correct(
                r["expected"], pol, retrieval_ok_lenient(rec)),
            "intersim": inter.get(r["id"]),
        })

    ans = [e for e in enriched if e["expected"] == "answer"]
    neg = [e for e in enriched if e["expected"] == "abstain"]

    def sweep(delta):
        aok = sum(1 for e in ans
                  if (e["s1"] >= TAU and e["margin"] >= delta)
                  and e["retrieval_ok_lenient"])
        nok = sum(1 for e in neg
                  if e["s1"] < TAU or e["margin"] < delta)
        return {"delta": delta,
                "answerable_recall_gate3": round(aok / len(ans), 3),
                "negative_abstention": round(nok / len(neg), 3),
                "accuracy_gate3": round((aok + nok) / len(enriched), 3)}

    report = {
        "frozen_at": datetime.datetime.now(datetime.timezone.utc)
        .astimezone().isoformat(timespec="seconds"),
        "scope": "DEV ONLY (abstention_results.json, 16 items). "
                 "Aucune lecture de holdout.json.",
        "frozen_point": {
            "tau": TAU, "delta": DELTA, "gamma": GAMMA,
            "primary": "decide(tau=0.40, delta=0.03) — politique publiee gate 3, "
                       "test de generalisation tel quel (pas de rechignage).",
            "secondary": "decide_cluster(gamma=0.70) — bras hypothetique "
                         "negatif (dev sans separation, cf. dev_intersim).",
        },
        "retrieval_dev_dense": {
            "rank1": mean([e["rank1"] for e in ans]),
            "recall_at3_lenient_any": mean(
                [1.0 if e["retrieval_ok_lenient"] else 0.0 for e in ans]),
            "n_answer": len(ans),
        },
        "decision_dev_policy": {
            "strict": mean([e["decision_strict"] for e in enriched]),
            "lenient": mean([e["decision_lenient"] for e in enriched]),
        },
        "sensitivity": {
            "note": "Point fragile : H2 marge 0.0292 vs delta 0.03 "
                    "(bascule a 0.0008) ; N5 s1 0.3987 vs tau 0.40 "
                    "(bascule a 0.0013). Plateau post-hoc delta "
                    "[0.015, 0.029] -> 0.875, NON retenu (sur-ajustement "
                    "sur n=16, un seul item d'ecart).",
            "delta_sweep": [sweep(d) for d in
                            (0.01, 0.015, 0.02, 0.025, 0.029, 0.03, 0.035)],
        },
        "items": enriched,
    }
    (HERE / "dev_freeze.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"frozen_point tau={TAU} delta={DELTA} gamma={GAMMA}")
    print("retrieval:", report["retrieval_dev_dense"])
    print("decision:", report["decision_dev_policy"])
    for s in report["sensitivity"]["delta_sweep"]:
        print(f"delta={s['delta']}: acc={s['accuracy_gate3']} "
              f"ans={s['answerable_recall_gate3']} neg={s['negative_abstention']}")
    return report


if __name__ == "__main__":
    main()
