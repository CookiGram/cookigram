"""Mesure holdout unique cycle 510 (GO_HOLDOUT_510).

Preconditions : 510_freeze.json fige (point tau=0.6, delta=0.03),
510_holdout.json (12 items), pins corpora sec 44/1c55730fe6de78e9
fact 414/07eae33590c88b5a. UNE seule execution : rebuild collections
dediees agent_memory_510 / agent_memory_fact_510, mesure lexical /
dense-sec / dense-fact + cellules A2=sec+politique /
B2=fact+politique au point fige. Aucun sweep, aucun retuning,
aucune modification d'item, aucun seuil invente. Ecrit
510_results.json (observations, regles, verdicts mecaniques,
incidents, conclusion descriptive).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
C1 = HERE.parent
C510 = HERE
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(C1))
sys.path.insert(0, str(C510))

from corpus510 import build_corpus_510, build_fact_corpus_510  # noqa: E402
from dense_qdrant import DenseQdrant, index_corpus  # noqa: E402
from policy import decide  # noqa: E402
from retrieval_metrics import (decision_correct, mean,  # noqa: E402
                               retrieval_ok_lenient, retrieval_ok_strict,
                               retrieval_scores)
from store import Collection, estimate_tokens  # noqa: E402

COL_SEC = "agent_memory_510"
COL_FACT = "agent_memory_fact_510"
TOP_K = 3
FILTERS = {"project": "cookigram"}
EXPECTED = "answer"  # holdout entierement answerable (12 golds)


def sha16(corpus: list[dict]) -> str:
    h = hashlib.sha256()
    for d in sorted(corpus, key=lambda d: d["id"]):
        h.update((d["id"] + "\x00" + d["text"]).encode())
    return h.hexdigest()[:16]


def locator(path: str, section: str) -> str:
    return f"{path}::{section}"


def main() -> dict:
    freeze = json.loads((HERE / "510_freeze.json").read_text(
        encoding="utf-8"))
    tau = freeze["config"]["point"]["tau"]
    delta = freeze["config"]["point"]["delta"]
    assert (tau, delta) == (0.6, 0.03), (tau, delta)
    holdout = json.loads((HERE / "510_holdout.json").read_text(
        encoding="utf-8"))["items"]
    assert len(holdout) == 12, len(holdout)
    pins = freeze["corpora_pins"]
    forbidden = json.loads(
        (HERE / "forbidden_508.json").read_text(encoding="utf-8"))
    banned = [rec["anchor"] for rec in forbidden["anchors"]]
    for it in holdout:
        blob = "\n".join([it["question"], it["answer"], it["evidence"]])
        for anchor in banned:
            if anchor in blob:
                raise SystemExit(f"REFUS : ancre #508 dans {it['id']}.")

    plan = json.loads(
        (HERE / "split_preregistration.json").read_text(encoding="utf-8"))
    base = plan["base_commit"]
    docs = ([d["path"] for d in plan["documents"]["dev"]]
            + [d["path"] for d in plan["documents"]["holdout_reserve"]])
    drift = subprocess.run(
        ["git", "diff", "--quiet", base, "--", *docs],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if drift.returncode != 0:
        raise SystemExit(f"REFUS : corpus derive de {base[:7]}.")
    sec_corpus = build_corpus_510(ROOT)
    fact_corpus = build_fact_corpus_510(ROOT)
    assert (len(sec_corpus), sha16(sec_corpus)) == (
        pins["section_chunks"], pins["section_sha"])
    assert (len(fact_corpus), sha16(fact_corpus)) == (
        pins["fact_chunks"], pins["fact_sha"])
    full_tokens = estimate_tokens("\n\n".join(d["text"] for d in sec_corpus))

    lex = Collection(COL_SEC)
    for d in sec_corpus:
        lex.upsert(d["id"], d["text"], d["payload"])
    dq_sec = DenseQdrant(collection=COL_SEC)
    idx_sec = index_corpus(dq_sec, sec_corpus)
    dq_fact = DenseQdrant(collection=COL_FACT)
    idx_fact = index_corpus(dq_fact, fact_corpus)
    time.sleep(1)
    if dq_sec.info()["points"] != len(sec_corpus):
        raise SystemExit("REFUS : index sec incomplet.")
    if dq_fact.info()["points"] != len(fact_corpus):
        raise SystemExit("REFUS : index fact incomplet.")
    server_version = dq_sec.version()

    rows = []
    for it in holdout:
        q = it["question"]
        gold = locator(it["anchor"]["path"],
                       it["anchor"]["heading_path"][-1])
        lr = lex.search(q, top_k=TOP_K, filters=FILTERS)
        sr = dq_sec.search(q, top_k=TOP_K, filters=FILTERS)
        fr = dq_fact.search(q, top_k=TOP_K, filters=FILTERS)

        def locs(hits):
            return [locator(h["citation"]["path"], h["citation"]["section"])
                    for h in hits]

        def retr(hits):
            return retrieval_scores(locs(hits), [gold])

        def succ(hits):
            ctx = " ".join(h["text"] for h in hits)
            return (gold in locs(hits)[:TOP_K]
                    and it["evidence"] in ctx)

        def slim(hits):
            return [{"path": h["citation"]["path"],
                     "section": h["citation"]["section"],
                     "score": h["score"]} for h in hits]

        def raw(hits, res):
            return {"success": succ(hits), "retrieval": retr(hits),
                    "tokens": estimate_tokens(q) + sum(
                        estimate_tokens(h["text"]) for h in hits),
                    "chunks": len(hits),
                    "latency_ms": res["latency_ms"],
                    "hits": slim(hits)}

        def cell(hits, res):
            scores = [h["score"] for h in hits]
            verdict, reason = decide(scores, tau=tau, delta=delta)
            kept = hits if verdict == "answer" else []
            rec = retr(hits)["recall_at3"]
            return {"decision": verdict, "reason": reason,
                    "success": succ(kept),
                    "retrieval": retr(hits),
                    "decision_correct_strict": decision_correct(
                        EXPECTED, verdict, retrieval_ok_strict(rec)),
                    "decision_correct_lenient": decision_correct(
                        EXPECTED, verdict, retrieval_ok_lenient(rec)),
                    "tokens": estimate_tokens(q) + sum(
                        estimate_tokens(h["text"]) for h in kept),
                    "chunks": len(kept),
                    "latency_ms": res["latency_ms"],
                    "hits": slim(kept),
                    "margin": round(scores[0] - scores[1], 4)
                              if len(scores) > 1 else None,
                    "s1": round(scores[0], 4) if scores else None}

        row = {"id": it["id"], "anchor_id": it["anchor"]["anchor_id"],
               "expected": EXPECTED, "tokens_full": full_tokens,
               "lexical": raw(lr["hits"], lr),
               "dense_sec": raw(sr["hits"], sr),
               "dense_fact": raw(fr["hits"], fr),
               "A2_sec_policy": cell(sr["hits"], sr),
               "B2_fact_policy": cell(fr["hits"], fr)}
        rows.append(row)
        print(f"{it['id']:10s} lex={row['lexical']['success']} "
              f"sec={row['dense_sec']['success']} "
              f"fact={row['dense_fact']['success']} "
              f"A2={row['A2_sec_policy']['success']} "
              f"B2={row['B2_fact_policy']['success']}")

    def col(key, sub):
        return [t[key].get(sub) for t in rows]

    def colr(key, sub):
        return [t[key]["retrieval"][sub] for t in rows]

    summary = {}
    for key in ("lexical", "dense_sec", "dense_fact"):
        summary[key] = {
            "success_answer_rate": mean(
                [1.0 if s else 0.0 for s in col(key, "success")]),
            "rank1": mean(colr(key, "rank1")),
            "recall_at3": mean(colr(key, "recall_at3"))}
    for key in ("A2_sec_policy", "B2_fact_policy"):
        summary[key] = {
            "success_rate": mean(
                [1.0 if s else 0.0 for s in col(key, "success")]),
            "rank1": mean(colr(key, "rank1")),
            "recall_at3": mean(colr(key, "recall_at3")),
            "decision_strict": mean(col(key, "decision_correct_strict")),
            "decision_lenient": mean(col(key, "decision_correct_lenient"))}

    from importlib.metadata import version as _pkg_version

    def _ver(dist: str) -> str:
        try:
            return _pkg_version(dist)
        except Exception:
            return "?"

    dev = json.loads((HERE / "510_calibration.json").read_text(
        encoding="utf-8"))["retrieval_dev"]
    report = {
        "issue": "CookiGram/cookigram#510",
        "phase": "holdout-measure-unique",
        "authorization": "GO_HOLDOUT_510",
        "runs": 1,
        "freeze_point": {"tau": tau, "delta": delta,
                         "dev_decision_lenient_fact":
                         freeze["config"]["point"][
                             "dev_decision_lenient_fact"]},
        "dev_n": 13, "dev_neg_n": 8, "holdout_n": len(rows),
        "top_k": TOP_K,
        "observations": {"summary": summary},
        "rules": {
            "retrieval": "510_calibration.json params (geles, verifies "
                         "par pins corpora)",
            "policy": "policy.decide @ (0.6, 0.03), precedent c2b",
            "cells": "A2=sec+politique, B2=fact+politique "
                      "(510_freeze.json) ; lexical/sec/fact bruts",
            "selection": "aucune selection sur le holdout ; "
                          "configuration transmise par la regle DEV",
        },
        "verdicts": {
            "note": "aucun seuil passe/echec pre-enregistre : "
                    "verdicts = metriques mecaniques ci-dessous",
            "A2_sec_policy": summary["A2_sec_policy"],
            "B2_fact_policy": summary["B2_fact_policy"],
        },
        "incidents": "aucun incident instrumental ; mesure unique "
                      "complete du premier run",
        "conclusion_descriptive": {
            "dev_retrieval": dev,
            "holdout_retrieval": {k: summary[k] for k in
                                  ("lexical", "dense_sec", "dense_fact")},
            "holdout_cells": {k: summary[k] for k in
                              ("A2_sec_policy", "B2_fact_policy")},
            "note": "comparaison descriptive DEV vs holdout (question "
                    "de replication) ; aucun seuil pre-enregistre ; "
                    "aucune implication de tuning",
        },
        "corpora": {"section_chunks": len(sec_corpus),
                    "section_sha": sha16(sec_corpus),
                    "fact_chunks": len(fact_corpus),
                    "fact_sha": sha16(fact_corpus),
                    "index_sec": idx_sec, "index_fact": idx_fact},
        "versions": {"qdrant_server": server_version,
                     "qdrant_client": _ver("qdrant-client"),
                     "fastembed": _ver("fastembed")},
        "tasks": rows,
    }
    (HERE / "510_results.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"holdout_n={len(rows)} summary={json.dumps(summary)}")
    return report


if __name__ == "__main__":
    main()
