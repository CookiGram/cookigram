#!/usr/bin/env python3
"""Check the immutable references shared by the public and private pipelines.

The checker intentionally validates provenance metadata only.  Recipe parsing
belongs to ``cookigram-contract`` and the private Core, so this script does
not duplicate either parser.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml


SHA_RE = re.compile(r"^[0-9a-f]{40}$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
CONTRACT_REPO = "https://github.com/PierreCsn/cookigram-contract.git"
CORE_REPO = "git@github.com:CookiGram/cookigram-core.git"
WORKFLOWS = (Path(".github/workflows/ci.yml"), Path(".github/workflows/pages.yml"))
BUILDER_CONFIG = Path(".builder.json")


@dataclass
class Finding:
    code: str
    status: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    status: str
    exit_code: int
    pins: dict[str, str | None]
    findings: list[Finding]

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["findings"] = [asdict(item) for item in self.findings]
        return result


Runner = Callable[..., subprocess.CompletedProcess[str]]


def _run(*args: str, cwd: Path | None = None, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=check)


def _read_pin(root: Path, name: str, findings: list[Finding]) -> str | None:
    path = root / ".core-version"
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        findings.append(Finding("missing-core-pin", "error", f"Impossible de lire {path}: {exc}"))
        return None
    if not SHA_RE.fullmatch(value):
        findings.append(Finding("invalid-core-sha", "error", f"{path} ne contient pas un SHA Git de 40 caractères."))
        return None
    return value


def _workflow_data(root: Path, findings: list[Finding]) -> dict[Path, dict[str, Any]]:
    data: dict[Path, dict[str, Any]] = {}
    for relative in WORKFLOWS:
        path = root / relative
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            findings.append(Finding("invalid-workflow", "error", f"{relative}: {exc}"))
            continue
        if not isinstance(loaded, dict):
            findings.append(Finding("invalid-workflow", "error", f"{relative} ne contient pas un mapping YAML."))
            continue
        data[relative] = loaded
    return data


def _check_workflows(root: Path, data: dict[Path, dict[str, Any]], findings: list[Finding]) -> tuple[str | None, str | None]:
    try:
        core_pin = (root / ".core-version").read_text(encoding="utf-8").strip()
    except OSError:
        core_pin = None
    ci = data.get(WORKFLOWS[0], {})
    pages = data.get(WORKFLOWS[1], {})
    ci_env = ci.get("jobs", {}).get("recipe-check", {}).get("env", {})
    version = ci_env.get("CONTRACT_VERSION")
    contract_sha = ci_env.get("CONTRACT_SHA")
    if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        findings.append(Finding("invalid-contract-version", "error", "CI.CONTRACT_VERSION doit être une version semver simple."))
        version = None
    if not isinstance(contract_sha, str) or not SHA_RE.fullmatch(contract_sha):
        findings.append(Finding("invalid-contract-sha", "error", "CI.CONTRACT_SHA doit être un SHA Git de 40 caractères."))
        contract_sha = None

    for relative, workflow in data.items():
        try:
            text = (root / relative).read_text(encoding="utf-8")
        except OSError:
            text = ""
        core_job = workflow.get("jobs", {}).get("private-integration" if relative.name == "ci.yml" else "build", {})
        checkout = next((step for step in core_job.get("steps", []) if isinstance(step, dict) and step.get("uses") == "actions/checkout@v4" and step.get("with", {}).get("repository") == "CookiGram/cookigram-core"), None)
        if relative.name == "pages.yml" and (root / BUILDER_CONFIG).is_file():
            if isinstance(checkout, dict):
                findings.append(Finding("private-core-checkout-in-pages", "error", "pages.yml checkout encore le Core privé."))
            qualified_artifact = "actions/download-artifact@v4" in text and "run-id:" in text and "cookigram-pages-" in text
            public_builder = ".builder.json" in text and "sha256sum" in text and "releases/download" in text
            if not qualified_artifact and not public_builder:
                findings.append(Finding("public-builder-not-verified", "error", "pages.yml ne consomme pas un builder public piné et vérifié."))
        else:
            if not isinstance(checkout, dict) or checkout.get("with", {}).get("ref") != "${{ steps.core-ref.outputs.sha }}":
                findings.append(Finding("core-pin-not-used", "error", f"{relative} ne checkout pas Core avec la sortie du pin local."))
            if "core-version" not in text:
                findings.append(Finding("core-pin-not-read", "error", f"{relative} ne lit pas .core-version."))

    if pages and "CONTRACT_VERSION:" in str(pages):
        findings.append(Finding("duplicate-contract-pin", "error", "La version du contrat est définie hors du job public CI."))
    builder = root / BUILDER_CONFIG
    if builder.is_file():
        try:
            config = json.loads(builder.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(Finding("invalid-builder-config", "error", f"{BUILDER_CONFIG}: {exc}"))
        else:
            for key in ("release", "artifact", "sha256", "core_sha"):
                value = config.get(key)
                if not isinstance(value, str) or not value.strip():
                    findings.append(Finding("invalid-builder-config", "error", f"{BUILDER_CONFIG} ne contient pas `{key}`."))
            if isinstance(config.get("sha256"), str) and not re.fullmatch(r"[0-9a-f]{64}", config["sha256"]):
                findings.append(Finding("invalid-builder-sha256", "error", f"{BUILDER_CONFIG}.sha256 doit être un SHA256 hexadécimal."))
            if isinstance(config.get("core_sha"), str) and config.get("core_sha") != core_pin:
                findings.append(Finding("builder-core-mismatch", "error", "Le builder public ne correspond pas à .core-version.", {"builder": config.get("core_sha"), "core_pin": core_pin}))
            for key in ("contract_version", "contract_source_sha", "contract_artifact", "contract_sha256"):
                if key in config and (not isinstance(config[key], str) or not config[key].strip()):
                    findings.append(Finding("invalid-builder-config", "error", f"{BUILDER_CONFIG} contient une valeur Contract vide pour `{key}`."))
            if isinstance(config.get("contract_sha256"), str) and not re.fullmatch(r"[0-9a-f]{64}", config["contract_sha256"]):
                findings.append(Finding("invalid-builder-contract-sha256", "error", f"{BUILDER_CONFIG}.contract_sha256 doit être un SHA256 hexadécimal."))
    return version, contract_sha


def _git_sha(root: Path, args: tuple[str, ...], findings: list[Finding], code: str) -> str | None:
    result = _run("git", *args, cwd=root)
    value = result.stdout.strip()
    if result.returncode or not SHA_RE.fullmatch(value):
        findings.append(Finding(code, "error", result.stderr.strip() or "Git n'a pas renvoyé un SHA valide."))
        return None
    return value


def _remote_sha(repo: str, ref: str, runner: Runner, findings: list[Finding], code: str, expected: str | None = None) -> str | None:
    result = runner("git", "ls-remote", repo, ref) if ref else runner("git", "ls-remote", repo)
    if result.returncode:
        findings.append(Finding(code, "error", result.stderr.strip() or f"Référence distante introuvable: {ref}"))
        return None
    values = result.stdout.split()
    value = values[0] if values and ref else next(
        (item for item in values[::2] if item == expected),
        next((item for item in values[::2] if SHA_RE.fullmatch(item)), ""),
    )
    if not SHA_RE.fullmatch(value):
        findings.append(Finding(code, "error", f"Réponse distante invalide pour {ref or repo}."))
        return None
    return value


def check(root: Path, *, runner: Runner = _run, remote: bool = True) -> Report:
    findings: list[Finding] = []
    core_sha = _read_pin(root, "CORE_SHA", findings)
    workflows = _workflow_data(root, findings)
    contract_version, contract_sha = _check_workflows(root, workflows, findings)

    expected_content = os.environ.get("CONTENT_SHA", "").strip() or _git_sha(root, ("rev-parse", "HEAD"), findings, "missing-content-sha")
    if expected_content and not SHA_RE.fullmatch(expected_content):
        findings.append(Finding("invalid-content-sha", "error", "CONTENT_SHA doit être un SHA Git de 40 caractères."))
    actual_content = _git_sha(root, ("rev-parse", "HEAD"), findings, "missing-content-sha")
    if expected_content and actual_content and expected_content != actual_content:
        findings.append(Finding("content-sha-mismatch", "error", "CONTENT_SHA ne correspond pas au commit de contenu checkouté.", {"expected": expected_content, "actual": actual_content}))

    core_path = root / "core"
    if core_path.is_dir() and core_sha:
        actual_core = _git_sha(core_path, ("rev-parse", "HEAD"), findings, "missing-core-checkout")
        if actual_core and actual_core != core_sha:
            findings.append(Finding("core-sha-mismatch", "error", "Le Core checkouté ne correspond pas à .core-version.", {"expected": core_sha, "actual": actual_core}))
    elif os.environ.get("CORE_SSH_KEY", ""):
        _remote_sha(CORE_REPO, core_sha or "", runner, findings, "core-remote-unavailable")
    else:
        findings.append(Finding("core-remote-skipped", "info", "Core privé non vérifié : CORE_SSH_KEY absent (fork/PR publique)."))

    if remote and contract_version and contract_sha:
        actual_contract = _remote_sha(CONTRACT_REPO, "", runner, findings, "contract-remote-unavailable", expected=contract_sha)
        if actual_contract and actual_contract != contract_sha:
            findings.append(Finding("contract-sha-mismatch", "error", "Le tag du contrat public ne correspond pas à CONTRACT_SHA.", {"expected": contract_sha, "actual": actual_contract}))

    errors = [item for item in findings if item.status == "error"]
    return Report("fail" if errors else "pass", 1 if errors else 0, {"CORE_SHA": core_sha, "CONTENT_SHA": expected_content, "CONTRACT_VERSION": contract_version, "CONTRACT_SHA": contract_sha}, findings)


def _markdown(report: Report) -> str:
    lines = [f"# Pin check: **{report.status}**", "", "| Pin | Valeur |", "| --- | --- |"]
    lines.extend(f"| `{key}` | `{value or 'inconnu'}` |" for key, value in report.pins.items())
    lines.extend(["", "## Contrôles", ""])
    for finding in report.findings:
        lines.append(f"- `{finding.status}` `{finding.code}` — {finding.message}")
    if not report.findings:
        lines.append("- `ok` Toutes les références sont cohérentes.")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="rapport JSON")
    output.add_argument("--markdown", action="store_true", help="rapport Markdown")
    parser.add_argument("--no-remote", action="store_true", help="ne pas interroger les références publiques distantes")
    args = parser.parse_args(argv)
    try:
        report = check(args.root.resolve(), remote=not args.no_remote)
    except OSError as exc:
        print(f"Erreur pendant le contrôle des pins : {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    elif args.markdown:
        print(_markdown(report), end="")
    else:
        print(f"Pin check: {report.status}")
        for finding in report.findings:
            print(f"[{finding.status}] {finding.code}: {finding.message}")
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
