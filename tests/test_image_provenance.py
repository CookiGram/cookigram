import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("audit_recipe_images", ROOT / "scripts/audit-recipe-images.py")
AUDIT = importlib.util.module_from_spec(SPEC)
import sys
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


class ImageProvenanceTests(unittest.TestCase):
    def test_generated_replacements_have_valid_provenance(self):
        findings = AUDIT.audit(ROOT)
        self.assertEqual(findings, [])

        manifest = yaml.safe_load((ROOT / AUDIT.PROVENANCE_MANIFEST).read_text(encoding="utf-8"))
        self.assertEqual(len(manifest), 15)
        self.assertEqual({record["recipe"] for record in manifest.values()}, {
            "air-fryer-pommes-terre-romarin",
            "air-fryer-poulet-paprika-herbes",
            "air-fryer-quesadillas-poulet-fromage",
            "air-fryer-saucisses-poivrons-oignons",
            "air-fryer-saumon-citron-aneth",
            "air-fryer-tofu-croustillant",
            "sheet-pan-fajitas-crevettes",
            "sheet-pan-feta-pois-chiches",
            "sheet-pan-filet-mignon-pommes-patates-douces",
            "sheet-pan-gnocchi-burrata",
            "sheet-pan-halloumi-pois-chiches-zaatar",
            "sheet-pan-poulet-citron-haricots-verts",
            "sheet-pan-poulet-shawarma",
            "sheet-pan-saucisses-toulouse-poivrons",
            "sheet-pan-saumon-brocoli-patate-douce",
        })

    def test_temporary_credit_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "recipes").mkdir()
            (root / "static/images").mkdir(parents=True)
            (root / "image-prompts").mkdir()
            (root / "static/images/test.webp").write_bytes(b"image")
            (root / "image-prompts/test.md").write_text("prompt\n", encoding="utf-8")
            (root / "recipes/test.gram").write_text(
                "---\nimage: images/test.webp\nimage_credit:\n  license: Illustration temporaire\nimage_generation: {prompt_file: image-prompts/test.md}\n---\n",
                encoding="utf-8",
            )
            statuses = {finding.status for finding in AUDIT.audit(root)}
            self.assertIn("temporary-credit", statuses)


if __name__ == "__main__":
    unittest.main()
