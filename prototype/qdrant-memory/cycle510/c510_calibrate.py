"""Calibration retrieval DEV ONLY cycle 510 (GO_CALIBRATION_DEV_510).

Mesure UNIQUE, bornee aux 13 items de dev_set.json. Aucune politique :
ni tau, ni delta, ni abstention, ni grille, ni seuil, ni decision.
Methode retrieval reprise de cycle2b/c2b_calibrate.py (methode #508
seule) : bras lexical (store.Collection, TF-IDF hache deterministe)
sur chunks sections + bras dense-sec / dense-fact (Qdrant reel,
fastembed paraphrase-multilingual-MiniLM-L12-v2, dim 384, COSINE),
top_k=3, filtre project=cookigram. Application mecanique au freeze
#510 : corpus = les 4 documents admissibles, gold = localisateur de
section <path>::<titre ##> (identite d'ancre du freeze), succes =
section gold dans le top-3 ET preuve evidence dans le contexte.

Refuse de tourner si : cycle510/holdout.json existe ; dev_set.json
n'est pas exactement les 13 items dev-only ; une ancre tombe sur
une section exclue ; les 4 docs ont derive du base_commit fige.
Ne lit aucun gold/question/reponse/preuve/label/cle du holdout
(aucun n'existe) et aucun gold #508. Ecrit 510_calibration.json.
Aucun retuning, aucune seconde mesure pour ameliorer le resultat.
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
from retrieval_metrics import mean, retrieval_scores  # noqa: E402
from store import Collection  # noqa: E402

COL_SEC = "agent_memory_510"
COL_FACT = "agent_memory_fact_510"
TOP_K = 3
FILTERS = {"project": "cookigram"}
EXPECTED_DEV_N = 13


def corpus_sha(corpus: list[dict]) -> str:
    h = hashlib.sha256()
    for d in sorted(corpus, key=lambda d: d["id"]):
        h.update((d["id"] + "\x00" + d["text"]).encode())
    return h.hexdigest()[:16]


def locator(path: str, section: str) -> str:
    return f"{path}::{section}"


def main() -> dict:
    if (HERE / "holdout.json").exists():
        raise SystemExit("REFUS : cycle510/holdout.json existe — "
                         "calibration post-holdout interdite.")
    plan = json.loads(
        (HERE / "split_preregistration.json").read_text(encoding="utf-8"))
    if plan.get("holdout_created"):
        raise SystemExit("REFUS : holdout_created est vrai.")
    spec = json.loads((HERE / "dev_set.json").read_text(encoding="utf-8"))
    if spec.get("phase") != "dev-only":
        raise SystemExit("REFUS : dev_set.json n'est pas dev-only.")
    items = spec["items"]
    if len(items) != EXPECTED_DEV_N:
        raise SystemExit(f"REFUS : {len(items)} items dev, "
                         f"{EXPECTED_DEV_N} attendus.")
    excluded = set(plan["excluded_sections"])
    for it in items:
        anchor_id = it["anchor"]["anchor_id"]
        if anchor_id in excluded:
            raise SystemExit(f"REFUS : {it['id']} sur section exclue "
                             f"{anchor_id}.")
    base = plan["base_commit"]
    docs = ([d["path"] for d in plan["documents"]["dev"]]
            + [d["path"] for d in plan["documents"]["holdout_reserve"]])
    drift = subprocess.run(
        ["git", "diff", "--quiet", base, "--", *docs],
        cwd=ROOT, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    if drift.returncode != 0:
        raise SystemExit(f"REFUS : corpus derive de {base[:7]}.")

    sec_corpus = build_corpus_510(ROOT)
    fact_corpus = build_fact_corpus_510(ROOT)
    sec_sha, fact_sha = corpus_sha(sec_corpus), corpus_sha(fact_corpus)
    # Pas de pin pre-enregistre dans le freeze #510 : (n, sha)
    # observes consommes tels quels dans le rapport, sans assert.

    lex = Collection(COL_SEC)
    for d in sec_corpus:
        lex.upsert(d["id"], d["text"], d["payload"])
    dq_sec = DenseQdrant(collection=COL_SEC)
    idx_sec = index_corpus(dq_sec, sec_corpus)
    dq_fact = DenseQdrant(collection=COL_FACT)
    idx_fact = index_corpus(dq_fact, fact_corpus)
    time.sleep(1)
    n_sec = dq_sec.info()["points"]
    n_fact = dq_fact.info()["points"]
    if n_sec != len(sec_corpus) or n_fact != len(fact_corpus):
        raise SystemExit(f"REFUS : index incomplet sec={n_sec} "
                         f"fact={n_fact}.")
    server_version = dq_sec.version()

    rows = []
    for it in items:
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

        def dense_row(res):
            scores = [h["score"] for h in res["hits"]]
            margin = (round(scores[0] - scores[1], 4)
                      if len(scores) > 1 else 1.0)
            return {"success": succ(res["hits"]),
                    "retrieval": retr(res["hits"]),
                    "scores": scores, "margin": margin,
                    "latency_ms": res["latency_ms"],
                    "hits": slim(res["hits"])}

        row = {
            "id": it["id"], "anchor_id": it["anchor"]["anchor_id"],
            "lexical": {"success": succ(lr["hits"]),
                        "retrieval": retr(lr["hits"]),
                        "latency_ms": lr["latency_ms"],
                        "hits": slim(lr["hits"])},
            "dense_sec": dense_row(sr),
            "dense_fact": dense_row(fr),
        }
        rows.append(row)
        print(f"{it['id']:10s} lex={row['lexical']['success']} "
              f"sec={row['dense_sec']['success']} "
              f"fact={row['dense_fact']['success']}")

    import fastembed
    from importlib.metadata import version as _pkg_version

    def _ver(dist: str) -> str:
        try:
            return _pkg_version(dist)
        except Exception:
            return "?"
    report = {
        "issue": "CookiGram/cookigram#510",
        "phase": "dev-calibration-retrieval-only",
        "authorization": "GO_CALIBRATION_DEV_510",
        "policy": "AUCUNE : ni tau, ni delta, ni abstention, ni grille, "
                  "ni decision. Metriques retrieval seules.",
        "params": {
            "top_k": TOP_K, "filters": FILTERS,
            "lexical": "store.Collection TF-IDF hache deterministe "
                       "(DIM 512), sur chunks sections",
            "dense_model": "sentence-transformers/"
                           "paraphrase-multilingual-MiniLM-L12-v2",
            "dense_dim": 384, "dense_distance": "COSINE",
            "score_threshold": 0.0,
            "collections": {"sec": COL_SEC, "fact": COL_FACT},
            "chunking": "corpus_manifest.chunk_markdown (##, CHUNK_MAX "
                        "1500) + chunk_facts.split_facts (FACT_MAX 400), "
                        "texte construit '# {nom}\\n## {section}\\n{corps}'",
            "gold_mapping": "localisateur de section "
                            "<path>::<titre ##> ; succes = section gold "
                            "dans top-3 ET evidence dans le contexte",
            "corpus_docs": docs,
            "base_commit": base,
            "versions": {"qdrant_server": server_version,
                         "qdrant_client": _ver("qdrant-client"),
                         "fastembed": _ver("fastembed")},
        },
        "corpora": {"section_chunks": len(sec_corpus),
                    "section_sha": sec_sha,
                    "fact_chunks": len(fact_corpus),
                    "fact_sha": fact_sha,
                    "index_sec": idx_sec, "index_fact": idx_fact},
        "retrieval_dev": {
            arm: {"success_answer_rate": mean(
                      [1.0 if r[arm]["success"] else 0.0 for r in rows]),
                  "rank1": mean([r[arm]["retrieval"]["rank1"]
                                 for r in rows]),
                  "recall_at3": mean([r[arm]["retrieval"]["recall_at3"]
                                      for r in rows])}
            for arm in ("lexical", "dense_sec", "dense_fact")},
        "items": rows,
    }
    (HERE / "510_calibration.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"n=13 summary={json.dumps(report['retrieval_dev'])}")
    return report


if __name__ == "__main__":
    main()
