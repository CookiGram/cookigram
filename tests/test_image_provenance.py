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
        self.assertEqual(len(manifest), 98)  # 62 + 36 (#493 wave)
        self.assertEqual({
            record.get("recipe") or record.get("subject", {}).get("recipe")
            for record in manifest.values()
            if record.get("recipe") or record.get("subject", {}).get("recipe")
        }, {
            "air-fryer-pommes-terre-romarin",
            "air-fryer-poulet-paprika-herbes",
            "air-fryer-quesadillas-poulet-fromage",
            "air-fryer-saucisses-poivrons-oignons",
            "air-fryer-saumon-citron-aneth",
            "air-fryer-tofu-croustillant",
            "overnight-oats-banane-cacahuete-chia",
            "overnight-oats-myrtille-citron-chia",
            "overnight-oats-pomme-cannelle-chia",
            "nettoyage-bol-thermomix-tm31",
            "sheet-pan-chou-fleur-pois-chiches-tahini",
            "sheet-pan-fajitas-crevettes",
            "sheet-pan-feta-pois-chiches",
            "sheet-pan-filet-mignon-pommes-patates-douces",
            "sheet-pan-gnocchi-burrata",
            "sheet-pan-halloumi-pois-chiches-zaatar",
            "sheet-pan-poulet-citron-haricots-verts",
            "sheet-pan-poulet-shawarma",
            "sheet-pan-saucisses-toulouse-poivrons",
            "sheet-pan-saumon-brocoli-patate-douce",
            "hachis-parmentier",
            "quiche-lorraine",
            "ratatouille",
            "sushi-cake-chirashi",
            "sushi-cake-double-saumon",
            "sushi-cake-philadelphia",
            "sushi-cake-saumon-aburi",
            "sushi-cake-saumon-thon-concombre-oeuf",
            "sushi-cake-saumon-fume-shiitake",
            "sushi-cake-thon-epice-crabe-saumon",
            "sushi-cake-thon-mangue-avocat",
            "sushi-cake-thon-mayonnaise-avocat",
            "sushi-cake-vegetarien",
            "onigiri-saumon-grille-sesame",
            "onigiri-tuna-mayo-japonais",
            "onigiri-poulet-miso-gingembre",
            "onigiri-kombu-sesame",
            "onigiri-umeboshi-shiso-sesame",
            "acras-de-morue",
            "aioli-citron-capres",
            "bretzels-maison",
            "calzone-aux-legumes",
            "cannelloni-epinards-ricotta-citron",
            "cheese-naan-indien",
            "chutney-mangue-pomme",
            "colombo-de-legumes-a-la-mangue",
            "crackers-aux-graines",
            "fougasse-au-levain",
            "gnocchi-romaine-miel-noix-gorgonzola",
            "guacamole-classique",
            "houmous-classique",
            "koftas-de-boeuf",
            "mayonnaise-aux-herbes",
            "moussaka-de-lentilles",
            "pain-de-mie-maison",
            "polenta-poireau-bleu-auvergne",
            "poulet-korma-safran-raisins",
            "sauce-tomate-herbes",
            "tapenade-noire",
            "tempura-de-legumes",
            "tortillas-de-ble-maison",
            "tzatziki-grec",
            # #493 wave (36)
            "beurre-blanc",
            "bouillon-de-legumes",
            "bouillon-de-volaille",
            "caramel-beurre-sale",
            "caviar-aubergine",
            "champignons-farcis",
            "chutney-cacahuetes",
            "chutney-coco",
            "chutney-coriandre-piment",
            "chutney-dattes-tamarin",
            "chutney-tamarin",
            "creme-anglaise-vanille",
            "creme-patissiere-vanille",
            "fond-brun-de-viande",
            "ganache-chocolat",
            "gougeres-fromage",
            "madeleines-salees",
            "minicanneles-chorizo",
            "mini-quiches",
            "oeufs-mimosa",
            "onion-bhaji",
            "pate-a-choux",
            "pate-a-crepes",
            "pate-a-gaufres",
            "pate-a-pancakes",
            "pate-a-pizza",
            "pate-brisee",
            "pate-sablee",
            "pesto-basilic",
            "puree-pommes-de-terre",
            "raita-concombre-menthe",
            "rillettes-thon-herbes",
            "sables-parmesan-sesame",
            "sauce-bechamel",
            "sauce-hollandaise",
            "sauce-mayonnaise",
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

    def _action_root(self, directory: str, record: dict) -> Path:
        import hashlib

        root = Path(directory)
        (root / "recipes").mkdir()
        (root / "static/illustrations/cooking-actions/v1").mkdir(parents=True)
        asset = root / "static/illustrations/cooking-actions/v1/cut-board.webp"
        asset.write_bytes(b"action")
        digest = hashlib.sha256(b"action").hexdigest()
        manifest = {"static/illustrations/cooking-actions/v1/cut-board.webp": {"sha256": digest, **record}}
        (root / "assets/provenance").mkdir(parents=True)
        (root / "assets/provenance/images.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
        return root

    def _new_style_record(self, **overrides) -> dict:
        record = {
            "origin": "generated",
            "subject": {"type": "cooking_action", "action": "cut", "context": "board"},
            "generation": {
                "tool": "agy",
                "provider": "google",
                "model": "unknown",
                "batch": "cooking-actions-v1-pilot-01",
                "visual_profile": {"name": "cookigram", "revision": 1},
            },
            "generated_at": "2026-09-20",
            "prompt": "manga culinary illustration, cut on board",
            "attribution": "CookiGram",
        }
        record.update(overrides)
        return record

    def test_cooking_action_subject_with_full_generation_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._action_root(directory, self._new_style_record())
            self.assertEqual(AUDIT.audit(root), [])

    def test_generation_block_requires_tool_and_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            record = self._new_style_record()
            record["generation"] = {"provider": "google", "model": "unknown",
                                    "visual_profile": {"name": "cookigram", "revision": 1}}
            root = self._action_root(directory, record)
            codes = {finding.prompt_file for finding in AUDIT.audit(root)}
            self.assertIn("incomplete-generation", codes)

    def test_unknown_model_is_explicit_and_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._action_root(directory, self._new_style_record())
            findings = AUDIT.audit(root)
            self.assertNotIn("incomplete-generation", {finding.prompt_file for finding in findings})

    def test_recipe_subject_form_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            import hashlib

            from PIL import Image as PILImage

            root = Path(directory)
            (root / "recipes").mkdir()
            (root / "static/images").mkdir(parents=True)
            (root / "recipes/soup.gram").write_text("---\ntitle: Soup\nimage: images/soup.png\n---\n", encoding="utf-8")
            PILImage.new("RGB", (4, 4)).save(root / "static/images/soup.png")
            digest = hashlib.sha256((root / "static/images/soup.png").read_bytes()).hexdigest()
            manifest = {"static/images/soup.png": {
                "origin": "generated", "subject": {"type": "recipe", "recipe": "soup"},
                "generator": "image_gen", "generated_at": "2026-09-20",
                "prompt": "soup", "sha256": digest, "attribution": "CookiGram"}}
            (root / "assets/provenance").mkdir(parents=True)
            (root / "assets/provenance/images.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
            self.assertEqual(AUDIT.audit(root), [])

    def test_nested_corrupt_missing_and_orphan_images_are_audited(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "recipes/nested/deeper").mkdir(parents=True)
            (root / "static/images/nested").mkdir(parents=True)
            (root / "static/images/placeholder-recipe.jpg").write_bytes(b"placeholder")
            (root / "static/images/nested/corrupt.webp").write_bytes(b"not an image")
            (root / "static/images/nested/orphan.webp").write_bytes(b"not an image")
            (root / "static/images/nested/directory-only").mkdir()
            (root / "recipes/nested/deeper/corrupt.gram").write_text(
                "---\nimage: images/nested/corrupt.webp\n---\n", encoding="utf-8"
            )
            (root / "recipes/nested/deeper/missing.gram").write_text(
                "---\nimage: images/nested/missing.webp\n---\n", encoding="utf-8"
            )

            findings = AUDIT.audit(root)
            statuses = {finding.status for finding in findings}
            self.assertIn("corrupt-image", statuses)
            self.assertIn("missing-image", statuses)
            self.assertIn("orphan-image", statuses)
            self.assertEqual(
                [finding.image for finding in findings if finding.status == "orphan-image"],
                ["images/nested/orphan.webp"],
            )


if __name__ == "__main__":
    unittest.main()
