"""Tests deterministes du freeze methodologique cycle2b (stdlib, sans Qdrant).

Verifient : inventaire ancien corpus (26), liste fermee c2b (18),
absence de chevauchement, exclusion des 26 bannis, presence des
30 ancres (1 occurrence nouveau perimetre, 0 ancien), tailles.
Aucune mesure retrieval, aucun tuning.
"""

import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
C1 = HERE.parent
ROOT = HERE.parent.parent.parent
import sys
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(C1))

from corpus2b import BANNED_GOLDS, C2B_PATHS  # noqa: E402
from corpus_manifest import chunk_markdown  # noqa: E402


def read(p: str) -> str:
    return (ROOT / p).read_text(encoding="utf-8")


class TestInventaire(unittest.TestCase):
    def test_ancien_corpus_26(self):
        docs = sorted(str(p.relative_to(ROOT))
                      for p in (ROOT / "docs").rglob("*.md"))
        dec = [str(p.relative_to(ROOT)) for p in (ROOT / "decisions").glob("*")
               if p.is_file()]
        self.assertEqual(len(docs), 24)
        self.assertEqual(dec,
                         ["decisions/PDR-0010-nutrition-plaisir-sante-meal-planning.md"])
        self.assertTrue((ROOT / ".agents" / "claims.json").is_file())
        self.assertEqual(len(docs) + len(dec) + 1, 26)

    def test_c2b_liste_fermee_18(self):
        self.assertEqual(len(C2B_PATHS), 18)
        self.assertEqual(len(set(C2B_PATHS)), 18)
        for p in C2B_PATHS:
            self.assertTrue((ROOT / p).is_file(), p)

    def test_bannis_26(self):
        self.assertEqual(len(BANNED_GOLDS), 26)
        self.assertEqual(len(set(BANNED_GOLDS)), 26)

    def test_disjonction_chemins(self):
        old = ({str(p.relative_to(ROOT)) for p in (ROOT / "docs").rglob("*.md")}
               | {"decisions/PDR-0010-nutrition-plaisir-sante-meal-planning.md",
                  ".agents/claims.json"})
        self.assertEqual(set(C2B_PATHS) & old, set())
        self.assertEqual(set(C2B_PATHS) & set(BANNED_GOLDS), set())


class TestAncres(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = json.loads((HERE / "c2b_method_freeze.json").read_text(
            encoding="utf-8"))
        cls.anchors = spec["anchor_table"]
        cls.new_whole = "\n".join(read(p) for p in C2B_PATHS)
        cls.old_whole = "\n".join(
            read(str(p.relative_to(ROOT)))
            for p in (ROOT / "docs").rglob("*.md")) + "\n" + read(
            "decisions/PDR-0010-nutrition-plaisir-sante-meal-planning.md")

    def test_30_ancres(self):
        self.assertEqual(len(self.anchors), 30)

    def test_unicite_nouveau_zero_ancien(self):
        for row in self.anchors:
            a = row["anchor"]
            self.assertEqual(self.new_whole.count(a), 1, a)
            self.assertEqual(self.old_whole.count(a), 0, a)
            self.assertIn(a, read(row["gold"]), row["gold"])

    def test_11_docs_distincts(self):
        self.assertEqual(len({r["gold"] for r in self.anchors}), 11)

    def test_chunks_suffisants(self):
        golds = {r["gold"] for r in self.anchors}
        tot = sum(len(chunk_markdown(ROOT / g, read(g))) for g in golds)
        self.assertGreaterEqual(tot, 60)


if __name__ == "__main__":
    unittest.main()
