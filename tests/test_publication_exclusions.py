import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check-publication-exclusions.py"
FOIE_GRAS_SLUGS = {
    "foie-gras-armagnac-quatre-epices-sous-vide",
    "foie-gras-nature-sous-vide",
    "foie-gras-poivre-vert-sous-vide",
    "foie-gras-sauternes-figue-sous-vide",
    "foie-gras-truffe-noire-sous-vide",
}


def test_sanitary_hold_recipes_are_absent_from_public_catalogue() -> None:
    manifest = json.loads((ROOT / ".gram/publication-exclusions.json").read_text(encoding="utf-8"))
    assert set(manifest["excluded_recipe_slugs"]) == FOIE_GRAS_SLUGS
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(ROOT), "--check"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_gate_rejects_any_excluded_recipe_added_to_catalogue(tmp_path: Path) -> None:
    (tmp_path / ".gram").mkdir()
    (tmp_path / "recipes").mkdir()
    manifest = json.loads((ROOT / ".gram/publication-exclusions.json").read_text(encoding="utf-8"))
    (tmp_path / ".gram/publication-exclusions.json").write_text(json.dumps(manifest), encoding="utf-8")
    for slug in manifest["excluded_recipe_slugs"]:
        (tmp_path / "recipes" / f"{slug}.gram").write_text("fixture", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--check"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    for slug in manifest["excluded_recipe_slugs"]:
        assert f"recipes/{slug}.gram" in result.stdout


def test_every_catalogue_build_and_pages_deployment_runs_the_gate_first() -> None:
    import yaml

    ci = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    for name, job in ci["jobs"].items():
        steps = job.get("steps", [])
        build_positions = [
            index for index, step in enumerate(steps)
            if "generator.build" in str(step.get("run", ""))
        ]
        for build_position in build_positions:
            assert any(
                "check-publication-exclusions.py --check" in str(step.get("run", ""))
                for step in steps[:build_position]
            ), f"publication exclusion gate missing before build in CI job {name}"

    pages = yaml.safe_load((ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8"))
    pages_steps = pages["jobs"]["build"]["steps"]
    deployment = next(i for i, step in enumerate(pages_steps) if step.get("name") == "Configure Pages")
    assert any(
        "check-publication-exclusions.py --check" in str(step.get("run", ""))
        for step in pages_steps[:deployment]
    ), "publication exclusion gate missing before Pages deployment"
