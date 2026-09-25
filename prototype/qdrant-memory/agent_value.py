"""Valeur agent (gate #508) : 4 methodes x 5 taches realistes, critere deterministe.

Methodes : full (borne sup, succes par construction) / lexical (store.py)
  / dense (Qdrant reel) / dense_mmr_policy (MMR fetch20/lambda0.5 + policy).
Succes : expected=answer -> gold path recupere ET ancre dans le contexte ;
         expected=abstain -> 0 chunk injecte (politique) ; les methodes sans
         politique ne peuvent pas reussir A5 (documente, pas contourne).
Ecrit agent_value_results.json.
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
from policy import decide  # noqa: E402
from store import Collection, estimate_tokens  # noqa: E402

TOP_K = 3


def main() -> dict:
    spec = json.loads((HERE / "agent_tasks.json").read_text())
    tasks = spec["items"]
    corpus = build_corpus(ROOT)
    full_text = "\n\n".join(d["text"] for d in corpus)
    full_tokens = estimate_tokens(full_text)

    lex = Collection("agent_memory")
    for d in corpus:
        lex.upsert(d["id"], d["text"], d["payload"])
    dq = DenseQdrant()
    index_corpus(dq, corpus)

    rows = []
    for t in tasks:
        q = t["query"]
        full_ok = (t["gold"] is None) or ((t["anchor"] or "") in full_text)
        lr = lex.search(q, top_k=TOP_K, filters={"project": "cookigram"})
        dr = dq.search(q, top_k=TOP_K, filters={"project": "cookigram"},
                       score_threshold=0.0)
        mr = dq.search_mmr(q, top_k=TOP_K, fetch_k=20, lambda_=0.5,
                           filters={"project": "cookigram"})
        # Politique calibree sur ranking brut : decide sur scores bruts,
        # MMR ne diversifie que si ANSWER (scores MMR non calibres).
        raw_scores = [h["score"] for h in dr["hits"]]
        verdict, reason = decide(raw_scores)

        def success(hits, anchor_needle=True):
            if t["expected"] == "abstain":
                return None  # sans politique : non applicable
            paths = [h["citation"]["path"] for h in hits]
            ctx = " ".join(h["text"] for h in hits)
            return (t["gold"] in paths) and (t["anchor"] in ctx)

        m_hits = mr["hits"] if verdict == "answer" else []
        m_ctx_tokens = (estimate_tokens(q) + sum(estimate_tokens(h["text"])
                                                 for h in m_hits))
        row = {
            "id": t["id"], "expected": t["expected"],
            "tokens_full": full_tokens,
            "full": {"success": True if t["expected"] == "answer" and full_ok
                     else (None if t["expected"] == "abstain" else False),
                     "tokens": full_tokens, "chunks": len(corpus)},
            "lexical": {"success": success(lr["hits"]),
                        "tokens": estimate_tokens(q) + sum(
                            estimate_tokens(h["text"]) for h in lr["hits"]),
                        "chunks": len(lr["hits"]),
                        "paths": [h["citation"]["path"] for h in lr["hits"]],
                        "latency_ms": lr["latency_ms"]},
            "dense": {"success": success(dr["hits"]),
                      "tokens": estimate_tokens(q) + sum(
                          estimate_tokens(h["text"]) for h in dr["hits"]),
                      "chunks": len(dr["hits"]),
                      "paths": [h["citation"]["path"] for h in dr["hits"]],
                      "latency_ms": dr["latency_ms"]},
            "dense_mmr_policy": {
                "decision": verdict, "reason": reason,
                "success": (len(m_hits) == 0) if t["expected"] == "abstain"
                           else success(m_hits),
                "tokens": m_ctx_tokens, "chunks": len(m_hits),
                "paths": [h["citation"]["path"] for h in m_hits],
                "latency_ms": mr["latency_ms"]},
        }
        rows.append(row)
        print(f"{t['id']:8s} full={row['full']['success']} "
              f"lex={row['lexical']['success']} dense={row['dense']['success']} "
              f"mmrpol={row['dense_mmr_policy']['success']}({verdict}) "
              f"tok {full_tokens}->{row['lexical']['tokens']}/"
              f"{row['dense']['tokens']}/{m_ctx_tokens}")
    report = {"top_k": TOP_K, "mmr": {"fetch_k": 20, "lambda": 0.5},
              "tasks": rows}
    (HERE / "agent_value_results.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


if __name__ == "__main__":
    main()
