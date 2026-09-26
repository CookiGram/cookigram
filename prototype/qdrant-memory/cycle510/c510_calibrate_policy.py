"""Calibration politique DEV ONLY cycle 510 (POLICY CALIBRATION DEV).

Grille pre-enregistree tau x delta (policy_preregistration.json),
appliquee mecaniquement, SANS re-mesure retrieval des 13 positifs
(lignes gelees de 510_calibration.json : scores denses + recall) et
avec UNE mesure retrieval unique des 8 negatifs (3 bras, parametres
geles strictement inchanges, corpora reconstruits et verifies aux
SHA geles). Grille purement computationnelle via policy.decide.
Selection mecanique : max decision_lenient sur dense_fact, egalite
-> tau superieur puis delta superieur. Conserve les 28+28 cellules,
pas seulement le meilleur. Ecrit 510_policy_calibration.json.

Refuse de tourner si : cycle510/holdout.json existe ; les negatifs
ne sont pas exactement les 8 items abstain sans slot ; les lignes
positives gelees ont change ; le corpus a derive ; un SHA corpora
differe du gele ; un champ negatif contient une ancre #508.
Ni holdout, ni tuning manuel, ni changement retrieval.
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
from store import Collection  # noqa: E402

COL_SEC = "agent_memory_510"
COL_FACT = "agent_memory_fact_510"
TOP_K = 3
FILTERS = {"project": "cookigram"}
POS_EXPECTED = "answer"  # 13 positifs answerable par construction (preuve)
NEG_EXPECTED = "abstain"
SLOT_KEYS = {"anchor", "anchor_id", "path", "section", "section_index",
             "heading_path", "slot", "slots", "evidence", "answer"}


def sha16(corpus: list[dict]) -> str:
    h = hashlib.sha256()
    for d in sorted(corpus, key=lambda d: d["id"]):
        h.update((d["id"] + "\x00" + d["text"]).encode())
    return h.hexdigest()[:16]


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main() -> dict:
    if (HERE / "holdout.json").exists():
        raise SystemExit("REFUS : cycle510/holdout.json existe.")
    plan = json.loads(
        (HERE / "split_preregistration.json").read_text(encoding="utf-8"))
    if plan.get("holdout_created"):
        raise SystemExit("REFUS : holdout_created est vrai.")
    policy = json.loads(
        (HERE / "policy_preregistration.json").read_text(encoding="utf-8"))
    negs = json.loads(
        (HERE / "dev_negatives.json").read_text(encoding="utf-8"))["items"]
    if len(negs) != 8:
        raise SystemExit(f"REFUS : {len(negs)} negatifs, 8 attendus.")
    for it in negs:
        if not SLOT_KEYS.isdisjoint(it.keys()):
            raise SystemExit(f"REFUS : slot dans {it['id']}.")
    frozen = json.loads(
        (HERE / "510_calibration.json").read_text(encoding="utf-8"))
    if frozen.get("phase") != "dev-calibration-retrieval-only":
        raise SystemExit("REFUS : lignes positives non gelees.")
    pos_rows = frozen["items"]
    if len(pos_rows) != 13:
        raise SystemExit(f"REFUS : {len(pos_rows)} positifs, 13 attendus.")
    forbidden = json.loads(
        (HERE / "forbidden_508.json").read_text(encoding="utf-8"))
    banned = [rec["anchor"] for rec in forbidden["anchors"]]
    for it in negs:
        blob = "\n".join([it["query"], it["rationale"]])
        for anchor in banned:
            if anchor in blob:
                raise SystemExit(f"REFUS : ancre #508 dans {it['id']}.")

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
    pins = policy["inputs"]["corpora_pins_verified_equal"]
    observed = {"section_chunks": len(sec_corpus),
                "section_sha": sha16(sec_corpus),
                "fact_chunks": len(fact_corpus),
                "fact_sha": sha16(fact_corpus)}
    for key in ("section_chunks", "section_sha", "fact_chunks", "fact_sha"):
        if observed[key] != pins[key] or observed[key] != frozen["corpora"][key]:
            raise SystemExit(f"REFUS : corpora {key} a derive "
                             f"({observed[key]}).")

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

    neg_rows = []
    for it in negs:
        lr = lex.search(it["query"], top_k=TOP_K, filters=FILTERS)
        sr = dq_sec.search(it["query"], top_k=TOP_K, filters=FILTERS)
        fr = dq_fact.search(it["query"], top_k=TOP_K, filters=FILTERS)

        def slim(hits):
            return [{"path": h["citation"]["path"],
                     "section": h["citation"]["section"],
                     "score": h["score"]} for h in hits]

        def arm_row(res):
            scores = [h["score"] for h in res["hits"]]
            return {"success": None,
                    "retrieval": retrieval_scores(
                        [f"{h['citation']['path']}::{h['citation']['section']}"
                         for h in res["hits"]], []),
                    "scores": scores, "latency_ms": res["latency_ms"],
                    "hits": slim(res["hits"])}

        neg_rows.append({"id": it["id"], "kind": it["kind"],
                         "expected": NEG_EXPECTED,
                         "lexical": arm_row(lr), "dense_sec": arm_row(sr),
                         "dense_fact": arm_row(fr)})
        print(f"{it['id']:10s} s1 sec="
              f"{sr['hits'][0]['score'] if sr['hits'] else 0:.3f} fact="
              f"{fr['hits'][0]['score'] if fr['hits'] else 0:.3f}")

    pos_inputs = [
        {"id": r["id"], "expected": POS_EXPECTED,
         "dense_sec": {"scores": r["dense_sec"]["scores"],
                       "recall": r["dense_sec"]["retrieval"]["recall_at3"]},
         "dense_fact": {"scores": r["dense_fact"]["scores"],
                        "recall": r["dense_fact"]["retrieval"]["recall_at3"]}}
        for r in pos_rows]
    neg_inputs = [
        {"id": r["id"], "expected": NEG_EXPECTED,
         "dense_sec": {"scores": r["dense_sec"]["scores"], "recall": None},
         "dense_fact": {"scores": r["dense_fact"]["scores"], "recall": None}}
        for r in neg_rows]
    all_inputs = pos_inputs + neg_inputs

    def grid_on(arm: str) -> list[dict]:
        out = []
        for tau in policy["grid"]["taus"]:
            for delta in policy["grid"]["deltas"]:
                oks_len, oks_str, oks_pos, oks_neg = [], [], [], []
                for inp in all_inputs:
                    verdict, _ = decide(inp[arm]["scores"],
                                        tau=tau, delta=delta)
                    rec = inp[arm]["recall"]
                    ok_l = decision_correct(
                        inp["expected"], verdict,
                        retrieval_ok_lenient(rec))
                    ok_s = decision_correct(
                        inp["expected"], verdict,
                        retrieval_ok_strict(rec))
                    oks_len.append(1.0 if ok_l else 0.0)
                    oks_str.append(1.0 if ok_s else 0.0)
                    target = oks_pos if inp["expected"] == POS_EXPECTED else oks_neg
                    target.append(1.0 if ok_l else 0.0)
                out.append({"tau": tau, "delta": delta,
                            "n": len(all_inputs),
                            "decision_lenient": mean(oks_len),
                            "decision_lenient_pos": mean(oks_pos),
                            "decision_lenient_neg": mean(oks_neg),
                            "decision_strict": mean(oks_str)})
        return out

    grid_fact = grid_on("dense_fact")
    grid_sec = grid_on("dense_sec")
    best = max(grid_fact,
               key=lambda c: (c["decision_lenient"], c["tau"], c["delta"]))
    same_on_sec = next(
        c for c in grid_sec
        if c["tau"] == best["tau"] and c["delta"] == best["delta"])

    from importlib.metadata import version as _pkg_version

    def _ver(dist: str) -> str:
        try:
            return _pkg_version(dist)
        except Exception:
            return "?"

    report = {
        "issue": "CookiGram/cookigram#510",
        "phase": "dev-policy-calibration",
        "authorization": "POLICY CALIBRATION DEV uniquement",
        "inputs": {
            "positives": {"file": "510_calibration.json (lignes gelees, "
                                  "sans re-mesure)",
                          "n": 13, "expected": POS_EXPECTED,
                          "file_sha16": file_sha(HERE / "510_calibration.json")},
            "negatives": {"file": "dev_negatives.json (mesure unique)",
                          "n": 8, "expected": NEG_EXPECTED,
                          "file_sha16": file_sha(HERE / "dev_negatives.json")},
            "preregistration_sha16": file_sha(
                HERE / "policy_preregistration.json"),
            "corpora_verified_equal": observed,
            "retrieval_params": "identiques au gele (top_k=3, filtre "
                                "project=cookigram, seuil 0.0, modele et "
                                "collections #510)",
        },
        "grid": {"taus": policy["grid"]["taus"],
                 "deltas": policy["grid"]["deltas"], "n_configs": 28},
        "grid_fact": grid_fact,
        "grid_sec": grid_sec,
        "chosen": {"tau": best["tau"], "delta": best["delta"],
                   "decision_lenient": best["decision_lenient"],
                   "decision_lenient_pos": best["decision_lenient_pos"],
                   "decision_lenient_neg": best["decision_lenient_neg"],
                   "decision_strict": best["decision_strict"],
                   "sec_same_point": same_on_sec,
                   "rule": "max decision_lenient sur dense_fact ; egalite "
                           "-> tau superieur puis delta superieur "
                           "(preference abstention). Ordre total."},
        "negatives": neg_rows,
        "versions": {"qdrant_server": server_version,
                     "qdrant_client": _ver("qdrant-client"),
                     "fastembed": _ver("fastembed")},
        "index": {"sec": idx_sec, "fact": idx_fact},
    }
    (HERE / "510_policy_calibration.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"CHOISI (regle pre-enregistree) : tau={best['tau']} "
          f"delta={best['delta']} lenient={best['decision_lenient']} "
          f"(pos={best['decision_lenient_pos']} "
          f"neg={best['decision_lenient_neg']})")
    return report


if __name__ == "__main__":
    main()
