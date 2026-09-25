"""Mesure holdout cycle 2 — UNE SEULE FOIS, point fige uniquement.

Lit c2_holdout.json + c2_freeze.json. Tous les parametres (tau, delta,
top_k, collections, criteres) viennent du freeze ; le script auto-verifie
son propre SHA contre le freeze (toute modification post-freeze = STOP).
Bras : lexical / dense-sec / dense-fact bruts + A2=sec+politique,
B2=fact+politique. Ecrit c2_results.json. Refuse d'ecraser un resultat
existant (mesure unique).
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
C1 = HERE.parent
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(C1))

from chunk_facts import build_fact_corpus  # noqa: E402
from corpus_manifest import build_corpus  # noqa: E402
from dense_qdrant import DenseQdrant, index_corpus  # noqa: E402
from policy import decide  # noqa: E402
from retrieval_metrics import (decision_correct, mean,  # noqa: E402
                               retrieval_ok_lenient, retrieval_ok_strict,
                               retrieval_scores)
from store import Collection, estimate_tokens  # noqa: E402

DATA_DIR = Path(os.environ.get("QDRANT_DATA_DIR",
                               "/home/pierrecsn/.cache/qdrant-508-exp/data"))


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def du(p: Path) -> int:
    try:
        return int(subprocess.check_output(
            ["du", "-s", str(p)], text=True).split()[0]) * 1024
    except Exception:
        return -1


def main() -> dict:
    freeze_path = HERE / "c2_freeze.json"
    if not freeze_path.is_file():
        raise SystemExit("REFUS : pas de freeze (c2_freeze.json absent).")
    if (HERE / "c2_results.json").exists():
        raise SystemExit("REFUS : c2_results.json existe deja (mesure unique).")
    freeze = json.loads(freeze_path.read_text())
    if sha_file(Path(__file__).resolve()) != freeze["code_shas"]["c2_measure.py"]:
        raise SystemExit("REFUS : c2_measure.py differe du freeze (STOP).")
    tau, delta = freeze["point"]["tau"], freeze["point"]["delta"]
    top_k = freeze["top_k"]
    holdout = json.loads((HERE / "c2_holdout.json").read_text())["items"]

    sec_corpus = build_corpus(ROOT)
    fact_corpus = build_fact_corpus(ROOT)
    assert len(sec_corpus) == 209 and len(fact_corpus) == 881
    full_tokens = estimate_tokens("\n\n".join(d["text"] for d in sec_corpus))
    lex = Collection("agent_memory_c2")
    for d in sec_corpus:
        lex.upsert(d["id"], d["text"], d["payload"])
    dq_sec = DenseQdrant(collection=freeze["collections"]["sec"])
    idx_sec = index_corpus(dq_sec, sec_corpus)
    dq_fact = DenseQdrant(collection=freeze["collections"]["fact"])
    idx_fact = index_corpus(dq_fact, fact_corpus)
    time.sleep(1)

    def success_answer(item, hits) -> bool:
        paths = [h["citation"]["path"] for h in hits]
        ctx = " ".join(h["text"] for h in hits)
        return any(g in paths for g in item["golds"]) and \
            any(a in ctx for a in item["anchors"])

    rows = []
    for it in holdout:
        q, ans = it["query"], it["expected"] == "answer"
        lr = lex.search(q, top_k=top_k, filters={"project": "cookigram"})
        sr = dq_sec.search(q, top_k=top_k, filters={"project": "cookigram"})
        fr = dq_fact.search(q, top_k=top_k, filters={"project": "cookigram"})

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

        def cell(search_hits):
            scores = [h["score"] for h in search_hits]
            verdict, reason = decide(scores, tau=tau, delta=delta)
            hits = search_hits if verdict == "answer" else []
            r = retr(search_hits)
            rec = r[f"recall_at{top_k}"]
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

        row = {
            "id": it["id"], "kind": it["kind"], "expected": it["expected"],
            "tokens_full": full_tokens,
            "full": {"success": True if ans and all(
                a in "\n\n".join(d["text"] for d in sec_corpus)
                for a in it["anchors"]) else (None if not ans else False),
                     "tokens": full_tokens},
            "lexical": {**raw(lr["hits"]), "latency_ms": lr["latency_ms"]},
            "dense_sec": {**raw(sr["hits"]), "latency_ms": sr["latency_ms"]},
            "dense_fact": {**raw(fr["hits"]), "latency_ms": fr["latency_ms"]},
            "A2_sec_policy": cell(sr["hits"]),
            "B2_fact_policy": cell(fr["hits"]),
        }
        rows.append(row)
        print(f"{it['id']:9s} lex={row['lexical']['success']} "
              f"sec={row['dense_sec']['success']} "
              f"fact={row['dense_fact']['success']} "
              f"A2={row['A2_sec_policy']['success']} "
              f"B2={row['B2_fact_policy']['success']}")

    def col(key, sub):
        return [t[key].get(sub) for t in rows]

    def colr(key, sub):
        return [t[key]["retrieval"][sub] for t in rows]

    rk = f"recall_at{top_k}"
    summary = {}
    for key in ("lexical", "dense_sec", "dense_fact"):
        summary[key] = {
            "success_answer_rate": mean(
                [1.0 if s else 0.0 for s in col(key, "success")
                 if s is not None]),
            "rank1": mean(colr(key, "rank1")), "recall_at3": mean(colr(key, rk))}
    for key in ("A2_sec_policy", "B2_fact_policy"):
        summary[key] = {
            "success_rate": mean(
                [1.0 if s else 0.0 for s in col(key, "success")]),
            "rank1": mean(colr(key, "rank1")),
            "recall_at3": mean(colr(key, rk)),
            "decision_strict": mean(col(key, "decision_correct_strict")),
            "decision_lenient": mean(col(key, "decision_correct_lenient"))}

    report = {
        "cycle": 2, "phase": "holdout-measure",
        "freeze_sha": sha_file(freeze_path),
        "point": {"tau": tau, "delta": delta}, "top_k": top_k,
        "summary": summary,
        "corpora": {"section_chunks": len(sec_corpus),
                    "fact_chunks": len(fact_corpus),
                    "index_sec": idx_sec, "index_fact": idx_fact},
        "footprint": {
            "disk_sec_bytes": du(DATA_DIR / "collections"
                                 / freeze["collections"]["sec"]),
            "disk_fact_bytes": du(DATA_DIR / "collections"
                                  / freeze["collections"]["fact"])},
        "tasks": rows,
    }
    (HERE / "c2_results.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


if __name__ == "__main__":
    main()
