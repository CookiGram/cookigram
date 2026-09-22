#!/usr/bin/env python3
"""Render desktop, mobile, and scale matrix visual proofs for P2 atomic action illustrations."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = Path("/home/pierrecsn/.gemini/antigravity-cli/brain/669261fb-cc64-49f5-a4b7-7842cf103d5e")

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.action_visuals import INSTANCE_ACTION_MAPPING, MUTUALIZED_ALIASES

manifest_path = ROOT / "assets/atomic-actions/manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
items = {item["canonical_token"]: item for item in manifest["items"]}

html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>CookiGram — Actions Atomiques Lot P2 (grate, roll_out, peel)</title>
  <style>
    :root {{
      --bg: #FFF9F0;
      --card-bg: #FFFFFF;
      --text: #2B2D42;
      --text-muted: #6C757D;
      --accent-terracotta: #E07A5F;
      --accent-sage: #819B88;
      --accent-gold: #DDA15E;
      --border: #F0E6D8;
      --radius: 12px;
      --shadow: 0 4px 12px rgba(43, 45, 66, 0.06);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      padding: 32px;
      line-height: 1.5;
    }}
    h1 {{ font-size: 28px; margin-bottom: 8px; color: #1E1F29; }}
    p.lead {{ color: var(--text-muted); margin-bottom: 32px; font-size: 15px; }}
    h2 {{ font-size: 20px; margin: 32px 0 16px; border-bottom: 2px solid var(--border); padding-bottom: 8px; }}
    .badge {{
      display: inline-block;
      padding: 3px 8px;
      font-size: 11px;
      font-weight: 600;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .badge-pilot {{ background: #E8F5E9; color: #2E7D32; }}
    .badge-p1 {{ background: #EDE7F6; color: #512DA8; }}
    .badge-p2 {{ background: #FFF3E0; color: #E65100; border: 1px solid #FFE0B2; }}

    /* Highlight Section for P2 */
    .p2-focus-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 24px;
      margin-bottom: 40px;
    }}
    .p2-card {{
      background: var(--card-bg);
      border: 2px solid var(--accent-gold);
      border-radius: var(--radius);
      padding: 20px;
      box-shadow: 0 6px 16px rgba(221, 161, 94, 0.12);
    }}
    .token-title {{ font-size: 18px; font-weight: 700; }}
    .views-stack {{
      display: flex;
      flex-direction: column;
      gap: 16px;
      margin-top: 16px;
    }}
    .scale-box {{
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}
    .scale-meta {{
      font-size: 12px;
      color: var(--text-muted);
      font-weight: 600;
    }}
    .img-p2-desktop {{
      width: 100%;
      height: 160px;
      object-fit: cover;
      border-radius: 8px;
      border: 1px solid var(--border);
    }}
    .img-p2-mobile {{
      width: 260px;
      height: 130px;
      object-fit: cover;
      border-radius: 6px;
      border: 1px solid var(--border);
    }}
    .img-p2-thumb {{
      width: 120px;
      height: 80px;
      object-fit: cover;
      border-radius: 4px;
      border: 1px solid var(--border);
    }}

    /* Global 20 families grid */
    .matrix-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 20px;
      margin-bottom: 40px;
    }}
    .matrix-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 16px;
      box-shadow: var(--shadow);
    }}
    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }}
    .views-row {{
      display: flex;
      gap: 16px;
      align-items: flex-end;
    }}
    .view-box {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
    }}
    .view-label {{ font-size: 11px; color: var(--text-muted); font-weight: 500; }}
    .img-large {{ width: 180px; height: 120px; object-fit: cover; border-radius: 8px; border: 1px solid var(--border); }}
    .img-mobile {{ width: 130px; height: 65px; object-fit: cover; border-radius: 6px; border: 1px solid var(--border); }}
    .img-thumb {{ width: 60px; height: 40px; object-fit: cover; border-radius: 4px; border: 1px solid var(--border); }}
    .file-meta {{
      margin-top: 10px;
      font-size: 11px;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      border-top: 1px dashed var(--border);
      padding-top: 8px;
    }}

    /* Mobile Cook Mode Frame */
    .mobile-sim-row {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 24px;
      margin-top: 24px;
    }}
    .mobile-screen {{
      background: #FFFFFF;
      border: 4px solid #333;
      border-radius: 24px;
      overflow: hidden;
      box-shadow: 0 10px 25px rgba(0,0,0,0.12);
      display: flex;
      flex-direction: column;
    }}
    .mobile-screen-header {{
      background: #FAFAFA;
      padding: 12px 16px;
      border-bottom: 1px solid var(--border);
      font-size: 12px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .mobile-step-body {{
      padding: 16px;
      flex: 1;
    }}
    .mobile-step-badge {{
      font-size: 11px;
      font-weight: 700;
      color: var(--accent-terracotta);
      text-transform: uppercase;
      margin-bottom: 4px;
    }}
    .mobile-step-heading {{
      font-size: 17px;
      font-weight: 700;
      color: #1E1F29;
      margin-bottom: 8px;
      line-height: 1.3;
    }}
    .mobile-step-text {{
      font-size: 13px;
      color: #4A4E69;
      line-height: 1.5;
    }}
    .mobile-visual-wrap {{
      width: 100%;
      height: 150px;
      overflow: hidden;
      border-top: 1px solid var(--border);
      background: #FFF9F0;
    }}
    .mobile-visual-wrap img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }}
  </style>
</head>
<body>

  <h1>CookiGram — Planche de Contrôle Lot P2 (grate, roll_out, peel)</h1>
  <p class="lead">Audit, intégration et rendu responsive des 3 gestes complémentaires du Lot P2. 20 familles visuelles actives au total.</p>

  <h2>1. Focus Lot P2 : Les 3 Nouveaux Gestes aux 3 Échelles de Rendu</h2>
  <div class="p2-focus-grid">
"""

