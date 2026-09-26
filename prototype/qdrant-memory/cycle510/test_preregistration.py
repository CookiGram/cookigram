import hashlib
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


def canonical_anchor_id(path: str, heading_path: list[str], proposition_key: str) -> str:
    normalized_path = Path(path).as_posix()
    headings = " / ".join(_canonical_piece(part) for part in heading_path)
    key = _canonical_piece(proposition_key)
    payload = f"cookigram-anchor-v1\n{normalized_path}\n{headings}\n{key}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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
        first = canonical_anchor_id("AGENTS.md", ["Règles", "  Accès  "], "qdrant.access.boundary")
        rephrased = canonical_anchor_id("AGENTS.md", ["RÈGLES", "Accès"], "qdrant.access.boundary")
        different_proposition = canonical_anchor_id("AGENTS.md", ["Règles", "Accès"], "qdrant.access.claim")
        self.assertEqual(first, rephrased)
        self.assertNotEqual(first, different_proposition)

    def test_canonical_anchor_overlap_is_rejected(self) -> None:
        dev = {canonical_anchor_id("AGENTS.md", ["Règles"], "access.boundary")}
        holdout = {canonical_anchor_id("AGENTS.md", ["RÈGLES"], "access.boundary")}
        self.assertFalse(dev.isdisjoint(holdout))


if __name__ == "__main__":
    unittest.main()
