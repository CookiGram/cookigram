import importlib.util
import json
import re
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
    monkeypatch.delenv("CONTENT_SHA", raising=False)

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
    monkeypatch.delenv("CONTENT_SHA", raising=False)
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
    monkeypatch.delenv("CONTENT_SHA", raising=False)

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
    triggers = workflow.get("on", workflow[True])
    expected_ref = "${{ github.event_name == 'workflow_dispatch' && inputs.content_sha || github.event.workflow_run.head_sha }}"

    assert build["env"]["CONTENT_SHA"] == expected_ref
    assert build["env"]["CI_RUN_ID"] == "${{ github.event_name == 'workflow_dispatch' && inputs.ci_run_id || github.event.workflow_run.id }}"
    assert "workflow_dispatch" in triggers
    assert set(triggers["workflow_dispatch"]["inputs"]) == {"content_sha", "ci_run_id"}
    checkout = next(step for step in build["steps"] if step.get("name") == "Checkout CookiGram Recettes (Public)")
    assert checkout["with"]["ref"] == "${{ env.CONTENT_SHA }}"

    artifact = next(step for step in build["steps"] if step.get("name") == "Download exactly the qualified Pages artifact")
    assert artifact["with"]["run-id"] == "${{ env.CI_RUN_ID }}"
    provenance = next(step for step in build["steps"] if step.get("name") == "Verify qualified artifact provenance")
    assert 'provenance = json.loads(Path("_site/provenance.json")' in provenance["run"]
    assert '"qualifying_ci_run_id"' in provenance["run"]


def test_qualified_contract_version_matches_builder(tmp_path, monkeypatch) -> None:
    root = _repo(tmp_path)
    monkeypatch.delenv("CORE_SSH_KEY", raising=False)
    monkeypatch.delenv("CONTENT_SHA", raising=False)

    nominal = check_pins.check(root, remote=False)

    assert not any(item.code == "qualified-contract-mismatch" for item in nominal.findings)

    builder_path = root / ".builder.json"
    config = json.loads(builder_path.read_text(encoding="utf-8"))
    config["contract_version"] = "9.9.9"
    builder_path.write_text(json.dumps(config), encoding="utf-8")

    drifted = check_pins.check(root, remote=False)

    assert drifted.exit_code == 1
    assert any(item.code == "qualified-contract-mismatch" and item.status == "error" for item in drifted.findings)


def test_sync_dispatches_pages_with_validated_sha_and_ci_run() -> None:
    workflow = (ROOT / ".github/workflows/sync-core-pin.yml").read_text(encoding="utf-8")
    assert "gh workflow run pages.yml" in workflow
    assert "--field content_sha='${{ steps.candidate.outputs.sha }}'" in workflow
    assert "--field ci_run_id='${{ steps.main_ci.outputs.run_id }}'" in workflow


def _pinned_builder() -> dict:
    return json.loads((ROOT / ".builder.json").read_text(encoding="utf-8"))


def _pinned_manifest() -> dict:
    config = _pinned_builder()
    return {
        "core": {"source_sha": config["core_sha"]},
        "contract": {
            "identity": "cookigram-contract",
            "version": config["contract_version"],
            "source_sha": config["contract_source_sha"],
            "sha256": config["contract_sha256"],
        },
    }


def _ci_soudure_wired(workflow_text: str) -> bool:
    try:
        workflow = yaml.safe_load(workflow_text)
    except yaml.YAMLError:
        return False
    if not isinstance(workflow, dict):
        return False
    steps = workflow.get("jobs", {}).get("qualified-pages-artifact", {}).get("steps", [])
    extract = next(
        (
            step
            for step in steps
            if isinstance(step, dict) and step.get("name") == "Extract and verify Core + Contract bundle"
        ),
        None,
    )
    if extract is None:
        return False
    run = extract.get("run", "")
    return (
        "--check-manifest" in run
        and "--contract-source-sha" in run
        and "steps.builder.outputs.contract_source_sha" in run
    )


