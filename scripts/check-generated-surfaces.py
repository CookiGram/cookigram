#!/usr/bin/env python3
"""Verify generated product pages and required local assets."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


MAIN_RE = re.compile(r"<main\b[^>]*>.*?</main>", re.DOTALL)
REQUIRED_ASSETS = (
    Path("assets/illustrations/empty-fridge.webp"),
)


def main_fragment(path: Path) -> str:
    match = MAIN_RE.search(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"Aucun élément <main> dans {path}")
    return match.group(0).strip()


def check(root: Path, site: Path) -> None:
    failures = []
    for source in sorted((root / "static").glob("*/index.html")):
        generated = site / source.parent.name / "index.html"
        if not generated.is_file():
            failures.append(f"page générée absente: {generated}")
            continue
        if main_fragment(source) != main_fragment(generated):
            failures.append(f"fragment divergent: {source} != {generated}")

    for relative in REQUIRED_ASSETS:
        generated_asset = site / relative
        if not generated_asset.is_file():
            failures.append(f"asset généré absent: {generated_asset}")

    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-dir", type=Path, required=True)
    args = parser.parse_args()
    check(Path(__file__).resolve().parents[1], args.site_dir)
