"""Freeze pre-holdout cycle 2 (dev uniquement, jamais le holdout).

Lit c2_calibration.json (point choisi par la regle pre-enregistree) et
fige : implementation (SHAs), parametres, seuils, politique, metriques,
criteres, dev-set, corpus. Ecrit c2_freeze.json. Refuse si
c2_holdout.json existe deja (le holdout se construit APRES freeze).
"""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main() -> dict:
    if (HERE / "c2_holdout.json").exists():
        raise SystemExit("REFUS : c2_holdout.json existe deja — "
                         "freeze posterieur au holdout interdit.")
    calib = json.loads((HERE / "c2_calibration.json").read_text())
    report = {
        "cycle": 2, "phase": "freeze-pre-holdout",
        "frozen_at": datetime.datetime.now(datetime.timezone.utc)
        .astimezone().isoformat(timespec="seconds"),
        "scope": "DEV ONLY (c2_calibration.json, 14 items). "
                 "Holdout inexistant a ce stade.",
        "point": {"tau": calib["chosen"]["tau"],
                  "delta": calib["chosen"]["delta"],
                  "primary_arm": "dense_fact+policy (B2)",
                  "secondary_arm": "dense_sec+policy, meme point (A2)",
                  "dev_decision_lenient_fact": calib["chosen"]["decision_lenient"],
                  "rule": calib["chosen"]["rule"]},
        "policy": "policy.decide(scores, tau, delta) fige ; "
                  "aucun retuning apres lecture du holdout.",
        "metrics": "success answer/abstain (cycle 1, comparabilite) + "
                   "retrieval rank-1/recall@3 + decision stricte/indulgente.",
        "top_k": 3,
        "collections": {"sec": "agent_memory_c2", "fact": "agent_memory_fact_c2"},
        "code_shas": {n: sha_file(HERE / n) for n in
                      ("c2_dev.json", "c2_calibrate.py", "c2_measure.py")},
        "c1_modules_reused_unmodified": ["store.py", "corpus_manifest.py",
                                         "chunk_facts.py", "dense_qdrant.py",
                                         "policy.py", "retrieval_metrics.py"],
        "corpora": calib["corpora"],
    }
    (HERE / "c2_freeze.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"FREEZE c2 : tau={report['point']['tau']} "
          f"delta={report['point']['delta']} a {report['frozen_at']}")
    return report


if __name__ == "__main__":
    main()