def test_manifest_soudure_nominale_passe_avec_pins_reels() -> None:
    config = _pinned_builder()

    findings = check_pins.verify_bundle_manifest(
        _pinned_manifest(),
        core_sha=config["core_sha"],
        contract_source_sha=config["contract_source_sha"],
    )

    assert [item for item in findings if item.status == "error"] == []


def test_manifest_soudure_contrat_divergent_invalide() -> None:
    config = _pinned_builder()
    manifest = _pinned_manifest()
    manifest["contract"]["source_sha"] = "f" * 40

    findings = check_pins.verify_bundle_manifest(
        manifest,
        core_sha=config["core_sha"],
        contract_source_sha=config["contract_source_sha"],
    )

    assert any(item.code == "manifest-contract-sha-mismatch" and item.status == "error" for item in findings)


def test_manifest_contrat_malforme_invalide() -> None:
    config = _pinned_builder()
    manifest = _pinned_manifest()
    manifest["contract"]["source_sha"] = "ad0a531"

    findings = check_pins.verify_bundle_manifest(
        manifest,
        core_sha=config["core_sha"],
        contract_source_sha=config["contract_source_sha"],
    )

    assert any(item.code == "manifest-invalid-contract-sha" and item.status == "error" for item in findings)


def test_manifest_core_divergent_invalide() -> None:
    config = _pinned_builder()
    manifest = _pinned_manifest()
    manifest["core"]["source_sha"] = "0" * 40

    findings = check_pins.verify_bundle_manifest(
        manifest,
        core_sha=config["core_sha"],
        contract_source_sha=config["contract_source_sha"],
    )

    assert any(item.code == "manifest-core-mismatch" and item.status == "error" for item in findings)


def test_ci_soudure_nominale() -> None:
    text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert _ci_soudure_wired(text)


def _private_contract_preinstalled(workflow_text: str) -> bool:
    try:
        workflow = yaml.safe_load(workflow_text)
    except yaml.YAMLError:
        return False
    if not isinstance(workflow, dict):
        return False
    steps = workflow.get("jobs", {}).get("private-integration", {}).get("steps", [])
    validation = next(
        (
            step
            for step in steps
            if isinstance(step, dict) and step.get("name") == "Validation avec CookiGram Core"
        ),
        None,
    )
    if validation is None:
        return False
    run = validation.get("run", "")
    marker = "pip install -e ./core"
    if marker not in run:
        return False
    head = run.split(marker)[0]
    if "cookigram-contract" not in head:
        return False
    if re.search(r"git\+https://\S+@[0-9a-f]{40}", head) is not None:
        return True
    if "steps.contract-ref.outputs.sha" not in head:
        return False
    contract_ref = next(
        (step for step in steps if isinstance(step, dict) and step.get("id") == "contract-ref"),
        None,
    )
    if contract_ref is None:
        return False
    source = contract_ref.get("run", "")
    return ".builder.json" in source and "contract_source_sha" in source


def test_private_contract_preinstall_nominal() -> None:
    text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert _private_contract_preinstalled(text)


def test_private_contract_preinstall_absent_invalide() -> None:
    text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)
    steps = workflow["jobs"]["private-integration"]["steps"]
    validation = next(step for step in steps if step.get("name") == "Validation avec CookiGram Core")
    validation["run"] = "python -m pip install --upgrade pip\npip install -e ./core"

    assert not _private_contract_preinstalled(yaml.safe_dump(workflow))


def test_ci_soudure_absente_invalide() -> None:
    text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)
    steps = workflow["jobs"]["qualified-pages-artifact"]["steps"]
    extract = next(step for step in steps if step.get("name") == "Extract and verify Core + Contract bundle")
    extract["run"] = "python scripts/check-pins.py --json"

    assert not _ci_soudure_wired(yaml.safe_dump(workflow))
