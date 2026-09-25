"""Calibration cycle 2 sur DEV UNIQUEMENT (jamais le holdout).

Lit c2_dev.json (14 items). Indexe les collections dediees agent_memory_c2
et agent_memory_fact_c2 (rebuild from scratch, jetables). Mesure les bras
lexical / dense-sec / dense-fact + balayage (tau, delta) pour la politique
sur le bras fact (primaire) et sec (secondaire, meme point).
Applique la regle de selection pre-enregistree dans c2_dev.json.
Ecrit c2_calibration.json. Refuse de tourner si c2_holdout.json existe
(gardefou aveuglement : calibrer apres holdout = fuite).
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
C1 = HERE.parent  # modules cycle 1 reutilises sans modification
ROOT = HERE.parent.parent.parent  # racine worktree (cycle2 est un niveau plus bas)
sys.path.insert(0, str(C1))

from chunk_facts import build_fact_corpus  # noqa: E402
from corpus_manifest import build_corpus  # noqa: E402
from dense_qdrant import DenseQdrant, index_corpus  # noqa: E402
from policy import decide  # noqa: E402
from retrieval_metrics import (decision_correct, mean,  # noqa: E402
                               retrieval_ok_lenient, retrieval_scores)
from store import Collection, estimate_tokens  # noqa: E402

COL_SEC = "agent_memory_c2"
COL_FACT = "agent_memory_fact_c2"
TOP_K = 3
TAUS = [round(0.30 + 0.05 * i, 2) for i in range(7)]
DELTAS = [0.01, 0.02, 0.03, 0.05]


def corpus_sha(corpus: list[dict]) -> str:
    h = hashlib.sha256()
    for d in sorted(corpus, key=lambda d: d["id"]):
        h.update((d["id"] + "\x00" + d["text"]).encode())
    return h.hexdigest()[:16]


def main() -> dict:
    if (HERE / "c2_holdout.json").exists():
        raise SystemExit("REFUS : c2_holdout.json existe deja — "
                         "calibration post-holdout interdite.")
    spec = json.loads((HERE / "c2_dev.json").read_text())
    items = spec["items"]
    assert len(items) == 14, len(items)

    sec_corpus = build_corpus(ROOT)
    fact_corpus = build_fact_corpus(ROOT)
    full_tokens = estimate_tokens("\n\n".join(d["text"] for d in sec_corpus))
    lex = Collection("agent_memory_c2")
    for d in sec_corpus:
        lex.upsert(d["id"], d["text"], d["payload"])
    dq_sec = DenseQdrant(collection=COL_SEC)
    idx_sec = index_corpus(dq_sec, sec_corpus)
    dq_fact = DenseQdrant(collection=COL_FACT)
    idx_fact = index_corpus(dq_fact, fact_corpus)
    time.sleep(1)
    assert len(sec_corpus) == 209, len(sec_corpus)  # pin environnement a5e7daa
    assert len(fact_corpus) == 881, len(fact_corpus)
    assert dq_sec.info()["points"] == len(sec_corpus)
    assert dq_fact.info()["points"] == len(fact_corpus)

    rows = []
    for it in items:
        q, ans = it["query"], it["expected"] == "answer"
        lr = lex.search(q, top_k=TOP_K, filters={"project": "cookigram"})
        sr = dq_sec.search(q, top_k=TOP_K, filters={"project": "cookigram"})
        fr = dq_fact.search(q, top_k=TOP_K, filters={"project": "cookigram"})

        def retr(hits):
            return retrieval_scores(
                [h["citation"]["path"] for h in hits],
                it["golds"] if ans else [])

        def succ(hits):
            if not ans:
                return None
            paths = [h["citation"]["path"] for h in hits]
            ctx = " ".join(h["text"] for h in hits)
            return (any(g in paths for g in it["golds"])
                    and any(a in ctx for a in it["anchors"]))

        s_scores = [h["score"] for h in sr["hits"]]
        f_scores = [h["score"] for h in fr["hits"]]
        s_margin = s_scores[0] - s_scores[1] if len(s_scores) > 1 else 1.0
        f_margin = f_scores[0] - f_scores[1] if len(f_scores) > 1 else 1.0
        row = {
            "id": it["id"], "kind": it["kind"], "expected": it["expected"],
            "lexical": {"success": succ(lr["hits"]), "retrieval": retr(lr["hits"]),
                        "latency_ms": lr["latency_ms"]},
            "dense_sec": {"success": succ(sr["hits"]), "retrieval": retr(sr["hits"]),
                          "scores": s_scores, "margin": round(s_margin, 4),
                          "latency_ms": sr["latency_ms"]},
            "dense_fact": {"success": succ(fr["hits"]), "retrieval": retr(fr["hits"]),
                           "scores": f_scores, "margin": round(f_margin, 4),
                           "latency_ms": fr["latency_ms"]},
        }
        rows.append(row)
        print(f"{it['id']:7s} lex={row['lexical']['success']} "
              f"sec={row['dense_sec']['success']}({s_scores[0] if s_scores else 0:.3f}) "
              f"fact={row['dense_fact']['success']}({f_scores[0] if f_scores else 0:.3f})")

    def grid_on(arm: str) -> list[dict]:
        out = []
        for tau in TAUS:
            for delta in DELTAS:
                oks = []
                for r, it in zip(rows, items):
                    sc = r[arm]["scores"]
                    verdict, _ = decide(sc, tau=tau, delta=delta)
                    rec = r[arm]["retrieval"]["recall_at3"]
                    oks.append(decision_correct(
                        it["expected"], verdict, retrieval_ok_lenient(rec)))
                out.append({"tau": tau, "delta": delta,
                            "decision_lenient": mean([1.0 if o else 0.0
                                                      for o in oks])})
        return out

    grid_fact = grid_on("dense_fact")
    best = max(grid_fact,
               key=lambda c: (c["decision_lenient"], c["tau"], c["delta"]))
    report = {
        "cycle": 2, "phase": "dev-calibration",
        "collections": {"sec": COL_SEC, "fact": COL_FACT},
        "corpora": {"section_chunks": len(sec_corpus),
                    "section_sha": corpus_sha(sec_corpus),
                    "fact_chunks": len(fact_corpus),
                    "fact_sha": corpus_sha(fact_corpus),
                    "tokens_full": full_tokens,
                    "index_sec": idx_sec, "index_fact": idx_fact},
        "retrieval_dev": {
            arm: {"success_answer_rate": mean(
                      [1.0 if r[arm]["success"] else 0.0 for r in rows
                       if r[arm]["success"] is not None]),
                  "rank1": mean([r[arm]["retrieval"]["rank1"] for r in rows]),
                  "recall_at3": mean([r[arm]["retrieval"]["recall_at3"]
                                      for r in rows])}
            for arm in ("lexical", "dense_sec", "dense_fact")},
        "grid_fact": grid_fact,
        "grid_sec": grid_on("dense_sec"),
        "chosen": {"tau": best["tau"], "delta": best["delta"],
                   "decision_lenient": best["decision_lenient"],
                   "rule": spec["selection_rule_preregistered"]},
        "items": rows,
    }
    (HERE / "c2_calibration.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"CHOISI (regle pre-enregistree) : tau={best['tau']} "
          f"delta={best['delta']} lenient={best['decision_lenient']}")
    return report


if __name__ == "__main__":
    main()
