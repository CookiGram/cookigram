"""Tests deterministes du freeze methodologique #510 (stdlib, sans Qdrant).

Verifient : les 4 docs admissibles (dans les 18, jamais golds #508),
le pool de 51 ancres (unicite 1-nouveau/0-ancien, grounding au gold,
disjonction des 75 ancres #508), le split aveugle (partition exacte,
dev 27 / reserve 24, disjointes). Aucune mesure, aucun tuning.
"""

import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
C1 = HERE.parent
ROOT = HERE.parent.parent.parent


def load_history_sets():
    golds, anchors = set(), set()
    for f in ("abstention_labels.json", "agent_tasks.json", "holdout.json",
              "cycle2/c2_dev.json", "cycle2/c2_holdout.json",
              "cycle2b/c2b_dev.json", "cycle2b/c2b_holdout.json"):
        d = json.loads((C1 / f).read_text(encoding="utf-8"))
        for it in d["items"]:
            golds.update(it.get("golds", []))
            if it.get("gold"):
                golds.add(it["gold"])
            anchors.update(it.get("anchors", []))
            if it.get("anchor"):
                anchors.add(it["anchor"])
    return golds, anchors


class TestFreeze(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fz = json.loads((HERE / "a510_method_freeze.json").read_text(
            encoding="utf-8"))
        paths18 = json.loads((C1 / "cycle2b/c2b_method_freeze.json")
                             .read_text(encoding="utf-8"))["new_paths"]
        cls.new_whole = "\n".join(
            (ROOT / p).read_text(encoding="utf-8") for p in paths18)
        cls.old_whole = "\n".join(
            p.read_text(encoding="utf-8")
            for p in (ROOT / "docs").rglob("*.md")) + "\n" + (
            ROOT / "decisions" /
            "PDR-0010-nutrition-plaisir-sante-meal-planning.md").read_text(
            encoding="utf-8")
        cls.golds508, cls.anchors508 = load_history_sets()

    def test_docs_admissibles(self):
        docs = self.fz["admissible_docs"]
        self.assertEqual(len(docs), 4)
        for g in docs:
            self.assertTrue((ROOT / g).is_file(), g)
            self.assertNotIn(g, self.golds508, g)

    def test_pool_51_valide(self):
        pool = self.fz["split"]["dev"] + self.fz["split"]["reserve"]
        self.assertEqual(self.fz["pool_n"], 51)
        self.assertEqual(len(pool), 51)
        for r in pool:
            a, g = r["anchor"], r["gold"]
            self.assertIn(g, self.fz["admissible_docs"], (a, g))
            self.assertIn(a, (ROOT / g).read_text(encoding="utf-8"), (a, g))
            self.assertEqual(self.new_whole.count(a), 1, a)
            self.assertEqual(self.old_whole.count(a), 0, a)
            self.assertNotIn(a, self.anchors508, a)

    def test_split_partition(self):
        dev = self.fz["split"]["dev"]
        res = self.fz["split"]["reserve"]
        self.assertEqual((len(dev), len(res)), (27, 24))
        da = {r["anchor"] for r in dev}
        ra = {r["anchor"] for r in res}
        self.assertEqual(len(da), 27)
        self.assertEqual(len(ra), 24)
        self.assertEqual(da & ra, set())

    def test_split_regle_aveugle(self):
        # Rejoue la regle : tri alpha par doc, alterne dev/reserve.
        by_doc = {}
        for r in self.fz["split"]["dev"] + self.fz["split"]["reserve"]:
            by_doc.setdefault(r["gold"], []).append(r["anchor"])
        exp_dev = {a for doc, aa in by_doc.items()
                   for i, a in enumerate(sorted(aa)) if i % 2 == 0}
        got_dev = {r["anchor"] for r in self.fz["split"]["dev"]}
        self.assertEqual(got_dev, exp_dev)


if __name__ == "__main__":
    unittest.main()
