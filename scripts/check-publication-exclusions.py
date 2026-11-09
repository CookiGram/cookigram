#!/usr/bin/env python3
"""Fail closed unless the public recipe corpus matches its reviewed baseline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

APPROVED_MANIFEST = Path(".gram/approved-recipes.json")
# Updated only with a reviewed change to the approved recipe baseline.
APPROVED_MANIFEST_SHA256 = "d4dac92516b3997868f6817be99d5a4a5d3b12afc23bcac9aea8e907b9719cc0"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate(root: Path, expected_manifest_sha256: str) -> list[str]:
    """Return publication blockers; the expected digest is pinned by the caller."""
    path = root / APPROVED_MANIFEST
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return [f"approved recipe manifest is unavailable: {exc}"]
    if sha256(raw) != expected_manifest_sha256:
        return [f"approved recipe manifest digest does not match the pinned value: {path}"]
    try:
        manifest = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"invalid approved recipe manifest: {exc}"]
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != 1
        or not isinstance(manifest.get("recipes"), dict)
    ):
        return [f"invalid approved recipe manifest schema: {path}"]

    approved = manifest["recipes"]
    if any(
        not isinstance(name, str)
        or not name.startswith("recipes/")
        or not name.endswith(".gram")
        or ".." in Path(name).parts
        or not isinstance(digest, str)
        or len(digest) != 64
        or any(char not in "0123456789abcdef" for char in digest)
        for name, digest in approved.items()
    ):
        return [f"invalid recipe path or SHA-256 entry in approved manifest: {path}"]

    recipes_root = root / "recipes"
    actual_paths = {
        recipe.relative_to(root).as_posix()
        for recipe in recipes_root.rglob("*.gram")
    } if recipes_root.is_dir() else set()
    approved_paths = set(approved)
    findings: list[str] = []
    for name in sorted(actual_paths - approved_paths):
        findings.append(f"unapproved recipe path: {name}")
    for name in sorted(approved_paths - actual_paths):
        findings.append(f"approved recipe is missing or renamed: {name}")
    for name in sorted(actual_paths & approved_paths):
        try:
            digest = sha256((root / name).read_bytes())
        except OSError as exc:
            findings.append(f"cannot read approved recipe {name}: {exc}")
            continue
        if digest != approved[name]:
            findings.append(f"approved recipe content changed: {name}")
    return findings


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = validate(root, APPROVED_MANIFEST_SHA256)
    if findings:
        print("ERROR: public recipe corpus differs from the reviewed approved baseline:")
        for finding in findings:
            print(f"  {finding}")
        print("See docs/foie-gras-mi-cuit-safety-dossier-2026-11-01.md for the reviewed update workflow.")
        return 1
    print("PASS: every public recipe path and content hash matches the reviewed baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
