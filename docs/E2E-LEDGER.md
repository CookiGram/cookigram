# Journal runtime E2E (ledger)

[`scripts/e2e_ledger.py`](../scripts/e2e_ledger.py) est le journal durable des
runs end-to-end : un fichier JSONL horodaté par run sous
`docs/e2e-runs/<run-id>.jsonl`. Il comble le trou constaté — avant lui, aucun
journal durable n'existait hors `claims.json` (état de coordination éphémère,
pas un journal de run) — et donne une base de reprise après interruption.

## Format

Une ligne = un objet JSON. Champs communs : `ts` (UTC ISO 8601, suffixe `Z`),
`run_id`, `seq` (1, 2, 3…), `type` (`run_started` | `event` | `run_finished`).

- `run_started` : `title`, `actor`.
- `event` : `phase`, `status` (`ok` | `ko` | `skip` | `info`), `detail`, plus
  tout objet passé via `--data-json`.
- `run_finished` : `result` (`pass` | `fail`), `summary`.

## Utilisation

Depuis la racine du dépôt :

```bash
python scripts/e2e_ledger.py init --run-id 2026-09-22-smoke --title "smoke local"
python scripts/e2e_ledger.py log --run-id 2026-09-22-smoke --phase build --status ok --detail "bundle hermétique"
python scripts/e2e_ledger.py close --run-id 2026-09-22-smoke --result pass --summary "tout vert"
python scripts/e2e_ledger.py show --run-id 2026-09-22-smoke
```

`init` refuse d'écraser un ledger existant sauf `--force`. `log` et `close`
échouent (code 2) si le run n'a pas été initialisé. `--data-json` doit être un
objet JSON. `--ledger-dir` redirige l'écriture (pratique pour les tests :
`--ledger-dir /tmp/e2e-runs-test`) ; par défaut `docs/e2e-runs/`.

## Reprise après interruption

1. `python scripts/e2e_ledger.py show --run-id <id>` rejoue le journal.
2. La dernière ligne donne le point de reprise : dernier `phase`/`status`, ou
   `run_finished` si le run est terminé (rien à reprendre).
3. Relancer à partir de la première phase non `ok` avec le même `--run-id`
   (nouveaux `seq` ajoutés, historique préservé), puis `close`.

## Où ça écrit — et où ça n'écrit jamais

- Écrit uniquement `docs/e2e-runs/<run-id>.jsonl` (ou le `--ledger-dir`
  explicite). Les fichiers de run sont des artefacts locaux : ils ne sont pas
  versionnés, à part une remontée en artefact CI si besoin.
- N'écrit JAMAIS dans `.agents/claims.json`, `.builder.json`,
  `.core-version`, `.github/workflows/*`, ni dans `recipes/*` (corpus gelé,
  PR #427). Le script résout chaque cible et refuse (code 2) toute écriture
  hors du répertoire ledger ou vers ces surfaces, ainsi que tout `--run-id`
  hors `[A-Za-z0-9._-]` ou tout `--ledger-dir` hors dépôt.
