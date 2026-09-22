import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("e2e_ledger", ROOT / "scripts/e2e_ledger.py")
assert SPEC and SPEC.loader
e2e_ledger = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = e2e_ledger
SPEC.loader.exec_module(e2e_ledger)


def _run(argv: list[str]) -> int:
    try:
        return e2e_ledger.main(argv)
    except SystemExit as exc:
        assert isinstance(exc.code, int)
        return exc.code


def _events(ledger_dir: Path, run_id: str = "run-1") -> list[dict]:
    return e2e_ledger.read_events(ledger_dir / f"{run_id}.jsonl")


def test_lifecycle_init_log_close_show(tmp_path: Path) -> None:
    assert _run(["--ledger-dir", str(tmp_path), "init", "--run-id", "run-1", "--title", "t"]) == 0
    assert _run(["--ledger-dir", str(tmp_path), "log", "--run-id", "run-1", "--phase", "p1", "--status", "ok"]) == 0
    assert _run(["--ledger-dir", str(tmp_path), "log", "--run-id", "run-1", "--phase", "p2", "--status", "skip"]) == 0
    assert _run(["--ledger-dir", str(tmp_path), "close", "--run-id", "run-1", "--result", "pass"]) == 0
    assert _run(["--ledger-dir", str(tmp_path), "show", "--run-id", "run-1"]) == 0

    events = _events(tmp_path)
    assert [item["seq"] for item in events] == [1, 2, 3, 4]
    assert [item["type"] for item in events] == ["run_started", "event", "event", "run_finished"]
    assert all(item["run_id"] == "run-1" and item["ts"].endswith("Z") for item in events)


def test_resume_reads_last_event_after_interruption(tmp_path: Path) -> None:
    assert _run(["--ledger-dir", str(tmp_path), "init", "--run-id", "run-1"]) == 0
    assert _run(["--ledger-dir", str(tmp_path), "log", "--run-id", "run-1", "--phase", "p1", "--status", "ok"]) == 0

    # Interruption simulée : on relit le journal, le dernier événement dit où reprendre.
    events = _events(tmp_path)
    assert events[-1]["type"] == "event"
    assert events[-1]["phase"] == "p1"

    assert _run(["--ledger-dir", str(tmp_path), "log", "--run-id", "run-1", "--phase", "p2", "--status", "ok"]) == 0
    assert _run(["--ledger-dir", str(tmp_path), "close", "--run-id", "run-1", "--result", "pass"]) == 0
    assert _events(tmp_path)[-1] == {**_events(tmp_path)[-1], "type": "run_finished"}


def test_reinit_requires_force(tmp_path: Path) -> None:
    assert _run(["--ledger-dir", str(tmp_path), "init", "--run-id", "run-1"]) == 0
    assert _run(["--ledger-dir", str(tmp_path), "init", "--run-id", "run-1"]) == 2
    assert _run(["--ledger-dir", str(tmp_path), "init", "--run-id", "run-1", "--force"]) == 0
    assert [item["seq"] for item in _events(tmp_path)] == [1]


def test_commands_refuse_missing_ledger(tmp_path: Path) -> None:
    assert _run(["--ledger-dir", str(tmp_path), "log", "--run-id", "nope", "--phase", "p", "--status", "ok"]) == 2
    assert _run(["--ledger-dir", str(tmp_path), "close", "--run-id", "nope", "--result", "pass"]) == 2
    assert _run(["--ledger-dir", str(tmp_path), "show", "--run-id", "nope"]) == 2


def test_forbidden_surfaces_are_rejected(tmp_path: Path) -> None:
    for forbidden in (".agents", "recipes", ".github/workflows"):
        assert _run(["--ledger-dir", forbidden, "init", "--run-id", "run-1"]) == 2
    assert _run(["--ledger-dir", "/etc", "init", "--run-id", "run-1"]) == 2
    assert _run(["--ledger-dir", str(tmp_path), "init", "--run-id", "../escape"]) == 2
    assert not list(tmp_path.iterdir())


def test_invalid_payloads_are_rejected(tmp_path: Path) -> None:
    assert _run(["--ledger-dir", str(tmp_path), "init", "--run-id", "run-1"]) == 0
    assert _run(["--ledger-dir", str(tmp_path), "log", "--run-id", "run-1", "--phase", "p", "--status", "bogus"]) == 2
    assert _run(["--ledger-dir", str(tmp_path), "close", "--run-id", "run-1", "--result", "bogus"]) == 2
    assert _run(["--ledger-dir", str(tmp_path), "log", "--run-id", "run-1", "--phase", "p", "--status", "ok", "--data-json", "not-json"]) == 2
    assert _run(["--ledger-dir", str(tmp_path), "log", "--run-id", "run-1", "--phase", "p", "--status", "ok", "--data-json", "[1,2]"]) == 2
    assert [item["seq"] for item in _events(tmp_path)] == [1]


def test_data_json_merges_into_event(tmp_path: Path) -> None:
    assert _run(["--ledger-dir", str(tmp_path), "init", "--run-id", "run-1"]) == 0
    payload = json.dumps({"pr": 431, "ci": "pass"})
    assert _run(["--ledger-dir", str(tmp_path), "log", "--run-id", "run-1", "--phase", "p", "--status", "ok", "--data-json", payload]) == 0
    last = _events(tmp_path)[-1]
    assert (last["pr"], last["ci"]) == (431, "pass")


def test_run_id_shape_is_enforced(tmp_path: Path) -> None:
    for bad in ("", "-x", "../x", "a" * 129):
        assert _run(["--ledger-dir", str(tmp_path), "init", "--run-id", bad]) == 2
    with pytest.raises(ValueError):
        e2e_ledger.validate_run_id("../x")
