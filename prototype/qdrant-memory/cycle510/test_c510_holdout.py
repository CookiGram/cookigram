import hashlib
import json
import re
import unittest
from pathlib import Path

from test_preregistration import PLAN, assert_disjoint, canonical_anchor_id


ROOT = Path(__file__).parent
HOLD = json.loads((ROOT / "510_holdout.json").read_text(encoding="utf-8"))
DEV = json.loads((ROOT / "dev_set.json").read_text(encoding="utf-8"))
NEGS = json.loads((ROOT / "dev_negatives.json").read_text(encoding="utf-8"))
FREEZE = json.loads((ROOT / "510_freeze.json").read_text(encoding="utf-8"))
REPO = ROOT.parents[2]

EXPECTED_IDS = {f"510-hold-{i:03d}" for i in range(1, 13)}
EXPECTED_SLOTS = ({f"GEMINI.md::h2:{i}" for i in range(1, 11)}
                  | {".agents/roles/README.md::h2:1",
                     ".agents/roles/README.md::h2:2"})


def h2_sections(path: str) -> list[tuple[str, str]]:
    text = (REPO / path).read_text(encoding="utf-8")
    sections: list[tuple[str, list[str]]] = []
    current_title = ""
    current_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current_title:
                sections.append((current_title, current_lines))
            current_title, current_lines = line[3:].strip(), []
        elif current_title:
            current_lines.append(line)
    if current_title:
        sections.append((current_title, current_lines))
    return [(title, "\n".join(lines)) for title, lines in sections]


class HoldoutTests(unittest.TestCase):
    def test_exactly_12_preregistered_reserve_slots(self) -> None:
        self.assertEqual(HOLD["phase"], "holdout")
        items = HOLD["items"]
        self.assertEqual({it["id"] for it in items}, EXPECTED_IDS)
        anchors = {it["anchor"]["anchor_id"] for it in items}
        self.assertEqual(anchors, EXPECTED_SLOTS)
        excluded = set(PLAN["excluded_sections"])
        self.assertTrue(anchors.isdisjoint(excluded))
        by_doc: dict[str, int] = {}
        for it in items:
            path = it["anchor"]["path"]
            by_doc[path] = by_doc.get(path, 0) + 1
        self.assertEqual(by_doc, {"GEMINI.md": 10,
                                  ".agents/roles/README.md": 2})

    def test_each_anchor_grounded_in_its_section(self) -> None:
        for item in HOLD["items"]:
            path = item["anchor"]["path"]
            sections = h2_sections(path)
            matches = [
                (index, body)
                for index, (heading, body) in enumerate(sections, start=1)
                if heading == item["anchor"]["heading_path"][-1]
            ]
            self.assertEqual(len(matches), 1, item["id"])
            self.assertEqual(matches[0][0],
                             item["anchor"]["section_index"], item["id"])
            self.assertEqual(
                item["anchor"]["anchor_id"],
                canonical_anchor_id(path, item["anchor"]["section_index"]),
                item["id"])
            self.assertIn(item["evidence"], matches[0][1], item["id"])
            self.assertTrue(item["question"].strip(), item["id"])
            self.assertTrue(item["answer"].strip(), item["id"])
            self.assertTrue(re.fullmatch(
                r"[a-z0-9]+(?:[.-][a-z0-9]+)*",
                item["anchor"]["proposition_key"]), item["id"])

    def test_ids_anchors_keys_unique_and_disjoint_from_dev_and_negs(self) -> None:
        items = HOLD["items"]
        self.assertEqual(len({it["id"] for it in items}), 12)
        self.assertEqual(
            len({it["anchor"]["anchor_id"] for it in items}), 12)
        keys = [it["anchor"]["proposition_key"] for it in items]
        self.assertEqual(len(keys), len(set(keys)))
        assert_disjoint(DEV["items"], items)
        neg_keys = {it["proposition_key"] for it in NEGS["items"]}
        self.assertTrue(set(keys).isdisjoint(neg_keys))

    def test_no_508_anchor_reuse_verbatim(self) -> None:
        forbidden = json.loads(
            (ROOT / "forbidden_508.json").read_text(encoding="utf-8"))
        banned = [rec["anchor"] for rec in forbidden["anchors"]]
        self.assertEqual(len(banned), 75)
        for item in HOLD["items"]:
            blob = "\n".join(
                [item["question"], item["answer"], item["evidence"]])
            for anchor in banned:
                self.assertNotIn(anchor, blob, (item["id"], anchor[:40]))

    def test_freeze_point_cells_and_input_identities(self) -> None:
        self.assertEqual(FREEZE["config"]["point"],
                         {"tau": 0.6, "delta": 0.03,
                          "dev_decision_lenient_fact": 0.905})
        self.assertEqual(FREEZE["config"]["policy_arm"],
                         "dense_fact (primaire, precedent c2b), "
                         "dense_sec au meme point (secondaire)")
        self.assertIn("A2_sec_policy", FREEZE["config"]["cells"])
        self.assertIn("B2_fact_policy", FREEZE["config"]["cells"])
        self.assertTrue(FREEZE["config"]["no_recalibration"])
        self.assertTrue(FREEZE["config"]["no_retuning"])
        for rel, want in FREEZE["inputs_sha16"].items():
            digest = hashlib.sha256(
                (ROOT / rel).read_bytes()).hexdigest()[:16]
            self.assertEqual(digest, want, rel)


if __name__ == "__main__":
    unittest.main()
