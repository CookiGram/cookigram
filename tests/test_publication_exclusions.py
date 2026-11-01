import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check-publication-exclusions.py"
spec = importlib.util.spec_from_file_location("publication_gate", SCRIPT)
gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gate)


def _manifest(root: Path, recipes: dict[str, bytes]) -> str:
    entries = {name: hashlib.sha256(content).hexdigest() for name, content in sorted(recipes.items())}
    raw = (json.dumps({"schema_version": 1, "recipes": entries}, indent=2) + "\n").encode()
    path = root / ".gram/approved-recipes.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    for name, content in recipes.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return hashlib.sha256(raw).hexdigest()


def test_unchanged_public_corpus_matches_pinned_baseline() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], check=False, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads((ROOT / ".gram/approved-recipes.json").read_text(encoding="utf-8"))
    actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / "recipes").rglob("*.gram")}
    assert set(manifest["recipes"]) == actual


def test_full_copy_renamed_and_reworded_is_rejected_by_path_inventory(tmp_path: Path) -> None:
    approved = {"recipes/legitimate.gram": b"---\ntitle: Approved\n---\n@duck{1 g}\n"}
    pinned = _manifest(tmp_path, approved)
    copy = (ROOT / "tests/fixtures/publication-exclusions/renamed-terrine-de-canard.gram").read_bytes()
    altered = copy.replace(b"bocal ouvert", b"bocal sans couvercle").replace(
        b"sac de cuisson sous vide", b"sac sous vide"
    ).replace(b"@foie de canard{", b"@foie de canard fermier{")
    (tmp_path / "recipes/terrine-reworded.gram").write_bytes(altered)

    findings = gate.validate(tmp_path, pinned)
    assert any("unapproved recipe path: recipes/terrine-reworded.gram" in item for item in findings)


def test_full_copy_over_existing_approved_path_is_rejected_by_content_hash(tmp_path: Path) -> None:
    path = "recipes/approved.gram"
    pinned = _manifest(tmp_path, {path: b"approved recipe\n"})
    (tmp_path / path).write_bytes(
        (ROOT / "tests/fixtures/publication-exclusions/renamed-terrine-de-canard.gram").read_bytes()
    )
    assert f"approved recipe content changed: {path}" in gate.validate(tmp_path, pinned)


def test_unmodified_approved_prose_quoting_method_terms_is_not_a_false_positive(tmp_path: Path) -> None:
    path = "recipes/editorial-note.gram"
    quoted_prose = (
        "---\ntitle: Note\n---\nCette recette compare les expressions bocal sans couvercle "
        "et sac sous vide, sans les appliquer.\n"
    ).encode()
    pinned = _manifest(tmp_path, {path: quoted_prose})
    assert gate.validate(tmp_path, pinned) == []


def test_added_recipe_requires_deliberate_baseline_update(tmp_path: Path) -> None:
    pinned = _manifest(tmp_path, {"recipes/approved.gram": b"approved\n"})
    (tmp_path / "recipes/new-recipe.gram").write_text("quoted method prose", encoding="utf-8")
    assert gate.validate(tmp_path, pinned) == ["unapproved recipe path: recipes/new-recipe.gram"]


def test_renamed_or_removed_approved_path_fails_closed(tmp_path: Path) -> None:
    old = "recipes/approved.gram"
    pinned = _manifest(tmp_path, {old: b"approved\n"})
    (tmp_path / old).rename(tmp_path / "recipes/renamed.gram")
    findings = gate.validate(tmp_path, pinned)
    assert f"unapproved recipe path: recipes/renamed.gram" in findings
    assert f"approved recipe is missing or renamed: {old}" in findings


def test_manifest_mutation_or_invalid_schema_fails_closed(tmp_path: Path) -> None:
    pinned = _manifest(tmp_path, {"recipes/approved.gram": b"approved\n"})
    manifest_path = tmp_path / ".gram/approved-recipes.json"
    manifest_path.write_text('{"schema_version":1,"recipes":{}}\n', encoding="utf-8")
    assert any(
        item.startswith("approved recipe manifest digest does not match the pinned value:")
        for item in gate.validate(tmp_path, pinned)
    )

    malformed = tmp_path / "bad"
    malformed_pin = _manifest(malformed, {"recipes/approved.gram": b"approved\n"})
    data = json.loads((malformed / ".gram/approved-recipes.json").read_text())
    data["recipes"] = []
    raw = (json.dumps(data) + "\n").encode()
    (malformed / ".gram/approved-recipes.json").write_bytes(raw)
    findings = gate.validate(malformed, hashlib.sha256(raw).hexdigest())
    assert any("invalid approved recipe manifest schema" in item for item in findings)


def test_recipe_hash_must_be_well_formed(tmp_path: Path) -> None:
    _manifest(tmp_path, {"recipes/approved.gram": b"approved\n"})
    path = tmp_path / ".gram/approved-recipes.json"
    data = json.loads(path.read_text())
    data["recipes"]["recipes/approved.gram"] = "not-a-hash"
    raw = (json.dumps(data) + "\n").encode()
    path.write_bytes(raw)
    findings = gate.validate(tmp_path, hashlib.sha256(raw).hexdigest())
    assert any("invalid recipe path or SHA-256" in item for item in findings)


def test_every_catalogue_build_and_pages_deployment_runs_the_gate_first() -> None:
    import yaml

    ci = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    for name, job in ci["jobs"].items():
        commands = "\n".join(str(step.get("run", "")) for step in job.get("steps", []))
        gate_position = commands.find("check-publication-exclusions.py")
        for marker in ("generator.build", "generator.recipe_check", "cookigram_contract validate"):
            if marker in commands:
                assert gate_position >= 0 and gate_position < commands.find(marker), (
                    f"publication gate missing before {marker} in CI job {name}"
                )

    pages = yaml.safe_load((ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8"))
    steps = pages["jobs"]["build"]["steps"]
    gate_positions = [i for i, step in enumerate(steps) if "check-publication-exclusions.py" in str(step.get("run", ""))]
    assert gate_positions, "publication gate missing from Pages workflow"
    for name in ("Download exactly the qualified Pages artifact", "Configure Pages", "Upload Pages Artifact", "Deploy to GitHub Pages"):
        target = next(i for i, step in enumerate(steps) if step.get("name") == name)
        assert any(i < target for i in gate_positions), f"publication gate missing before {name}"
