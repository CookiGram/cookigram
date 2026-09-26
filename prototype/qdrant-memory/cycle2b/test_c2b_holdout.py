"""Tests deterministes du holdout cycle2b (stdlib, sans Qdrant).

Verifient : taille >=30, mix answer/abstain et familles, autorite
freeze (18 chemins, 26 bannis), unicite ancres (1 nouveau / 0 ancien),
golds contenant leurs ancres, ids uniques, disjonction totale avec
dev cycle2b (ids, ancres, formulations), gate4, cycle2 dev/holdout,
bannis. Aucune mesure retrieval, aucun tuning.
"""

import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
C1 = HERE.parent
ROOT = HERE.parent.parent.parent
import sys
sys.path.insert(0, str(C1))


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


class TestHoldout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mf = load("c2b_method_freeze.json")
        cls.dev = load("c2b_dev.json")["items"]
        cls.ho = load("c2b_holdout.json")["items"]
        cls.new_paths = cls.mf["new_paths"]
        cls.new_whole = "\n".join(
            (ROOT / p).read_text(encoding="utf-8") for p in cls.new_paths)
        cls.old_whole = "\n".join(
            p.read_text(encoding="utf-8")
            for p in (ROOT / "docs").rglob("*.md")) + "\n" + (
            ROOT / "decisions" /
            "PDR-0010-nutrition-plaisir-sante-meal-planning.md").read_text(
            encoding="utf-8")
        cls.dev_ids = {i["id"] for i in cls.dev}
        cls.dev_anchors = {a for i in cls.dev if i["expected"] == "answer"
                           for a in i["anchors"]}
        cls.dev_queries = {i["query"] for i in cls.dev}

    def test_taille_et_mix(self):
        self.assertGreaterEqual(len(self.ho), 30)
        ans = [i for i in self.ho if i["expected"] == "answer"]
        neg = [i for i in self.ho if i["expected"] == "abstain"]
        self.assertGreaterEqual(len(ans), 20)
        self.assertGreaterEqual(len(neg), 5)
        kinds = {i["kind"] for i in self.ho}
        self.assertTrue({"direct", "paraphrase", "hard", "negative-trap",
                         "negative-ood"} <= kinds)

    def test_autorite_freeze(self):
        for it in self.ho:
            if it["expected"] == "answer":
                self.assertTrue(it["golds"] and it["anchors"], it["id"])
                for g in it["golds"]:
                    self.assertIn(g, self.new_paths, (it["id"], g))
                    self.assertNotIn(g, self.mf["banned_golds"],
                                     (it["id"], g))
                    t = (ROOT / g).read_text(encoding="utf-8")
                    for a in it["anchors"]:
                        self.assertIn(a, t, (it["id"], a))
                        self.assertEqual(self.new_whole.count(a), 1,
                                         (it["id"], a))
                        self.assertEqual(self.old_whole.count(a), 0,
                                         (it["id"], a))
            else:
                self.assertEqual((it["golds"], it["anchors"]), ([], []))

    def test_ids_uniques(self):
        ids = [i["id"] for i in self.ho]
        self.assertEqual(len(ids), len(set(ids)))

    def test_disjonction_dev(self):
        ho_ids = {i["id"] for i in self.ho}
        ho_anchors = {a for i in self.ho if i["expected"] == "answer"
                      for a in i["anchors"]}
        ho_queries = {i["query"] for i in self.ho}
        self.assertEqual(ho_ids & self.dev_ids, set())
        self.assertEqual(ho_anchors & self.dev_anchors, set())
        self.assertEqual(ho_queries & self.dev_queries, set())

    def test_zero_recyclage_historique(self):
        c1_ids, c1_anchors, c1_golds = set(), set(), set()
        for f in ("abstention_labels.json", "agent_tasks.json"):
            d = json.loads((C1 / f).read_text(encoding="utf-8"))
            for it in d["items"]:
                c1_ids.add(it["id"])
                if it.get("anchor"):
                    c1_anchors.add(it["anchor"])
                if it.get("gold"):
                    c1_golds.add(it["gold"])
                c1_golds.update(it.get("golds", []))
        h = json.loads((C1 / "holdout.json").read_text(encoding="utf-8"))
        for it in h["items"]:
            c1_ids.add(it["id"])
            c1_anchors.update(it.get("anchors", []))
            c1_golds.update(it.get("golds", []))
        for f in ("c2_dev.json", "c2_holdout.json"):
            d = json.loads((C1 / "cycle2" / f).read_text(encoding="utf-8"))
            for it in d["items"]:
                c1_ids.add(it["id"])
                c1_anchors.update(it.get("anchors", []))
                c1_golds.update(it.get("golds", []))
        ho_ids = {i["id"] for i in self.ho}
        ho_anchors = {a for i in self.ho if i["expected"] == "answer"
                      for a in i["anchors"]}
        ho_golds = {g for i in self.ho for g in i["golds"]}
        self.assertEqual(ho_ids & c1_ids, set())
        self.assertEqual(ho_anchors & c1_anchors, set())
        self.assertEqual(ho_golds & c1_golds, set())
        self.assertEqual(ho_golds & set(self.mf["banned_golds"]), set())

    def test_reservees_utilisees(self):
        ho_anchors = {a for i in self.ho if i["expected"] == "answer"
                      for a in i["anchors"]}
        self.assertIn("Matrice d'Attribution", ho_anchors)
        self.assertIn("Règle 24", ho_anchors)


if __name__ == "__main__":
    unittest.main()
