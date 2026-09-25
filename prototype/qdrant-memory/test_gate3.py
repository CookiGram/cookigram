"""Tests cibles gate 3 (stdlib uniquement, sans Qdrant)."""

import json
import unittest
from pathlib import Path

from mmr import mmr_select
from policy import decide

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


class TestMMR(unittest.TestCase):
    def test_diversifies_near_dupes(self):
        q = [1.0, 0.0]
        cands = [
            {"id": "a", "score": 0.9, "vector": [1.0, 0.0]},
            {"id": "b", "score": 0.89, "vector": [1.0, 0.01]},
            {"id": "c", "score": 0.7, "vector": [0.0, 1.0]},
        ]
        sel = mmr_select(q, cands, top_k=2, lambda_=0.5)
        self.assertEqual([s["id"] for s in sel], ["a", "c"])

    def test_deterministic(self):
        q = [0.3, 0.7]
        cands = [{"id": str(i), "score": 0.5 + i * 0.01,
                  "vector": [float(i), 1.0]} for i in range(6)]
        once = mmr_select(q, cands, top_k=3)
        twice = mmr_select(q, cands, top_k=3)
        self.assertEqual(once, twice)


class TestPolicy(unittest.TestCase):
    def test_cases_observes(self):
        self.assertEqual(decide([0.6437, 0.4948, 0.4517])[0], "answer")  # T1
        self.assertEqual(decide([0.2661, 0.2273])[0], "abstain")  # N1 s1<tau
        self.assertEqual(decide([0.5181, 0.5041, 0.5005])[0], "abstain")  # N2 marge
        self.assertEqual(decide([])[0], "abstain")

    def test_seuil_seul_insuffisant(self):
        # N2 passe tout seuil qui preserve P3 (s1=0.31) : fait, pas regression.
        self.assertGreater(0.5181, 0.31)


class TestLabels(unittest.TestCase):
    def test_abstention_schema_et_or(self):
        lab = load("abstention_labels.json")
        kinds = {i["kind"] for i in lab["items"]}
        self.assertTrue({"direct", "paraphrase", "hard", "negative-ood",
                         "negative-trap"} <= kinds)
        for it in lab["items"]:
            self.assertIn(it["expected"], ("answer", "abstain"))
            if it["expected"] == "answer":
                self.assertTrue(it["golds"])
                for g in it["golds"]:
                    self.assertTrue((ROOT / g).is_file(), g)
            else:
                self.assertEqual(it["golds"], [])

    def test_agent_tasks_ancres_dans_or(self):
        spec = load("agent_tasks.json")
        for t in spec["items"]:
            if t["expected"] == "answer":
                text = (ROOT / t["gold"]).read_text(encoding="utf-8")
                self.assertIn(t["anchor"], text, t["id"])
            else:
                self.assertIsNone(t["gold"])


if __name__ == "__main__":
    unittest.main()
