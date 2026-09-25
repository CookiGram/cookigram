# Qdrant mémoire/retrieval — prototype isolé (#508)

> **Statut : exploration réversible.** Aucune intégration à `cookigram-mcp`,
> aucune dépendance produit CookiGram → Qdrant, aucun merge sans validation PO.
> GitHub + artefacts durables restent la source de vérité ; Qdrant n'est qu'un
> **index dérivé** (reconstructible, supprimable).

## 1. Architecture proposée (cible réelle)

```
canonique (vérité)                dérivé (jetable)
─────────────────                ─────────────────
GitHub issues/PRs/comments ─┐
docs/, decisions/            ├─► indexation (chunks + embeddings + payload) ─► Qdrant
.agents/claims.json, ledger ─┘         ▲ re-index à chaque changement canonique
                                       │
agent ──► retrieval (top-k + filtres) ─┘──► contexte injecté + citations
```

- **Une collection** `agent_memory` : chunks de sections (`path` + ancre `##`),
  payload `{project, work_id, kind, path, section, updated_at, sha}`.
- **Payload indexes** Qdrant sur `project`, `work_id`, `kind` (filtres `must`).
- **Retrieval** : `search(top_k=3..5, filter={must:[project, work_id?]},
  score_threshold)` → injecte uniquement les chunks retournés, avec citation
  `(path, section)`. Jamais d'écriture canonique depuis Qdrant.
- **Cycle de vie** : ré-indexé sur changement canonique (futur hook CI) ;
  l'éphémère runtime (panes, outputs bruts) n'est **pas** indexé tel quel —
  seul un résumé durable peut l'être, avec TTL court.
- **Données exclues** : secrets, tokens Herdr, contenus non versionnés.

## 2. Ce que contient ce prototype (substitut local, stdlib uniquement)

Qdrant réel indisponible ici (pas de serveur, pas de dépendance ajoutée —
politique du dépôt). `store.py` expose donc la **même surface minimale**
(`upsert` / `search` avec filtres `must`, seuil, citations) avec des
embeddings TF-IDF hashés déterministes. Le passage au vrai Qdrant consiste à
remplacer `embed()` par un modèle dense + `Collection` par `qdrant-client`,
**sans changer** le schéma payload, les filtres ni la stratégie top-k —
voir `QDRANT_MAP` dans `store.py`.

## 3. Reproductibilité / réversibilité

```bash
python3 prototype/qdrant-memory/benchmark.py   # index + benchmark avant/après
python3 -m unittest prototype.qdrant-memory.test_store -v  # (ou) python3 prototype/qdrant-memory/test_store.py
```

Supprimer `prototype/qdrant-memory/` + la branche `chore/qdrant-memory-508`
annule 100 % du chantier. Rien d'autre n'est touché.

## 4. Fichiers

| Fichier | Rôle |
|---|---|
| `store.py` | surface Qdrant-compatible minimale + embeddings stdlib + `QDRANT_MAP` |
| `corpus_manifest.py` | construit le corpus depuis les artefacts durables réels du repo |
| `benchmark.py` | 3 tâches représentatives, mesures avant/après |
| `benchmark_results.json` | résultats durables du dernier run (à régénérer) |
| `test_store.py` | tests `unittest`, zéro dépendance |
