"""Mesure unique du holdout cycle2b (C2B_HOLDOUT_MEASURE_GO, etape B).

Preconditions : c2b_holdout.json fige par commit, point (tau=0.60,
delta=0.05) de c2b_freeze.json, pins corpus sec 350/72b391ca91fb2460
fact 1912/38431cd1458610eb. UNE seule execution : rebuild collections
dediees agent_memory_c2b(_holdout run) / agent_memory_fact_c2b, mesure
lexical / dense-sec / dense-fact + cellules A2=sec+politique /
B2=fact+politique au point fige. Aucun sweep, aucun retuning,
aucune modification d'item. Ecrit c2b_results.json.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
C1 = HERE.parent
C2B = HERE
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(C1))
sys.path.insert(0, str(C2B))

from corpus2b import build_corpus_c2b, build_fact_corpus_c2b  # noqa: E402
from dense_qdrant import DenseQdrant, index_corpus  # noqa: E402
from policy import decide  # noqa: E402
from retrieval_metrics import (decision_correct, mean,  # noqa: E402
                               retrieval_ok_lenient, retrieval_ok_strict,
                               retrieval_scores)
from store import Collection, estimate_tokens  # noqa: E402

COL_SEC = "agent_memory_c2b"
COL_FACT = "agent_memory_fact_c2b"
TOP_K = 3
PIN_SEC = (350, "72b391ca91fb2460")
PIN_FACT = (1912, "38431cd1458610eb")


def corpus_sha(corpus: list[dict]) -> str:
    h = hashlib.sha256()
    for d in sorted(corpus, key=lambda d: d["id"]):
        h.update((d["id"] + "\x00" + d["text"]).encode())
    return h.hexdigest()[:16]


def success_answer(item, hits) -> bool:
    paths = [h["citation"]["path"] for h in hits]
    ctx = " ".join(h["text"] for h in hits)
    return (any(g in paths for g in item["golds"])
            and any(a in ctx for a in item["anchors"]))


def main() -> dict:
    freeze = json.loads((HERE / "c2b_freeze.json").read_text(
        encoding="utf-8"))
    tau, delta = freeze["point"]["tau"], freeze["point"]["delta"]
    assert (tau, delta) == (0.60, 0.05), (tau, delta)
    holdout = json.loads((HERE / "c2b_holdout.json").read_text(
        encoding="utf-8"))["items"]
    assert len(holdout) >= 30
    dev_n = freeze["dev_composition"]["n"]

    sec_corpus = build_corpus_c2b(ROOT)
    fact_corpus = build_fact_corpus_c2b(ROOT)
    assert (len(sec_corpus), corpus_sha(sec_corpus)) == PIN_SEC
    assert (len(fact_corpus), corpus_sha(fact_corpus)) == PIN_FACT
    full_tokens = estimate_tokens("\n\n".join(d["text"] for d in sec_corpus))

    lex = Collection("agent_memory_c2b")
    for d in sec_corpus:
        lex.upsert(d["id"], d["text"], d["payload"])
    dq_sec = DenseQdrant(collection=COL_SEC)
    idx_sec = index_corpus(dq_sec, sec_corpus)
    dq_fact = DenseQdrant(collection=COL_FACT)
    idx_fact = index_corpus(dq_fact, fact_corpus)
    time.sleep(1)

    rows = []
    for it in holdout:
        q, ans = it["query"], it["expected"] == "answer"
        lr = lex.search(q, top_k=TOP_K, filters={"project": "cookigram"})
        sr = dq_sec.search(q, top_k=TOP_K, filters={"project": "cookigram"})
        fr = dq_fact.search(q, top_k=TOP_K, filters={"project": "cookigram"})

        def retr(hits):
            return retrieval_scores(
                [h["citation"]["path"] for h in hits],
                it["golds"] if ans else [])

        def raw(hits):
            return {"success": None if not ans else success_answer(it, hits),
                    "retrieval": retr(hits),
                    "tokens": estimate_tokens(q) + sum(
                        estimate_tokens(h["text"]) for h in hits),
                    "chunks": len(hits),
                    "paths": [h["citation"]["path"] for h in hits]}

        def cell(hits):
            scores = [h["score"] for h in hits]
            verdict, reason = decide(scores, tau=tau, delta=delta)
            kept = hits if verdict == "answer" else []
            r = retr(hits)
            rec = r["recall_at3"]
            return {"decision": verdict, "reason": reason,
                    "success": (len(kept) == 0) if not ans
                               else success_answer(it, kept),
                    "retrieval": r,
                    "decision_correct_strict": decision_correct(
                        it["expected"], verdict, retrieval_ok_strict(rec)),
                    "decision_correct_lenient": decision_correct(
                        it["expected"], verdict, retrieval_ok_lenient(rec)),
                    "tokens": estimate_tokens(q) + sum(
                        estimate_tokens(h["text"]) for h in kept),
                    "chunks": len(kept),
                    "paths": [h["citation"]["path"] for h in kept],
                    "margin": round(scores[0] - scores[1], 4)
                              if len(scores) > 1 else None,
                    "s1": round(scores[0], 4) if scores else None}

        row = {"id": it["id"], "kind": it["kind"], "expected": it["expected"],
               "tokens_full": full_tokens,
               "lexical": {**raw(lr["hits"]), "latency_ms": lr["latency_ms"]},
               "dense_sec": {**raw(sr["hits"]), "latency_ms": sr["latency_ms"]},
               "dense_fact": {**raw(fr["hits"]),
                              "latency_ms": fr["latency_ms"]},
               "A2_sec_policy": cell(sr["hits"]),
               "B2_fact_policy": cell(fr["hits"])}
        rows.append(row)
        r = row
        print(f"{it['id']:10s} lex={r['lexical']['success']} "
              f"sec={r['dense_sec']['success']} fact={r['dense_fact']['success']} "
              f"A2={r['A2_sec_policy']['success']} "
              f"B2={r['B2_fact_policy']['success']}")

    def col(key, sub):
        return [t[key].get(sub) for t in rows]

    def colr(key, sub):
        return [t[key]["retrieval"][sub] for t in rows]

    summary = {}
    for key in ("lexical", "dense_sec", "dense_fact"):
        summary[key] = {
            "success_answer_rate": mean(
                [1.0 if s else 0.0 for s in col(key, "success")
                 if s is not None]),
            "rank1": mean(colr(key, "rank1")),
            "recall_at3": mean(colr(key, "recall_at3"))}
    for key in ("A2_sec_policy", "B2_fact_policy"):
        summary[key] = {
            "success_rate": mean([1.0 if s else 0.0 for s in col(key, "success")]),
            "rank1": mean(colr(key, "rank1")),
            "recall_at3": mean(colr(key, "recall_at3")),
            "decision_strict": mean(col(key, "decision_correct_strict")),
            "decision_lenient": mean(col(key, "decision_correct_lenient"))}

    report = {
        "cycle": "2b", "phase": "holdout-measure-unique",
        "freeze_point": {"tau": tau, "delta": delta,
                         "dev_decision_lenient_fact":
                         freeze["point"]["dev_decision_lenient_fact"]},
        "dev_n": dev_n, "holdout_n": len(rows), "top_k": TOP_K,
        "summary": summary,
        "corpora": {"section_chunks": len(sec_corpus),
                    "section_sha": corpus_sha(sec_corpus),
                    "fact_chunks": len(fact_corpus),
                    "fact_sha": corpus_sha(fact_corpus),
                    "index_sec": idx_sec, "index_fact": idx_fact},
        "tasks": rows,
    }
    (HERE / "c2b_results.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"holdout_n={len(rows)} summary={json.dumps(summary)}")
    return report


if __name__ == "__main__":
    main()
