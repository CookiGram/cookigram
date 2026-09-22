#!/usr/bin/env python3
"""CookiGram instance resolver and mapping for atomic cooking action illustrations.

Architecture principle:
- Core owns the semantic tokens (cut, rinse, mix, saute, etc.) and fallback slots.
- The CookiGram instance defines its own visual representation, asset paths,
  and artistic contract (warm gouache, soft cel-shading, 3:2 ratio).
- An unknown token, missing file, or unsupported action falls back gracefully
  without ever breaking recipe rendering or page generation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# Instance-owned visual mapping: canonical token -> relative asset path
INSTANCE_ACTION_MAPPING: dict[str, str] = {
    # Lot Pilote (validé)
    "cut": "images/atomic-actions/cut.webp",
    "rinse": "images/atomic-actions/rinse.webp",
    "mix": "images/atomic-actions/mix.webp",
    "whisk": "images/atomic-actions/whisk.webp",
    "pour": "images/atomic-actions/pour.webp",
    "saute": "images/atomic-actions/saute.webp",
    "simmer": "images/atomic-actions/simmer.webp",
    "knead": "images/atomic-actions/knead.webp",
    "rest": "images/atomic-actions/rest.webp",
    "serve": "images/atomic-actions/serve.webp",
    # Lot P1 (validé)
    "oven": "images/atomic-actions/oven.webp",
    "boil": "images/atomic-actions/boil.webp",
    "assemble": "images/atomic-actions/assemble.webp",
    "steam": "images/atomic-actions/steam.webp",
    "season": "images/atomic-actions/season.webp",
    "air_fry": "images/atomic-actions/air_fry.webp",
    "blend": "images/atomic-actions/blend.webp",
    # Lot P2 (validé)
    "grate": "images/atomic-actions/grate.webp",
    "roll_out": "images/atomic-actions/roll_out.webp",
    "peel": "images/atomic-actions/peel.webp",
}

# Semantic mutualization aliases: secondary/fine-grained gestures mapped to archetypes
MUTUALIZED_ALIASES: dict[str, str] = {
    # Lot Pilote aliases
    "chop": "cut",
    "slice": "cut",
    "dice": "cut",
    "mince": "cut",
    "julienne": "cut",
    "drain": "rinse",
    "wash": "rinse",
    "strain": "rinse",
    "stir": "mix",
    "combine": "mix",
    "toss": "mix",
    "beat": "whisk",
    "emulsify": "whisk",
    "froth": "whisk",
    "drizzle": "pour",
    "add_liquid": "pour",
    "deglaze": "pour",
    "sear": "saute",
    "brown": "saute",
    "fry": "saute",
    "stew": "simmer",
    "braise": "simmer",
    "reduce": "simmer",
    "fold_dough": "knead",
    "shape_dough": "knead",
    "punch_down": "knead",
    "cool": "rest",
    "stand": "rest",
    "settle": "rest",
    "plate": "serve",
    "garnish_final": "serve",
    "dish_out": "serve",
    # Lot P1 aliases
    "preheat": "oven",
    "bake": "oven",
    "roast": "oven",
    "broil": "oven",
    "gratin": "oven",
    "baking": "oven",
    "in_oven": "oven",
    "rolling_boil": "boil",
    "blanch": "boil",
    "poach": "boil",
    "pasta_boil": "boil",
    "water_cook": "boil",
    "layer": "assemble",
    "garnish_intermediate": "assemble",
    "spread_layer": "assemble",
    "mount": "assemble",
    "stuff": "assemble",
    "fill": "assemble",
    "varoma": "steam",
    "bamboo_steam": "steam",
    "steam_cook": "steam",
    "steamer": "steam",
    "salt": "season",
    "pepper": "season",
    "spice": "season",
    "sprinkle": "season",
    "coat": "season",
    "marinate_season": "season",
    "crisp_air_fry": "air_fry",
    "airfryer_basket": "air_fry",
    "shake_basket": "air_fry",
    "puree": "blend",
    "crush_food": "blend",
    "immersion_blend": "blend",
    "liquidize": "blend",
    "smoothie_blend": "blend",
    # Lot P2 aliases
    "zest": "grate",
    "microplane": "grate",
    "shred_cheese": "grate",
    "grater": "grate",
    "zester": "grate",
    "finely_grate": "grate",
    "roll_dough": "roll_out",
    "flatten_dough": "roll_out",
    "rolling_pin": "roll_out",
    "roll_flat": "roll_out",
    "sheet_dough": "roll_out",
    "abaisser": "roll_out",
    "vegetable_peel": "peel",
    "skin_vegetables": "peel",
    "econome": "peel",
    "pare": "peel",
    "peeling": "peel",
}


def normalize_token(token: str) -> str:
    """Normalize action token to lowercase stripped string."""
    return (token or "").strip().lower().replace("-", "_").replace(" ", "_")


def resolve_canonical_token(token: str) -> str:
    """Resolve token to canonical action token via mutualization aliases."""
    normalized = normalize_token(token)
    return MUTUALIZED_ALIASES.get(normalized, normalized)


def resolve_action_asset(token: str, root: Path | None = None, prefix: str = "") -> str:
    """Resolve an action token to its instance asset path.

    Returns empty string if the token has no mapped illustration or if the asset file
    is missing on disk when root is provided (safe fallback).
    """
    canonical = resolve_canonical_token(token)
    rel_path = INSTANCE_ACTION_MAPPING.get(canonical)
    if not rel_path:
        return ""

    if root is not None:
        target_file = root / "static" / rel_path
        if not target_file.is_file():
            return ""

    return f"{prefix}{rel_path}" if prefix else rel_path


def audit_action_assets(root: Path = ROOT) -> list[dict[str, Any]]:
    """Audit the instance action assets against the manifest and filesystem."""
    issues = []
    manifest_path = root / "assets/atomic-actions/manifest.json"
    if not manifest_path.is_file():
        issues.append({"severity": "error", "message": "Manifest file missing: assets/atomic-actions/manifest.json"})
        return issues

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        issues.append({"severity": "error", "message": f"Malformed manifest: {exc}"})
        return issues

    items = {item["canonical_token"]: item for item in manifest.get("items", [])}

    for token, rel_path in INSTANCE_ACTION_MAPPING.items():
        if token not in items:
            issues.append({"token": token, "severity": "warning", "message": f"Token {token} mapped but not in manifest"})
        asset_file = root / "static" / rel_path
        if not asset_file.is_file():
            issues.append({"token": token, "severity": "error", "message": f"Asset file missing on disk: {asset_file}"})
        prompt_file = root / "image-prompts/atomic-actions" / f"{token}.md"
        if not prompt_file.is_file():
            issues.append({"token": token, "severity": "warning", "message": f"Prompt file missing: {prompt_file}"})

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit and resolve CookiGram atomic action illustrations.")
    parser.add_argument("--check", action="store_true", help="Audit all mapped assets and exit non-zero on error.")
    parser.add_argument("--json", action="store_true", help="Output audit report as JSON.")
    parser.add_argument("--resolve", type=str, help="Resolve a single action token.")
    args = parser.parse_args()

    if args.resolve:
        asset = resolve_action_asset(args.resolve, root=ROOT)
        if asset:
            print(f"{args.resolve} -> {asset}")
            return 0
        else:
            print(f"{args.resolve} -> (fallback: no asset)")
            return 1

    if args.check or args.json:
        issues = audit_action_assets(ROOT)
        errors = [i for i in issues if i.get("severity") == "error"]
        if args.json:
            print(json.dumps({"issues": issues, "error_count": len(errors)}, indent=2))
        else:
            if not issues:
                print("✓ All atomic action illustrations, prompts, and manifest entries are valid.")
            for i in issues:
                print(f"[{i.get('severity', 'info').upper()}] {i.get('token', '')}: {i['message']}")
        return 1 if errors else 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
