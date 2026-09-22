from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

MARKERS = (
    "--strict-atomic",
    "compare/",
    "pull_request.base.sha",
    "event.before",
    "recipes/",
)


def _strict_gate_wired(workflow_text: str) -> bool:
    try:
        workflow = yaml.safe_load(workflow_text)
    except yaml.YAMLError:
        return False
    if not isinstance(workflow, dict):
        return False
    steps = workflow.get("jobs", {}).get("qualified-pages-artifact", {}).get("steps", [])
    for step in steps:
        if not isinstance(step, dict):
            continue
        body = yaml.safe_dump(step)
        if all(marker in body for marker in MARKERS):
            return True
    return False


def test_strict_gate_nominal() -> None:
    text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert _strict_gate_wired(text)


def test_strict_gate_absent_invalide() -> None:
    text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)
    steps = workflow["jobs"]["qualified-pages-artifact"]["steps"]
    workflow["jobs"]["qualified-pages-artifact"]["steps"] = [
        step for step in steps if "--strict-atomic" not in step.get("run", "")
    ]

    assert not _strict_gate_wired(yaml.safe_dump(workflow))