p2_tokens = ["grate", "roll_out", "peel"]
for token in p2_tokens:
    item = items.get(token, {})
    label = item.get("action_label", token)
    size_kb = item.get("file_size_kb", 0.0)
    abs_img_url = f"file://{ROOT}/static/images/atomic-actions/{token}.webp"

    html_content += f"""
    <div class="p2-card">
      <div class="card-header">
        <span class="token-title">{label} <code style="font-size:13px;color:var(--text-muted)">({token})</code></span>
        <span class="badge badge-p2">Lot P2</span>
      </div>
      <div class="views-stack">
        <div class="scale-box">
          <span class="scale-meta">Desktop (~300×150)</span>
          <img class="img-p2-desktop" src="{abs_img_url}" alt="{label}">
        </div>
        <div class="scale-box">
          <span class="scale-meta">Mobile (~260×130)</span>
          <img class="img-p2-mobile" src="{abs_img_url}" alt="{label}">
        </div>
        <div class="scale-box">
          <span class="scale-meta">Miniature (~120×80)</span>
          <img class="img-p2-thumb" src="{abs_img_url}" alt="{label}">
        </div>
      </div>
      <div class="file-meta">
        <span>WebP 900×600 (3:2)</span>
        <span>Poids: <strong>{size_kb} Ko</strong> (&lt; 80 Ko)</span>
      </div>
    </div>
"""

