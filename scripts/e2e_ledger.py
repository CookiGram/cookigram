#!/usr/bin/env python3
"""Durable runtime ledger for end-to-end runs (timestamped JSONL).

One ledger file per run under ``docs/e2e-runs/<run-id>.jsonl`` (override with
``--ledger-dir``). Each line is a self-contained JSON object with a UTC
timestamp (``ts``), the ``run_id``, a monotonic ``seq`` and an event ``type``.

The ledger is the durable, resumable record of a run. It intentionally fills
the gap left by ``.agents/claims.json`` (ephemeral coordination state, not a
run journal): after an interruption, ``show`` replays the file and the last
event tells the operator where to resume.

This script NEVER writes to coordination or config surfaces:
``.agents/claims.json``, ``.builder.json``, ``.core-version``,
``.github/workflows/*`` — nor to ``recipes/*`` (frozen by PR #427).
The target file is always resolved and rejected when it escapes the ledger
directory.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LEDGER_DIR = REPO_ROOT / "docs" / "e2e-runs"

# Surfaces this script must never touch (repo-relative prefixes).
FORBIDDEN_PREFIXES = (
    ".agents/claims.json",
    ".builder.json",
    ".core-version",
    ".github/workflows",
    "recipes/",
)

RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
STATUSES = ("ok", "ko", "skip", "info")
RESULTS = ("pass", "fail")
EVENT_TYPES = ("run_started", "event", "run_finished")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def validate_run_id(run_id: str) -> str:
    if not RUN_ID_RE.match(run_id):
        raise ValueError(
            f"invalid --run-id {run_id!r}: use 1-128 chars [A-Za-z0-9._-], "
            "starting with an alphanumeric"
        )
    return run_id


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _reject_forbidden_repo_path(rel: Path, what: str) -> None:
    for prefix in FORBIDDEN_PREFIXES:
        forbidden = Path(prefix)
        if rel == forbidden or _is_within(rel, forbidden) or _is_within(forbidden, rel):
            raise ValueError(f"{what} collides with forbidden surface {prefix}")


def resolve_ledger_dir(raw: str | None) -> Path:
    base = Path(raw).expanduser() if raw else DEFAULT_LEDGER_DIR
    if not base.is_absolute():
        base = (REPO_ROOT / base).resolve()
    else:
        base = base.resolve()
    try:
        rel = base.relative_to(REPO_ROOT)
    except ValueError:
        # Outside the repo: only the system temp dir is accepted (tests).
        tmp = Path(tempfile.gettempdir()).resolve()
        if not _is_within(base, tmp):
            raise ValueError(f"ledger dir {base} is outside the repository")
        return base
    _reject_forbidden_repo_path(rel, f"ledger dir {base}")
    return base


def resolve_ledger_file(ledger_dir: Path, run_id: str) -> Path:
    validate_run_id(run_id)
    resolved_dir = ledger_dir.resolve()
    target = (resolved_dir / f"{run_id}.jsonl").resolve()
    try:
        target.relative_to(resolved_dir)
    except ValueError:
        raise ValueError(f"refusing to write outside ledger dir: {target}")
    try:
        rel = target.relative_to(REPO_ROOT)
    except ValueError:
        return target  # vetted tmp-dir ledger (see resolve_ledger_dir)
    _reject_forbidden_repo_path(rel, f"refusing target {rel}")
    return target


def read_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def append_event(path: Path, payload: dict) -> dict:
    events = read_events(path)
    payload = {"ts": utc_now_iso(), **payload, "seq": len(events) + 1}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return payload


def cmd_init(args: argparse.Namespace) -> int:
    ledger_dir = resolve_ledger_dir(getattr(args, "ledger_dir", None))
    path = resolve_ledger_file(ledger_dir, args.run_id)
    if path.exists() and not args.force:
        print(f"ledger already exists: {path} (use --force to re-init)", file=sys.stderr)
        return 2
    if args.force and path.exists():
        path.unlink()
    payload = append_event(
        path,
        {
            "type": "run_started",
            "run_id": args.run_id,
            "title": args.title or args.run_id,
            "actor": args.actor or "",
        },
    )
    print(str(path))
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    ledger_dir = resolve_ledger_dir(getattr(args, "ledger_dir", None))
    path = resolve_ledger_file(ledger_dir, args.run_id)
    if not path.exists():
        print(f"no ledger for run {args.run_id!r}: run init first", file=sys.stderr)
        return 2
    extra: dict = {}
    if args.data_json:
        try:
            extra = json.loads(args.data_json)
        except json.JSONDecodeError as exc:
            print(f"invalid --data-json: {exc}", file=sys.stderr)
            return 2
        if not isinstance(extra, dict):
            print("--data-json must decode to an object", file=sys.stderr)
            return 2
    payload = append_event(
        path,
        {
            "type": "event",
            "run_id": args.run_id,
            "phase": args.phase,
            "status": args.status,
            "detail": args.detail or "",
            **extra,
        },
    )
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


def _phase_last_status(events: list[dict]) -> dict[str, str]:
    last: dict[str, str] = {}
    for item in events:
        if item.get("type") == "event" and "phase" in item:
            last[item["phase"]] = item.get("status", "")
    return last


def cmd_close(args: argparse.Namespace) -> int:
    ledger_dir = resolve_ledger_dir(getattr(args, "ledger_dir", None))
    path = resolve_ledger_file(ledger_dir, args.run_id)
    if not path.exists():
        print(f"no ledger for run {args.run_id!r}: run init first", file=sys.stderr)
        return 2
    if args.result == "pass":
        failing = sorted(phase for phase, status in _phase_last_status(read_events(path)).items() if status == "ko")
        if failing:
            print(
                f"cannot close pass with failing phase(s): {', '.join(failing)}"
                " (log a fix or close --result fail)",
                file=sys.stderr,
            )
            return 2
    payload = append_event(
        path,
        {
            "type": "run_finished",
            "run_id": args.run_id,
            "result": args.result,
            "summary": args.summary or "",
        },
    )
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    ledger_dir = resolve_ledger_dir(getattr(args, "ledger_dir", None))
    path = resolve_ledger_file(ledger_dir, args.run_id)
    if not path.exists():
        print(f"no ledger for run {args.run_id!r}", file=sys.stderr)
        return 2
    print(path.read_text(encoding="utf-8"), end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Append timestamped JSONL events to docs/e2e-runs/<run-id>.jsonl"
    )
    parser.add_argument(
        "--ledger-dir",
        default=None,
        help="ledger directory (default: docs/e2e-runs; tests should use a tmp dir)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="start a new run ledger")
    init.add_argument("--run-id", required=True)
    init.add_argument("--title", default="")
    init.add_argument("--actor", default="")
    init.add_argument("--force", action="store_true")
    init.add_argument("--ledger-dir", default=argparse.SUPPRESS)
    init.set_defaults(func=cmd_init)

    log = sub.add_parser("log", help="append a phase event to a run ledger")
    log.add_argument("--run-id", required=True)
    log.add_argument("--phase", required=True)
    log.add_argument("--status", required=True, choices=STATUSES)
    log.add_argument("--detail", default="")
    log.add_argument("--data-json", default="")
    log.add_argument("--ledger-dir", default=argparse.SUPPRESS)
    log.set_defaults(func=cmd_log)

    close = sub.add_parser("close", help="append the final result to a run ledger")
    close.add_argument("--run-id", required=True)
    close.add_argument("--result", required=True, choices=RESULTS)
    close.add_argument("--summary", default="")
    close.add_argument("--ledger-dir", default=argparse.SUPPRESS)
    close.set_defaults(func=cmd_close)

    show = sub.add_parser("show", help="print a run ledger (replay for resume)")
    show.add_argument("--run-id", required=True)
    show.add_argument("--ledger-dir", default=argparse.SUPPRESS)
    show.set_defaults(func=cmd_show)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
