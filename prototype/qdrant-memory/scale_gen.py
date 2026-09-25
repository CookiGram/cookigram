"""Generateur synthetique determine (seed=508) pour le test d'echelle.

Chunks markdown ~800 chars, vocabulaire tire du corpus reel (distribution
approximative), titres/paths synthetiques. Meme generateur -> memes donnees.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

from corpus_manifest import build_corpus  # noqa: E402
from store import tokenize  # noqa: E402

SEED = 508


def vocab(top: int = 3000) -> list[str]:
    freq: dict[str, int] = {}
    for d in build_corpus(ROOT):
        for tok in tokenize(d["text"]):
            freq[tok] = freq.get(tok, 0) + 1
    return sorted(freq, key=freq.get, reverse=True)[:top]


def gen_chunks(n: int, seed: int = SEED) -> list[dict]:
    rng = random.Random(seed)
    words = vocab()
    sections = ["contrat", "cycle de vie", "exigences", "exemples",
                "annexe", "verdict", "protocole", "limites"]
    out = []
    for i in range(n):
        sec = sections[i % len(sections)]
        body = " ".join(rng.choice(words) for _ in range(rng.randint(90, 130)))
        text = f"# doc-synth-{i:06d}\n## {sec}\n{body}"
        out.append({"id": f"synth/doc-{i:06d}::{sec}",
                    "text": text,
                    "payload": {"project": "synth", "work_id": None,
                                "kind": "synth", "path": f"synth/doc-{i:06d}.md",
                                "section": sec, "updated_at": "gen",
                                "sha": f"s{i}"}})
    return out
