#!/usr/bin/env python3
"""Fail when a recipe with an unresolved publication exclusion is in recipes/."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

REQUIRED_CONTENT_TERMS = {"foie gras"}


def normalize_identity(text: str) -> str:
    """Normalize punctuation, accents, case and whitespace for family matching."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    unaccented = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", unaccented).strip()


def excluded_recipes(root: Path) -> list[tuple[str, str]]:
    manifest_path = root / ".gram/publication-exclusions.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError(f"Invalid publication exclusion manifest: {manifest_path}")
    slugs = manifest.get("excluded_recipe_slugs")
    terms = manifest.get("excluded_content_terms")
    if (manifest.get("schema_version") != 1 or not isinstance(slugs, list)
            or not isinstance(terms, list) or not slugs or not terms):
        raise ValueError(f"Invalid publication exclusion manifest: {manifest_path}")
    if any(not isinstance(slug, str) or not slug or "/" in slug for slug in slugs):
        raise ValueError(f"Invalid recipe slug in publication exclusion manifest: {manifest_path}")
    normalized_terms = [normalize_identity(term) for term in terms if isinstance(term, str) and term.strip()]
    if (len(normalized_terms) != len(terms) or any(not term for term in normalized_terms)
            or not REQUIRED_CONTENT_TERMS.issubset(normalized_terms)):
        raise ValueError(f"Invalid content term in publication exclusion manifest: {manifest_path}")

    findings: list[tuple[str, str]] = []
    for recipe in sorted((root / "recipes").rglob("*.gram")):
        relative_path = recipe.relative_to(root).as_posix()
        if recipe.stem in slugs:
            findings.append((relative_path, "excluded recipe slug"))
            continue
        content = normalize_identity(recipe.read_text(encoding="utf-8"))
        matched_terms = [term for term in normalized_terms if re.search(rf"\b{re.escape(term)}\b", content)]
        if matched_terms:
            findings.append((relative_path, f"excluded content identity: {', '.join(matched_terms)}"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    present = excluded_recipes(args.root.resolve())
    if present:
        print("ERROR: excluded recipes are present in the public catalogue:")
        for recipe, reason in present:
            print(f"  {recipe} ({reason})")
        print("See docs/foie-gras-mi-cuit-safety-dossier-2026-11-01.md before removing this gate.")
        return 1
    print("PASS: no temporarily excluded recipe is present in recipes/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
