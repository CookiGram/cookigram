"""Herdr workspace identity derives from durable work (no LLM bookkeeping)."""

import importlib.util
import inspect
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "herdr_workspaces", ROOT / "scripts/herdr_workspaces.py")
assert SPEC and SPEC.loader
hw = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = hw
SPEC.loader.exec_module(hw)


class FakeHerdr:
    """In-memory stand-in for HerdrClient with list-shaped payloads."""

    def __init__(self):
        self.workspaces: dict[str, dict] = {}
        self.counter = 0

    def list_workspaces(self):
        return [dict(ws) for ws in self.workspaces.values()]

    def create_workspace(self, label, cwd=None):
        self.counter += 1
        wid = f"w9{self.counter}"
        ws = {"workspace_id": wid, "label": label, "number": self.counter,
              "agent_status": "idle", "tokens": {}}
        self.workspaces[wid] = ws
        return {"workspace": dict(ws),
                "root_pane": {"pane_id": f"{wid}:p1"}}

    def rename_workspace(self, workspace_id, label):
        self.workspaces[workspace_id]["label"] = label

    def report_metadata(self, workspace_id, tokens, source="herdr-workspaces"):
        assert source == "herdr-workspaces"
        self.workspaces[workspace_id]["tokens"] = dict(tokens)

    def close_workspace(self, workspace_id):
        del self.workspaces[workspace_id]


def _client_with(fake):
    return fake  # duck-typed: spawn/ensure only use the five methods above


# --- naming contract -----------------------------------------------------

def test_stable_name_generation():
    first = hw.build_display_name("cookigram", 482, "Actions storage audit")
    for _ in range(3):
        assert hw.build_display_name("cookigram", 482, "Actions storage audit") == first
    assert first == "cookigram-482-actions-storage-audit"


def test_suggested_shapes():
    assert hw.build_display_name("orchestra", "ORC-0071", "Grafana cockpit") == \
        "orchestra-orc-0071-grafana-cockpit"
    assert hw.build_display_name("core", 368, "Cuisine strict mode").startswith(
        "core-368-cuisine-strict-mode")


def test_distinct_work_items_distinguishable_from_list_alone():
    fake = FakeHerdr()
    hw.spawn_for_work(_client_with(fake), "cookigram", 482, "Actions storage")
    hw.spawn_for_work(_client_with(fake), "cookigram", 368, "Cuisine strict mode")
    live = fake.list_workspaces()
    labels = [ws["label"] for ws in live]
    assert len(set(labels)) == 2
    found = hw.find_workspace_for_work(live, "cookigram", 482, "Actions storage")
    assert found is not None and "482" in found["label"]
    assert "368" not in found["label"]


def test_long_title_truncated_deterministically():
    title = ("Audit transverse de la couverture nutritionnelle et des "
             "illustrations du catalogue avec reconciliation complete")
    first = hw.build_display_name("cookigram", 432, title)
    assert hw.build_display_name("cookigram", 432, title) == first
    assert len(first) <= hw.MAX_LABEL_LEN
    assert first.startswith("cookigram-432-")
    assert "-" in first.split("cookigram-432-", 1)[1]  # word boundary kept


def test_unicode_and_special_chars_normalized():
    name = hw.build_display_name("cookigram", 101, "Crème brûlée & café — été!")
    assert name == hw.build_display_name("cookigram", 101, "Crème brûlée & café — été!")
    assert name == "cookigram-101-creme-brulee-cafe-ete"
    assert name.isascii()


def test_missing_title_fallback_uses_durable_identity():
    assert hw.build_display_name("cookigram", 482, "") == "cookigram-482-untitled"
    assert hw.build_display_name("cookigram", 482, "!!!") == "cookigram-482-untitled"
    assert hw.build_display_name("cookigram", 482, None) == "cookigram-482-untitled"


def test_no_runtime_or_model_identity_in_primary_name():
    params = set(inspect.signature(hw.build_display_name).parameters)
    assert params == {"project", "work_id", "title", "max_len"}
    for label in (
        hw.build_display_name("cookigram", 482, "Actions storage"),
        hw.build_display_name("orchestra", "ORC-0071", "Grafana cockpit"),
        hw.build_display_name("cookigram", 101, "Crème brûlée"),
    ):
        assert not hw.is_runtime_like_name(label)
        assert "worker-" not in label and "lead-" not in label
    assert hw.is_runtime_like_name("worker-3")
    assert hw.is_runtime_like_name("lead-2")
    assert hw.is_runtime_like_name("w4P:p1")
    assert hw.is_runtime_like_name("123e4567-e89b-12d3-a456-426614174000")


def test_agent_name_stays_secondary_and_valid():
    name = hw.agent_name_for_work("cookigram", 482)
    assert hw.AGENT_NAME_RE.match(name)
    assert "482" in name


# --- lifecycle propagation (no pane reads) --------------------------------

def test_spawn_list_identify_without_pane_output():
    fake = FakeHerdr()
    record = hw.spawn_for_work(
        _client_with(fake), "cookigram", "482", "Actions storage")
    live = fake.list_workspaces()  # only list_workspaces is consulted
    found = hw.find_workspace_for_work(live, "cookigram", "482")
    assert found is not None
    assert found["workspace_id"] == record["workspace_id"]
    assert found["label"] == "cookigram-482-actions-storage"
    assert found["tokens"]["work_key"] == "cookigram:482"
    assert record["tokens"]["work_id"] == "482"  # runtime id kept separate


