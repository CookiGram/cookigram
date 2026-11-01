#!/usr/bin/env python3
"""Fail when a recipe with an unresolved publication exclusion is in recipes/."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def excluded_recipes(root: Path) -> list[str]:
    manifest_path = root / ".gram/publication-exclusions.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    slugs = manifest.get("excluded_recipe_slugs")
    if manifest.get("schema_version") != 1 or not isinstance(slugs, list):
        raise ValueError(f"Invalid publication exclusion manifest: {manifest_path}")
    if any(not isinstance(slug, str) or not slug or "/" in slug for slug in slugs):
        raise ValueError(f"Invalid recipe slug in publication exclusion manifest: {manifest_path}")
    return sorted(slug for slug in slugs if (root / "recipes" / f"{slug}.gram").is_file())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true", help="fail if any excluded recipe is present")
    args = parser.parse_args()
    present = excluded_recipes(args.root.resolve())
    if present:
        print("ERROR: excluded recipes are present in the public catalogue:")
        for slug in present:
            print(f"  recipes/{slug}.gram")
        print("See docs/foie-gras-mi-cuit-safety-dossier-2026-11-01.md before removing this gate.")
        return 1 if args.check else 0
    print("PASS: no temporarily excluded recipe is present in recipes/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
