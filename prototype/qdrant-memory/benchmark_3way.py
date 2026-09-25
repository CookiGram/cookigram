"""Benchmark 3 voies (gate #508) : contexte plein vs lexical vs dense Qdrant reel.

Taches : 3 originales (conservees), 3 paraphrases (recouvrement reduit),
2 difficiles (multi-golds), 2 negatives (abstention attendue).
Seuil : scores bruts captures a 0.0, abstention recalculee a
tau = {0.30, 0.40, 0.50} pour documenter les echecs honnetement.
Requiert le venv experimental (dense_qdrant). Ecrit benchmark_3way_results.json.
"""

from __future__ import annotations

import json
import os
import pickle
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

from corpus_manifest import build_corpus  # noqa: E402
from dense_qdrant import COLLECTION, DenseQdrant  # noqa: E402
from store import Collection, estimate_tokens  # noqa: E402

TOP_K = 3
TAUS = (0.30, 0.40, 0.50)

TASKS = [
    {"id": "T1-orig", "kind": "original",
     "query": "Comment nommer un workspace Herdr depuis le travail durable assigne ?",
     "golds": ["docs/HERDR-WORKSPACE-NAMING.md"]},
    {"id": "T2-orig", "kind": "original",
     "query": "Que conserve la CI comme artefacts _site sur main et apres Pages ?",
     "golds": ["docs/CI-ARTIFACT-STORAGE.md"]},
    {"id": "T3-orig", "kind": "original",
     "query": "Quelle est la frontiere de contrat catalogue entre Core et instance ?",
     "golds": ["docs/CATALOGUE-CONTRACT-CORE.md"]},
    {"id": "P1-para", "kind": "paraphrase",
     "query": "Comment un operateur comprend-il l'activite de chaque agent sans ouvrir son panneau ?",
     "golds": ["docs/HERDR-WORKSPACE-NAMING.md"]},
    {"id": "P2-para", "kind": "paraphrase",
     "query": "Apres publication du site, quels fichiers de construction sont gardes ou supprimes ?",
     "golds": ["docs/CI-ARTIFACT-STORAGE.md"]},
    {"id": "P3-para", "kind": "paraphrase",
     "query": "Ou s'arrete le moteur partage et ou commence la personnalisation d'un deploiement ?",
     "golds": ["docs/CATALOGUE-CONTRACT-CORE.md"]},
    {"id": "H1-hard", "kind": "hard",
     "query": "Comment sont decrites les images et illustrations, et qui en garde la trace ?",
     "golds": ["docs/IMAGE-PROVENANCE.md", "docs/ATOMIC_ACTION_ILLUSTRATIONS.md",
               "docs/INSTANCE-IDENTITY.md"]},
    {"id": "H2-hard", "kind": "hard",
     "query": "Quelles regles encadrent les appareils, leurs reglages et leur ajout au catalogue ?",
     "golds": ["docs/equipment-contract-495.md", "docs/equipment-audit-495.md",
               "docs/equipment-add-appliance.md"]},
    {"id": "N1-neg", "kind": "negative",
     "query": "Quel est le tarif de l'offre Qdrant Cloud ?",
     "golds": []},
    {"id": "N2-neg", "kind": "negative",
     "query": "Comment brancher Qdrant dans le service cookigram-mcp ?",
     "golds": []},
]


def qdrant_rss_mb() -> float | None:
    try:
        pid = subprocess.check_output(
            ["pgrep", "-f", "qdrant-508-exp/bin/qdrant"], text=True).split()[0]
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return round(int(line.split()[1]) / 1024, 1)
    except Exception:
        return None
    return None


