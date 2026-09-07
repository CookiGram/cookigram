#!/usr/bin/env python3
"""Deterministic linter for public CookiGram recipe frontmatter."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
TRANSITIONAL_RULES = {"title-length", "description-length"}
DATE_KEY = re.compile(r"(?:^date$|_date$|_at$)", re.IGNORECASE)
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?$")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int | None
    rule: str
    level: str
    message: str


class DuplicateKeyError(yaml.YAMLError):
    def __init__(self, key: Any, line: int):
        super().__init__(f"clé YAML dupliquée: {key!r}")
        self.line = line


class NoDuplicateLoader(yaml.SafeLoader):
    """SafeLoader which does not silently overwrite duplicate mapping keys."""


def _mapping(loader: NoDuplicateLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise DuplicateKeyError(key, key_node.start_mark.line + 1)
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


NoDuplicateLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def _finding(path: Path, root: Path, line: int | None, rule: str, level: str, message: str) -> Finding:
    return Finding(path.relative_to(root).as_posix(), line, rule, level, message)


def _frontmatter(path: Path) -> tuple[str, int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("frontmatter YAML absent")
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as exc:
        raise ValueError("frontmatter YAML non fermé") from exc
    return "\n".join(lines[1:end]), 2


def _date_is_valid(value: Any) -> bool:
    if isinstance(value, (dt.date, dt.datetime)):
        return True
    if not isinstance(value, str) or not ISO_DATE.fullmatch(value):
        return False
    try:
        dt.date.fromisoformat(value[:10])
        if len(value) > 10:
            dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def lint_recipe(path: Path, root: Path, images: dict[str, Path], *, warn_only: bool = False) -> list[Finding]:
    try:
        raw, start_line = _frontmatter(path)
        data = yaml.load(raw, Loader=NoDuplicateLoader)
    except DuplicateKeyError as exc:
        return [_finding(path, root, 1 + exc.line, "duplicate-yaml-key", "error", str(exc))]
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [_finding(path, root, 1, "frontmatter", "error", str(exc))]

    if not isinstance(data, dict):
        return [_finding(path, root, start_line, "frontmatter", "error", "frontmatter YAML doit être un mapping")]

    findings: list[Finding] = []

    def add(rule: str, message: str, line: int | None = start_line) -> None:
        level = "warning" if warn_only and rule in TRANSITIONAL_RULES else "error"
        findings.append(_finding(path, root, line, rule, level, message))

    title = data.get("title")
    if "title" not in data or not isinstance(title, str) or not title.strip():
        add("required-field", "title doit être une chaîne non vide")
    if isinstance(title, str) and len(title.strip()) > 65:
        add("title-length", "title dépasse 65 caractères")
    description = data.get("description")
    if "description" not in data or not isinstance(description, str) or not description.strip():
        add("required-field", "description doit être une chaîne non vide")
    if isinstance(description, str) and not 50 <= len(description.strip()) <= 160:
        add("description-length", "description doit contenir entre 50 et 160 caractères")

    tags = data.get("tags")
    if "tags" not in data or not isinstance(tags, list) or not tags:
        add("required-field", "tags doit être une liste non vide")
    elif any(not isinstance(tag, str) or not tag.strip() for tag in tags):
        add("tags", "tags doit contenir uniquement des chaînes non vides")
    elif len({tag.strip().casefold() for tag in tags}) != len(tags):
        add("tags", "tags contient un doublon")

    image = data.get("image")
    if not isinstance(image, str) or not image.strip():
        add("image-path", "image doit être un chemin non vide")
    else:
        image = image.strip()
        if image in images and images[image] < path:
            add("image-path", f"chemin image dupliqué: {image}")

    def visit(value: Any, key: str = "") -> None:
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                visit(child_value, str(child_key))
        elif isinstance(value, list):
            for child_value in value:
                visit(child_value, key)
        elif DATE_KEY.search(key) and not _date_is_valid(value):
            add("date-format", f"date non ISO 8601 pour {key}")

    visit(data)
    return findings


def run(root: Path, *, warn_only: bool = False) -> dict[str, Any]:
    root = root.resolve()
    files = sorted(root.glob("recipes/*.gram"))
    images: dict[str, Path] = {}
    for path in files:
        try:
            raw, _ = _frontmatter(path)
            data = yaml.load(raw, Loader=NoDuplicateLoader)
        except (OSError, ValueError, yaml.YAMLError):
            continue
        image = data.get("image") if isinstance(data, dict) else None
        if isinstance(image, str) and image.strip():
            images.setdefault(image.strip(), path)
    findings = [finding for path in files for finding in lint_recipe(path, root, images, warn_only=warn_only)]
    errors = sum(finding.level == "error" for finding in findings)
    warnings = sum(finding.level == "warning" for finding in findings)
    return {"version": "1", "tool": "cookigram-public-content-lint", "files": len(files), "summary": {"errors": errors, "warnings": warnings, "status": "fail" if errors else "pass"}, "findings": [asdict(finding) for finding in findings]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true", help="produire le rapport JSON")
    parser.add_argument("--check", action="store_true", help="retourner 1 si une erreur est détectée")
    parser.add_argument("--warn-only", action="store_true", help="maintenir les règles transitoires en avertissement")
    args = parser.parse_args(argv)
    try:
        result = run(args.root, warn_only=args.warn_only)
    except (OSError, ValueError) as exc:
        print(f"Erreur pendant le lint: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for finding in result["findings"]:
            print(f"{finding['path']}:{finding['line']}: {finding['rule']} [{finding['level']}] {finding['message']}")
        print(f"{result['summary']['status']}: {len(result['findings'])} finding(s)")
    return 1 if args.check and result["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
