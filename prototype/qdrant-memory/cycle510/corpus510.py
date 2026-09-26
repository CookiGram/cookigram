"""Corpus ferme cycle 510 (GO_CALIBRATION_DEV_510).

Mecanique reprise a l'identique de cycle2b/corpus2b.py (methode #508
seule, aucun gold #508 lu) : chunk_markdown pour les sections,
split_facts pour les faits, meme schema payload, meme texte
"# {nom}\\n## {section}\\n{corps}", meme particularite (split_facts
recoit le texte construit avec en-tete, comme corpus2b).

Difference pre-enregistree par le freeze #510 : le corpus est limite
aux 4 documents admissibles de split_preregistration.json (dev +
reserve holdout comme distracteurs indexes, jamais golds). Aucune
autre source. Les sections exclues restent indexees comme texte
brut (distracteurs) ; l'exclusion porte sur les slots de golds.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
C1 = HERE.parent

KIND_510 = "doc-510"


def corpus_paths_510() -> list[str]:
    """Les 4 documents admissibles, lus du split pre-enregistre."""
    plan = json.loads(
        (HERE / "split_preregistration.json").read_text(encoding="utf-8"))
    paths = [d["path"] for d in plan["documents"]["dev"]]
    paths += [d["path"] for d in plan["documents"]["holdout_reserve"]]
    assert len(paths) == 4, paths
    assert len(set(paths)) == 4, paths
    return paths


def build_corpus_510(root: Path) -> list[dict]:
    """Chunks sections sur les 4 docs (miroir build_corpus_c2b)."""
    import sys
    sys.path.insert(0, str(C1))
    from corpus_manifest import chunk_markdown
    import corpus_manifest as cm

    docs: list[dict] = []
    for rel_str in corpus_paths_510():
        rel = Path(rel_str)
        full = root / rel
        if not full.is_file():
            raise SystemExit(f"REFUS : document admissible manquant : {rel_str}")
        text = full.read_text(encoding="utf-8")
        for c in chunk_markdown(full, text):
            sha = hashlib.sha256(c["text"].encode()).hexdigest()[:12]
            docs.append({
                "id": f"{rel_str}::{c['section']}"[:200],
                "text": f"# {full.name}\n## {c['section']}\n{c['text']}",
                "payload": {"project": cm.PROJECT, "work_id": c["work_id"],
                            "kind": KIND_510,
                            "path": rel_str,
                            "section": c["section"], "updated_at": "git",
                            "sha": sha},
            })
    seen_ids: dict[str, int] = {}
    for d in docs:
        n = seen_ids.get(d["id"], 0)
        seen_ids[d["id"]] = n + 1
        if n:
            d["id"] = f"{d['id']}#p{n}"
    return docs


def build_fact_corpus_510(root: Path) -> list[dict]:
    """Variante faits (miroir build_fact_corpus_c2b)."""
    import sys
    sys.path.insert(0, str(C1))
    import corpus_manifest as cm
    from chunk_facts import split_facts

    tmp = build_corpus_510(root)
    by_doc: dict[str, list[dict]] = {}
    for d in tmp:
        by_doc.setdefault(d["payload"]["path"], []).append(d)
    out: list[dict] = []
    for path, chunks in by_doc.items():
        for c in chunks:
            for n, fact in enumerate(
                    split_facts(c["payload"]["section"], c["text"])):
                sha = hashlib.sha256(fact.encode()).hexdigest()[:12]
                out.append({
                    "id": f"{path}::{c['payload']['section']}#f{n}"[:200],
                    "text": fact,
                    "payload": {"project": cm.PROJECT,
                                "work_id": c["payload"]["work_id"],
                                "kind": KIND_510, "path": path,
                                "section": c["payload"]["section"],
                                "updated_at": "git", "sha": sha,
                                "chunking": "fact"},
                })
    seen_ids: dict[str, int] = {}
    for d in out:
        k = seen_ids.get(d["id"], 0)
        seen_ids[d["id"]] = k + 1
        if k:
            d["id"] = f"{d['id']}#p{k}"
    return out
