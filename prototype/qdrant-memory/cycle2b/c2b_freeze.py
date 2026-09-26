"""Freeze de calibration DEV cycle2b (C2B_DEV_CALIBRATION_GO) — PRE-holdout.

Point issu de la regle pre-enregistree cycle 2, appliquee a
c2b_calibration.json (dev 34 items, bras fact). Aucun holdout
c2b_holdout.json n'existe a ce stade (verifie : absent du worktree
et de HEAD). Aucun retuning apres ceci. STOP : holdout + mesure
exigent un nouveau GO Human Owner.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main() -> dict:
    assert not (HERE / "c2b_holdout.json").exists(), \
        "c2b_holdout.json existe : freeze pre-holdout impossible"
    cal = json.loads((HERE / "c2b_calibration.json").read_text(
        encoding="utf-8"))
    dev = json.loads((HERE / "c2b_dev.json").read_text(encoding="utf-8"))
    mf = json.loads((HERE / "c2b_method_freeze.json").read_text(
        encoding="utf-8"))
    assert len(dev["items"]) >= 30
    assert cal["corpora"]["section_chunks"] == 350
    assert cal["corpora"]["fact_chunks"] == 1912
    freeze = {
        "cycle": "2b",
        "phase": "freeze-pre-holdout",
        "frozen_at": datetime.datetime.now(datetime.timezone.utc)
        .astimezone().isoformat(timespec="seconds"),
        "scope": "DEV ONLY (c2b_calibration.json, %d items). "
                 "Holdout inexistant a ce stade." % len(dev["items"]),
        "point": {
            "tau": cal["chosen"]["tau"],
            "delta": cal["chosen"]["delta"],
            "primary_arm": "dense_fact+policy (B2)",
            "secondary_arm": "dense_sec+policy, meme point (A2)",
            "dev_decision_lenient_fact": cal["chosen"]["decision_lenient"],
            "rule": cal["chosen"]["rule"],
        },
        "tie_break_applied": "Ex-aequo (0.60,0.02) vs (0.60,0.05) a "
                             "0.765 : delta superieur (0.05) par la regle "
                             "pre-enregistree (preference abstention).",
        "fragilities": "Dev : B2-B marge 0.0533 (~delta), B2-Y s1 0.6002 "
                       "(~tau), B2-Z s1 0.6012 (~tau), B2-N6 piege s1 "
                       "0.6016 (~tau, fuit si s1>=tau et marge>=delta).",
        "policy": "policy.decide(scores, tau, delta) fige ; aucun "
                  "retuning apres lecture du holdout.",
        "metrics": "success answer/abstain + retrieval rank-1/recall@3 + "
                   "decision stricte/indulgente (comparabilite protocole).",
        "top_k": 3,
        "collections": {"sec": "agent_memory_c2b",
                        "fact": "agent_memory_fact_c2b"},
        "code_shas": {f: sha_file(HERE / f) for f in
                      ("c2b_dev.json", "c2b_calibrate.py", "test_c2b_dev.py",
                       "corpus2b.py")},
        "c1_modules_reused_unmodified": [
            "store.py", "corpus_manifest.py", "chunk_facts.py",
            "dense_qdrant.py", "policy.py", "retrieval_metrics.py"],
        "corpora": cal["corpora"],
        "retrieval_dev": cal["retrieval_dev"],
        "dev_composition": {
            "n": len(dev["items"]),
            "kinds": {k: sum(1 for i in dev["items"] if i["kind"] == k)
                      for k in sorted({i["kind"] for i in dev["items"]})},
            "golds_distincts": len({g for i in dev["items"]
                                    for g in i["golds"]}),
        },
    }
    (HERE / "c2b_freeze.json").write_text(
        json.dumps(freeze, indent=1, ensure_ascii=False), encoding="utf-8")
    print("freeze: tau=%s delta=%s lenient=%s" % (
        freeze["point"]["tau"], freeze["point"]["delta"],
        freeze["point"]["dev_decision_lenient_fact"]))
    return freeze


if __name__ == "__main__":
    main()
