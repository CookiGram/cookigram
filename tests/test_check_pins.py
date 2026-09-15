import importlib.util
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_pins", ROOT / "scripts/check-pins.py")
assert SPEC and SPEC.loader
check_pins = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_pins
SPEC.loader.exec_module(check_pins)


def _repo(tmp_path: Path) -> Path:
    (tmp_path / ".github/workflows").mkdir(parents=True)
    for relative in (".core-version", ".builder.json", ".github/workflows/ci.yml", ".github/workflows/pages.yml"):
        destination = tmp_path / relative
        destination.write_text((ROOT / relative).read_text(encoding="utf-8"), encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Tests"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=tmp_path, check=True)
    return tmp_path


def test_fork_report_passes_without_private_core(tmp_path, monkeypatch) -> None:
    root = _repo(tmp_path)
    monkeypatch.delenv("CORE_SSH_KEY", raising=False)

    report = check_pins.check(root, remote=False)

    assert report.exit_code == 0
    actual = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
    assert report.pins["CONTENT_SHA"] == actual
    assert any(item.code == "core-remote-skipped" for item in report.findings)


def test_content_pin_mismatch_is_explicit(tmp_path, monkeypatch) -> None:
    root = _repo(tmp_path)
    monkeypatch.setenv("CONTENT_SHA", "0" * 40)

    report = check_pins.check(root, remote=False)

    assert report.exit_code == 1
    assert any(item.code == "content-sha-mismatch" for item in report.findings)


def test_contract_remote_sha_is_checked(tmp_path, monkeypatch) -> None:
    root = _repo(tmp_path)
    monkeypatch.delenv("CORE_SSH_KEY", raising=False)
    calls = []

    def fake_runner(*args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "b567e88acdcee69302c926caa6f5222508b7a051\tref\n", "")

    report = check_pins.check(root, runner=fake_runner)

    assert report.exit_code == 0
    assert calls == [("git", "ls-remote", check_pins.CONTRACT_REPO, "refs/tags/v1.0.0^{}")]


def test_contract_remote_sha_mismatch_is_explicit(tmp_path, monkeypatch) -> None:
    root = _repo(tmp_path)
    monkeypatch.delenv("CORE_SSH_KEY", raising=False)

    def fake_runner(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0, "0" * 40 + "\tref\n", "")

    report = check_pins.check(root, runner=fake_runner)

    assert report.exit_code == 1
    assert any(item.code == "contract-sha-mismatch" for item in report.findings)


def test_invalid_core_pin_fails_before_remote_lookup(tmp_path) -> None:
    root = _repo(tmp_path)
    (root / ".core-version").write_text("not-a-sha\n", encoding="utf-8")

    report = check_pins.check(root, remote=False)

    assert report.exit_code == 1
    assert any(item.code == "invalid-core-sha" for item in report.findings)


def test_pages_provenance_uses_the_checked_out_content_sha() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8"))
    build = workflow["jobs"]["build"]
    expected_ref = "${{ github.event.workflow_run.head_sha }}"

    assert build["env"]["CONTENT_SHA"] == expected_ref
    checkout = next(step for step in build["steps"] if step.get("name") == "Checkout CookiGram Recettes (Public)")
    assert checkout["with"]["ref"] == "${{ env.CONTENT_SHA }}"

    artifact = next(step for step in build["steps"] if step.get("name") == "Download exactly the qualified Pages artifact")
    assert artifact["with"]["run-id"] == "${{ github.event.workflow_run.id }}"
    provenance = next(step for step in build["steps"] if step.get("name") == "Verify qualified artifact provenance")
    assert 'provenance = json.loads(Path("_site/provenance.json")' in provenance["run"]
    assert '"qualifying_ci_run_id"' in provenance["run"]
