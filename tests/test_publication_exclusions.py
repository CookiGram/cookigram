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
        [sys.executable, str(SCRIPT), "--root", str(ROOT)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _fixture_root(tmp_path: Path) -> None:
    (tmp_path / ".gram").mkdir()
    (tmp_path / "recipes").mkdir()
    manifest = json.loads((ROOT / ".gram/publication-exclusions.json").read_text(encoding="utf-8"))
    (tmp_path / ".gram/publication-exclusions.json").write_text(json.dumps(manifest), encoding="utf-8")


def _run_gate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)],
        check=False,
        capture_output=True,
        text=True,
    )


def test_gate_rejects_excluded_slugs_even_without_recipe_content(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    manifest = json.loads((tmp_path / ".gram/publication-exclusions.json").read_text(encoding="utf-8"))
    for slug in manifest["excluded_recipe_slugs"]:
        (tmp_path / "recipes" / f"{slug}.gram").write_text("fixture", encoding="utf-8")

    result = _run_gate(tmp_path)
    assert result.returncode == 1
    for slug in manifest["excluded_recipe_slugs"]:
        assert f"recipes/{slug}.gram" in result.stdout


def test_gate_rejects_renamed_copies_by_stable_content_identity(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    renamed_copies = {
        "maison-du-foie-gras.gram": "---\ntitle: Terrine maison\ntags: [canard]\n---\n@foie-gras cru de canard{450 g}\nCuire sous vide.",
        "terrine-festive.gram": "---\ntitle: Preparation festive\n---\n@FOIE\u00a0GRAS cru de canard{450 g}\nCuire sous-vide.",
        "delice-canard.gram": "---\ntitle: Délice\n---\n@foie gras cru de canard{450 g}\nCuire au bain-marie.",
    }
    for filename, content in renamed_copies.items():
        (tmp_path / "recipes" / filename).write_text(content, encoding="utf-8")

    result = _run_gate(tmp_path)
    assert result.returncode == 1
    for filename in renamed_copies:
        assert f"recipes/{filename}" in result.stdout
    assert "excluded content identity: foie gras" in result.stdout


def test_gate_allows_legitimate_non_foie_gras_recipes(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    controls = {
        "foie-de-volaille-poele.gram": "---\ntitle: Foie de volaille poêlé\ntags: [volaille]\n---\n@foie de volaille{300 g}\nPoêler jusqu'à cuisson complète.",
        "magret-canard-sous-vide.gram": "---\ntitle: Magret de canard sous vide\ntags: [canard, sous-vide]\n---\n@magret de canard cru{400 g}\nCuire sous vide.",
        "pate-vegetal.gram": "---\ntitle: Pâté végétal\n---\n@lentilles{250 g}\nCuire puis mixer.",
    }
    for filename, content in controls.items():
        (tmp_path / "recipes" / filename).write_text(content, encoding="utf-8")

    result = _run_gate(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_gate_fails_closed_when_manifest_loses_identity_rule(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    manifest_path = tmp_path / ".gram/publication-exclusions.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["excluded_content_terms"] = []
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = _run_gate(tmp_path)
    assert result.returncode != 0


def test_every_catalogue_build_and_pages_deployment_runs_the_gate_first() -> None:
    import yaml

    ci = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    for name, job in ci["jobs"].items():
        steps = job.get("steps", [])
        protected_positions = [
            index for index, step in enumerate(steps)
            if any(marker in str(step.get("run", "")) for marker in (
                "generator.build", "generator.recipe_check", "cookigram_contract validate"
            ))
        ]
        for protected_position in protected_positions:
            assert any(
                "check-publication-exclusions.py" in str(step.get("run", ""))
                for step in steps[:protected_position]
            ), f"publication exclusion gate missing before content processing in CI job {name}"

    pages = yaml.safe_load((ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8"))
    pages_steps = pages["jobs"]["build"]["steps"]
    gate_positions = [
        i for i, step in enumerate(pages_steps)
        if "check-publication-exclusions.py" in str(step.get("run", ""))
    ]
    assert gate_positions, "publication exclusion gate missing from Pages workflow"
    for name in ("Download exactly the qualified Pages artifact", "Configure Pages", "Upload Pages Artifact", "Deploy to GitHub Pages"):
        target = next(i for i, step in enumerate(pages_steps) if step.get("name") == name)
        assert any(i < target for i in gate_positions), f"publication exclusion gate missing before {name}"