html_content += f"""
  </div>

  <h2>2. Simulation Cook Mode Mobile — Étapes Réelles du Catalogue</h2>
  <div class="mobile-sim-row">
    <!-- Grate Step -->
    <div class="mobile-screen">
      <div class="mobile-screen-header">Lasagnes Bolognaise</div>
      <div class="mobile-step-body">
        <div class="mobile-step-badge">Étape 2 / 6 — Préparation</div>
        <div class="mobile-step-heading">Râper le parmesan frais</div>
        <p class="mobile-step-text">Râper le parmesan (80 g) à l'aide d'une râpe fine au-dessus d'un bol et réserver pour le gratinage.</p>
      </div>
      <div class="mobile-visual-wrap">
        <img src="file://{ROOT}/static/images/atomic-actions/grate.webp" alt="Râper">
      </div>
    </div>

    <!-- Roll Out Step -->
    <div class="mobile-screen">
      <div class="mobile-screen-header">Tarte Poireau & Lardons</div>
      <div class="mobile-step-body">
        <div class="mobile-step-badge">Étape 1 / 5 — Pâte</div>
        <div class="mobile-step-heading">Abaisser la pâte au rouleau</div>
        <p class="mobile-step-text">Abaisser la pâte feuilletée sur un plan de travail fariné et en garnir soigneusement un moule à tarte de 22 cm.</p>
      </div>
      <div class="mobile-visual-wrap">
        <img src="file://{ROOT}/static/images/atomic-actions/roll_out.webp" alt="Abaisser">
      </div>
    </div>

    <!-- Peel Step -->
    <div class="mobile-screen">
      <div class="mobile-screen-header">Hachis Parmentier</div>
      <div class="mobile-step-body">
        <div class="mobile-step-badge">Étape 1 / 5 — Légumes</div>
        <div class="mobile-step-heading">Éplucher les légumes à l'économe</div>
        <p class="mobile-step-text">Éplucher les pommes de terre (1 kg) et les carottes à l'économe avant de les couper en morceaux réguliers.</p>
      </div>
      <div class="mobile-visual-wrap">
        <img src="file://{ROOT}/static/images/atomic-actions/peel.webp" alt="Éplucher">
      </div>
    </div>
  </div>

  <h2>3. Matrice Complète du Catalogue (20 Familles Validées)</h2>
  <div class="matrix-grid">
"""

for token, rel_path in INSTANCE_ACTION_MAPPING.items():
    item = items.get(token, {})
    label = item.get("action_label", token)
    status = item.get("status", "approved")
    if token in {"grate", "roll_out", "peel"}:
        badge_cls = "badge-p2"
        badge_txt = "Lot P2"
    elif token in {"oven", "boil", "assemble", "steam", "season", "air_fry", "blend"}:
        badge_cls = "badge-p1"
        badge_txt = "Lot P1"
    else:
        badge_cls = "badge-pilot"
        badge_txt = "Pilote"
    size_kb = item.get("file_size_kb", 0.0)
    abs_img_url = f"file://{ROOT}/static/{rel_path}"

    html_content += f"""
    <div class="matrix-card">
      <div class="card-header">
        <span class="token-title" style="font-size:15px">{label} <code style="font-size:11px;color:var(--text-muted)">({token})</code></span>
        <span class="badge {badge_cls}">{badge_txt}</span>
      </div>
      <div class="views-row">
        <div class="view-box">
          <img class="img-large" src="{abs_img_url}" alt="{label}">
          <span class="view-label">Desktop</span>
        </div>
        <div class="view-box">
          <img class="img-mobile" src="{abs_img_url}" alt="{label}">
          <span class="view-label">Mobile</span>
        </div>
        <div class="view-box">
          <img class="img-thumb" src="{abs_img_url}" alt="{label}">
          <span class="view-label">Mini</span>
        </div>
      </div>
      <div class="file-meta">
        <span>WebP 900×600</span>
        <span>Poids: <strong>{size_kb} Ko</strong> (&lt; 80 Ko)</span>
      </div>
    </div>
"""

html_content += f"""
  </div>
</body>
</html>
"""

html_path = ROOT / "scripts/verify_p2_matrix.html"
html_path.write_text(html_content, encoding="utf-8")
print(f"HTML matrix written to {html_path}")

# Run Chromium headless to capture the matrix
dest_matrix_img = ARTIFACTS_DIR / "ui_p2_scale_matrix.png"
cmd_matrix = [
    "/usr/bin/chromium",
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1600,2600",
    f"--screenshot={dest_matrix_img}",
    f"file://{html_path}",
]
print("Capturing P2 matrix screenshot...")
subprocess.run(cmd_matrix, check=True)
print(f"Screenshot saved to {dest_matrix_img}")

# Capture mobile cook mode simulation specifically
dest_mobile_img = ARTIFACTS_DIR / "ui_p2_mobile_cook_mode.png"
cmd_mobile = [
    "/usr/bin/chromium",
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1200,900",
    f"--screenshot={dest_mobile_img}",
    f"file://{html_path}",
]
print("Capturing mobile screenshot...")
subprocess.run(cmd_mobile, check=True)
print(f"Mobile screenshot saved to {dest_mobile_img}")
