"""Benchmark avant/apres : contexte plein vs retrieval top-k (3 taches representatives).

AVANT  = injection plein contexte (tous les chunks du corpus) — pratique agent actuelle.
APRES  = retrieval top-3 + filtres project — prototype Qdrant.
Mesures : tokens injectes (heuristique ~4 chars/token), rappel des docs gold,
latence search, taille index (proxy consommation). Ecrit benchmark_results.json.
"""

from __future__ import annotations

import json
import pickle
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent  # racine repo (worktree)
sys.path.insert(0, str(HERE))

from corpus_manifest import build_corpus  # noqa: E402
from store import Collection, estimate_tokens  # noqa: E402

TASKS = [
    {"id": "T1-herdr-naming",
     "query": "Comment nommer un workspace Herdr depuis le travail durable assigne ?",
     "gold": ["docs/HERDR-WORKSPACE-NAMING.md"]},
    {"id": "T2-artifact-storage",
     "query": "Que conserve la CI comme artefacts _site sur main et apres Pages ?",
     "gold": ["docs/CI-ARTIFACT-STORAGE.md"]},
    {"id": "T3-catalogue-contract",
     "query": "Quelle est la frontiere de contrat catalogue entre Core et instance ?",
     "gold": ["docs/CATALOGUE-CONTRACT-CORE.md"]},
]

TOP_K = 3


def main() -> dict:
    corpus = build_corpus(ROOT)
    col = Collection("agent_memory")
    t_index = time.perf_counter()
    for d in corpus:
        col.upsert(d["id"], d["text"], d["payload"])
    index_ms = round((time.perf_counter() - t_index) * 1000, 1)

    full_text = "\n\n".join(d["text"] for d in corpus)
    before_tokens = estimate_tokens(full_text)
    index_bytes = len(pickle.dumps(col._points))

    tasks_out = []
    for t in TASKS:
        res = col.search(t["query"], top_k=TOP_K, filters={"project": "cookigram"})
        after_tokens = estimate_tokens(t["query"]) + sum(
            estimate_tokens(h["text"]) for h in res["hits"])
        got = {h["citation"]["path"] for h in res["hits"]}
        recall = round(sum(1 for g in t["gold"] if g in got) / len(t["gold"]), 2)
        tasks_out.append({
            "id": t["id"], "gold": t["gold"], "retrieved": sorted(got),
            "recall_gold": recall, "latency_ms": res["latency_ms"],
            "tokens_before": before_tokens, "tokens_after": after_tokens,
            "token_ratio": round(after_tokens / before_tokens, 4),
        })

    report = {
        "corpus_chunks": len(corpus), "index_ms": index_ms,
        "tokens_before_full_context": before_tokens,
        "index_bytes_proxy": index_bytes,
        "note_tokens": "heuristique len/4 ; latences search in-memory (borne basse vs Qdrant reseau)",
        "tasks": tasks_out,
    }
    (HERE / "benchmark_results.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    for t in tasks_out:
        print(f"{t['id']}: recall={t['recall_gold']} "
              f"tokens {t['tokens_before']} -> {t['tokens_after']} "
              f"(x{t['token_ratio']}) latency={t['latency_ms']}ms")
    print(f"corpus={len(corpus)} chunks, index={index_ms}ms, index_bytes={index_bytes}")
    return report


if __name__ == "__main__":
    main()
