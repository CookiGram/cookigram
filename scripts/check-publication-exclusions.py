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
REQUIRED_CANONICAL_INGREDIENT_NAME = "Foie gras cru de canard"
REQUIRED_CANONICAL_INGREDIENT_ALIASES = frozenset({
    "foie gras cru de canard",
    "foie gras de canard cru",
    "foie gras cru",
})
BLOCKED_INGREDIENT_TOKENS = frozenset({
    "foie gras cru de canard",
    "foie gras de canard cru",
    "foie gras cru",
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
    ingredient_source = ingredient_manifest.read_text(encoding="utf-8")
    protected_canonical_id = next(iter(BLOCKED_CANONICAL_INGREDIENT_IDS))
    canonical_declarations = re.findall(
        rf"(?m)^  {re.escape(protected_canonical_id)}\s*:", ingredient_source
    )
    if len(canonical_declarations) != 1:
        raise ValueError(f"Required canonical ingredient declaration is missing or duplicated: {ingredient_manifest}")
    ingredient_data = yaml.safe_load(ingredient_source)
    ingredients = ingredient_data.get("ingredients") if isinstance(ingredient_data, dict) else None
    if not isinstance(ingredients, dict):
        raise ValueError(f"Invalid ingredient registry: {ingredient_manifest}")
    protected_entry = ingredients.get(protected_canonical_id)
    if not isinstance(protected_entry, dict):
        raise ValueError(f"Required canonical ingredient {protected_canonical_id!r} is missing: {ingredient_manifest}")
    if normalize_identity(str(protected_entry.get("name", ""))) != normalize_identity(REQUIRED_CANONICAL_INGREDIENT_NAME):
        raise ValueError(f"Required canonical ingredient name was changed: {ingredient_manifest}")
    protected_aliases = protected_entry.get("aliases", [])
    if not isinstance(protected_aliases, list) or any(not isinstance(alias, str) for alias in protected_aliases):
        raise ValueError(f"Invalid aliases for protected ingredient {protected_canonical_id!r}: {ingredient_manifest}")
    normalized_protected_aliases = {normalize_identity(alias) for alias in protected_aliases}
    required_aliases = {normalize_identity(alias) for alias in REQUIRED_CANONICAL_INGREDIENT_ALIASES}
    if not required_aliases.issubset(normalized_protected_aliases):
        raise ValueError(f"Required aliases for canonical ingredient {protected_canonical_id!r} were changed: {ingredient_manifest}")

    alias_to_ids: dict[str, set[str]] = {}
    for registry_id, entry in ingredients.items():
        if not isinstance(registry_id, str) or not isinstance(entry, dict):
            raise ValueError(f"Invalid ingredient entry in {ingredient_manifest}: {registry_id!r}")
        aliases = entry.get("aliases", [])
        if not isinstance(aliases, list) or any(not isinstance(alias, str) for alias in aliases):
            raise ValueError(f"Invalid aliases for ingredient {registry_id!r} in {ingredient_manifest}")
        labels = [registry_id, entry.get("name", ""), *aliases]
        for label in labels:
            if isinstance(label, str) and label.strip():
                alias_to_ids.setdefault(normalize_identity(label), set()).add(registry_id)

    for alias in required_aliases:
        if alias_to_ids.get(alias) != {protected_canonical_id}:
            raise ValueError(f"Protected ingredient alias collision or reassignment for {alias!r}: {ingredient_manifest}")

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
            continue

        # The source #534 full-copy method fingerprint catches a copied recipe
        # whose canonical ingredient ID and wording were both replaced. It is
        # intentionally specific to the unvalidated 500 ml jar/bag/barème.
        method = normalize_identity(source)
        method_markers = (
            bool(re.search(r"\b500\s*(?:ml|millilitres?|milliliters?)\b", method)),
            bool(re.search(r"\b55\s*(?:c(?:elsius)?|(?:degrees?|degres?)\s*(?:c|celsius))\b", method)),
            bool(re.search(r"\b80\s*(?:min(?:ute)?s?)\b", method)),
            "bocal ouvert" in method and "sac de cuisson sous vide" in method,
        )
        if all(method_markers):
            findings.append((relative_path, "excluded unqualified jar/bag/55 C/80 min method fingerprint"))
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
