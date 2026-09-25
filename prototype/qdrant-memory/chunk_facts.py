"""Chunking oriente-faits (gate 4, #508) — bras d'ablation du chunking.

Section (corpus_manifest, ~1500 chars) vs fait (ici) : items de liste,
lignes de table (avec entete), blocs de code, phrases regroupees <=400 chars.
Deterministe, stdlib. Meme schema payload + champ "chunking".
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from corpus_manifest import chunk_markdown

LIST_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
SENT_RE = re.compile(r"(?<=[.!?…])\s+|\n+")
FACT_MAX = 400


def split_facts(section: str, body: str) -> list[str]:
    facts: list[str] = []
    lines = body.split("\n")
    i, buf, table_head = 0, [], None
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if s.startswith("```"):
            if buf:
                facts.extend(_prose("\n".join(buf)))
                buf = []
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                j += 1
            facts.append("\n".join(lines[i:j + 1]))
            i = j + 1
            continue
        if s.startswith("|"):
            if buf:
                facts.extend(_prose("\n".join(buf)))
                buf = []
            cells = [c.strip() for c in s.strip("|").split("|")]
            if set(cells) <= {"", "-", ":", "---", ":---", "---:", ":---:"}:
                i += 1
                continue
            if table_head is None:
                table_head = s
                i += 1
                continue
            facts.append(f"{table_head}\n{s}")
            i += 1
            continue
        table_head = None
        if LIST_RE.match(line):
            if buf:
                facts.extend(_prose("\n".join(buf)))
                buf = []
            item = [line]
            i += 1
            while i < len(lines) and lines[i].startswith((" ", "\t")) \
                    and lines[i].strip():
                item.append(lines[i])
                i += 1
            facts.append("\n".join(item))
            continue
        buf.append(line)
        i += 1
    if buf:
        facts.extend(_prose("\n".join(buf)))
    return [f for f in (x.strip() for x in facts) if f]


def _prose(text: str) -> list[str]:
    sents = [s for s in SENT_RE.split(text.strip()) if s.strip()]
    out, cur = [], ""
    for s in sents:
        if cur and len(cur) + 1 + len(s) > FACT_MAX:
            out.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        out.append(cur)
    return out or ([text.strip()] if text.strip() else [])


def build_fact_corpus(root: Path) -> list[dict]:
    import corpus_manifest as cm
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
            for n, fact in enumerate(split_facts(c["section"], c["text"])):
                sha = hashlib.sha256(fact.encode()).hexdigest()[:12]
                docs.append({
                    "id": f"{rel.relative_to(root)}::{c['section']}#f{n}"[:200],
                    "text": f"# {rel.name}\n## {c['section']}\n{fact}",
                    "payload": {"project": cm.PROJECT, "work_id": c["work_id"],
                                "kind": kind,
                                "path": str(rel.relative_to(root)),
                                "section": c["section"], "updated_at": "git",
                                "sha": sha, "chunking": "fact"},
                })
    claims = root / ".agents" / "claims.json"
    if claims.is_file():
        try:
            import json
            data = json.loads(claims.read_text(encoding="utf-8"))
            seen = [c for c in data.get("completed_claims", [])][-8:]
            summary = "\n".join(
                f"- #{c.get('issue')} {c.get('title')} [{c.get('status')}]"
                for c in seen)
            docs.append({"id": "claims::recent",
                         "text": "# claims.json (resume)\n" + summary,
                         "payload": {"project": cm.PROJECT, "work_id": None,
                                     "kind": "claim",
                                     "path": ".agents/claims.json",
                                     "section": "recent", "updated_at": "git",
                                     "sha": "summary", "chunking": "fact"}})
        except (OSError, ValueError):
            pass
    seen_ids: dict[str, int] = {}
    for d in docs:
        k = seen_ids.get(d["id"], 0)
        seen_ids[d["id"]] = k + 1
        if k:
            d["id"] = f"{d['id']}#p{k}"
    return docs
