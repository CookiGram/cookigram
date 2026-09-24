import importlib.util
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("compile_image_prompt", ROOT / "scripts/compile-image-prompt.py")
assert SPEC and SPEC.loader
compiler = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = compiler
SPEC.loader.exec_module(compiler)


def _profile() -> dict:
    return yaml.safe_load((ROOT / "assets/visual-profile/cookigram-v1.yaml").read_text(encoding="utf-8"))


def _run(*argv: str) -> tuple[int, str]:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = compiler.main(["--root", str(ROOT), *argv])
    return code, buffer.getvalue()


def test_profile_is_versioned() -> None:
    profile = _profile()
    assert profile["name"] == "cookigram"
    assert isinstance(profile["revision"], int) and profile["revision"] >= 1


def test_same_subject_same_revision_is_stable() -> None:
    profile = _profile()
    facts = compiler._recipe_facts(ROOT, "pizza-margherita")
    first = compiler.compile_prompt(profile, {"kind": "recipe", "slug": "pizza-margherita", **facts})
    second = compiler.compile_prompt(profile, {"kind": "recipe", "slug": "pizza-margherita", **facts})
    assert first == second
    assert "revision 1" in first


def test_recipe_categories_derive_only_from_facts() -> None:
    profile = _profile()
    cases = {
        "pizza-margherita": ["Margherita", "mozzarella"],
        "sushi-cake-thon-mangue-avocat": ["thon", "mangue"],
        "foret-noire-cyril-lignac": ["Forêt", "cerises"],
    }
    for slug, markers in cases.items():
        facts = compiler._recipe_facts(ROOT, slug)
        prompt = compiler.compile_prompt(profile, {"kind": "recipe", "slug": slug, **facts})
        for marker in markers:
            assert marker.lower() in prompt.lower(), (slug, marker)
        assert "truffe" not in prompt.lower()


def test_action_subjects_compile() -> None:
    profile = _profile()
    for action, context in (("cut", "board"), ("steam", "thermomix")):
        prompt = compiler.compile_prompt(profile, {"kind": "cooking_action", "action": action, "context": context})
        assert action in prompt and context in prompt


def test_cli_preview_and_json_fragment() -> None:
    code, out = _run("--recipe", "pizza-marinara")
    assert code == 0 and "Marinara" in out
    code, out = _run("--action", "cut", "--context", "board", "--format", "json")
    assert code == 0
    fragment = json.loads(out)
    assert fragment["subject"] == {"type": "cooking_action", "action": "cut", "context": "board"}
    assert fragment["visual_profile"] == {"name": "cookigram", "revision": 1}
    assert "cut" in fragment["prompt"]


def test_cli_rejects_unknown_recipe_and_missing_context() -> None:
    assert _run("--recipe", "no-such-recipe")[0] == 1
    assert _run("--action", "cut")[0] == 1
