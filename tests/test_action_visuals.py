import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.action_visuals import (
    INSTANCE_ACTION_MAPPING,
    MUTUALIZED_ALIASES,
    audit_action_assets,
    resolve_action_asset,
    resolve_canonical_token,
)


class ActionVisualsContractTests(unittest.TestCase):
    def test_known_token_resolves_correct_asset(self):
        self.assertEqual(resolve_action_asset("cut", root=ROOT), "images/atomic-actions/cut.webp")
        self.assertEqual(resolve_action_asset("saute", root=ROOT), "images/atomic-actions/saute.webp")
        self.assertEqual(resolve_action_asset("simmer", root=ROOT), "images/atomic-actions/simmer.webp")
        self.assertEqual(resolve_action_asset("mix", root=ROOT), "images/atomic-actions/mix.webp")
        self.assertEqual(resolve_action_asset("whisk", root=ROOT), "images/atomic-actions/whisk.webp")
        self.assertEqual(resolve_action_asset("rest", root=ROOT), "images/atomic-actions/rest.webp")
        self.assertEqual(resolve_action_asset("knead", root=ROOT), "images/atomic-actions/knead.webp")

    def test_mutualized_aliases_resolve_to_canonical_assets(self):
        self.assertEqual(resolve_canonical_token("chop"), "cut")
        self.assertEqual(resolve_canonical_token("slice"), "cut")
        self.assertEqual(resolve_canonical_token("dice"), "cut")
        self.assertEqual(resolve_action_asset("chop", root=ROOT), "images/atomic-actions/cut.webp")
        self.assertEqual(resolve_action_asset("dice", root=ROOT), "images/atomic-actions/cut.webp")
        self.assertEqual(resolve_action_asset("emulsify", root=ROOT), "images/atomic-actions/whisk.webp")
        self.assertEqual(resolve_action_asset("sear", root=ROOT), "images/atomic-actions/saute.webp")

    def test_unknown_token_uses_fallback(self):
        self.assertEqual(resolve_action_asset("unknown_gesture", root=ROOT), "")
        self.assertEqual(resolve_action_asset("generic", root=ROOT), "")
        self.assertEqual(resolve_action_asset("", root=ROOT), "")

    def test_missing_asset_uses_fallback_gracefully(self):
        # A token that is theoretically in the mapping but missing on disk
        fake_token = "fake_action"
        try:
            INSTANCE_ACTION_MAPPING[fake_token] = "images/atomic-actions/missing_file.webp"
            self.assertEqual(resolve_action_asset(fake_token, root=ROOT), "")
        finally:
            INSTANCE_ACTION_MAPPING.pop(fake_token, None)

    def test_no_cookigram_visual_path_in_core(self):
        # Verify that Core cooking_actions module does not import or hardcode CookiGram instance paths
        import generator.cooking_actions as core_ca

        # Core defines ASSET_ROOT and COOKING_ACTIONS, but has zero CookiGram-specific image paths
        self.assertFalse(hasattr(core_ca, "INSTANCE_ACTION_MAPPING"))
        source = Path(core_ca.__file__).read_text(encoding="utf-8")
        self.assertNotIn("atomic-actions", source)
        self.assertNotIn("cut.webp", source)
        self.assertNotIn("CookiGram", source)

    def test_all_10_pilot_assets_exist_and_meet_budget(self):
        for token, rel_path in INSTANCE_ACTION_MAPPING.items():
            asset_file = ROOT / "static" / rel_path
            self.assertTrue(asset_file.is_file(), f"Asset {asset_file} must exist")
            size_kb = asset_file.stat().st_size / 1024
            self.assertLess(size_kb, 85, f"Asset {token} should be under 85KB, got {size_kb:.1f}KB")

    def test_manifest_matches_filesystem(self):
        issues = audit_action_assets(ROOT)
        errors = [i for i in issues if i.get("severity") == "error"]
        self.assertEqual(errors, [], f"Audit reported errors: {errors}")


if __name__ == "__main__":
    unittest.main()
