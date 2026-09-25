"""Tests stdlib du contrat retrieval (zero dependance)."""

import unittest

from store import Collection, embed, estimate_tokens


class TestRetrievalContract(unittest.TestCase):
    def setUp(self):
        self.col = Collection("agent_memory")
        self.col.upsert("a", "Herdr workspace naming derive du travail durable",
                        {"project": "cookigram", "work_id": "487",
                         "kind": "doc", "path": "docs/HERDR-WORKSPACE-NAMING.md",
                         "section": "Contrat", "updated_at": "git", "sha": "x"})
        self.col.upsert("b", "recette fondamentaux mayonnaise plongeante",
                        {"project": "cookigram", "work_id": "493",
                         "kind": "doc", "path": "docs/X.md",
                         "section": "s", "updated_at": "git", "sha": "y"})

    def test_must_filter(self):
        res = self.col.search("workspace Herdr", filters={"project": "cookigram",
                                                          "work_id": "487"})
        self.assertEqual([h["id"] for h in res["hits"]], ["a"])

    def test_filter_excludes(self):
        res = self.col.search("mayonnaise", filters={"work_id": "487"})
        self.assertEqual(res["hits"], [])

    def test_none_filter_matches_null_or_missing(self):
        # Contrat F3 (gate 4) : None = nul ou absent, jamais ignore.
        self.col.upsert("c", "workspace Herdr sans rattachement",
                        {"project": "cookigram", "work_id": None,
                         "kind": "doc", "path": "docs/Y.md",
                         "section": "s", "updated_at": "git", "sha": "z"})
        res = self.col.search("workspace Herdr", filters={"work_id": None})
        self.assertEqual([h["id"] for h in res["hits"]], ["c"])

    def test_none_in_list_rejected(self):
        with self.assertRaises(ValueError):
            self.col.search("workspace", filters={"work_id": ["487", None]})

    def test_citation_present(self):
        res = self.col.search("workspace Herdr")
        self.assertIn("path", res["hits"][0]["citation"])
        self.assertIn("section", res["hits"][0]["citation"])

    def test_deterministic_embed(self):
        self.assertEqual(embed("qdrant memoire"), embed("qdrant memoire"))

    def test_drop_reversible(self):
        self.col.drop()
        self.assertEqual(len(self.col), 0)
        res = self.col.search("workspace")
        self.assertEqual(res["hits"], [])

    def test_token_heuristic(self):
        self.assertEqual(estimate_tokens("a" * 400), 100)


if __name__ == "__main__":
    unittest.main()
