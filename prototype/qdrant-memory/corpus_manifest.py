"""Corpus derive des artefacts durables (source de verite) — jamais l'inverse.

Indexe : docs/*.md, decisions/*, .agents/claims.json (resume), docs/work-items/*.
Payload : {project, work_id, kind, path, section, updated_at, sha}.
Decoupage : une section `##` = un chunk (max ~1500 chars, decoupe dure au-dela).
work_id : extrait du titre/path (#NNN) quand present, sinon None (filtrable).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

PROJECT = "cookigram"
SECTION_RE = re.compile(r"^##\s+(.*)", re.MULTILINE)
WORK_ID_RE = re.compile(r"#(\d{2,4})")
CHUNK_MAX = 1500


def _work_id(*texts: str) -> str | None:
    for t in texts:
        m = WORK_ID_RE.search(t or "")
        if m:
            return m.group(1)
    return None


def chunk_markdown(path: Path, text: str) -> list[dict]:
    parts = SECTION_RE.split(text)
    head, rest = parts[0], parts[1:]
    chunks: list[dict] = []
    if head.strip():
        chunks.append(("(intro)", head.strip()))
    for i in range(0, len(rest), 2):
        title, body = rest[i], rest[i + 1] if i + 1 < len(rest) else ""
        chunks.append((title.strip(), body.strip()))
    out = []
    for title, body in chunks:
        while len(body) > CHUNK_MAX:
            cut = body.rfind("\n", 0, CHUNK_MAX) or CHUNK_MAX
            out.append((title, body[:cut]))
            body = body[cut:]
        if body:
            out.append((title, body))
    wid = _work_id(path.name, text[:500])
    return [{"section": t, "text": b, "work_id": wid} for t, b in out]


def build_corpus(root: Path) -> list[dict]:
    docs: list[dict] = []
    for rel in [*(root / "docs").rglob("*.md"), *(root / "decisions").glob("*")]:
        if not rel.is_file() or rel.suffix != ".md":
            continue
        try:
            text = rel.read_text(encoding="utf-8")
        except OSError:
            continue
        kind = "work-item" if "work-items" in rel.parts else "doc"
        for c in chunk_markdown(rel, text):
            sha = hashlib.sha256(c["text"].encode()).hexdigest()[:12]
            docs.append({
                "id": f"{rel.relative_to(root)}::{c['section']}"[:200],
                "text": f"# {rel.name}\n## {c['section']}\n{c['text']}",
                "payload": {"project": PROJECT, "work_id": c["work_id"],
                            "kind": kind, "path": str(rel.relative_to(root)),
                            "section": c["section"], "updated_at": "git",
                            "sha": sha},
            })
    claims = root / ".agents" / "claims.json"
    if claims.is_file():
        try:
            data = json.loads(claims.read_text(encoding="utf-8"))
            seen = [c for c in data.get("completed_claims", [])][-8:]
            summary = "\n".join(
                f"- #{c.get('issue')} {c.get('title')} [{c.get('status')}]"
                for c in seen)
            docs.append({"id": "claims::recent",
                         "text": "# claims.json (resume)\n" + summary,
                         "payload": {"project": PROJECT, "work_id": None,
                                     "kind": "claim", "path": ".agents/claims.json",
                                     "section": "recent", "updated_at": "git",
                                     "sha": "summary"}})
        except (OSError, ValueError):
            pass
    # Unicite des ids : les sections longues decoupees partagent (path, section).
    seen_ids: dict[str, int] = {}
    for d in docs:
        n = seen_ids.get(d["id"], 0)
        seen_ids[d["id"]] = n + 1
        if n:
            d["id"] = f"{d['id']}#p{n}"
    return docs
