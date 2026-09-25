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
- `test_gate3.py` : 6/6 OK au gate 3 (MMR, politique, schémas, ancres dans l'or).

## 7. Gate 4 — freeze dev + UNE mesure holdout + preuve scale (2026-09-26)

Point figé sur dev (`dev_freeze.json`, pré-holdout) : τ=0.40, δ=0.03
(politique publiée, testée telle quelle), γ=0.70 (bras cluster,
hypothèse négative : dev sans séparation, inter-sim pièges >
réponses). Contrat `work_id=None` = nul/absent des deux côtés (F3,
`test_filters_dense.py`). Métriques séparées (`retrieval_metrics.py`) :
rank-1 + recall@3 (retrieval) vs correction conditionnelle (décision).

`ablation_results.json` (8 items v2, sections×faits × politique×cluster,
zéro retuning, négatifs conservés) :
- Retrieval : faits recall@3 **0.7** > lexical 0.5 > sections dense **0.3**
  (rank-1 : 0.4 partout). **Le dense-sections ne généralise pas**
  (dev 0.75 → holdout 0.3) ; le chunking domine le choix de méthode.
- Succès : D (faits+cluster) 5/8, B (faits+politique) 4/8,
  A=C (sections) 3/8. Décision indulgente : D 0.875, B 0.75, A=C 0.625.
- La politique sur-abstient (H-A : s1=0.387, retrieval correct) et
  fuit avec confiance côté sections (H-B, H-N3 : marge 0.055/0.089).
- γ ne change qu'1 décision/8 (H-D : inter=0.701, marge 0.001) :
  signal inutile en l'état — résultat négatif conservé.
- Trappes H-N2 et OOD H-N1 abstenu(e)s par les 4 cellules ; H-C
  (paraphrase) gagnée par les seuls faits ; H-E montre la limite
  inverse (faits sans ancre). Tokens : 44 456 → 9–999.

`scale_results.json` (**provenance séparée**, run lane voisin adopté,
script commis non modifié) : 1k/10k embeddings réels (36.2 chunks/s,
re-index ≈ embed+upsert), 100k proxy aléatoire serveur seul ;
disque 3.9/37/554 Mo, latences **serveur seul** p50 ~1.4–2.1 ms
(vecteurs pré-calculés, hors embedding — non comparable au gate 2
bout-en-bout), RSS = processus serveur total. Projection 100k
réels : ~46 min CPU one-shot + payloads `_text` non mesurés.

## 8. Gate 4 — mesure holdout (run unique, 2026-09-26)

Figés **avant** mesure (`6a3e9d0`, aucune mesure holdout à ce stade) :
`holdout.json` v2 (8 items, ancre H-D durcie unknown vers forme exacte),
`dev_freeze.json` (τ=0.40, δ=0.03, γ=0.70 + sensibilité, dev uniquement),
`policy.py` (GAMMA=0.70, bras hypothétique négatif : dev sans séparation),
contrat F3 `None` (parité `store`/`dense_qdrant`, `test_filters_dense.py`).
Mesure unique, aucun retuning post-hoc :

```bash
FASTEMBED_CACHE_PATH=/home/pierrecsn/.cache/opencode-bun-tmp/fastembed_cache \
QDRANT_DATA_DIR=/home/pierrecsn/.cache/qdrant-508-exp/data \
/home/pierrecsn/.cache/qdrant-508-exp/venv/bin/python prototype/qdrant-memory/ablation.py
# → ablation_results.json (sec=209 chunks / fact=881 chunks, top_k=3)
```

Succès answer = ≥1 gold path top-3 ET ≥1 ancre dans le contexte ;
succès abstain = 0 chunk injecté. Résultat brut (`ablation_results.json`) :

| Méthode | succès answer (5) | succès global (8) | rank-1 | recall@3 | décision stricte/indulgente |
|---|---|---|---|---|---|
| lexical sec (réf) | 3/5 | — | 0.40 | 0.50 | — |
| dense brut sec | 2/5 | — | 0.40 | 0.30 | — |
| dense brut fact | 3/5 | — | 0.40 | 0.70 | — |
| A sec+politique | — | 3/8 | 0.40 | 0.30 | 0.50 / 0.625 |
| B fact+politique | — | 4/8 | 0.40 | 0.70 | 0.625 / 0.75 |
| C sec+cluster | — | 3/8 | 0.40 | 0.30 | 0.50 / 0.625 |
| D fact+cluster | — | **5/8** | 0.40 | 0.70 | **0.75 / 0.875** |

Item par item (A/B/C/D) : H-A 0/0/0/0 (retrieval parfait partout, politique
abstient à tort : s1=0.387<τ, marge 0.009) ; H-B 0/0/0/0 sauf B/D abstention
lucide (retrieval 0.0 partout, sec répond à tort) ; H-C B=D=1 (seul le fact
récupère) ; H-D D=1 seul (cluster inter=0.701 ≥ 0.70 — bascule à 0.001,
fragile) ; H-E A=C=1, B=D=0 (top-3 fact 100 % mono-doc `MEAL_PLANNING_NUTRITION.md`
sans `kiffs` ni `benefits_from` dans le contexte : rappel partiel 0.5
mais ancre perdue — même dilution que A4 gate 3) ;
H-N1 1 partout (s1<τ) ; H-N2 1 partout (marge/cluster — piège dev capté) ;
H-N3 B=D=1, A=C=0 (**fuite sec** : s1=0.486 marge=0.089, le fact sauve).

Limites : n=8, aucune puissance statistique ; γ=0.70 ne fait basculer qu'un
item au seuil près ; H-E strict/indulgent divergent (multi-gold partiel) ;
aucune mesure qualité à l'échelle. F3 (crash contrat `None` dense) résolu :
`test_filters_dense.py` 5/5 + parité stdlib. Tests : `test_store` 8/8,
`test_gate3` 9/9, YAML public OK. Verdict : voir handoff sur #508 —
pas une décision d'architecture.
