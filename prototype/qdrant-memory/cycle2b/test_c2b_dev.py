"""Tests deterministes du dev-set cycle2b (stdlib, sans Qdrant).

Verifient : taille >=30, autorite freeze (18 chemins, 26 bannis,
ancres dans les 30 pre-enregistrees), unicite (1 nouveau / 0 ancien),
golds existants contenant leurs ancres, ids uniques, zero recyclage
gate4/cycle2 (ids, ancres, golds), reserve holdout disjointe et
suffisante (>=30 ancres : 2 freeze + 48 supp verifiees ici meme).
Aucune mesure retrieval, aucun tuning.
"""

import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
C1 = HERE.parent
ROOT = HERE.parent.parent.parent
import sys
sys.path.insert(0, str(C1))

SUPP_RESERVE = [
    "Standard des recettes", "Images et licences", "Travail d’agent",
    "Les Six Piliers du Manifeste", "Licence Libre", "Esprit Communautaire",
    "Promesse du Projet", "Contrôles locaux", "Pull request",
    "Contributions assistées", "Simplicité et frugalité",
    "Identité visuelle", "données déterministes",
    "spécialistes conseillent, le Product Lead orchestre",
    "Nutrition positive et décomplexée", "Frontière avec",
    "Validation disponible", "Format d’une recette", "Café, Digestif",
    "for users", "Official CookiGram vocabulary", "Related documents",
    "P0 —", "P3 —", "filet de sécurité", "contrat des recettes",
    "PWA réellement utilisable", "dette frontend", "Tâches en cours",
    "Kitchen OS", "Livraisons Clôturées", "Spécialités de l'équipe",
    "multi-agents CookiGram", "Règle Absolue",
    "Direction artistique & Style", "Tolérance de repli",
    "Cartographie Réelle", "Matrice d'Attribution Opérationnelle",
    "Principes non négociables", "Ordre de traitement impératif",
    "Prérequis pour entamer", "Timeout et Heartbeat",
    "Libération du Claim", "vérification pré-PR", "Principe Directeur",
    "Déterminisme d'Abord", "Coût : 0 Token", "Concision des Échanges",
]


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


class TestDev(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mf = load("c2b_method_freeze.json")
        cls.dev = load("c2b_dev.json")["items"]
        cls.free30 = {r["anchor"] for r in cls.mf["anchor_table"]}
        cls.new_paths = cls.mf["new_paths"]
        cls.new_whole = "\n".join(
            (ROOT / p).read_text(encoding="utf-8") for p in cls.new_paths)
        cls.old_whole = "\n".join(
            p.read_text(encoding="utf-8")
            for p in (ROOT / "docs").rglob("*.md")) + "\n" + (
            ROOT / "decisions" /
            "PDR-0010-nutrition-plaisir-sante-meal-planning.md").read_text(
            encoding="utf-8")

    def test_taille(self):
        self.assertGreaterEqual(len(self.dev), 30)
        ans = [i for i in self.dev if i["expected"] == "answer"]
        neg = [i for i in self.dev if i["expected"] == "abstain"]
        self.assertGreaterEqual(len(ans), 20)
        self.assertGreaterEqual(len(neg), 5)
        kinds = {i["kind"] for i in self.dev}
        self.assertTrue({"direct", "paraphrase", "hard", "negative-trap",
                         "negative-ood"} <= kinds)

    def test_autorite_freeze(self):
        self.assertEqual(len(self.mf["new_paths"]), 18)
        self.assertEqual(len(self.mf["banned_golds"]), 26)
        for it in self.dev:
            if it["expected"] == "answer":
                self.assertTrue(it["golds"] and it["anchors"], it["id"])
                for g in it["golds"]:
                    self.assertIn(g, self.mf["new_paths"], (it["id"], g))
                    self.assertNotIn(g, self.mf["banned_golds"],
                                     (it["id"], g))
                    t = (ROOT / g).read_text(encoding="utf-8")
                    for a in it["anchors"]:
                        self.assertIn(a, t, (it["id"], a))
                        self.assertIn(a, self.free30, (it["id"], a))
                        self.assertEqual(self.new_whole.count(a), 1,
                                         (it["id"], a))
                        self.assertEqual(self.old_whole.count(a), 0,
                                         (it["id"], a))
            else:
                self.assertEqual((it["golds"], it["anchors"]), ([], []))

    def test_ids_uniques(self):
        ids = [i["id"] for i in self.dev]
        self.assertEqual(len(ids), len(set(ids)))

    def test_zero_recyclage(self):
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
        dev_ids = {i["id"] for i in self.dev}
        dev_anchors = {a for i in self.dev for a in i["anchors"]}
        dev_golds = {g for i in self.dev for i in [i] for g in i["golds"]}
        self.assertEqual(dev_ids & c1_ids, set())
        self.assertEqual(dev_anchors & c1_anchors, set())
        self.assertEqual(dev_golds & c1_golds, set())
        self.assertEqual(dev_golds & set(self.mf["banned_golds"]), set())

    def test_reserve_holdout_suffisante(self):
        dev_anchors = {a for i in self.dev for a in i["anchors"]}
        reserve_freeze = self.free30 - dev_anchors
        self.assertGreaterEqual(len(reserve_freeze), 2)
        for a in SUPP_RESERVE:
            self.assertNotIn(a, dev_anchors, a)
            self.assertEqual(self.new_whole.count(a), 1, a)
            self.assertEqual(self.old_whole.count(a), 0, a)
        self.assertEqual(
            len([a for a in SUPP_RESERVE if a not in dev_anchors]), 48)
        self.assertGreaterEqual(len(reserve_freeze) + 48, 30)


if __name__ == "__main__":
    unittest.main()
