#!/usr/bin/env python3
"""Write deterministic ``_site/provenance.json`` plus its run attestation (#434).

Reproducible-build contract: two builds of the same content commit must
produce byte-identical ``provenance.json``. ``built_at`` therefore honors
``SOURCE_DATE_EPOCH`` (https://reproducible-builds.org/specs/source-date-epoch/)
when set, else falls back to the content commit timestamp
(``git log -1 --format=%ct``), and only then to the current UTC time.

Two runs of the same content commit must
produce byte-identical output regardless of wall-clock time or
dependency drift. All its fields are pure functions of the CI
environment (content SHA, builder pins, contract pins).

The qualifying CI run id is inherently per-run, so it must never live in
``provenance.json`` (review of PR #573). It is recorded separately in
``_site/provenance-run.json``, which binds the deterministic artifact to
the run that qualified it — Pages verifies both files together, so the
provenance control is preserved, never weakened.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
from pathlib import Path


def resolve_epoch(content_sha: str, environ: dict[str, str] | None = None) -> int | None:
    """Return the epoch to stamp, or ``None`` when nothing pins it."""
    source = environ if environ is not None else os.environ
    raw = source.get("SOURCE_DATE_EPOCH", "").strip()
    if raw:
        try:
            epoch = int(raw)
        except ValueError:
            raise SystemExit(f"SOURCE_DATE_EPOCH invalide : {raw!r} (entier attendu).")
        if epoch < 0:
            raise SystemExit(f"SOURCE_DATE_EPOCH invalide : {raw!r} (entier positif attendu).")
        return epoch
    if content_sha:
        try:
            proc = subprocess.run(
                ["git", "log", "-1", "--format=%ct", content_sha],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            proc = None
        if proc is not None and proc.returncode == 0 and proc.stdout.strip().isdigit():
            return int(proc.stdout.strip())
    return None


def build_provenance(environ: dict[str, str], *, now: datetime.datetime | None = None) -> dict[str, str]:
    """Build the provenance mapping from CI environment variables."""
    content_sha = environ.get("CONTENT_SHA", "")
    epoch = resolve_epoch(content_sha, environ)
    if epoch is not None:
        built_at = datetime.datetime.fromtimestamp(epoch, tz=datetime.timezone.utc).isoformat()
    else:
        moment = now or datetime.datetime.now(datetime.timezone.utc)
        built_at = moment.isoformat()
    return {
        "content_sha": content_sha,
        "core_sha": environ.get("BUILDER_CORE_SHA", ""),
        "built_at": built_at,
        "contract_version": environ.get("CONTRACT_VERSION", ""),
        "contract_source_sha": environ.get("COOKIGRAM_CONTRACT_SHA", ""),
        "contract_artifact": environ.get("COOKIGRAM_CONTRACT_ARTIFACT", ""),
        "contract_sha256": environ.get("COOKIGRAM_CONTRACT_SHA256", ""),
        "builder_release": environ.get("BUILDER_RELEASE", ""),
        "builder_artifact": environ.get("BUILDER_ARTIFACT", ""),
        "builder_sha256": environ.get("BUILDER_SHA256", ""),
        "pages_artifact": environ.get("PAGES_ARTIFACT", ""),
    }


def build_run_attestation(environ: dict[str, str], provenance: dict[str, str]) -> dict[str, str]:
    """Bind the deterministic artifact to the CI run that qualified it.

    Every field here is either copied from ``provenance`` (so Pages can
    verify the attestation designates exactly the verified artifact) or
    the per-run id. ``provenance.json`` itself stays run-independent.
    """
    return {
        "content_sha": provenance["content_sha"],
        "pages_artifact": provenance["pages_artifact"],
        "qualifying_ci_run_id": environ.get("QUALIFYING_RUN_ID", ""),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", type=Path, default=Path("_site"))
    args = parser.parse_args(argv)

    provenance = build_provenance(dict(os.environ))
    required = ("content_sha", "core_sha", "built_at")
    missing = [key for key in required if not provenance[key]]
    if missing:
        print(f"Variables d'environnement manquantes : {', '.join(missing)}", flush=True)
        return 1
    attestation = build_run_attestation(dict(os.environ), provenance)
    if not attestation["qualifying_ci_run_id"]:
        print("Variable d'environnement manquante : QUALIFYING_RUN_ID", flush=True)
        return 1
    args.site_dir.mkdir(parents=True, exist_ok=True)
    (args.site_dir / "provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )
    (args.site_dir / "provenance-run.json").write_text(
        json.dumps(attestation, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(provenance, indent=2))
    print(json.dumps(attestation, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
