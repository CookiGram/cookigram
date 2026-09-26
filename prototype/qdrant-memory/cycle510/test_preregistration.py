import json
import unicodedata
import unittest
from pathlib import Path


ROOT = Path(__file__).parent
PLAN = json.loads((ROOT / "split_preregistration.json").read_text(encoding="utf-8"))


def _canonical_piece(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value).casefold()
    normalized = " ".join(normalized.split())
    return normalized.strip(" .,:;!?\"'`()[]{}")


def canonical_anchor_id(path: str, section_index: int) -> str:
    normalized_path = Path(path).as_posix()
    if section_index < 1:
        raise ValueError("H2 section index is one-based")
    return f"{normalized_path}::h2:{section_index}"


def assert_disjoint(dev_items: list[dict], holdout_items: list[dict]) -> None:
    dev_anchors = {item["anchor"]["anchor_id"] for item in dev_items}
    holdout_anchors = {item["anchor"]["anchor_id"] for item in holdout_items}
    dev_keys = {_canonical_piece(item["anchor"]["proposition_key"]) for item in dev_items}
    holdout_keys = {_canonical_piece(item["anchor"]["proposition_key"]) for item in holdout_items}
    if not dev_anchors.isdisjoint(holdout_anchors):
        raise ValueError("anchor overlap")
    if not dev_keys.isdisjoint(holdout_keys):
        raise ValueError("semantic proposition overlap")


def structural_slots(side: str) -> set[str]:
    return {
        f"{document['path']}::h2:{index}"
        for document in PLAN["documents"][side]
        for index in range(1, document["h2_sections"] + 1)
    }


class SplitPreregistrationTests(unittest.TestCase):
    def test_exception_is_local_and_holdout_is_not_materialized(self) -> None:
        self.assertEqual(PLAN["issue"], "CookiGram/cookigram#510")
        self.assertIn("local to #510", PLAN["exception_scope"])
        self.assertFalse(PLAN["holdout_created"])
        self.assertFalse(PLAN["measurement_started"])

    def test_fixed_document_split_has_useful_capacity_on_both_sides(self) -> None:
        dev = PLAN["documents"]["dev"]
        reserve = PLAN["documents"]["holdout_reserve"]
        self.assertEqual(sum(item["h2_sections"] for item in dev), 14)
        self.assertEqual(sum(item["h2_sections"] for item in reserve), 13)
        self.assertTrue(structural_slots("dev"))
        self.assertTrue(structural_slots("holdout_reserve"))
        self.assertTrue(structural_slots("dev").isdisjoint(structural_slots("holdout_reserve")))
        self.assertTrue(
            {item["path"] for item in dev}.isdisjoint({item["path"] for item in reserve})
        )

    def test_anchor_identity_ignores_prompt_rewording_and_row_identity(self) -> None:
        first = canonical_anchor_id("AGENTS.md", 2)
        rephrased = canonical_anchor_id("AGENTS.md", 2)
        different_section = canonical_anchor_id("AGENTS.md", 3)
        self.assertEqual(first, rephrased)
        self.assertNotEqual(first, different_section)

    def test_canonical_anchor_overlap_is_rejected(self) -> None:
        dev = [{"anchor": {"anchor_id": "AGENTS.md::h2:2", "proposition_key": "access.boundary"}}]
        paraphrased = [{"anchor": {"anchor_id": "GEMINI.md::h2:4", "proposition_key": "access.boundary"}}]
        with self.assertRaisesRegex(ValueError, "semantic proposition overlap"):
            assert_disjoint(dev, paraphrased)

    def test_forbidden_508_anchors_and_excluded_sections(self) -> None:
        # Réparation FREEZE_REPAIR_GO : 75 ancres interdites, 2 sections
        # exclues, capacités utilisables 13/12.
        forbidden = json.loads(
            (ROOT / "forbidden_508.json").read_text(encoding="utf-8"))
        self.assertEqual(forbidden["n"], 75)
        self.assertEqual(len(forbidden["anchors"]), 75)
        self.assertEqual(PLAN["forbidden_508_n"], 75)
        self.assertEqual(
            set(PLAN["excluded_sections"]),
            {"AGENTS.md::h2:2", ".agents/roles/README.md::h2:3"},
        )
        self.assertEqual(PLAN["usable_slots"], {"dev": 13, "holdout_reserve": 12})
        contaminated = {
            slot
            for rec in forbidden["anchors"]
            for slot in rec["occurrences_4docs"]
        }
        self.assertEqual(contaminated, set(PLAN["excluded_sections"]))

    def test_508_artifacts_unmutated_sha_tripwire(self) -> None:
        # Réparation FREEZE_REPAIR_GO : les 7 fichiers items #508 sont
        # épinglés ; toute mutation les invalide.
        import hashlib

        pins = {
            "abstention_labels.json": "c296a48ada8b517f",
            "agent_tasks.json": "751b05b4f6e0356b",
            "holdout.json": "b43a5e88872a5e53",
            "cycle2/c2_dev.json": "56b37957f5977fd",
            "cycle2/c2_holdout.json": "8194f3a055768041",
            "cycle2b/c2b_dev.json": "cc9da45bd3eaed91",
            "cycle2b/c2b_holdout.json": "dd98c28fbd282101",
        }
        c1 = ROOT.parent
        for rel, prefix in pins.items():
            digest = hashlib.sha256(
                (c1 / rel).read_bytes()).hexdigest()
            self.assertTrue(digest.startswith(prefix), rel)


if __name__ == "__main__":
    unittest.main()
