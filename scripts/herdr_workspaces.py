#!/usr/bin/env python3
"""Deterministic Herdr workspace identity derived from durable work.

Ownership split (explicit):

* LLM / Lead reasons about work and interprets results. It never invents
  runtime identity.
* Bandleader state (``.agents/claims.json``: work-item / assignment identity,
  ownership, claim status) is the durable source of truth. This module reads
  it but never creates a parallel lifecycle or second state machine.
* This module (Herdr runtime scripts) owns lifecycle mechanics only: build
  the display name, create/rename/retoken/close workspaces through the
  ``herdr`` CLI, and compute reconcile plans. Every mutation goes through
  :class:`HerdrClient` so there is one testable implementation.

Naming contract: ``<project>-<work-id>-<short-subject>`` built only from
(project, work-id, title). Runtime values (pane id, UUID, worker-N, model
name, tier) are never inputs and stay in ``tokens``/CLI metadata for
diagnostics, never in the label.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CLAIMS = REPO_ROOT / ".agents" / "claims.json"

MANAGED_SOURCE = "herdr-workspaces"
DEFAULT_PROJECT = "cookigram"
FALLBACK_SUBJECT = "untitled"
MAX_LABEL_LEN = 60
MAX_SUBJECT_LEN = 36
MAX_PROJECT_LEN = 24
AGENT_NAME_LEN = 32

AGENT_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)
_PANE_REF_RE = re.compile(r"\bw\d+[a-z]*:[tp]\d+\b", re.IGNORECASE)
_WORKER_LEAD_RE = re.compile(r"(?:^|-)(?:worker|lead)-\d+(?:-|$)", re.IGNORECASE)
_WS_ID_RE = re.compile(r"^w\d+[a-z]*$", re.IGNORECASE)


class SafetyRefusal(Exception):
    """Raised when a lifecycle mutation is refused by a safety rule."""


class HerdrError(Exception):
    """Raised when the ``herdr`` CLI call fails."""


def slugify(value: str, max_len: int) -> str:
    """Lowercase ASCII slug; deterministic word-boundary truncation."""
    ascii_text = (
        unicodedata.normalize("NFKD", value or "")
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    if max_len <= 0 or len(slug) <= max_len:
        return slug
    cut = slug[:max_len]
    if "-" in cut:
        head = cut.rsplit("-", 1)[0]
        if head:
            return head
    return cut.strip("-")


def normalize_work_id(work_id: Any) -> str:
    """Normalize durable work identity (issue number, ORC id, e2e id)."""
    raw = str(work_id).strip() if work_id is not None else ""
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", raw).strip("-")
    if not cleaned:
        raise ValueError(f"empty work id from {work_id!r}: durable identity required")
    return cleaned.lower()


def normalize_project(project: Any) -> str:
    """Normalize project/repo segment, defaulting to the durable default."""
    return slugify(str(project or ""), MAX_PROJECT_LEN) or DEFAULT_PROJECT


def short_subject(title: Any, max_len: int = MAX_SUBJECT_LEN) -> str:
    """Subject slug with an explicit deterministic fallback."""
    return slugify(str(title or ""), max_len) or FALLBACK_SUBJECT


def build_display_name(
    project: Any,
    work_id: Any,
    title: Any,
    max_len: int = MAX_LABEL_LEN,
) -> str:
    """Build ``<project>-<work-id>-<short-subject>`` deterministically.

    Only durable inputs are accepted: there is deliberately no parameter
    for pane id, agent name, model, or tier.
    """
    proj = normalize_project(project)
    wid = normalize_work_id(work_id)
    base = f"{proj}-{wid}-"
    budget = max_len - len(base)
    if budget < len(FALLBACK_SUBJECT):
        raise ValueError(
            f"project/work-id too long for max_len={max_len}: {base!r}"
        )
    subject = slugify(str(title or ""), budget) or FALLBACK_SUBJECT
    return base + subject


def work_key(project: Any, work_id: Any) -> str:
    """Canonical durable key ``<project>:<work-id>``."""
    return f"{normalize_project(project)}:{normalize_work_id(work_id)}"


def tokens_for_work(project: Any, work_id: Any, title: Any) -> dict[str, str]:
    """Herdr metadata tokens: technical association, kept out of the label."""
    proj = normalize_project(project)
    wid = normalize_work_id(work_id)
    return {
        "managed": "1",
        "project": proj,
        "work_id": wid,
        "work_key": f"{proj}:{wid}",
        "subject": short_subject(title),
    }


def agent_name_for_work(project: Any, work_id: Any) -> str:
    """Deterministic agent name (secondary metadata, not workspace identity)."""
    slug = slugify(f"{project or DEFAULT_PROJECT}-{work_id}", AGENT_NAME_LEN)
    if not slug or not slug[0].isalpha():
        slug = f"w-{slug}" if slug else "w-work"
    return slug[:AGENT_NAME_LEN]


def workspace_work_key(workspace: dict[str, Any]) -> str | None:
    """Durable key advertised by a workspace, or None when unmanaged."""
    tokens = workspace.get("tokens") or {}
    if tokens.get("managed") != "1":
        return None
    key = tokens.get("work_key")
    return key if key else None


def is_runtime_like_name(name: str) -> bool:
    """Heuristic: True when a label looks like raw runtime identity.

    Used to flag legacy labels, never to reject generator output (a title
    may legitimately contain such words; the generator takes no runtime
    input by construction).
    """
    text = (name or "").strip()
    if not text:
        return True
    if _UUID_RE.search(text) or _PANE_REF_RE.search(text):
        return True
    if _WORKER_LEAD_RE.search(text):
        return True
    if _WS_ID_RE.match(text):
        return True
    return False


def label_matches_work(
    label: str, project: Any, work_id: Any, title: Any
) -> bool:
    """True when the label equals the deterministic name for this work."""
    try:
        return label == build_display_name(project, work_id, title)
    except ValueError:
        return False


def claim_to_work(
    key: Any, claim: dict[str, Any], project_default: str = DEFAULT_PROJECT
) -> dict[str, str]:
    """Project a Bandleader claim onto durable (project, work-id, title)."""
    issue = claim.get("issue", key)
    return {
        "project": str(claim.get("project") or project_default),
        "work_id": str(issue),
        "title": str(claim.get("title") or ""),
    }


def desired_labels(
    active_claims: dict[str, Any], project_default: str = DEFAULT_PROJECT
) -> dict[str, dict[str, str]]:
    """Map durable work-key -> {label, project, work_id, title}."""
    desired: dict[str, dict[str, str]] = {}
    for key, claim in (active_claims or {}).items():
        if not isinstance(claim, dict):
            continue
        work = claim_to_work(key, claim, project_default)
        wid = normalize_work_id(work["work_id"])
        proj = normalize_project(work["project"])
        desired[f"{proj}:{wid}"] = {
            "label": build_display_name(proj, wid, work["title"]),
            "project": proj,
            "work_id": wid,
            "title": work["title"],
        }
    return desired


@dataclass
class ReconcilePlan:
    ok: list[dict[str, Any]] = field(default_factory=list)
    rename: list[dict[str, Any]] = field(default_factory=list)
    missing: list[dict[str, Any]] = field(default_factory=list)
    stale: list[dict[str, Any]] = field(default_factory=list)
    duplicate: list[dict[str, Any]] = field(default_factory=list)
    ignored: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "ok": self.ok,
            "rename": self.rename,
            "missing": self.missing,
            "stale": self.stale,
            "duplicate": self.duplicate,
            "ignored": self.ignored,
        }


def reconcile(
    workspaces: Sequence[dict[str, Any]],
    active_claims: dict[str, Any],
    project_default: str = DEFAULT_PROJECT,
) -> ReconcilePlan:
    """Compare live workspaces against durable claims without mutating.

    Only workspaces carrying our managed tokens are planned; everything
    else is reported under ``ignored`` and never touched.
    """
    plan = ReconcilePlan()
    desired = desired_labels(active_claims, project_default)
    by_key: dict[str, list[dict[str, Any]]] = {}
    for ws in workspaces:
        key = workspace_work_key(ws)
        if key is None:
            plan.ignored.append(ws)
            continue
        by_key.setdefault(key, []).append(ws)
    for key, entry in desired.items():
        live = by_key.pop(key, [])
        if not live:
            plan.missing.append({"work_key": key, **entry})
            continue
        ordered = sorted(live, key=lambda w: w.get("number", 0))
        first, rest = ordered[0], ordered[1:]
        if first.get("label") == entry["label"]:
            plan.ok.append(
                {"work_key": key, "workspace_id": first.get("workspace_id"),
                 "label": first.get("label")}
            )
        else:
            plan.rename.append(
                {"work_key": key, "workspace_id": first.get("workspace_id"),
                 "label": first.get("label"), "expected_label": entry["label"],
                 "agent_status": first.get("agent_status")}
            )
        for extra in rest:
            plan.duplicate.append(
                {"work_key": key, "workspace_id": extra.get("workspace_id"),
                 "label": extra.get("label"),
                 "agent_status": extra.get("agent_status")}
            )
    for key, live in by_key.items():
        for ws in live:
            plan.stale.append(
                {"work_key": key, "workspace_id": ws.get("workspace_id"),
                 "label": ws.get("label"),
                 "agent_status": ws.get("agent_status")}
            )
    return plan


def _get_workspace(
    workspaces: Sequence[dict[str, Any]], workspace_id: str
) -> dict[str, Any]:
    for ws in workspaces:
        if ws.get("workspace_id") == workspace_id:
            return ws
    raise SafetyRefusal(f"unknown workspace {workspace_id!r}")


def check_reassign_safe(
    workspace: dict[str, Any],
    expected_work_key: str | None = None,
    force: bool = False,
) -> str:
    """Refuse unsafe reassignment: unmanaged, key mismatch, or busy agent."""
    key = workspace_work_key(workspace)
    if key is None:
        raise SafetyRefusal(
            f"refusing reassign of unmanaged workspace "
            f"{workspace.get('workspace_id')!r} (no managed tokens)"
        )
    if expected_work_key is not None and key != expected_work_key:
        raise SafetyRefusal(
            f"refusing reassign: workspace holds {key!r}, "
            f"expected {expected_work_key!r} (pass force to override)"
            if not force
            else f"workspace holds {key!r}, expected {expected_work_key!r}"
        )
    if workspace.get("agent_status") == "working" and not force:
        raise SafetyRefusal(
            f"refusing reassign of busy workspace "
            f"{workspace.get('workspace_id')!r} (agent working; use --force)"
        )
    return key


def check_close_safe(
    workspace: dict[str, Any], force: bool = False
) -> str | None:
    """Refuse unsafe close: unmanaged or busy agent without force."""
    key = workspace_work_key(workspace)
    if key is None:
        raise SafetyRefusal(
            f"refusing close of unmanaged workspace "
            f"{workspace.get('workspace_id')!r}"
        )
    if workspace.get("agent_status") == "working" and not force:
        raise SafetyRefusal(
            f"refusing close of busy workspace "
            f"{workspace.get('workspace_id')!r} (agent working; use --force)"
        )
    return key


def reassign_plan(
    workspaces: Sequence[dict[str, Any]],
    workspace_id: str,
    project: Any,
    work_id: Any,
    title: Any,
    force: bool = False,
) -> dict[str, Any]:
    """Compute the rename+retoken step for genuinely different work."""
    ws = _get_workspace(workspaces, workspace_id)
    old_key = check_reassign_safe(ws, force=force)
    proj = normalize_project(project)
    wid = normalize_work_id(work_id)
    new_key = f"{proj}:{wid}"
    return {
        "workspace_id": workspace_id,
        "old_work_key": old_key,
        "old_label": ws.get("label"),
        "new_work_key": new_key,
        "new_label": build_display_name(proj, wid, title),
        "new_tokens": tokens_for_work(proj, wid, title),
    }


class HerdrClient:
    """Single deterministic path for every Herdr lifecycle mutation."""

    def __init__(
        self,
        herdr_bin: str = "herdr",
        run: Callable[..., subprocess.CompletedProcess] | None = None,
    ) -> None:
        self.herdr_bin = herdr_bin
        self._run = run or subprocess.run

    def _call(self, *args: str) -> dict[str, Any]:
        try:
            proc = self._run(
                [self.herdr_bin, *args],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            raise HerdrError(f"cannot execute {self.herdr_bin}: {exc}") from exc
        if proc.returncode != 0:
            raise HerdrError(
                f"herdr {' '.join(args)} failed: "
                f"{(proc.stderr or proc.stdout or '').strip()}"
            )
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise HerdrError(f"herdr {' '.join(args)}: invalid JSON") from exc

    def list_workspaces(self) -> list[dict[str, Any]]:
        payload = self._call("workspace", "list")
        return list(payload.get("result", {}).get("workspaces", []))

    def create_workspace(
        self, label: str, cwd: str | None = None
    ) -> dict[str, Any]:
        args = ["workspace", "create", "--label", label, "--no-focus"]
        if cwd:
            args += ["--cwd", cwd]
        payload = self._call(*args)
        result = payload.get("result", {})
        return {
            "workspace": result.get("workspace", {}),
            "root_pane": result.get("root_pane", {}),
        }

    def rename_workspace(self, workspace_id: str, label: str) -> None:
        self._call("workspace", "rename", workspace_id, label)

    def report_metadata(
        self,
        workspace_id: str,
        tokens: dict[str, str],
        source: str = MANAGED_SOURCE,
    ) -> None:
        args: list[str] = ["workspace", "report-metadata", workspace_id,
                           "--source", source]
        for name, value in tokens.items():
            args += ["--token", f"{name}={value}"]
        self._call(*args)

    def close_workspace(self, workspace_id: str) -> None:
        self._call("workspace", "close", workspace_id)

    def start_agent(
        self, name: str, kind: str, pane_id: str,
        agent_args: Sequence[str] = (),
    ) -> None:
        if not AGENT_NAME_RE.match(name):
            raise ValueError(f"invalid agent name {name!r}")
        self._call("agent", "start", name, "--kind", kind,
                   "--pane", pane_id, *agent_args)


def spawn_for_work(
    client: HerdrClient,
    project: Any,
    work_id: Any,
    title: Any,
    cwd: str | None = None,
) -> dict[str, Any]:
    """Create a workspace for durable work and associate it via tokens."""
    proj = normalize_project(project)
    wid = normalize_work_id(work_id)
    label = build_display_name(proj, wid, title)
    created = client.create_workspace(label, cwd=cwd)
    workspace = created.get("workspace", {})
    workspace_id = workspace.get("workspace_id", "")
    tokens = tokens_for_work(proj, wid, title)
    client.report_metadata(workspace_id, tokens)
    return {
        "workspace_id": workspace_id,
        "pane_id": created.get("root_pane", {}).get("pane_id", ""),
        "label": label,
        "work_key": tokens["work_key"],
        "tokens": tokens,
    }


def find_workspace_for_work(
    workspaces: Sequence[dict[str, Any]],
    project: Any,
    work_id: Any,
    title: Any = "",
) -> dict[str, Any] | None:
    """Identify the workspace handling work from list output alone.

    Token match first (exact durable association), label match second
    (tokens may expire while the derived label persists). Pane output
    is never consulted.
    """
    key = work_key(project, work_id)
    for ws in workspaces:
        if workspace_work_key(ws) == key:
            return ws
    try:
        label = build_display_name(project, work_id, title)
    except ValueError:
        return None
    for ws in workspaces:
        if ws.get("label") == label and workspace_work_key(ws) is None:
            return ws
    return None


def ensure_workspace_for_work(
    client: HerdrClient,
    project: Any,
    work_id: Any,
    title: Any,
    cwd: str | None = None,
) -> dict[str, Any]:
    """Restart-safe spawn: reuse the workspace, fixing stale identity."""
    live = client.list_workspaces()
    existing = find_workspace_for_work(live, project, work_id, title)
    proj = normalize_project(project)
    wid = normalize_work_id(work_id)
    expected = build_display_name(proj, wid, title)
    if existing is None:
        return spawn_for_work(client, proj, wid, title, cwd=cwd)
    if existing.get("label") != expected:
        client.rename_workspace(str(existing.get("workspace_id")), expected)
    client.report_metadata(
        str(existing.get("workspace_id")), tokens_for_work(proj, wid, title)
    )
    return {
        "workspace_id": existing.get("workspace_id", ""),
        "pane_id": "",
        "label": expected,
        "work_key": work_key(proj, wid),
        "reused": True,
    }


def apply_reassign(
    client: HerdrClient,
    workspace_id: str,
    project: Any,
    work_id: Any,
    title: Any,
    force: bool = False,
) -> dict[str, Any]:
    """Reassign to genuinely different work: no stale identity left behind."""
    live = client.list_workspaces()
    ws = _get_workspace(live, workspace_id)
    check_reassign_safe(ws, force=force)
    plan = reassign_plan(live, workspace_id, project, work_id, title,
                         force=True)
    client.rename_workspace(workspace_id, plan["new_label"])
    client.report_metadata(workspace_id, plan["new_tokens"])
    return plan


def apply_close(
    client: HerdrClient, workspace_id: str, force: bool = False
) -> dict[str, Any]:
    """Close a managed workspace after safety checks."""
    live = client.list_workspaces()
    ws = _get_workspace(live, workspace_id)
    key = check_close_safe(ws, force=force)
    client.close_workspace(workspace_id)
    return {"workspace_id": workspace_id, "work_key": key, "closed": True}


def load_active_claims(claims_path: Path = DEFAULT_CLAIMS) -> dict[str, Any]:
    try:
        data = json.loads(claims_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    claims = data.get("active_claims", {})
    return claims if isinstance(claims, dict) else {}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deterministic Herdr workspace identity from durable work"
    )
    parser.add_argument("--herdr-bin", default="herdr")
    parser.add_argument("--claims", default=str(DEFAULT_CLAIMS))
    parser.add_argument("--project-default", default=DEFAULT_PROJECT)
    sub = parser.add_subparsers(dest="command", required=True)

    name = sub.add_parser("name", help="print the display name for work")
    name.add_argument("--project", default=DEFAULT_PROJECT)
    name.add_argument("--work-id", required=True)
    name.add_argument("--title", default="")

    key = sub.add_parser("key", help="print the durable work key")
    key.add_argument("--project", default=DEFAULT_PROJECT)
    key.add_argument("--work-id", required=True)

    spawn = sub.add_parser("spawn", help="create a workspace for work")
    spawn.add_argument("--project", default=DEFAULT_PROJECT)
    spawn.add_argument("--work-id", required=True)
    spawn.add_argument("--title", default="")
    spawn.add_argument("--cwd", default=None)
    spawn.add_argument("--kind", default=None,
                       help="also start an agent of this kind in the new tab")
    spawn.add_argument("--agent-name", default=None)

    ensure = sub.add_parser("ensure",
                            help="restart-safe spawn (reuse + fix label)")
    ensure.add_argument("--project", default=DEFAULT_PROJECT)
    ensure.add_argument("--work-id", required=True)
    ensure.add_argument("--title", default="")
    ensure.add_argument("--cwd", default=None)

    sub.add_parser("reconcile", help="print the reconcile plan as JSON")
    sub.add_parser("list", help="print managed workspaces as JSON")

    reassign = sub.add_parser("reassign", help="move a workspace to new work")
    reassign.add_argument("--workspace-id", required=True)
    reassign.add_argument("--project", default=DEFAULT_PROJECT)
    reassign.add_argument("--work-id", required=True)
    reassign.add_argument("--title", default="")
    reassign.add_argument("--force", action="store_true")

    cleanup = sub.add_parser("cleanup", help="close a managed workspace")
    cleanup.add_argument("--workspace-id", required=True)
    cleanup.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "name":
            print(build_display_name(args.project, args.work_id, args.title))
            return 0
        if args.command == "key":
            print(work_key(args.project, args.work_id))
            return 0
        client = HerdrClient(herdr_bin=args.herdr_bin)
        if args.command == "spawn":
            record = spawn_for_work(client, args.project, args.work_id,
                                    args.title, cwd=args.cwd)
            if args.kind:
                pane = record.get("pane_id") or ""
                name = args.agent_name or agent_name_for_work(
                    args.project, args.work_id)
                client.start_agent(name, args.kind, pane)
                record["agent"] = name
            print(json.dumps(record, ensure_ascii=False, sort_keys=True))
            return 0
        if args.command == "ensure":
            record = ensure_workspace_for_work(client, args.project,
                                               args.work_id, args.title,
                                               cwd=args.cwd)
            print(json.dumps(record, ensure_ascii=False, sort_keys=True))
            return 0
        if args.command == "reconcile":
            claims = load_active_claims(Path(args.claims))
            plan = reconcile(client.list_workspaces(), claims,
                             args.project_default)
            print(json.dumps(plan.as_dict(), ensure_ascii=False,
                             sort_keys=True, indent=2))
            return 0
        if args.command == "list":
            claims = load_active_claims(Path(args.claims))
            _ = claims  # durable source noted; listing shows live projection
            managed = [ws for ws in client.list_workspaces()
                       if workspace_work_key(ws) is not None]
            print(json.dumps(managed, ensure_ascii=False, sort_keys=True,
                             indent=2))
            return 0
        if args.command == "reassign":
            plan = apply_reassign(client, args.workspace_id, args.project,
                                  args.work_id, args.title, force=args.force)
            print(json.dumps(plan, ensure_ascii=False, sort_keys=True))
            return 0
        if args.command == "cleanup":
            record = apply_close(client, args.workspace_id, force=args.force)
            print(json.dumps(record, ensure_ascii=False, sort_keys=True))
            return 0
    except SafetyRefusal as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    except (ValueError, HerdrError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
