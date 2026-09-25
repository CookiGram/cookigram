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
| `dense_qdrant.py` | **gate 2** : adaptateur Qdrant réel (requiert le venv expérimental, jamais le produit) |
| `benchmark_3way.py` | **gate 2** : plein vs lexical vs dense, 10 tâches (originales + paraphrases + hard + négatives) |
| `benchmark_3way_results.json` | résultats durables du gate 2 |
| `retrieval_metrics.py` | **gate 4** : retrieval (rank-1, recall@k) vs décision, pures stdlib |
| `freeze_dev.py` → `dev_freeze.json` | **gate 4** : point (τ=0.40, δ=0.03, γ=0.70) figé sur dev + sensibilité, pré-holdout |
| `holdout.json` (v2) | **gate 4** : 8 items aveugles, ancre H-D durcie pré-mesure |
| `ablation.py` → `ablation_results.json` | **gate 4** : UNE mesure holdout (sections×faits × politique×cluster) |
| `test_filters_dense.py` | **gate 4** : non-régression contrat `None` dense (F3, venv + serveur) |
| `scale_gen.py` / `scale_bench.py` → `scale_results.json` | preuve d'échelle 1k/10k/100k, **séparée** du holdout |

## 5. Gate 2 — Qdrant réel + dense local (2026-09-25)

Infra jetable, hors repo : binaire Qdrant 1.19.1 sur `127.0.0.1:6333`
(télémétrie off, data sous `/home/pierrecsn/.cache/qdrant-508-exp/data`,
supprimable), venv expérimental (`qdrant-client` + `fastembed`,
modèle `paraphrase-multilingual-MiniLM-L12-v2`, 384 dim, CPU/ONNX).
Aucun Cloud, aucune intégration produit, aucun hook de ré-index.

```bash
# serveur (data jetable) :
QDRANT__STORAGE__STORAGE_PATH=/home/pierrecsn/.cache/qdrant-508-exp/data \
QDRANT__SERVICE__HOST=127.0.0.1 QDRANT__TELEMETRY_DISABLED=true qdrant
# benchmark (venv expérimental) :
QDRANT_DATA_DIR=/home/pierrecsn/.cache/qdrant-508-exp/data \
  /home/pierrecsn/.cache/qdrant-508-exp/venv/bin/python prototype/qdrant-memory/benchmark_3way.py
```

Résultat : recall@3 moyen (8 requêtes avec réponse) lexical **0.54** vs
dense **0.75** ; contexte 44 456 tok → 210–1 100 tok dans les deux cas ;
latence ~10 ms ; collection 209 pts ≈ **2 Mo disque, ~70 Mo RSS**.
Échecs documentés dans `benchmark_3way_results.json` (P3 manquée des deux
côtés, N2 sans abstention même à τ=0.5, top-k mono-doc sans diversification).
Verdict : voir handoff sur #508 — pas une décision d'architecture.

## 6. Gate cas réalistes/difficiles (après crash, reprise sur `a256e8c`)

Reprise sans second lifecycle : résidu `abstention_*` revalidé à l'identique
par rerun (scores à 4 décimales, courbe et politique inchangés).
`scale_*.py` présents mais **non exécutés** (hors scope de ce gate).

- `mmr.py` + `search_mmr` (fetch 20, λ=0.5) : diversifie réellement
  (`mmr_results.json`) — H1/H2 ne gagnent pas en recall, H2 dilue la
  précision (doc hors sujet injecté), rank-1 préservé sur 4/4 cas,
  latence ×2 (~20 ms).
- `policy.py` (τ=0.40 + marge δ=0.03, post-hoc) : `abstention_results.json`
  — seuil seul insuffisant (N2/N4 fuient sous tout τ qui préserve le rappel),
  marge capte les 5 négatifs mais abstient à tort H2/D1 (candidats groupés).
- `agent_value.py` (`agent_tasks.json`, ancre exacte comme critère) :
  `agent_value_results.json` — plein 4/4, lexical 2/4, dense 2/4,
  dense+MMR+politique **0/4** + piège A5 abstenu (A4 perd son ancre
  `_site` après diversification MMR : rank-1 gold conservé mais
  contexte dilué). **Bon doc ≠ bon chunk.** Erratum gate 4 : les
  publications gate 3 annonçaient 1/4 par erreur de report — le JSON
  faisait foi (voir commentaire correctif sur #508).
- `test_gate3.py` : 6/6 OK (MMR, politique, schémas, ancres dans l'or).
