import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("public_content_lint", ROOT / "scripts/lint-public-content.py")
LINTER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = LINTER
SPEC.loader.exec_module(LINTER)


class PublicContentLintTests(unittest.TestCase):
    def test_public_corpus_is_deterministically_clean_except_seo_advisories(self) -> None:
        result = LINTER.run(ROOT, warn_only=True)
        self.assertEqual(result["files"], 162)
        self.assertEqual(result["summary"]["errors"], 0)
        self.assertGreater(result["summary"]["warnings"], 0)
        self.assertEqual(json.dumps(result, ensure_ascii=False), json.dumps(LINTER.run(ROOT, warn_only=True), ensure_ascii=False))
        self.assertTrue(all(not item["path"].startswith("/") for item in result["findings"]))


    def test_duplicate_yaml_key_is_a_blocking_error(self) -> None:
        result = LINTER.run(ROOT / "tests/fixtures/public-content-lint/duplicate")
        self.assertEqual(result["summary"]["errors"], 1)
        self.assertEqual(result["findings"][0]["rule"], "duplicate-yaml-key")
        self.assertEqual(result["summary"]["errors"], 1)
        warning_result = LINTER.run(ROOT / "tests/fixtures/public-content-lint/duplicate", warn_only=True)
        self.assertEqual(warning_result["summary"]["errors"], 1)
        self.assertEqual(warning_result["findings"][0]["level"], "error")


    def test_invalid_date_and_duplicate_tag_are_reported(self) -> None:
        result = LINTER.run(ROOT / "tests/fixtures/public-content-lint/invalid")
        rules = {item["rule"] for item in result["findings"]}
        self.assertTrue({"tags", "date-format"} <= rules)

    def test_image_paths_and_seo_thresholds_are_deterministic(self) -> None:
        fixture = ROOT / "tests/fixtures/public-content-lint/invalid"
        result = LINTER.run(fixture)
        self.assertEqual(result["summary"]["errors"], 3)
        self.assertEqual({item["rule"] for item in result["findings"]}, {"tags", "date-format", "image-path"})
        duplicate_image = LINTER.run(ROOT / "tests/fixtures/public-content-lint/image-duplicate")
        self.assertEqual(duplicate_image["summary"]["errors"], 1)
        self.assertEqual(duplicate_image["findings"][0]["rule"], "image-path")

    def test_check_exit_codes(self) -> None:
        script = ROOT / "scripts/lint-public-content.py"
        strict = subprocess.run(["python", str(script), "--root", "tests/fixtures/public-content-lint/duplicate", "--check"], cwd=ROOT)
        report = subprocess.run(["python", str(script), "--root", "tests/fixtures/public-content-lint/duplicate", "--check", "--warn-only"], cwd=ROOT)
        self.assertEqual(strict.returncode, 1)
        self.assertEqual(report.returncode, 1)

    def test_production_transition_blocks_duplicate_but_warns_seo_lengths(self) -> None:
        duplicate = subprocess.run(
            ["python", str(ROOT / "scripts/lint-public-content.py"), "--root", "tests/fixtures/public-content-lint/duplicate", "--check", "--warn-only"],
            cwd=ROOT,
        )
        transition = LINTER.run(ROOT / "tests/fixtures/public-content-lint/transition", warn_only=True)
        self.assertEqual(duplicate.returncode, 1)
        self.assertEqual(transition["summary"]["errors"], 0)
        self.assertEqual({finding["level"] for finding in transition["findings"]}, {"warning"})

    def test_production_invocation_returns_json_findings(self) -> None:
        completed = subprocess.run(
            ["python", str(ROOT / "scripts/lint-public-content.py"), "--check", "--warn-only", "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(set(report), {"version", "tool", "files", "summary", "findings"})
        self.assertTrue(all(set(finding) == {"path", "line", "rule", "level", "message"} for finding in report["findings"]))
        self.assertEqual(report["summary"]["errors"], 0)


if __name__ == "__main__":
    unittest.main()
