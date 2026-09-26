import json
import re
import unittest
from pathlib import Path

from test_preregistration import PLAN, canonical_anchor_id, structural_slots


ROOT = Path(__file__).parent
DEV = json.loads((ROOT / "dev_set.json").read_text(encoding="utf-8"))
REPO = ROOT.parents[2]


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


class DevSetTests(unittest.TestCase):
    def test_dev_only_uses_preregistered_dev_documents(self) -> None:
        self.assertEqual(DEV["phase"], "dev-only")
        allowed = {entry["path"] for entry in PLAN["documents"]["dev"]}
        reserve = {entry["path"] for entry in PLAN["documents"]["holdout_reserve"]}
        paths = {item["anchor"]["path"] for item in DEV["items"]}
        self.assertTrue(paths <= allowed)
        self.assertTrue(paths.isdisjoint(reserve))
        self.assertFalse((ROOT / "holdout.json").exists())

    def test_dev_anchor_ids_and_keys_are_unique_and_stable(self) -> None:
        items = DEV["items"]
        ids = [item["id"] for item in items]
        anchors = [item["anchor"]["anchor_id"] for item in items]
        keys = [item["anchor"]["proposition_key"] for item in items]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(anchors), len(set(anchors)))
        self.assertEqual(len(keys), len(set(keys)))
        for item in items:
            self.assertEqual(
                item["anchor"]["anchor_id"],
                canonical_anchor_id(item["anchor"]["path"], item["anchor"]["section_index"]),
            )

    def test_each_anchor_is_grounded_in_its_dev_source_section(self) -> None:
        for item in DEV["items"]:
            path = item["anchor"]["path"]
            self.assertRegex(path, r"^[A-Za-z0-9_.-]+$")
            sections = h2_sections(path)
            matches = [
                (index, body)
                for index, (heading, body) in enumerate(sections, start=1)
                if heading == item["anchor"]["heading_path"][-1]
            ]
            self.assertEqual(len(matches), 1, item["id"])
            self.assertEqual(matches[0][0], item["anchor"]["section_index"], item["id"])
            self.assertIn(item["evidence"], matches[0][1], item["id"])
            self.assertTrue(item["question"].strip())
            self.assertTrue(item["answer"].strip())
            self.assertTrue(re.fullmatch(r"[a-z0-9]+(?:[.-][a-z0-9]+)*", item["anchor"]["proposition_key"]))

    def test_dev_capacity_coverage_and_zero_reserved_slot_overlap(self) -> None:
        # Réparation FREEZE_REPAIR_GO : 510-dev-002 (AGENTS.md::h2:2,
        # ancre H2-V) retiré sans remplacement ; 13 items restants.
        items = DEV["items"]
        self.assertEqual(len(items), 13)
        actual_by_doc: dict[str, int] = {}
        actual_doc_type: dict[tuple[str, str], int] = {}
        actual_by_type: dict[str, int] = {}
        for item in items:
            path = item["anchor"]["path"]
            actual_by_doc[path] = actual_by_doc.get(path, 0) + 1
            anchor_type = item["anchor_type"]
            actual_doc_type[(path, anchor_type)] = actual_doc_type.get((path, anchor_type), 0) + 1
            actual_by_type[anchor_type] = actual_by_type.get(anchor_type, 0) + 1
        self.assertEqual(actual_by_doc, {"AGENTS.md": 4, "README.en.md": 9})
        self.assertEqual(
            actual_by_type,
            {"fact": 4, "rule": 4, "workflow": 2, "definition": 1, "structure": 1, "navigation": 1},
        )
        self.assertEqual(
            actual_doc_type,
            {
                ("AGENTS.md", "fact"): 1,
                ("AGENTS.md", "rule"): 2,
                ("AGENTS.md", "workflow"): 1,
                ("README.en.md", "fact"): 3,
                ("README.en.md", "rule"): 2,
                ("README.en.md", "workflow"): 1,
                ("README.en.md", "definition"): 1,
                ("README.en.md", "structure"): 1,
                ("README.en.md", "navigation"): 1,
            },
        )

        dev_slots = set()
        for item in items:
            path = item["anchor"]["path"]
            heading = item["anchor"]["heading_path"][-1]
            titles = [title for title, _ in h2_sections(path)]
            self.assertEqual(titles.count(heading), 1)
            index = titles.index(heading) + 1
            dev_slots.add(canonical_anchor_id(path, index))
        reserve_slots = structural_slots("holdout_reserve")
        self.assertEqual(len(dev_slots), 13)
        self.assertTrue(dev_slots.isdisjoint(reserve_slots))

    def test_zero_508_anchor_reuse_verbatim_or_section(self) -> None:
        # Réparation FREEZE_REPAIR_GO : aucune ancre #508 dans les
        # champs dev, et aucun slot exclu (section contaminée).
        forbidden = json.loads(
            (ROOT / "forbidden_508.json").read_text(encoding="utf-8"))
        banned = [rec["anchor"] for rec in forbidden["anchors"]]
        self.assertEqual(len(banned), 75)
        excluded = set(PLAN["excluded_sections"])
        for item in DEV["items"]:
            self.assertNotIn(item["anchor"]["anchor_id"], excluded, item["id"])
            blob = "\n".join(
                [item["question"], item["answer"], item["evidence"]])
            for anchor in banned:
                self.assertNotIn(anchor, blob, (item["id"], anchor[:40]))


if __name__ == "__main__":
    unittest.main()
