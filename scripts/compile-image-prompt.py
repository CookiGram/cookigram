#!/usr/bin/env python3
"""Compile a deterministic image-generation prompt (#396).

Reads the versioned instance visual profile plus a canonical subject only:

    profile versionné de l'instance + sujet canonique -> prompt compilé

The compiler derives nothing beyond the facts it is given (recipe title,
description and tags, or an explicitly provided action/context). It imposes
no provider or model, calls no runtime AI, and never generates an image:
use the printed prompt as a preview.

Example:
    python scripts/compile-image-prompt.py --recipe pizza-margherita
    python scripts/compile-image-prompt.py --action cut --context board --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / "assets/visual-profile/cookigram-v1.yaml"


def _frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path} has no YAML frontmatter")
    _, _, body = text.partition("\n")
    frontmatter, separator, _ = body.partition("\n---")
    if not separator:
        raise ValueError(f"{path} has unterminated YAML frontmatter")
    data = yaml.safe_load(frontmatter) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} frontmatter is not a mapping")
    return data


def _recipe_facts(root: Path, slug: str) -> dict[str, str]:
    path = root / "recipes" / f"{slug}.gram"
    if not path.is_file():
        raise ValueError(f"unknown recipe: {slug}")
    metadata = _frontmatter(path)
    title = metadata.get("title", "")
    description = metadata.get("description", "")
    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"{slug} has no usable title")
    if not isinstance(description, str) or not description.strip():
        raise ValueError(f"{slug} has no usable description")
    return {"title": title.strip(), "description": description.strip()}


def compile_prompt(profile: dict[str, Any], subject: dict[str, str]) -> str:
    """Render the prompt deterministically from profile + subject facts."""
    subjects = profile.get("subjects", {})
    kind = subject["kind"]
    if kind not in subjects:
        raise ValueError(f"subject kind not covered by profile: {kind}")
    framing = subjects[kind].get("framing", "")
    asset_type = subjects[kind].get("asset_type", "")
    if kind == "recipe":
        subject_line = f'"{subject["title"]}" - {subject["description"]}'
    else:
        subject_line = f'guided-cooking gesture "{subject["action"]}" in context "{subject["context"]}"'
    lines = [
        f"Use case: {profile.get('use_case', '')}",
        f"Asset type: {asset_type}",
        "Primary request: Create an entirely original manga-inspired culinary illustration of",
        f"{subject_line} based only on these written culinary facts, not on any existing photograph.",
        f"Scene/backdrop: {profile.get('scene', '')}",
        f"Subject: {subject_line}.",
        f"Style/medium: {profile.get('style_medium', '')}",
        f"Composition/framing: {framing}",
        f"Lighting/mood: {profile.get('lighting', '')}",
        f"Constraints: {profile.get('constraints', '')}",
        f"Avoid: {profile.get('avoid', '')}",
        f"Visual profile: {profile.get('name', '')} revision {profile.get('revision', '')}.",
    ]
    return "\n".join(lines) + "\n"


def manifest_fragment(profile: dict[str, Any], subject: dict[str, str], prompt: str) -> dict[str, Any]:
    """#393-compatible provenance fragment (prompt + subject + profile)."""
    if subject["kind"] == "recipe":
        subject_block = {"type": "recipe", "recipe": subject["slug"]}
    else:
        subject_block = {"type": "cooking_action", "action": subject["action"], "context": subject["context"]}
    return {
        "subject": subject_block,
        "visual_profile": {"name": profile.get("name"), "revision": profile.get("revision")},
        "prompt": prompt,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--recipe", help="recipe slug from recipes/")
    target.add_argument("--action", help="cooking-action verb (requires --context)")
    parser.add_argument("--context", default="", help="cooking-action context")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        profile = yaml.safe_load(args.profile.read_text(encoding="utf-8"))
        if not isinstance(profile, dict) or not isinstance(profile.get("revision"), int):
            raise ValueError(f"invalid visual profile: {args.profile}")
        if args.recipe:
            facts = _recipe_facts(args.root, args.recipe)
            subject = {"kind": "recipe", "slug": args.recipe, **facts}
        else:
            if not args.context.strip():
                raise ValueError("--action requires --context")
            subject = {"kind": "cooking_action", "action": args.action.strip(), "context": args.context.strip()}
        prompt = compile_prompt(profile, subject)
    except (OSError, yaml.YAMLError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.format == "json":
        print(json.dumps(manifest_fragment(profile, subject, prompt), ensure_ascii=False, indent=2))
    else:
        print(prompt, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
