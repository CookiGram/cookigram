"""Banc d'echelle synthetique (gate 3) : 1k / 10k / 100k chunks.

- 1k, 10k : embeddings reels (fastembed, mesure du debit).
- 100k : vecteurs unitaires aleatoires seedes (PROXY serveurs uniquement :
  upsert/disque/RSS/latence ; cout d'embedding projete depuis le debit mesure).
- Re-index = drop + recreate + re-upsert (vects regeneres a seed identique).
- Latence : 5 requetes reelles x 10 runs -> p50/p95 par echelle.
- Collections scale_* supprimees en fin de run (jetable).
Ecrit scale_results.json.
"""

from __future__ import annotations

import json
import math
import os
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from dense_qdrant import MODEL  # noqa: E402
from fastembed import TextEmbedding  # noqa: E402
from qdrant_client import QdrantClient  # noqa: E402
from qdrant_client.models import (Distance, PointStruct, VectorParams)  # noqa: E402
from scale_gen import SEED, gen_chunks  # noqa: E402

URL = "http://127.0.0.1:6333"
DIM = 384
DATA_DIR = Path(os.environ.get("QDRANT_DATA_DIR",
                               "/home/pierrecsn/.cache/qdrant-508-exp/data"))
QUERIES = ["nom workspace agent", "artefacts CI conserves",
           "contrat catalogue Core", "appareils et reglages",
           "illustrations et provenance"]


def rss_mb() -> float | None:
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


def du(p: Path) -> int:
    try:
        return int(subprocess.check_output(
            ["du", "-s", str(p)], text=True).split()[0]) * 1024
    except Exception:
        return -1


def rand_unit(rng: random.Random) -> list[float]:
    v = [rng.gauss(0, 1) for _ in range(DIM)]
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def main() -> dict:
    client = QdrantClient(url=URL, timeout=120)
    model = TextEmbedding(MODEL)
    qvecs = [list(model.embed([q]))[0].tolist() for q in QUERIES]
    out: dict = {"model": MODEL, "dim": DIM, "scales": {}}
    embed_rate = None

    for n in (1_000, 10_000, 100_000):
        name = f"scale_{n // 1000}k"
        real = n <= 10_000
        chunks = gen_chunks(n)
        if client.collection_exists(name):
            client.delete_collection(name)
        client.create_collection(
            name, vectors_config=VectorParams(size=DIM, distance=Distance.COSINE))

        t0 = time.perf_counter()
        if real:
            vecs = list(model.embed([c["text"] for c in chunks]))
            embed_ms = round((time.perf_counter() - t0) * 1000, 1)
            embed_rate = round(n / ((time.perf_counter() - t0) or 1), 1)
            vecs = [v.tolist() for v in vecs]
        else:
            rng = random.Random(SEED)
            vecs = [rand_unit(rng) for _ in range(n)]
            embed_ms = None
        t1 = time.perf_counter()
        for i in range(0, n, 512):
            pts = [PointStruct(id=i + j,
                               vector=vecs[i + j],
                               payload={"project": "synth", "seq": i + j})
                   for j in range(min(512, n - i))]
            client.upsert(name, pts)
        upsert_ms = round((time.perf_counter() - t1) * 1000, 1)
        time.sleep(2)

        # latences p50/p95 : 5 requetes x 10 runs
        lat: list[float] = []
        for qv in qvecs:
            for _ in range(10):
                t = time.perf_counter()
                client.query_points(name, query=qv, limit=3)
                lat.append((time.perf_counter() - t) * 1000)
        lat.sort()
        p50 = round(lat[len(lat) // 2], 2)
        p95 = round(lat[int(len(lat) * 0.95) - 1], 2)

        # re-index : drop + recreate + re-upsert (regen deterministe)
        t0 = time.perf_counter()
        client.delete_collection(name)
        client.create_collection(
            name, vectors_config=VectorParams(size=DIM, distance=Distance.COSINE))
        if real:
            vecs2 = [v.tolist() for v in model.embed([c["text"] for c in chunks])]
        else:
            rng = random.Random(SEED)
            vecs2 = [rand_unit(rng) for _ in range(n)]
        for i in range(0, n, 512):
            pts = [PointStruct(id=i + j, vector=vecs2[i + j],
                               payload={"project": "synth", "seq": i + j})
                   for j in range(min(512, n - i))]
            client.upsert(name, pts)
        reindex_ms = round((time.perf_counter() - t0) * 1000, 1)
        time.sleep(2)

        disk = du(DATA_DIR / "collections" / name)
        out["scales"][name] = {
            "n": n, "vectors": "real-embed" if real else "RANDOM-PROXY",
            "embed_ms": embed_ms, "upsert_ms": upsert_ms,
            "reindex_ms": reindex_ms, "disk_bytes": disk,
            "rss_mb": rss_mb(), "latency_ms_p50": p50, "latency_ms_p95": p95}
        print(f"{name}: vectors={out['scales'][name]['vectors']} "
              f"embed={embed_ms}ms upsert={upsert_ms}ms reindex={reindex_ms}ms "
              f"disk={disk}B rss={out['scales'][name]['rss_mb']}MB p50={p50} p95={p95}",
              flush=True)
        client.delete_collection(name)  # jetable : mesure gardee, index jete

    out["embed_chunks_per_s"] = embed_rate
    out["note"] = ("100k = proxy vecteurs aleatoires (serveur seul) ; "
                   "cout embedding 100k projete depuis le debit mesure ; "
                   "payload synth minimal (pas de _text).")
    (HERE / "scale_results.json").write_text(json.dumps(out, indent=2))
    print("embed_rate:", embed_rate, "chunks/s")
    return out


if __name__ == "__main__":
    main()
