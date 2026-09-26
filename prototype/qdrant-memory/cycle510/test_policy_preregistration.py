import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parent
PLAN = json.loads((ROOT / "split_preregistration.json").read_text(encoding="utf-8"))
POLICY = json.loads((ROOT / "policy_preregistration.json").read_text(encoding="utf-8"))
NEGS = json.loads((ROOT / "dev_negatives.json").read_text(encoding="utf-8"))
DEV = json.loads((ROOT / "dev_set.json").read_text(encoding="utf-8"))
REPO = ROOT.parents[2]

SLOT_KEYS = {"anchor", "anchor_id", "path", "section", "section_index",
             "heading_path", "slot", "slots", "evidence", "answer"}
EXPECTED_IDS = {f"510-neg-{i:03d}" for i in range(1, 9)}


def corpus_blobs() -> list[str]:
    docs = ([d["path"] for d in PLAN["documents"]["dev"]]
            + [d["path"] for d in PLAN["documents"]["holdout_reserve"]])
    return [(REPO / p).read_text(encoding="utf-8").casefold() for p in docs]


class PolicyPreregistrationTests(unittest.TestCase):
    def test_prereg_files_grid_and_rule_serialized_before_measure(self) -> None:
        self.assertTrue((ROOT / "policy-amendment.md").is_file())
        self.assertTrue((ROOT / "dev_negatives.json").is_file())
        self.assertTrue((ROOT / "c510_calibrate_policy.py").is_file())
        self.assertEqual(
            POLICY["grid"]["taus"], [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6])
        self.assertEqual(POLICY["grid"]["deltas"], [0.01, 0.02, 0.03, 0.05])
        self.assertEqual(POLICY["grid"]["n_configs"], 28)
        self.assertEqual(POLICY["selection"]["primary_arm"], "dense_fact")
        self.assertTrue(
            POLICY["selection"]["key"].startswith("decision_lenient"))
        self.assertEqual(len(POLICY["selection"]["tiebreaks"]), 2)
        self.assertIn("tau superieur", POLICY["selection"]["tiebreaks"][0])
        self.assertIn("delta superieur", POLICY["selection"]["tiebreaks"][1])
        amendment = (ROOT / "policy-amendment.md").read_text(encoding="utf-8")
        for section in range(1, 9):
            self.assertIn(f"## {section}.", amendment)
        self.assertFalse(PLAN["holdout_created"])
        self.assertFalse((ROOT / "holdout.json").exists())

    def test_negatives_identity_and_zero_slot_consumption(self) -> None:
        items = NEGS["items"]
        self.assertEqual(NEGS["expected"], "abstain")
        self.assertEqual({it["id"] for it in items}, EXPECTED_IDS)
        kinds = [it["kind"] for it in items]
        self.assertEqual(kinds.count("ood"), 6)
        self.assertEqual(kinds.count("trap"), 2)
        for item in items:
            self.assertTrue(item["query"].strip())
            self.assertTrue(item["rationale"].strip())
            self.assertTrue(SLOT_KEYS.isdisjoint(item.keys()), item["id"])
        keys = [it["proposition_key"] for it in items]
        self.assertEqual(len(keys), len(set(keys)))
        for key in keys:
            self.assertTrue(
                re.fullmatch(r"[a-z0-9]+(?:[.-][a-z0-9]+)*", key), key)
        dev_keys = {it["anchor"]["proposition_key"] for it in DEV["items"]}
        self.assertTrue(set(keys).isdisjoint(dev_keys))

    def test_absent_terms_truly_absent_from_closed_corpus(self) -> None:
        blobs = corpus_blobs()
        self.assertEqual(len(blobs), 4)
        for item in NEGS["items"]:
            self.assertTrue(item["absent_terms"], item["id"])
            for term in item["absent_terms"]:
                folded = term.casefold()
                self.assertTrue(folded.strip(), (item["id"], term))
                for blob in blobs:
                    self.assertNotIn(folded, blob, (item["id"], term))

    def test_no_508_anchor_reuse_in_negatives(self) -> None:
        forbidden = json.loads(
            (ROOT / "forbidden_508.json").read_text(encoding="utf-8"))
        banned = [rec["anchor"] for rec in forbidden["anchors"]]
        self.assertEqual(len(banned), 75)
        for item in NEGS["items"]:
            blob = "\n".join([item["query"], item["rationale"]])
            for anchor in banned:
                self.assertNotIn(anchor, blob, (item["id"], anchor[:40]))

    def test_grid_selection_is_totally_ordered(self) -> None:
        pairs = {(tau, delta)
                 for tau in POLICY["grid"]["taus"]
                 for delta in POLICY["grid"]["deltas"]}
        self.assertEqual(len(pairs), 28)

    def test_positive_inputs_frozen_and_pins_match(self) -> None:
        frozen = json.loads(
            (ROOT / "510_calibration.json").read_text(encoding="utf-8"))
        self.assertEqual(frozen["phase"], "dev-calibration-retrieval-only")
        self.assertEqual(len(frozen["items"]), 13)
        for row in frozen["items"]:
            self.assertTrue(row["dense_fact"]["scores"], row["id"])
            self.assertTrue(row["dense_sec"]["scores"], row["id"])
        pins = POLICY["inputs"]["corpora_pins_verified_equal"]
        self.assertEqual(pins["section_sha"],
                         frozen["corpora"]["section_sha"])
        self.assertEqual(pins["fact_sha"], frozen["corpora"]["fact_sha"])
        self.assertEqual(pins["section_chunks"],
                         frozen["corpora"]["section_chunks"])
        self.assertEqual(pins["fact_chunks"],
                         frozen["corpora"]["fact_chunks"])


if __name__ == "__main__":
    unittest.main()
