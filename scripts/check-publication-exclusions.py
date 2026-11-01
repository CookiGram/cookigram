#!/usr/bin/env python3
"""Fail when a recipe with an unresolved publication exclusion is in recipes/."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

import yaml

REQUIRED_EXCLUDED_RECIPE_SLUGS = frozenset({
    "foie-gras-armagnac-quatre-epices-sous-vide",
    "foie-gras-nature-sous-vide",
    "foie-gras-poivre-vert-sous-vide",
    "foie-gras-sauternes-figue-sous-vide",
    "foie-gras-truffe-noire-sous-vide",
})
BLOCKED_CANONICAL_INGREDIENT_IDS = frozenset({"foie-gras-de-canard-cru"})
BLOCKED_INGREDIENT_TOKENS = frozenset({
    "foie gras cru de canard",
    "foie gras de canard cru",
    "foie gras cru",
    "foie de canard",
    "foie de canard cru",
})


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
    if manifest.get("schema_version") != 1 or not isinstance(slugs, list):
        raise ValueError(f"Invalid publication exclusion manifest: {manifest_path}")
    if any(not isinstance(slug, str) or not slug or "/" in slug for slug in slugs):
        raise ValueError(f"Invalid recipe slug in publication exclusion manifest: {manifest_path}")
    if frozenset(slugs) != REQUIRED_EXCLUDED_RECIPE_SLUGS:
        raise ValueError(f"Required recipe exclusions were changed: {manifest_path}")

    ingredient_manifest = root / ".gram/ingredients.yaml"
    ingredient_data = yaml.safe_load(ingredient_manifest.read_text(encoding="utf-8"))
    ingredients = ingredient_data.get("ingredients") if isinstance(ingredient_data, dict) else None
    if not isinstance(ingredients, dict):
        raise ValueError(f"Invalid ingredient registry: {ingredient_manifest}")
    alias_to_ids: dict[str, set[str]] = {}
    for canonical_id, entry in ingredients.items():
        if not isinstance(canonical_id, str) or not isinstance(entry, dict):
            raise ValueError(f"Invalid ingredient entry in {ingredient_manifest}: {canonical_id!r}")
        aliases = entry.get("aliases", [])
        if not isinstance(aliases, list) or any(not isinstance(alias, str) for alias in aliases):
            raise ValueError(f"Invalid aliases for ingredient {canonical_id!r} in {ingredient_manifest}")
        labels = [canonical_id, entry.get("name", ""), *aliases]
        for label in labels:
            if isinstance(label, str) and label.strip():
                alias_to_ids.setdefault(normalize_identity(label), set()).add(canonical_id)

    blocked_ids = BLOCKED_CANONICAL_INGREDIENT_IDS
    blocked_tokens = {normalize_identity(token) for token in BLOCKED_INGREDIENT_TOKENS}

    findings: list[tuple[str, str]] = []
    for recipe in sorted((root / "recipes").rglob("*.gram")):
        relative_path = recipe.relative_to(root).as_posix()
        if recipe.stem in slugs:
            findings.append((relative_path, "excluded recipe slug"))
            continue
        source = recipe.read_text(encoding="utf-8")
        tokens = [normalize_identity(token) for token in re.findall(r"@([^{}\n]+)\{", source)]
        matched = sorted({
            token for token in tokens
            if token in blocked_tokens or alias_to_ids.get(token, set()) & blocked_ids
        })
        if matched:
            findings.append((relative_path, f"excluded canonical ingredient identity: {', '.join(matched)}"))
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
