"""Matrice d'ablation gate 4 (holdout aveugle v2, UNE seule mesure).

Cellules : A=sec+politique / B=fact+politique / C=sec+cluster / D=fact+cluster.
References : full, lexical(sec), dense brut sec, dense brut fact.
Succes answer : >=1 gold path top-3 ET >=1 ancre dans le contexte.
Succes abstain : 0 chunk injecte (cellules a politique ; N/A sinon).
Ecrit ablation_results.json (brut par item et par methode).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

from chunk_facts import build_fact_corpus  # noqa: E402
from corpus_manifest import build_corpus  # noqa: E402
from dense_qdrant import COLLECTION_FACT, DenseQdrant, index_corpus  # noqa: E402
from policy import DELTA, GAMMA, TAU, decide, decide_cluster  # noqa: E402
from retrieval_metrics import (decision_correct, mean,  # noqa: E402
                               retrieval_ok_lenient, retrieval_ok_strict,
                               retrieval_scores)
from store import Collection, estimate_tokens  # noqa: E402

TOP_K = 3
DATA_DIR = Path(os.environ.get("QDRANT_DATA_DIR",
                               "/home/pierrecsn/.cache/qdrant-508-exp/data"))


def du(p: Path) -> int:
    try:
        return int(subprocess.check_output(
            ["du", "-s", str(p)], text=True).split()[0]) * 1024
    except Exception:
        return -1


def rss() -> float | None:
    try:
        pid = subprocess.check_output(
            ["pgrep", "-f", "qdrant-508-exp/bin/qdran[t]"],
            text=True).split()[0]
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return round(int(line.split()[1]) / 1024, 1)
    except Exception:
        return None
    return None


def success_answer(item, hits) -> bool:
    paths = [h["citation"]["path"] for h in hits]
    ctx = " ".join(h["text"] for h in hits)
    return any(g in paths for g in item["golds"]) and \
        any(a in ctx for a in item["anchors"])


def main() -> dict:
    holdout = json.loads((HERE / "holdout.json").read_text())["items"]
    sec_corpus = build_corpus(ROOT)
    fact_corpus = build_fact_corpus(ROOT)
    full_text = "\n\n".join(d["text"] for d in sec_corpus)
    full_tokens = estimate_tokens(full_text)

    lex = Collection("agent_memory")
    for d in sec_corpus:
        lex.upsert(d["id"], d["text"], d["payload"])
    dq_sec = DenseQdrant()
    idx_sec = index_corpus(dq_sec, sec_corpus)
    dq_fact = DenseQdrant(collection=COLLECTION_FACT)
    idx_fact = index_corpus(dq_fact, fact_corpus)
    time.sleep(1)

    rows = []
    for it in holdout:
        q = it["query"]
        ans = it["expected"] == "answer"
        lr = lex.search(q, top_k=TOP_K, filters={"project": "cookigram"})
        sr = dq_sec.search(q, top_k=TOP_K, filters={"project": "cookigram"})
        fr = dq_fact.search(q, top_k=TOP_K, filters={"project": "cookigram"})
        sv = dq_sec.search(q, top_k=TOP_K, filters={"project": "cookigram"},
                           with_vectors=True)
        fv = dq_fact.search(q, top_k=TOP_K, filters={"project": "cookigram"},
                            with_vectors=True)

        def retr(hits):
            # Retrieval pur : independant de toute decision.
            return retrieval_scores(
                [h["citation"]["path"] for h in hits],
                it["golds"] if ans else [])

        def cell(search_hits, vec_hits, policy_fn):
            scores = [h["score"] for h in search_hits]
            vecs = [h.get("vector", []) for h in vec_hits["hits"]]
            verdict, reason = policy_fn(scores, vecs)
            hits = search_hits if verdict == "answer" else []
            r = retr(search_hits)  # retrieval AVANT gating politique
            rec = r["recall_at3"]
            return {"decision": verdict, "reason": reason,
                    "success": (len(hits) == 0) if not ans
                               else success_answer(it, hits),
                    "retrieval": r,
                    "decision_correct_strict": decision_correct(
                        it["expected"], verdict, retrieval_ok_strict(rec)),
                    "decision_correct_lenient": decision_correct(
                        it["expected"], verdict, retrieval_ok_lenient(rec)),
                    "tokens": estimate_tokens(q) + sum(
                        estimate_tokens(h["text"]) for h in hits),
                    "chunks": len(hits),
                    "paths": [h["citation"]["path"] for h in hits]}

        def raw(hits):
            return {"success": None if not ans else success_answer(it, hits),
                    "retrieval": retr(hits),
                    "tokens": estimate_tokens(q) + sum(
                        estimate_tokens(h["text"]) for h in hits),
                    "chunks": len(hits),
                    "paths": [h["citation"]["path"] for h in hits]}

        from policy import decide as _d, decide_cluster as _dc
        row = {
            "id": it["id"], "kind": it["kind"], "expected": it["expected"],
            "tokens_full": full_tokens,
            "full": {"success": True if ans and all(
                a in full_text for a in it["anchors"]) else (None if not ans
                                                             else False),
                     "tokens": full_tokens},
            "lexical_sec": {**raw(lr["hits"]), "latency_ms": lr["latency_ms"]},
            "dense_raw_sec": {**raw(sr["hits"]),
                              "latency_ms": sr["latency_ms"]},
            "dense_raw_fact": {**raw(fr["hits"]),
                               "latency_ms": fr["latency_ms"]},
            "A_sec_policy": cell(sr["hits"], sv, lambda s, v: _d(s)),
            "B_fact_policy": cell(fr["hits"], fv, lambda s, v: _d(s)),
            "C_sec_cluster": cell(sr["hits"], sv, lambda s, v: _dc(s, v)),
            "D_fact_cluster": cell(fr["hits"], fv, lambda s, v: _dc(s, v)),
        }
        rows.append(row)
        r = row
        print(f"{it['id']:10s} full={r['full']['success']} "
              f"lex={r['lexical_sec']['success']} drawS={r['dense_raw_sec']['success']} "
              f"drawF={r['dense_raw_fact']['success']} A={r['A_sec_policy']['success']} "
              f"B={r['B_fact_policy']['success']} C={r['C_sec_cluster']['success']} "
              f"D={r['D_fact_cluster']['success']}")

    def col(key, sub):
        return [t[key].get(sub) for t in rows]

    def colr(key, sub):
        return [t[key]["retrieval"][sub] for t in rows]

    summary = {}
    for key in ("lexical_sec", "dense_raw_sec", "dense_raw_fact"):
        summary[key] = {
            "success_answer_rate": mean(
                [1.0 if s else 0.0 for s in col(key, "success")
                 if s is not None]),
            "rank1": mean(colr(key, "rank1")),
            "recall_at3": mean(colr(key, "recall_at3"))}
    for key in ("A_sec_policy", "B_fact_policy", "C_sec_cluster",
                "D_fact_cluster"):
        summary[key] = {
            "success_rate": mean(
                [1.0 if s else 0.0 for s in col(key, "success")]),
            "rank1": mean(colr(key, "rank1")),
            "recall_at3": mean(colr(key, "recall_at3")),
            "decision_strict": mean(col(key, "decision_correct_strict")),
            "decision_lenient": mean(col(key, "decision_correct_lenient"))}

    report = {
        "holdout_frozen": "holdout.json v2 (ancre H-D durcie pre-mesure)",
        "dev_freeze": "dev_freeze.json (point tau/delta/gamma fige sur dev)",
        "top_k": TOP_K, "summary": summary,
        "policy": {"tau": TAU, "delta": DELTA, "gamma": GAMMA,
                   "gamma_note": "dev: aucune separation (grappes reponse "
                   "{D1:0.587,H2:0.733} vs pieges {N2:0.706,N4:0.824}, "
                   "meilleur 2/4 = hasard) ; 0.70 fige pour tester "
                   "l'hypothese negative"},
        "corpora": {"section_chunks": len(sec_corpus),
                    "fact_chunks": len(fact_corpus),
                    "index_sec": idx_sec, "index_fact": idx_fact},
        "footprint": {"disk_sec_bytes": du(DATA_DIR / "collections" / "agent_memory"),
                      "disk_fact_bytes": du(DATA_DIR / "collections" / COLLECTION_FACT),
                      "rss_mb": rss()},
        "tasks": rows,
    }
    (HERE / "ablation_results.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"sec={len(sec_corpus)} fact={len(fact_corpus)} "
          f"disk={report['footprint']['disk_sec_bytes']}/"
          f"{report['footprint']['disk_fact_bytes']}B rss={report['footprint']['rss_mb']}MB")
    return report


if __name__ == "__main__":
    main()