def test_restart_same_work_keeps_human_identity():
    fake = FakeHerdr()
    first = hw.spawn_for_work(
        _client_with(fake), "cookigram", 482, "Actions storage")
    again = hw.ensure_workspace_for_work(
        _client_with(fake), "cookigram", 482, "Actions storage")
    assert again["label"] == first["label"] == "cookigram-482-actions-storage"
    assert again["workspace_id"] == first["workspace_id"]
    claims = {"482": {"issue": 482, "title": "Actions storage"}}
    plan = hw.reconcile(fake.list_workspaces(), claims)
    assert len(plan.ok) == 1 and not plan.missing and not plan.rename


def test_reconciliation_fixes_stale_label():
    fake = FakeHerdr()
    record = hw.spawn_for_work(
        _client_with(fake), "cookigram", 482, "Actions storage")
    fake.rename_workspace(record["workspace_id"], "cookigram")  # drift
    fixed = hw.ensure_workspace_for_work(
        _client_with(fake), "cookigram", 482, "Actions storage")
    assert fixed["label"] == "cookigram-482-actions-storage"
    assert fixed["workspace_id"] == record["workspace_id"]


def test_reassignment_leaves_no_stale_identity():
    fake = FakeHerdr()
    record = hw.spawn_for_work(
        _client_with(fake), "cookigram", 482, "Actions storage")
    plan = hw.apply_reassign(
        _client_with(fake), record["workspace_id"],
        "cookigram", 368, "Cuisine strict mode")
    assert plan["new_label"] == "cookigram-368-cuisine-strict-mode"
    live = fake.list_workspaces()
    assert live[0]["label"] == "cookigram-368-cuisine-strict-mode"
    assert live[0]["tokens"]["work_key"] == "cookigram:368"
    assert "482" not in live[0]["label"]
    assert hw.find_workspace_for_work(live, "cookigram", 482) is None
    assert hw.find_workspace_for_work(live, "cookigram", 368) is not None


def test_reconcile_plans_missing_stale_and_ignores_unmanaged():
    fake = FakeHerdr()
    hw.spawn_for_work(_client_with(fake), "cookigram", 482, "Actions storage")
    fake.workspaces["wX"] = {"workspace_id": "wX", "label": "cookigram",
                             "number": 99, "agent_status": "idle", "tokens": {}}
    claims = {"482": {"issue": 482, "title": "Actions storage"},
              "368": {"issue": 368, "title": "Cuisine strict mode"}}
    plan = hw.reconcile(fake.list_workspaces(), claims)
    assert [m["work_key"] for m in plan.missing] == ["cookigram:368"]
    assert [s["workspace_id"] for s in plan.ignored] == ["wX"]
    assert not plan.stale
    orphan_claims = {"368": {"issue": 368, "title": "Cuisine strict mode"}}
    plan2 = hw.reconcile(fake.list_workspaces(), orphan_claims)
    assert len(plan2.stale) == 1
    assert plan2.stale[0]["work_key"] == "cookigram:482"


# --- existing safety rules remain intact -----------------------------------

def test_lifecycle_mutations_use_common_path_and_refuse_unsafe():
    fake = FakeHerdr()
    record = hw.spawn_for_work(
        _client_with(fake), "cookigram", 482, "Actions storage")
    fake.workspaces["wU"] = {"workspace_id": "wU", "label": "cookigram",
                             "number": 50, "agent_status": "idle", "tokens": {}}
    with pytest.raises(hw.SafetyRefusal):
        hw.apply_close(_client_with(fake), "wU")  # unmanaged: never touched
    with pytest.raises(hw.SafetyRefusal):
        hw.apply_reassign(_client_with(fake), "wU",
                          "cookigram", 1, "Other")
    fake.workspaces[record["workspace_id"]]["agent_status"] = "working"
    with pytest.raises(hw.SafetyRefusal):
        hw.apply_close(_client_with(fake), record["workspace_id"])
    with pytest.raises(hw.SafetyRefusal):
        hw.apply_reassign(_client_with(fake), record["workspace_id"],
                          "cookigram", 368, "Cuisine strict mode")
    done = hw.apply_close(_client_with(fake), record["workspace_id"], force=True)
    assert done["closed"] is True


def test_watchdog_safety_rule_still_intact():
    spec = importlib.util.spec_from_file_location(
        "watchdog", ROOT / ".agents" / "scripts" / "watchdog.py")
    assert spec and spec.loader
    watchdog = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = watchdog
    spec.loader.exec_module(watchdog)
    old = "2000-01-01T00:00:00+00:00"
    data = {"active_claims": {
        "1": {"agent": "a", "branch": "b", "status": "in_progress",
              "claimed_at": old, "last_heartbeat": old},
        "2": {"agent": "a", "branch": "b", "status": "pr_open",
              "claimed_at": old, "last_heartbeat": old},
    }}
    stale = watchdog.check_claims(data, cleanup=False)
    assert len(stale) == 1  # only the non-pr_open claim expires
    assert set(data["active_claims"]) == {"1", "2"}  # no cleanup without flag


def test_ledger_forbidden_surfaces_still_rejected(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "e2e_ledger", ROOT / "scripts" / "e2e_ledger.py")
    assert spec and spec.loader
    ledger = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = ledger
    spec.loader.exec_module(ledger)
    assert ledger.main(["--ledger-dir", "recipes", "init",
                        "--run-id", "run-1"]) == 2
    assert ledger.main(["--ledger-dir", str(tmp_path), "init",
                        "--run-id", "../escape"]) == 2


def test_claims_are_the_only_durable_source_no_second_lifecycle():
    claims = {"394": {"issue": 394, "title": "Nutrition profile"}}
    desired = hw.desired_labels(claims)
    assert desired == {"cookigram:394": {
        "label": "cookigram-394-nutrition-profile",
        "project": "cookigram", "work_id": "394",
        "title": "Nutrition profile"}}
    assert not (ROOT / "scripts" / "herdr_lifecycle_state.json").exists()
