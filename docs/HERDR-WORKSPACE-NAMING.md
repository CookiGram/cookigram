# Herdr workspace identity from durable work

> Principle: agents reason, scripts manage lifecycle, durable work defines identity.

An operator running `herdr workspace list` must understand what each agent
is working on from the workspace `label` alone, without opening any pane.

## Ownership split

| Owner | Responsibility |
| --- | --- |
| LLM / Lead | Understand work, choose next action, interpret results, escalate ambiguity. Never invents runtime identity. |
| Bandleader (`.agents/claims.json`) | Durable facts: work-item identity, ownership, claim status. Sole source for reconciliation. |
| `scripts/herdr_workspaces.py` | Runtime mechanics only: display-name generation, create/rename/retoken/close via the `herdr` CLI, reconcile plans. |

No second lifecycle exists: association lives in Herdr metadata tokens on
the workspace itself, and durable truth stays in `claims.json`. No
`herdr_lifecycle_state.json` or parallel registry is introduced.

## Naming contract

`<project>-<work-id>-<short-subject>`, built only from durable inputs:

* `cookigram-482-actions-storage`
* `orchestra-orc-0071-grafana-cockpit`

Rules: lowercase ASCII slug (accents normalized, punctuation to hyphens),
deterministic word-boundary truncation to 60 chars, `untitled` fallback when
no title survives normalization. Runtime values (pane id, UUID, `worker-3`,
model, tier) are never inputs; technical ids stay in tokens for diagnostics.

## Usage

```bash
python scripts/herdr_workspaces.py name --work-id 482 --title "Actions storage"
python scripts/herdr_workspaces.py spawn --work-id 482 --title "Actions storage"
python scripts/herdr_workspaces.py ensure --work-id 482 --title "Actions storage"
python scripts/herdr_workspaces.py reconcile
python scripts/herdr_workspaces.py reassign --workspace-id w4P --work-id 368 --title "Cuisine strict mode"
python scripts/herdr_workspaces.py cleanup --workspace-id w4P
```

Safety: only workspaces carrying our managed tokens are ever renamed or
closed; unmanaged ones are reported as ignored. Closing or reassigning a
workspace whose agent is `working` requires `--force`.
