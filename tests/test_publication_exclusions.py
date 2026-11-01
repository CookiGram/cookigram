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
    (tmp_path / ".gram").mkdir(parents=True)
    (tmp_path / "recipes").mkdir()
    manifest = json.loads((ROOT / ".gram/publication-exclusions.json").read_text(encoding="utf-8"))
    (tmp_path / ".gram/publication-exclusions.json").write_text(json.dumps(manifest), encoding="utf-8")
    (tmp_path / ".gram/ingredients.yaml").write_text(
        """ingredients:
  foie-gras-de-canard-cru:
    name: Foie gras cru de canard
    aliases:
      - foie gras cru de canard
      - foie gras de canard cru
      - foie gras cru
  foie-de-volaille:
    name: Foie de volaille
    aliases:
      - foie de volaille
  foie-de-canard-frais:
    name: Foie de canard frais
    aliases:
      - foie de canard
  magret-de-canard:
    name: Magret de canard
    aliases:
      - magret de canard cru
  gras-de-canard:
    name: Gras de canard
    aliases:
      - gras de canard
  lentilles:
    name: Lentilles
    aliases:
      - lentilles
""",
        encoding="utf-8",
    )


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


def test_gate_rejects_full_recipe_copy_renamed_and_reworded_via_canonical_id(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    fixture = ROOT / "tests/fixtures/publication-exclusions/renamed-terrine-de-canard.gram"
    copy = tmp_path / "recipes/renamed-terrine-de-canard.gram"
    copy.parent.mkdir(exist_ok=True)
    copy.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")

    result = _run_gate(tmp_path)
    assert result.returncode == 1
    assert "recipes/renamed-terrine-de-canard.gram" in result.stdout
    assert "method fingerprint" in result.stdout


def test_gate_resolves_new_ingredient_aliases_to_blocked_canonical_id(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    registry_path = tmp_path / ".gram/ingredients.yaml"
    registry = registry_path.read_text(encoding="utf-8").replace(
        "      - foie gras cru\n", "      - foie gras cru\n      - foie de canard fermier\n"
    )
    registry_path.write_text(registry, encoding="utf-8")
    recipe = tmp_path / "recipes/terrine-paraphrase.gram"
    recipe.write_text(
        "---\ntitle: Terrine familiale\ntags: [canard]\n---\n@foie de canard fermier{450 g}\nCuire au bain-marie.",
        encoding="utf-8",
    )

    result = _run_gate(tmp_path)
    assert result.returncode == 1
    assert "excluded canonical ingredient identity" in result.stdout
    assert "foie de canard fermier" in result.stdout


def test_gate_rejects_full_copy_using_new_canonical_id_by_method_fingerprint(tmp_path: Path) -> None:
    formatting_variants = (
        ("500 mL", "^{55 degrees Celsius}", "80 minutes"),
        ("0.5 L", "^{131°F}", "1 h 20 min"),
    )
    for index, (volume, temperature, duration) in enumerate(formatting_variants):
        root = tmp_path / f"variant-{index}"
        _fixture_root(root)
        registry_path = root / ".gram/ingredients.yaml"
        registry = registry_path.read_text(encoding="utf-8") + """\n  foie-de-canard-fermier:
    name: Foie de canard fermier
    aliases:
      - foie de canard fermier
"""
        registry_path.write_text(registry, encoding="utf-8")
        fixture = ROOT / "tests/fixtures/publication-exclusions/renamed-terrine-de-canard.gram"
        recipe = root / "recipes/paraphrased/terrine-de-canard-fermier.gram"
        recipe.parent.mkdir(parents=True)
        altered_full_copy = (
            fixture.read_text(encoding="utf-8")
            .replace("500 ml", volume)
            .replace("^{55 C}", temperature)
            .replace("80 min", duration)
            .replace("@foie de canard{", "@foie de canard fermier{")
        )
        recipe.write_text(altered_full_copy, encoding="utf-8")

        result = _run_gate(root)
        assert result.returncode == 1, result.stdout + result.stderr
        assert "method fingerprint" in result.stdout


def test_gate_fails_closed_if_mandatory_canonical_id_is_removed_or_renamed(tmp_path: Path) -> None:
    for replacement in ("", "  foie-de-canard-fermier:\n    name: Foie gras cru de canard\n    aliases:\n      - foie gras cru de canard\n      - foie gras de canard cru\n      - foie gras cru\n    category: Viandes\n"):
        fixture_root = tmp_path / ("removed" if not replacement else "renamed")
        _fixture_root(fixture_root)
        registry_path = fixture_root / ".gram/ingredients.yaml"
        registry = registry_path.read_text(encoding="utf-8")
        old_entry = "  foie-gras-de-canard-cru:\n    name: Foie gras cru de canard\n    aliases:\n      - foie gras cru de canard\n      - foie gras de canard cru\n      - foie gras cru\n"
        registry_path.write_text(registry.replace(old_entry, replacement), encoding="utf-8")
        result = _run_gate(fixture_root)
        assert result.returncode != 0


def test_gate_fails_closed_on_protected_alias_collision(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    registry_path = tmp_path / ".gram/ingredients.yaml"
    registry_path.write_text(
        registry_path.read_text(encoding="utf-8") + """\n  foie-gras-alternate:
    name: Foie gras cru de canard
    aliases:
      - foie gras cru de canard
""",
        encoding="utf-8",
    )

    result = _run_gate(tmp_path)
    assert result.returncode != 0


def test_manifest_cannot_weaken_hardcoded_canonical_exclusion(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    manifest_path = tmp_path / ".gram/publication-exclusions.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["blocked_canonical_ingredient_ids"] = []
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    recipe = tmp_path / "recipes/terrine-fromage.gram"
    recipe.write_text(
        "---\ntitle: Terrine\n---\n@foie gras cru de canard{450 g}", encoding="utf-8"
    )

    result = _run_gate(tmp_path)
    assert result.returncode == 1
    assert "terrine-fromage.gram" in result.stdout


def test_gate_allows_legitimate_non_foie_gras_recipes(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    controls = {
        "foie-de-volaille-poele.gram": "---\ntitle: Foie de volaille poêlé\ntags: [volaille]\n---\n@foie de volaille{300 g}\nPoêler jusqu'à cuisson complète.",
        "magret-canard-sous-vide.gram": "---\ntitle: Magret de canard sous vide\ndescription: Une note rappelle le foie gras servi en accompagnement.\ntags: [canard, sous-vide]\n---\n@magret de canard cru{400 g}\nCuire sous vide.",
        "foie-de-canard-saute.gram": "---\ntitle: Foie de canard frais sauté\ntags: [canard]\n---\n@foie de canard{300 g}\nPoêler à la dernière minute.",
        "gras-de-canard.gram": "---\ntitle: Pommes de terre au gras de canard\n---\n@gras de canard{30 g}\nRôtir les pommes de terre.",
        "pate-vegetal.gram": "---\ntitle: Pâté végétal\n---\n@lentilles{250 g}\nCuire puis mixer.",
    }
    for filename, content in controls.items():
        (tmp_path / "recipes" / filename).write_text(content, encoding="utf-8")

    result = _run_gate(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_gate_fails_closed_if_manifest_omits_required_recipe_ids(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    manifest_path = tmp_path / ".gram/publication-exclusions.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["excluded_recipe_slugs"] = []
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = _run_gate(tmp_path)
    assert result.returncode != 0


def test_gate_fails_closed_if_ingredient_registry_is_malformed(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    (tmp_path / ".gram/ingredients.yaml").write_text("ingredients: []\n", encoding="utf-8")

    result = _run_gate(tmp_path)
    assert result.returncode != 0


def test_gate_fails_closed_if_mandatory_alias_is_removed(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    registry_path = tmp_path / ".gram/ingredients.yaml"
    registry_path.write_text(
        registry_path.read_text(encoding="utf-8").replace("      - foie gras cru de canard\n", "", 1),
        encoding="utf-8",
    )

    result = _run_gate(tmp_path)
    assert result.returncode != 0


def test_gate_fails_closed_on_duplicate_registry_keys(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    registry_path = tmp_path / ".gram/ingredients.yaml"
    registry_path.write_text(
        registry_path.read_text(encoding="utf-8") + """\n  foie-gras-de-canard-cru:
    name: Replaced alias entry
    aliases: []
""",
        encoding="utf-8",
    )

    result = _run_gate(tmp_path)
    assert result.returncode != 0


def test_every_catalogue_build_and_pages_deployment_runs_the_gate_first() -> None:
    import yaml

    ci = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    for name, job in ci["jobs"].items():
        steps = job.get("steps", [])
        commands = "\n".join(str(step.get("run", "")) for step in steps)
        gate_position = commands.find("check-publication-exclusions.py")
        protected = [marker for marker in (
            "generator.build", "generator.recipe_check", "cookigram_contract validate"
        ) if marker in commands]
        for marker in protected:
            assert gate_position >= 0 and gate_position < commands.find(marker), (
                f"publication exclusion gate missing before {marker} in CI job {name}"
            )
        if gate_position >= 0:
            assert "PyYAML==6.0.2" in commands[:gate_position], (
                f"PyYAML must be installed before ingredient identity resolution in CI job {name}"
            )

    pages = yaml.safe_load((ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8"))
    pages_steps = pages["jobs"]["build"]["steps"]
    gate_positions = [
        i for i, step in enumerate(pages_steps)
        if "check-publication-exclusions.py" in str(step.get("run", ""))
    ]
    assert gate_positions, "publication exclusion gate missing from Pages workflow"
    gate_position = next(i for i, step in enumerate(pages_steps) if "check-publication-exclusions.py" in str(step.get("run", "")))
    yaml_install = next(i for i, step in enumerate(pages_steps) if "PyYAML==6.0.2" in str(step.get("run", "")))
    assert yaml_install < gate_position, "PyYAML must be installed before ingredient identity resolution in Pages"
    for name in ("Download exactly the qualified Pages artifact", "Configure Pages", "Upload Pages Artifact", "Deploy to GitHub Pages"):
        target = next(i for i, step in enumerate(pages_steps) if step.get("name") == name)
        assert any(i < target for i in gate_positions), f"publication exclusion gate missing before {name}"
