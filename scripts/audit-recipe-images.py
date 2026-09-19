#!/usr/bin/env python3
"""Find recipe illustrations that are still stranded behind a placeholder.

The audit deliberately lives in the content repository so it also works when
the private CookiGram engine is unavailable (for example on fork pull
requests).  ``--check`` is intended for CI and exits non-zero for every
actionable image/prompt mismatch.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml
from PIL import Image, UnidentifiedImageError


PLACEHOLDER = "images/placeholder-recipe.jpg"
TEMPORARY_CREDIT = "Illustration temporaire"
GENERATED_CREDIT = "Illustration générée pour CookiGram"
# Migration boundary: the older "Illustration générée par IA pour CookiGram"
# records are intentionally not required to have a manifest entry yet. New or
# repaired generated assets use GENERATED_CREDIT and must be manifested.
PROVENANCE_MANIFEST = "assets/provenance/images.yaml"


@dataclass(frozen=True)
class Finding:
    recipe: str
    image: str
    prompt_file: str
    status: str
    message: str


def _frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    _, _, body = text.partition("\n")
    frontmatter, separator, _ = body.partition("\n---")
    if not separator:
        return {}
    data = yaml.safe_load(frontmatter) or {}
    return data if isinstance(data, dict) else {}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest(root: Path) -> dict[str, Any]:
    path = root / PROVENANCE_MANIFEST
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _manifest_findings(root: Path, manifest: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    mapped_recipes: dict[str, str] = {}
    for asset, record in manifest.items():
        if not isinstance(asset, str) or not isinstance(record, dict):
            findings.append(Finding(PROVENANCE_MANIFEST, None, "invalid-manifest", "manifest", "chaque asset doit avoir un mapping YAML"))
            continue
        asset_path = root / asset
        if not asset_path.is_file():
            findings.append(Finding(PROVENANCE_MANIFEST, None, "missing-provenance-asset", "manifest", f"fichier absent: {asset}"))
            continue
        expected_hash = record.get("sha256")
        if not isinstance(expected_hash, str) or expected_hash != _sha256(asset_path):
            findings.append(Finding(PROVENANCE_MANIFEST, None, "provenance-hash", "manifest", f"SHA-256 incorrect: {asset}"))
        recipe = record.get("recipe")
        if not isinstance(recipe, str) or not recipe.strip():
            findings.append(Finding(PROVENANCE_MANIFEST, None, "provenance-recipe", "manifest", f"recipe absente: {asset}"))
        elif recipe in mapped_recipes:
            findings.append(Finding(PROVENANCE_MANIFEST, None, "duplicate-provenance-recipe", "manifest", f"recipe mappée deux fois: {recipe}"))
        else:
            mapped_recipes[recipe] = asset
            recipe_path = root / "recipes" / f"{recipe}.gram"
            if not recipe_path.is_file():
                findings.append(Finding(PROVENANCE_MANIFEST, None, "unknown-provenance-recipe", "manifest", f"recipe introuvable: {recipe}"))
        for key in ("origin", "generator", "prompt", "attribution"):
            if not isinstance(record.get(key), str) or not record[key].strip():
                findings.append(Finding(PROVENANCE_MANIFEST, None, "incomplete-provenance", "manifest", f"{key} absent pour {asset}"))
        generated_at = record.get("generated_at")
        if isinstance(generated_at, (dt.date, dt.datetime)):
            pass
        elif not isinstance(generated_at, str) or not generated_at.strip():
            findings.append(Finding(PROVENANCE_MANIFEST, None, "incomplete-provenance", "manifest", f"generated_at absent pour {asset}"))
        if record.get("origin") != "generated":
            findings.append(Finding(PROVENANCE_MANIFEST, None, "provenance-origin", "manifest", f"origin non générée pour {asset}"))
    return findings


def _recipe_image_refs(root: Path) -> dict[str, list[str]]:
    refs: dict[str, list[str]] = {}
    for recipe_path in sorted((root / "recipes").rglob("*.gram")):
        metadata = _frontmatter(recipe_path)
        image = metadata.get("image")
        if isinstance(image, str) and image.strip():
            refs.setdefault(f"static/{image.strip()}", []).append(recipe_path.stem)
    return refs


def _image_findings(root: Path, refs: dict[str, list[str]]) -> list[Finding]:
    findings: list[Finding] = []
    for asset, recipes in refs.items():
        path = root / asset
        if not path.is_file():
            findings.append(Finding(
                recipe=recipes[0], image=asset.removeprefix("static/"),
                prompt_file="", status="missing-image",
                message=f"fichier image introuvable: {asset}",
            ))
            continue
        try:
            with Image.open(path) as image:
                image.verify()
        except (OSError, UnidentifiedImageError) as exc:
            findings.append(Finding(
                recipe=recipes[0], image=asset.removeprefix("static/"),
                prompt_file="", status="corrupt-image",
                message=f"image illisible: {asset} ({exc})",
            ))

    # placeholder-recipe.jpg is an intentional shared fallback, not a recipe
    # asset. All other files in this directory must be referenced by a recipe.
    image_dir = root / "static" / "images"
    for path in sorted(image_dir.rglob("*")) if image_dir.is_dir() else []:
        if not path.is_file():
            continue
        asset = path.relative_to(root).as_posix()
        if asset not in refs and path.name != "placeholder-recipe.jpg":
            findings.append(Finding(
                recipe=PROVENANCE_MANIFEST, image=asset.removeprefix("static/"),
                prompt_file="", status="orphan-image",
                message=f"image recipe sans référence: {asset}",
            ))
    return findings


def audit(root: Path) -> list[Finding]:
    manifest = _manifest(root)
    findings: list[Finding] = _manifest_findings(root, manifest)
    findings.extend(_image_findings(root, _recipe_image_refs(root)))
    recipes_dir = root / "recipes"

    for recipe_path in sorted(recipes_dir.rglob("*.gram")):
        metadata = _frontmatter(recipe_path)
        generation = metadata.get("image_generation")
        if not isinstance(generation, dict):
            continue

        prompt = generation.get("prompt_file")
        if not isinstance(prompt, str) or not prompt.strip():
            continue

        image = metadata.get("image")
        image = image.strip() if isinstance(image, str) else ""
        prompt_path = root / prompt
        image_path = root / "static" / image if image else None

        if image == PLACEHOLDER:
            findings.append(
                Finding(
                    recipe=recipe_path.relative_to(root).as_posix(),
                    image=image,
                    prompt_file=prompt,
                    status="placeholder",
                    message="prompt présent mais image encore sur le placeholder",
                )
            )
        elif image_path is None or not image_path.is_file():
            findings.append(
                Finding(
                    recipe=recipe_path.relative_to(root).as_posix(),
                    image=image,
                    prompt_file=prompt,
                    status="missing-image",
                    message="prompt présent mais fichier image introuvable",
                )
            )

        credit = metadata.get("image_credit")
        license_name = credit.get("license") if isinstance(credit, dict) else None
        if license_name == TEMPORARY_CREDIT:
            findings.append(
                Finding(
                    recipe=recipe_path.relative_to(root).as_posix(),
                    image=image,
                    prompt_file=prompt,
                    status="temporary-credit",
                    message="crédit d'illustration temporaire encore présent",
                )
            )
        elif license_name == GENERATED_CREDIT:
            asset_key = f"static/{image}" if image else ""
            record = manifest.get(asset_key)
            if not isinstance(record, dict):
                findings.append(
                    Finding(
                        recipe=recipe_path.relative_to(root).as_posix(),
                        image=image,
                        prompt_file=prompt,
                        status="missing-provenance",
                        message="illustration générée sans entrée de provenance",
                    )
                )
            elif record.get("recipe") != recipe_path.stem:
                findings.append(
                    Finding(
                        recipe=recipe_path.relative_to(root).as_posix(),
                        image=image,
                        prompt_file=prompt,
                        status="provenance-mismatch",
                        message="la recette du manifest ne correspond pas au fichier",
                    )
                )
            elif prompt_path.is_file() and record.get("prompt") != prompt_path.read_text(encoding="utf-8").strip():
                findings.append(
                    Finding(
                        recipe=recipe_path.relative_to(root).as_posix(),
                        image=image,
                        prompt_file=prompt,
                        status="provenance-prompt-mismatch",
                        message="le prompt du manifest diffère du prompt versionné",
                    )
                )
        if not prompt_path.is_file():
            findings.append(
                Finding(
                    recipe=recipe_path.relative_to(root).as_posix(),
                    image=image,
                    prompt_file=prompt,
                    status="missing-prompt",
                    message="fichier de prompt introuvable",
                )
            )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="racine du dépôt (défaut: répertoire courant)")
    parser.add_argument("--json", action="store_true", help="produire un inventaire JSON")
    parser.add_argument("--check", action="store_true", help="échouer si un cas à traiter est détecté")
    args = parser.parse_args(argv)

    try:
        findings = audit(args.root.resolve())
    except (OSError, yaml.YAMLError) as exc:
        print(f"Erreur pendant l'audit des images : {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    elif findings:
        for item in findings:
            print(f"{item.status}: {item.recipe} — {item.message} ({item.image or 'image non déclarée'})")
        print(f"{len(findings)} anomalie(s) d'image détectée(s).", file=sys.stderr)
    else:
        print("Aucune recette avec prompt stranded détectée.")

    return 1 if args.check and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
