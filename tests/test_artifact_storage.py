"""Stockage des artefacts Actions (#482).

La CI doit valider `_site` sur les PR sans conserver le build complet, réserver
l'artefact Pages aux runs qualifiés sur `main`, et nettoyer après déploiement.
"""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github/workflows"


def _load(name: str) -> dict:
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def _steps(workflow: dict, job: str) -> list:
    return workflow["jobs"][job]["steps"]


def test_site_build_and_verification_still_run_unconditionally() -> None:
    steps = _steps(_load("ci.yml"), "qualified-pages-artifact")
    by_name = {step.get("name"): step for step in steps if isinstance(step, dict)}
    for name in ("Build qualified static site once", "Verify generated site and write qualification provenance"):
        assert name in by_name, f"missing validation step: {name}"
        assert "if" not in by_name[name], f"{name} must run on PRs too (#482)"


def test_site_upload_reserved_to_qualified_main_runs() -> None:
    steps = _steps(_load("ci.yml"), "qualified-pages-artifact")
    uploads = [step for step in steps if isinstance(step, dict) and step.get("uses") == "actions/upload-artifact@v4"]
    assert len(uploads) == 1
    upload = uploads[0]
    assert upload["with"]["path"] == "_site"
    assert upload["with"]["retention-days"] == 1
    condition = upload.get("if", "")
    assert "refs/heads/main" in condition
    assert "pull_request" in condition


def test_no_other_general_artifact_upload_in_ci() -> None:
    text = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    assert text.count("actions/upload-artifact@") == 1


def test_pages_still_consumes_qualified_artifact_then_cleans_up() -> None:
    workflow = _load("pages.yml")
    steps = _steps(workflow, "build")
    by_name = {step.get("name"): step for step in steps if isinstance(step, dict)}

    download = by_name["Download exactly the qualified Pages artifact"]
    assert download["with"]["run-id"] == "${{ env.CI_RUN_ID }}"

    assert "Upload Pages Artifact" in by_name  # requis par le déploiement Pages

    cleanup = by_name["Delete consumed qualified artifact"]
    assert cleanup.get("continue-on-error") is True
    run = cleanup.get("run", "")
    assert "DELETE" in run and "actions/artifacts" in run
    assert "cookigram-pages-" in run


def test_pages_can_delete_consumed_artifacts() -> None:
    workflow = _load("pages.yml")
    assert workflow["permissions"]["actions"] == "write"


def test_sync_workflow_uploads_no_artifact() -> None:
    text = (WORKFLOWS / "sync-core-pin.yml").read_text(encoding="utf-8")
    assert "actions/upload-artifact@" not in text
