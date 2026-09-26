"""Extension deterministe du corpus pour cycle2b (REDEFINE_CORPUS_GO).

Ancien corpus inchange (Gate 4 / cycle 2) + 18 chemins neufs listes
en C2B_PATHS (racine gouvernante + gouvernance agent). kind=`doc-c2b`
pour tracer la rupture. Aucune mesure retrieval ici.
"""

from __future__ import annotations

from pathlib import Path

C2B_PATHS = [
    # A. Racine gouvernante (8)
    "AGENTS.md",
    "CHARTER.md",
    "CONTRIBUTING.md",
    "GEMINI.md",
    "PRODUCT_PRINCIPLES.md",
    "README.md",
    "README.en.md",
    "TODO.md",
    # B. Gouvernance agent (10)
    ".agents/STATUS.md",
    ".agents/roles/README.md",
    ".agents/rules/cooking-execution.md",
    ".agents/rules/git-workflow.md",
    ".agents/rules/image-assets.md",
    ".agents/rules/ingredient-icons.md",
    ".agents/rules/multi-agent-orchestration.md",
    ".agents/rules/product-governance.md",
    ".agents/rules/task-claiming.md",
    ".agents/rules/token-frugality.md",
]

# Les 26 golds historiques, bannis comme golds dev/holdout cycle2b.
BANNED_GOLDS = [
    # Gate 4 / cycle 1 (13)
    "docs/ATOMIC_ACTION_ILLUSTRATIONS.md",
    "docs/CATALOGUE-CONTRACT-CORE.md",
    "docs/CI-ARTIFACT-STORAGE.md",
    "docs/E2E-LEDGER.md",
    "docs/HERDR-WORKSPACE-NAMING.md",
    "docs/IMAGE-PROVENANCE.md",
    "docs/INSTANCE-IDENTITY.md",
    "docs/MEAL-COMPOSITION-V1.md",
    "docs/MEAL_PLANNING_NUTRITION.md",
    "docs/PUBLIC-CONTENT-LINT.md",
    "docs/equipment-add-appliance.md",
    "docs/equipment-audit-495.md",
    "docs/equipment-contract-495.md",
    # dev-14 (8)
    ".agents/claims.json",
    "docs/E2E-LEAD-PROTOCOL.md",
    "docs/E2E-WORK-ITEM.md",
    "docs/PUBLIC-CONTRACT.md",
    "docs/nutrition-profile-issue-136.md",
    "docs/review-169-design.md",
    "docs/work-items/391-lot-icons.md",
    "docs/work-items/391-lot-ui-icons.md",
    # holdout-8 mesure (5)
    "decisions/PDR-0010-nutrition-plaisir-sante-meal-planning.md",
    "docs/review-169-cooking.md",
    "docs/review-169-recipe.md",
    "docs/work-items/391-lot-header-brand.md",
    "docs/work-items/391-lot-typography.md",
]


def build_corpus_c2b(root: Path) -> list[dict]:
    """Ancien corpus (modules cycle 1, inchanges) + 18 chemins c2b."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from corpus_manifest import build_corpus, chunk_markdown
    import corpus_manifest as cm
    import hashlib

    docs = build_corpus(root)
    for rel_str in C2B_PATHS:
        rel = Path(rel_str)
        full = root / rel
        if not full.is_file():
            continue
        try:
            text = full.read_text(encoding="utf-8")
        except OSError:
            continue
        for c in chunk_markdown(full, text):
            sha = hashlib.sha256(c["text"].encode()).hexdigest()[:12]
            docs.append({
                "id": f"{rel_str}::{c['section']}"[:200],
                "text": f"# {full.name}\n## {c['section']}\n{c['text']}",
                "payload": {"project": cm.PROJECT, "work_id": c["work_id"],
                            "kind": "doc-c2b",
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


def build_fact_corpus_c2b(root: Path) -> list[dict]:
    """Variante faits (chunk_facts) appliquee au corpus etendu."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import corpus_manifest as cm
    from chunk_facts import split_facts
    from corpus_manifest import chunk_markdown
    import hashlib

    tmp = build_corpus_c2b(root)
    # Regroupe par doc source pour re-decouper en faits.
    by_doc: dict[str, list[dict]] = {}
    for d in tmp:
        by_doc.setdefault(d["payload"]["path"], []).append(d)
    out: list[dict] = []
    for path, chunks in by_doc.items():
        for c in chunks:
            for n, fact in enumerate(
                    split_facts(c["payload"]["section"], c["text"])):
                sha = hashlib.sha256(fact.encode()).hexdigest()[:12]
                wid = c["payload"]["work_id"]
                kind = ("claim" if path == ".agents/claims.json"
                        else c["payload"]["kind"])
                out.append({
                    "id": f"{path}::{c['payload']['section']}#f{n}"[:200],
                    "text": fact,
                    "payload": {"project": cm.PROJECT, "work_id": wid,
                                "kind": kind, "path": path,
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
