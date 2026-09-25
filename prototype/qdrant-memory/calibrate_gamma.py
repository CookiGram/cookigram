"""Calibrage de gamma (inter-sim) sur le DEV, jamais sur le holdout.

Affiche pour chaque item dev : marge, inter-sim top-3, chemins, statut attendu.
gamma se choisit pour separer (si possible) les grappes corroborantes
(H2, D1 : meme doc, doivent repondre) des competitions reelles
(N2, N4 : doivent abstenir). Valeur fige ensuite dans policy.GAMMA.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

from corpus_manifest import build_corpus  # noqa: E402
from dense_qdrant import DenseQdrant, index_corpus  # noqa: E402
from policy import mean_intersim  # noqa: E402


def main() -> dict:
    labels = json.loads((HERE / "abstention_labels.json").read_text())
    dq = DenseQdrant()
    idx = index_corpus(dq, build_corpus(ROOT))
    print("indexed:", idx, dq.info())
    out = {}
    for it in labels["items"]:
        res = dq.search(it["query"], top_k=3, filters={"project": "cookigram"},
                        with_vectors=True)
        s = [h["score"] for h in res["hits"]]
        margin = s[0] - s[1] if len(s) > 1 else s[0] if s else 0.0
        inter = mean_intersim([h["vector"] for h in res["hits"]])
        paths = [h["citation"]["path"] for h in res["hits"]]
        flag = "MARGIN<0.03" if margin < 0.03 and s and s[0] >= 0.40 else ""
        out[it["id"]] = round(inter, 4)
        print(f"{it['id']:8s} exp={it['expected']:7s} "
              f"s1={s[0] if s else 0:.4f} marge={margin:.4f} inter={inter:.4f} "
              f"{flag} {paths}")
    (HERE / "dev_intersim.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print("wrote dev_intersim.json (DEV ONLY, jamais le holdout)")
    return out


if __name__ == "__main__":
    main()
