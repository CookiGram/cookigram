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
        # Pilot
        self.assertEqual(resolve_action_asset("cut", root=ROOT), "images/atomic-actions/cut.webp")
        self.assertEqual(resolve_action_asset("saute", root=ROOT), "images/atomic-actions/saute.webp")
        self.assertEqual(resolve_action_asset("simmer", root=ROOT), "images/atomic-actions/simmer.webp")
        self.assertEqual(resolve_action_asset("mix", root=ROOT), "images/atomic-actions/mix.webp")
        self.assertEqual(resolve_action_asset("whisk", root=ROOT), "images/atomic-actions/whisk.webp")
        self.assertEqual(resolve_action_asset("rest", root=ROOT), "images/atomic-actions/rest.webp")
        self.assertEqual(resolve_action_asset("knead", root=ROOT), "images/atomic-actions/knead.webp")
        # Lot P1
        self.assertEqual(resolve_action_asset("oven", root=ROOT), "images/atomic-actions/oven.webp")
        self.assertEqual(resolve_action_asset("boil", root=ROOT), "images/atomic-actions/boil.webp")
        self.assertEqual(resolve_action_asset("assemble", root=ROOT), "images/atomic-actions/assemble.webp")
        self.assertEqual(resolve_action_asset("steam", root=ROOT), "images/atomic-actions/steam.webp")
        self.assertEqual(resolve_action_asset("season", root=ROOT), "images/atomic-actions/season.webp")
        self.assertEqual(resolve_action_asset("air_fry", root=ROOT), "images/atomic-actions/air_fry.webp")
        self.assertEqual(resolve_action_asset("blend", root=ROOT), "images/atomic-actions/blend.webp")
        # Lot P2
        self.assertEqual(resolve_action_asset("grate", root=ROOT), "images/atomic-actions/grate.webp")
        self.assertEqual(resolve_action_asset("roll_out", root=ROOT), "images/atomic-actions/roll_out.webp")
        self.assertEqual(resolve_action_asset("peel", root=ROOT), "images/atomic-actions/peel.webp")

    def test_mutualized_aliases_resolve_to_canonical_assets(self):
        self.assertEqual(resolve_canonical_token("chop"), "cut")
        self.assertEqual(resolve_canonical_token("slice"), "cut")
        self.assertEqual(resolve_canonical_token("dice"), "cut")
        self.assertEqual(resolve_action_asset("chop", root=ROOT), "images/atomic-actions/cut.webp")
        self.assertEqual(resolve_action_asset("dice", root=ROOT), "images/atomic-actions/cut.webp")
        self.assertEqual(resolve_action_asset("emulsify", root=ROOT), "images/atomic-actions/whisk.webp")
        self.assertEqual(resolve_action_asset("sear", root=ROOT), "images/atomic-actions/saute.webp")
        # P1 aliases
        self.assertEqual(resolve_canonical_token("preheat"), "oven")
        self.assertEqual(resolve_canonical_token("bake"), "oven")
        self.assertEqual(resolve_canonical_token("blanch"), "boil")
        self.assertEqual(resolve_canonical_token("layer"), "assemble")
        self.assertEqual(resolve_canonical_token("varoma"), "steam")
        self.assertEqual(resolve_canonical_token("salt"), "season")
        self.assertEqual(resolve_canonical_token("puree"), "blend")
        self.assertEqual(resolve_action_asset("preheat", root=ROOT), "images/atomic-actions/oven.webp")
        self.assertEqual(resolve_action_asset("varoma", root=ROOT), "images/atomic-actions/steam.webp")
        self.assertEqual(resolve_action_asset("puree", root=ROOT), "images/atomic-actions/blend.webp")
        # P2 aliases
        self.assertEqual(resolve_canonical_token("zest"), "grate")
        self.assertEqual(resolve_canonical_token("microplane"), "grate")
        self.assertEqual(resolve_canonical_token("roll_dough"), "roll_out")
        self.assertEqual(resolve_canonical_token("rolling_pin"), "roll_out")
        self.assertEqual(resolve_canonical_token("vegetable_peel"), "peel")
        self.assertEqual(resolve_canonical_token("econome"), "peel")
        self.assertEqual(resolve_action_asset("zest", root=ROOT), "images/atomic-actions/grate.webp")
        self.assertEqual(resolve_action_asset("rolling_pin", root=ROOT), "images/atomic-actions/roll_out.webp")
        self.assertEqual(resolve_action_asset("econome", root=ROOT), "images/atomic-actions/peel.webp")

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

    def test_instance_visual_mapping_stays_local_to_public_catalogue(self):
        source = (ROOT / "scripts/action_visuals.py").read_text(encoding="utf-8")
        self.assertIn("INSTANCE_ACTION_MAPPING", source)
        self.assertIn("images/atomic-actions/cut.webp", source)
        self.assertNotIn("import generator.", source)
        self.assertNotIn("from generator.", source)

    def test_all_20_assets_exist_and_meet_budget(self):
        self.assertEqual(len(INSTANCE_ACTION_MAPPING), 20)
        for token, rel_path in INSTANCE_ACTION_MAPPING.items():
            asset_file = ROOT / "static" / rel_path
            self.assertTrue(asset_file.is_file(), f"Asset {asset_file} must exist")
            size_kb = asset_file.stat().st_size / 1024
            self.assertLess(size_kb, 80, f"Asset {token} should be under 80KB, got {size_kb:.1f}KB")

    def test_manifest_matches_filesystem(self):
        issues = audit_action_assets(ROOT)
        errors = [i for i in issues if i.get("severity") == "error"]
        self.assertEqual(errors, [], f"Audit reported errors: {errors}")

    def test_all_20_svg_wrappers_exist_and_are_non_empty(self):
        # The SVG wrappers are shipped Core-bridge fallbacks; a missing
        # wrapper used to leave the whole suite green (proven by mutation
        # on peel.svg, issue #416).
        wrappers = ROOT / "static/illustrations/cooking-actions/v1"
        self.assertTrue(wrappers.is_dir(), f"SVG wrapper dir {wrappers} must exist")
        on_disk = {p.name for p in wrappers.glob("*.svg")}
        expected = {f"{token}.svg" for token in INSTANCE_ACTION_MAPPING}
        self.assertEqual(on_disk, expected, "SVG wrappers must match mapping 1:1")
        for token in INSTANCE_ACTION_MAPPING:
            wrapper = wrappers / f"{token}.svg"
            self.assertTrue(wrapper.is_file(), f"SVG wrapper {wrapper} must exist")
            self.assertGreater(wrapper.stat().st_size, 0, f"SVG wrapper {token} must not be empty")


if __name__ == "__main__":
    unittest.main()
