"""Surface Qdrant-compatible minimale (stdlib uniquement).

But : prototyper le contrat d'index/retrieval SANS serveur Qdrant et SANS
nouvelle dependance. Le jour du passage au vrai Qdrant, remplacer
`embed()` par un modele dense et `Collection` par `qdrant-client`
en gardant : nom de collection, schema payload, filtres `must`,
top-k + seuil, citations. Voir QDRANT_MAP.

QDRANT_MAP (passage au reel, 1:1) :
  Collection("agent_memory", dim)  ->  qdrant_client.create_collection(
                                         "agent_memory",
                                         vectors_config=VectorParams(size=<dense_dim>,
                                                                     distance=Distance.COSINE),
                                         hnsw_config=HnswConfigDiff())
  upsert(id, text, payload)        ->  client.upsert("agent_memory",
                                                     [PointStruct(id=..., vector=embed_dense(text),
                                                                  payload={project, work_id, kind,
                                                                           path, section,
                                                                           updated_at, sha})])
  Filtres {"k": v} / {"k": [..]}   ->  Filter(must=[FieldCondition(key=k,
                                                     match=MatchValue/Any(...))])
  Filtre {"k": None} (nul/absent) ->  Filter(must=[IsNullCondition(...)])
                                                     (jamais ignore ; None
                                                     dans une liste = erreur)
  search(query, top_k, filters,     ->  client.search(..., search_params=...,
        min_score)                           score_threshold=min_score)
  + payload indexes Qdrant sur project / work_id / kind.
"""

from __future__ import annotations

import hashlib
import math
import re
import time

DIM = 512
_TOKEN_RE = re.compile(r"[a-z\u00e0\u00e2\u00e4\u00e9\u00e8\u00ea\u00eb\u00ee\u00ef\u00f4\u00f6\u00f9\u00fb\u00fc\u00e70-9]+", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def estimate_tokens(text: str) -> int:
    """Heuristique ~4 chars/token (ordre de grandeur, pas une mesure modele)."""
    return max(1, len(text) // 4)


def embed(text: str, dim: int = DIM) -> list[float]:
    """Embedding TF-IDF hashe deterministe (substitut local, pas semantique dense)."""
    vec = [0.0] * dim
    for tok in tokenize(text):
        h = int.from_bytes(hashlib.sha256(tok.encode()).digest()[:4], "big") % dim
        vec[h] += 1.0
    vec = [math.log1p(v) for v in vec]
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class Collection:
    """Collection in-memory : upsert/search avec filtres must + seuil + citations."""

    def __init__(self, name: str, dim: int = DIM) -> None:
        self.name = name
        self.dim = dim
        self._points: dict[str, dict] = {}

    def upsert(self, pid: str, text: str, payload: dict) -> None:
        self._points[pid] = {"vector": embed(text, self.dim), "text": text,
                             "payload": dict(payload)}

    def drop(self) -> None:
        """Reversibilite : l'index se jette, le canonique reste inchange."""
        self._points.clear()

    def __len__(self) -> int:
        return len(self._points)

    @staticmethod
    def _match(payload: dict, filters: dict | None) -> bool:
        # Parite dense (F3) : None seul = nul/absent ; None en liste = erreur.
        if not filters:
            return True
        for key, want in filters.items():
            got = payload.get(key)
            if isinstance(want, (list, tuple, set)):
                if any(v is None for v in want):
                    raise ValueError(f"filtre {key!r} : None interdit dans une liste")
                if got not in want:
                    return False
            elif got != want:
                return False
        return True

    def search(self, query: str, top_k: int = 3, filters: dict | None = None,
               min_score: float = 0.0) -> dict:
        t0 = time.perf_counter()
        q = embed(query, self.dim)
        scored = [(cosine(q, p["vector"]), pid, p)
                  for pid, p in self._points.items()
                  if self._match(p["payload"], filters)]
        scored.sort(key=lambda r: r[0], reverse=True)
        hits = [{"id": pid, "score": round(s, 4), "text": p["text"],
                 "citation": {k: p["payload"].get(k)
                              for k in ("path", "section", "kind", "work_id")}}
                for s, pid, p in scored if s > min_score][:top_k]
        return {"hits": hits,
                "latency_ms": round((time.perf_counter() - t0) * 1000, 2)}