def dir_bytes(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def du_bytes(path: Path) -> int:
    """Occupation disque reelle (blocs du) — `du -b` mentirait (apparent/sparse)."""
    try:
        out = subprocess.check_output(["du", "-s", str(path)], text=True)
        return int(out.split()[0]) * 1024
    except Exception:
        return -1


def run() -> dict:
    corpus = build_corpus(ROOT)
    full_tokens = estimate_tokens("\n\n".join(d["text"] for d in corpus))

    # --- lexical (contrat existant) ---
    lex = Collection("agent_memory")
    t0 = time.perf_counter()
    for d in corpus:
        lex.upsert(d["id"], d["text"], d["payload"])
    lex_index_ms = round((time.perf_counter() - t0) * 1000, 1)
    lex_bytes = len(pickle.dumps(lex._points))

    # --- dense Qdrant reel ---
    dq = DenseQdrant()
    qdrant_version = dq.version()
    dq.drop() if dq.client.collection_exists(COLLECTION) else None
    dq.ensure_collection()
    texts = [d["text"] for d in corpus]
    t0 = time.perf_counter()
    vecs = list(dq.embedder.embed(texts))
    embed_ms = round((time.perf_counter() - t0) * 1000, 1)
    from qdrant_client.models import PointStruct
    import uuid as uuid_mod
    pts = [PointStruct(id=str(uuid_mod.uuid5(uuid_mod.NAMESPACE_URL, d["id"])),
                       vector=v.tolist(),
                       payload={**d["payload"], "_text": d["text"]})
           for d, v in zip(corpus, vecs)]
    t0 = time.perf_counter()
    for i in range(0, len(pts), 64):
        dq.client.upsert(COLLECTION, pts[i:i + 64])
    dense_index_ms = round((time.perf_counter() - t0) * 1000, 1)
    time.sleep(1)
    dense_info = dq.info()
    data_dir = Path(os.environ.get("QDRANT_DATA_DIR",
                                   "/home/pierrecsn/.cache/qdrant-508-exp/data"))
    coll_dir = data_dir / "collections" / COLLECTION
    dense_disk_bytes = dir_bytes(coll_dir) \
        if coll_dir.exists() else dir_bytes(data_dir)
    dense_rss = qdrant_rss_mb()

    # --- requetes ---
    rows = []
    for t in TASKS:
        lr = lex.search(t["query"], top_k=TOP_K, filters={"project": "cookigram"})
        dr = dq.search(t["query"], top_k=TOP_K, filters={"project": "cookigram"},
                       score_threshold=0.0)
        lpaths = [h["citation"]["path"] for h in lr["hits"]]
        dpaths = [h["citation"]["path"] for h in dr["hits"]]
        dscores = [h["score"] for h in dr["hits"]]
        lscores = [h["score"] for h in lr["hits"]]
        row = {
            "id": t["id"], "kind": t["kind"], "query": t["query"], "golds": t["golds"],
            "tokens_full": full_tokens,
            "lex": {"paths": lpaths, "scores": lscores,
                    "recall_at3": round(sum(g in lpaths for g in t["golds"])
                                       / len(t["golds"]), 2) if t["golds"] else None,
                    "tokens": estimate_tokens(t["query"]) + sum(
                        estimate_tokens(h["text"]) for h in lr["hits"]),
                    "latency_ms": lr["latency_ms"]},
            "dense": {"paths": dpaths, "scores": dscores,
                      "recall_at3": round(sum(g in dpaths for g in t["golds"])
                                         / len(t["golds"]), 2) if t["golds"] else None,
                      "tokens": estimate_tokens(t["query"]) + sum(
                          estimate_tokens(h["text"]) for h in dr["hits"]),
                      "latency_ms": dr["latency_ms"],
                      "abstains_at": {str(tau): (not dscores or max(dscores) < tau)
                                      for tau in TAUS}},
        }
        rows.append(row)
        print(f"{t['id']:8s} lex_recall={row['lex']['recall_at3']} "
              f"dense_recall={row['dense']['recall_at3']} "
              f"tok {full_tokens}->{row['lex']['tokens']}/{row['dense']['tokens']} "
              f"lat {row['lex']['latency_ms']}/{row['dense']['latency_ms']}ms "
              f"dscores={dscores} abst@0.4={row['dense']['abstains_at']['0.4']}")

    report = {
        "qdrant_version": qdrant_version, "model": dq.MODEL if hasattr(dq, "MODEL")
        else "paraphrase-multilingual-MiniLM-L12-v2",
        "corpus_chunks": len(corpus), "tokens_full_context": full_tokens,
        "lexical": {"index_ms": lex_index_ms, "index_bytes": lex_bytes},
        "dense": {"embed_all_ms": embed_ms, "index_ms": dense_index_ms,
                  "info": dense_info, "disk_bytes_du": du_bytes(coll_dir),
                  "disk_bytes_apparent": dense_disk_bytes,
                  "rss_mb": dense_rss},
        "note": ("tokens=heuristique len/4 ; latences mesurees, HTTP local vs "
                 "in-memory ; seuils analyses a posteriori (TAUS)"),
        "tasks": rows,
    }
    (HERE / "benchmark_3way_results.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"corpus={len(corpus)} dense_embed={embed_ms}ms dense_index={dense_index_ms}ms "
          f"disk={dense_disk_bytes}B rss={dense_rss}MB qdrant={qdrant_version}")
    return report


if __name__ == "__main__":
    run()
