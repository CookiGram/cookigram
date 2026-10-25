"""Build reproducibility (#434).

Two builds of the same content commit must produce byte-identical
``provenance.json``: ``built_at`` derives from ``SOURCE_DATE_EPOCH`` (or the
content commit timestamp), never from the wall clock. CI actions must be
pinned by commit SHA and Python/Node dependencies by exact version.
"""

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github/workflows"
SPEC = importlib.util.spec_from_file_location(
    "write_provenance", ROOT / "scripts/write-provenance.py"
)
assert SPEC and SPEC.loader
write_provenance = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = write_provenance
SPEC.loader.exec_module(write_provenance)

CHECKED_WORKFLOWS = ("ci.yml", "pages.yml", "sync-core-pin.yml")
PINNED_PYTHON_DEPS = {
    "Pillow": "Pillow==11.3.0",
    "pytest": "pytest==8.3.5",
    "PyYAML": "PyYAML==6.0.2",
    "Jinja2": "Jinja2==3.1.6",
    "pip": "pip==25.3",
}
EPOCH = 1761300000
EPOCH_ISO = "2025-10-24T10:00:00+00:00"


def _base_env(**overrides: str) -> dict[str, str]:
    env = {
        "CONTENT_SHA": "0" * 40,
        "BUILDER_CORE_SHA": "1" * 40,
        "CONTRACT_VERSION": "1.1.0",
        "COOKIGRAM_CONTRACT_SHA": "2" * 40,
        "COOKIGRAM_CONTRACT_ARTIFACT": "cookigram_contract-1.1.0-py3-none-any.whl",
        "COOKIGRAM_CONTRACT_SHA256": "3" * 64,
        "BUILDER_RELEASE": "core-5c91478",
        "BUILDER_ARTIFACT": "cookigram-builder-5c91478.tar.gz",
        "BUILDER_SHA256": "4" * 64,
        "PAGES_ARTIFACT": "cookigram-pages-" + "0" * 40,
        "QUALIFYING_RUN_ID": "123456",
        "SOURCE_DATE_EPOCH": str(EPOCH),
    }
    env.update(overrides)
    return env


def test_provenance_honors_source_date_epoch() -> None:
    provenance = write_provenance.build_provenance(_base_env())
    assert provenance["built_at"] == EPOCH_ISO
    assert provenance["content_sha"] == "0" * 40


def test_provenance_deterministic_for_same_inputs() -> None:
    first = write_provenance.build_provenance(_base_env())
    second = write_provenance.build_provenance(_base_env())
    assert first == second
    assert json.dumps(first, indent=2) == json.dumps(second, indent=2)


def test_provenance_rejects_invalid_epoch(monkeypatch) -> None:
    for bad in ("not-a-number", "-12", "12.5"):
        monkeypatch.setenv("SOURCE_DATE_EPOCH", bad)
        try:
            write_provenance.resolve_epoch("0" * 40)
        except SystemExit:
            continue
        raise AssertionError(f"SOURCE_DATE_EPOCH={bad!r} should be rejected")


def test_provenance_falls_back_to_commit_timestamp(tmp_path, monkeypatch) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Tests"], cwd=tmp_path, check=True)
    (tmp_path / "recipe.gram").write_text("canon\n", encoding="utf-8")
    env = {"GIT_AUTHOR_DATE": "@1761300000 +0000", "GIT_COMMITTER_DATE": "@1761300000 +0000"}
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=tmp_path, check=True, env={**dict(__import__("os").environ), **env})
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path, check=True, capture_output=True, text=True).stdout.strip()
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    assert write_provenance.resolve_epoch(head) == EPOCH
    provenance = write_provenance.build_provenance(_base_env(CONTENT_SHA=head, SOURCE_DATE_EPOCH=""))
    # Empty SOURCE_DATE_EPOCH behaves as unset: commit timestamp wins.
    assert provenance["built_at"] == EPOCH_ISO


def test_write_provenance_end_to_end_deterministic(tmp_path, monkeypatch) -> None:
    site = tmp_path / "_site"
    for key, value in _base_env().items():
        monkeypatch.setenv(key, value)
    monkeypatch.chdir(tmp_path)
    assert write_provenance.main(["--site-dir", str(site)]) == 0
    first = (site / "provenance.json").read_bytes()
    assert write_provenance.main(["--site-dir", str(site)]) == 0
    second = (site / "provenance.json").read_bytes()
    assert first == second
    assert json.loads(first)["built_at"] == EPOCH_ISO


def _all_uses() -> list[tuple[str, str, str]]:
    found = []
    for name in CHECKED_WORKFLOWS:
        workflow = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))
        for job_name, job in (workflow.get("jobs") or {}).items():
            for step in (job.get("steps") or []):
                if isinstance(step, dict) and isinstance(step.get("uses"), str):
                    found.append((name, job_name, step["uses"]))
    assert found, "expected at least one `uses:` across checked workflows"
    return found


def test_workflows_pin_all_actions_by_sha() -> None:
    for name, job_name, uses in _all_uses():
        assert re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", uses), (
            f"{name} [{job_name}]: action `{uses}` must be pinned by commit SHA (#434)"
        )


def test_workflows_reference_human_readable_action_tags() -> None:
    text = "".join((WORKFLOWS / name).read_text(encoding="utf-8") for name in CHECKED_WORKFLOWS)
    # The major-version tag stays as a trailing comment so updates remain reviewable.
    assert re.search(r"actions/checkout@[0-9a-f]{40} # v4", text)
    assert re.search(r"actions/setup-python@[0-9a-f]{40} # v5", text)


def test_workflows_pin_pip_dependencies() -> None:
    for name in ("ci.yml", "pages.yml"):
        for lineno, line in enumerate((WORKFLOWS / name).read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#") or "pip install" not in stripped:
                continue
            if re.search(r"pip install --upgrade pip(\s|$|\"|')", stripped):
                assert "==" in stripped, f"{name}:{lineno}: pip upgrade must be pinned (#434)"
            for package, pinned in PINNED_PYTHON_DEPS.items():
                if package in stripped and package != "pip":
                    assert pinned in stripped, f"{name}:{lineno}: {package} must be pinned as {pinned} (#434)"
                    assert not re.search(rf"{package}(>=|<=|~=|>|<)", stripped), (
                        f"{name}:{lineno}: floating range for {package} (#434)"
                    )


def test_node_runtime_pinned_in_recipe_check() -> None:
    workflow = yaml.safe_load((WORKFLOWS / "ci.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["recipe-check"]["steps"]
    setup_node = next((s for s in steps if isinstance(s, dict) and str(s.get("uses", "")).startswith("actions/setup-node@")), None)
    assert setup_node is not None, "recipe-check must pin its Node runtime (#434)"
    assert re.fullmatch(r"actions/setup-node@[0-9a-f]{40}", setup_node["uses"])
    version = setup_node.get("with", {}).get("node-version", "")
    assert re.fullmatch(r"\d+\.\d+\.\d+", str(version)), f"node-version must be exact, got {version!r}"


def test_provenance_steps_avoid_wall_clock() -> None:
    text = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    assert "datetime.datetime.now" not in text
    assert text.count("scripts/write-provenance.py") == 2
    assert "SOURCE_DATE_EPOCH" in text
