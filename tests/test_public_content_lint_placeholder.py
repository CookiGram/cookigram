import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("public_content_lint_placeholder", ROOT / "scripts/lint-public-content.py")
LINTER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = LINTER
SPEC.loader.exec_module(LINTER)


def _write_recipe(root: Path, name: str, image: str) -> None:
    (root / "recipes").mkdir(exist_ok=True)
    (root / "recipes" / f"{name}.gram").write_text(
        "---\n"
        f"title: Recette de test {name}\n"
        "description: Une description de test suffisamment longue pour le frontmatter public.\n"
        "tags: [test]\n"
        f"image: {image}\n"
        "---\n"
        "[Tester]\n"
        "- Tester.\n",
        encoding="utf-8",
    )


class PlaceholderImageLintTests(unittest.TestCase):
    def test_shared_placeholder_is_not_a_duplicate_image(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_recipe(root, "one", "images/placeholder-recipe.jpg")
            _write_recipe(root, "two", "images/placeholder-recipe.jpg")

            result = LINTER.run(root)

        self.assertEqual(result["summary"]["errors"], 0)

    def test_shared_regular_image_remains_a_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_recipe(root, "one", "images/shared.jpg")
            _write_recipe(root, "two", "images/shared.jpg")

            result = LINTER.run(root)

        self.assertEqual(result["summary"]["errors"], 1)
        self.assertEqual(result["findings"][0]["rule"], "image-path")


if __name__ == "__main__":
    unittest.main()
