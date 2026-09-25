"""Non-regression filtres dense (F3, gate 4) — requiert venv + serveur Qdrant.

Collection isolee `test_f3_filters` (creee puis detruite par le test) :
aucun contact avec agent_memory*, scale_* ni le holdout.
Contrat : None = payload nul ou absent (IsNullCondition), jamais ignore ;
None dans une liste = ValueError. Parite avec store.Collection._match.

Lancement (existant lifecycle uniquement) :
  QDRANT_DATA_DIR=... qdrant   # si aucun serveur lane ne tourne
  FASTEMBED_CACHE_PATH=/home/pierrecsn/.cache/opencode-bun-tmp/fastembed_cache \\
  QDRANT_TEST_URL=http://127.0.0.1:6333 \\
  /home/pierrecsn/.cache/qdrant-508-exp/venv/bin/python \\
    prototype/qdrant-memory/test_filters_dense.py
"""

import os
import unittest

from dense_qdrant import DenseQdrant

URL = os.environ.get("QDRANT_TEST_URL", "http://127.0.0.1:6333")
COLLECTION = "test_f3_filters"


class TestDenseFilters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dq = DenseQdrant(url=URL, collection=COLLECTION)
        if cls.dq.client.collection_exists(COLLECTION):
            cls.dq.drop()
        cls.dq.ensure_collection()
        base = {"project": "cookigram", "kind": "doc",
                "path": "docs/T.md", "section": "s",
                "updated_at": "git", "sha": "t"}
        cls.dq.upsert("a", "Herdr workspace naming derive du travail durable",
                      {**base, "work_id": "487"})
        cls.dq.upsert("b", "recette fondamentaux mayonnaise plongeante",
                      {**base, "work_id": "493"})
        cls.dq.upsert("c", "workspace Herdr sans rattachement",
                      {**base, "work_id": None})

    @classmethod
    def tearDownClass(cls):
        cls.dq.drop()

    def _ids(self, query, filters, top_k=5):
        res = self.dq.search(query, top_k=top_k, filters=filters)
        return sorted(h["citation"]["work_id"] or "∅" for h in res["hits"])

    def test_none_matches_null(self):
        # Echec authentique avant F3 : ValidationError (MatchValue, None refuse).
        self.assertEqual(
            self._ids("workspace Herdr", {"work_id": None}), ["∅"])

    def test_value_still_exact(self):
        self.assertEqual(
            self._ids("workspace Herdr", {"work_id": "487"}), ["487"])

    def test_project_mismatch_empty(self):
        res = self.dq.search("workspace Herdr", filters={"project": "nope"})
        self.assertEqual(res["hits"], [])

    def test_none_in_list_rejected(self):
        with self.assertRaises(ValueError):
            self.dq.search("workspace", filters={"work_id": ["487", None]})

    def test_kind_list(self):
        res = self.dq.search("workspace Herdr",
                             filters={"project": "cookigram",
                                      "kind": ["doc", "claim"]})
        self.assertTrue(res["hits"])
        self.assertTrue(all(h["citation"]["kind"] == "doc"
                            for h in res["hits"]))


if __name__ == "__main__":
    unittest.main()
