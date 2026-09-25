"""Adaptateur Qdrant reel (gate experimental #508) — hors produit.

Realise le QDRANT_MAP de store.py : meme collection, meme schema payload,
memes filtres must, meme forme de retour. Requiert le venv experimental
(/home/pierrecsn/.cache/qdrant-508-exp/venv) : qdrant-client + fastembed.
Serveur : Qdrant local 127.0.0.1:6333, data jetable. Aucun Cloud.
"""

from __future__ import annotations

import time
import uuid

MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION = "agent_memory"
URL = "http://127.0.0.1:6333"

try:
    from fastembed import TextEmbedding
    from qdrant_client import QdrantClient
    from qdrant_client.models import (Distance, FieldCondition, Filter,
                                      MatchAny, MatchValue, PayloadSchemaType,
                                      PointStruct, VectorParams)
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Deps experimentales manquantes : utiliser le venv qdrant-508-exp "
        "(qdrant-client + fastembed). Rien a ajouter au produit.") from exc


class DenseQdrant:
    def __init__(self, url: str = URL, model: str = MODEL) -> None:
        self.client = QdrantClient(url=url, timeout=60)
        self.embedder = TextEmbedding(model)
        self.dim = 384

    def version(self) -> str:
        import json
        import urllib.request
        with urllib.request.urlopen(URL + "/", timeout=10) as r:
            return json.load(r).get("version", "?")

    def ensure_collection(self) -> None:
        if not self.client.collection_exists(COLLECTION):
            self.client.create_collection(
                COLLECTION,
                vectors_config=VectorParams(size=self.dim, distance=Distance.COSINE))
            for key in ("project", "work_id", "kind"):
                self.client.create_payload_index(
                    COLLECTION, field_name=key, field_schema=PayloadSchemaType.KEYWORD)

    def drop(self) -> None:
        self.client.delete_collection(COLLECTION)

    def _vec(self, text: str) -> list[float]:
        return list(self.embedder.embed([text]))[0].tolist()

    def upsert(self, pid: str, text: str, payload: dict) -> None:
        full = dict(payload)
        full["_text"] = text  # payload = ce qui serait injecte (cout honnete)
        self.client.upsert(COLLECTION, [PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, pid)),
            vector=self._vec(text), payload=full)])

    @staticmethod
    def _filter(filters: dict | None) -> Filter | None:
        if not filters:
            return None
        must = []
        for key, want in filters.items():
            if isinstance(want, (list, tuple, set)):
                must.append(FieldCondition(key=key, match=MatchAny(any=list(want))))
            else:
                must.append(FieldCondition(key=key, match=MatchValue(value=want)))
        return Filter(must=must)

    def search(self, query: str, top_k: int = 3, filters: dict | None = None,
               score_threshold: float = 0.0) -> dict:
        t0 = time.perf_counter()
        res = self.client.query_points(
            COLLECTION, query=self._vec(query), limit=top_k,
            query_filter=self._filter(filters),
            score_threshold=score_threshold or None).points
        hits = [{"id": str(p.id), "score": round(p.score, 4),
                 "text": (p.payload or {}).get("_text", ""),
                 "citation": {k: (p.payload or {}).get(k)
                              for k in ("path", "section", "kind", "work_id")}}
                for p in res]
        return {"hits": hits,
                "latency_ms": round((time.perf_counter() - t0) * 1000, 2)}

    def search_mmr(self, query: str, top_k: int = 3, fetch_k: int = 20,
                   lambda_: float = 0.5, filters: dict | None = None) -> dict:
        """Dense + diversification MMR locale (fetch_k -> top_k)."""
        from mmr import mmr_select
        t0 = time.perf_counter()
        res = self.client.query_points(
            COLLECTION, query=self._vec(query), limit=fetch_k,
            query_filter=self._filter(filters), with_vectors=True).points
        cands = [{"id": str(p.id), "score": p.score, "vector": list(p.vector),
                  "text": (p.payload or {}).get("_text", ""),
                  "citation": {k: (p.payload or {}).get(k)
                               for k in ("path", "section", "kind", "work_id")}}
                 for p in res if p.vector is not None]
        hits = mmr_select(self._vec(query), cands, top_k, lambda_)
        for h in hits:
            h["score"] = round(h["score"], 4)
            del h["vector"]
        return {"hits": hits, "fetch_k": fetch_k, "lambda": lambda_,
                "latency_ms": round((time.perf_counter() - t0) * 1000, 2)}

    def info(self) -> dict:
        c = self.client.get_collection(COLLECTION)
        return {"points": c.points_count,
                "indexed_vectors": getattr(c, "indexed_vectors_count", None),
                "status": str(c.status)}


def index_corpus(dq: "DenseQdrant", corpus: list[dict],
                 batch: int = 64) -> dict:
    """(Re)indexation derivee complete du corpus canonique. Jetable."""
    from qdrant_client.models import PointStruct
    dq.drop() if dq.client.collection_exists(COLLECTION) else None
    dq.ensure_collection()
    t0 = time.perf_counter()
    vecs = list(dq.embedder.embed([d["text"] for d in corpus]))
    embed_ms = round((time.perf_counter() - t0) * 1000, 1)
    t0 = time.perf_counter()
    for i in range(0, len(corpus), batch):
        pts = [PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, d["id"])),
            vector=v.tolist(), payload={**d["payload"], "_text": d["text"]})
            for d, v in zip(corpus[i:i + batch], vecs[i:i + batch])]
        dq.client.upsert(COLLECTION, pts)
    return {"embed_ms": embed_ms,
            "upsert_ms": round((time.perf_counter() - t0) * 1000, 1)}
