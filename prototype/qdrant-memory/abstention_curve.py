"""Courbe d'abstention (gate 3) : seuil cosinus seul vs politique minimale.

Protocole : collection agent_memory re-indexee (derivee), puis pour chaque
item du jeu etiquete : search dense top-3 sans seuil (scores bruts).
- Courbe : prediction ANSWER ssi s1 >= tau, grille 0.00..0.80.
- Politique : policy.decide (tau=0.40 + marge delta=0.03), mesuree separement.
Ecrit abstention_results.json (donnees brutes par item + courbe).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

from corpus_manifest import build_corpus  # noqa: E402
from dense_qdrant import DenseQdrant, index_corpus  # noqa: E402
from policy import DELTA, TAU, decide  # noqa: E402

TAUS = [round(x * 0.05, 2) for x in range(0, 17)]


def main() -> dict:
    labels = json.loads((HERE / "abstention_labels.json").read_text())
    items = labels["items"]
    dq = DenseQdrant()
    idx = index_corpus(dq, build_corpus(ROOT))

    rows = []
    for it in items:
        res = dq.search(it["query"], top_k=3, filters={"project": "cookigram"},
                        score_threshold=0.0)
        scores = [h["score"] for h in res["hits"]]
        paths = [h["citation"]["path"] for h in res["hits"]]
        verdict, reason = decide(scores)
        rows.append({"id": it["id"], "kind": it["kind"], "expected": it["expected"],
                     "golds": it["golds"], "scores": scores, "paths": paths,
                     "policy": verdict, "policy_reason": reason,
                     "latency_ms": res["latency_ms"]})

    def metrics(predict):
        ans = [r for r in rows if r["expected"] == "answer"]
        neg = [r for r in rows if r["expected"] == "abstain"]
        ans_ok = sum(1 for r in ans
                     if predict(r) == "answer"
                     and any(g in r["paths"] for g in r["golds"]))
        neg_ok = sum(1 for r in neg if predict(r) == "abstain")
        return {"answerable_recall": round(ans_ok / len(ans), 3),
                "negative_abstention": round(neg_ok / len(neg), 3),
                "accuracy": round((ans_ok + neg_ok) / len(rows), 3)}

    curve = [{"tau": t, **metrics(lambda r, t=t: "answer"
                                  if (r["scores"] and r["scores"][0] >= t)
                                  else "abstain")}
             for t in TAUS]
    policy_m = metrics(lambda r: r["policy"])
    report = {"index": idx, "tau_default": TAU, "delta": DELTA,
              "curve": curve,
              "policy": {"rule": "abstain si s1<tau ou marge<delta sinon answer",
                         **policy_m},
              "items": rows}
    (HERE / "abstention_results.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("tau   ans_recall neg_abst accuracy")
    for c in curve:
        print(f"{c['tau']:.2f}  {c['answerable_recall']:.3f}      "
              f"{c['negative_abstention']:.3f}      {c['accuracy']:.3f}")
    print("policy:", policy_m)
    for r in rows:
        print(f"{r['id']:8s} exp={r['expected']:7s} pol={r['policy']:7s} "
              f"{r['scores']} {r['policy_reason']}")
    return report


if __name__ == "__main__":
    main()
