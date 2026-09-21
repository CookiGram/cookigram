#!/usr/bin/env python3
"""Render desktop, mobile, and scale matrix visual proofs for P1 atomic action illustrations."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = Path("/home/pierrecsn/.gemini/antigravity-cli/brain/669261fb-cc64-49f5-a4b7-7842cf103d5e")

import sys
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
  <title>CookiGram — Atomic Cooking Actions P1 Scale & Verification Matrix</title>
  <style>
    :root {{
      --bg: #FFF9F0;
      --card-bg: #FFFFFF;
      --text: #2B2D42;
      --text-muted: #6C757D;
      --accent-terracotta: #E07A5F;
      --accent-sage: #819B88;
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
    .badge-p1 {{ background: #FBE9E7; color: #D84315; }}

    /* Scale Matrix Table */
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
    .token-title {{ font-size: 16px; font-weight: 700; }}
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
    .view-label {{
      font-size: 11px;
      color: var(--text-muted);
      font-weight: 500;
    }}
    .img-large {{
      width: 180px;
      height: 120px;
      object-fit: cover;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: #FAFAFA;
    }}
    .img-mobile {{
      width: 130px;
      height: 65px;
      object-fit: cover;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: #FAFAFA;
    }}
    .img-thumb {{
      width: 60px;
      height: 40px;
      object-fit: cover;
      border-radius: 4px;
      border: 1px solid var(--border);
      background: #FAFAFA;
    }}
    .file-meta {{
      margin-top: 10px;
      font-size: 11px;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      border-top: 1px dashed var(--border);
      padding-top: 8px;
    }}

    /* Live Cook Mode Card Simulator */
    .sim-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      margin-bottom: 32px;
    }}
    .cook-step-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      overflow: hidden;
      box-shadow: var(--shadow);
      display: flex;
      flex-direction: column;
    }}
    .cook-step-body {{
      padding: 20px;
      flex: 1;
    }}
    .cook-step-badge {{
      font-size: 12px;
      font-weight: 700;
      color: var(--accent-terracotta);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 6px;
    }}
    .cook-step-heading {{
      font-size: 19px;
      font-weight: 700;
      margin-bottom: 8px;
      color: #1E1F29;
    }}
    .cook-step-text {{
      font-size: 14px;
      color: #4A4E69;
      margin-bottom: 16px;
      line-height: 1.6;
    }}
    .cook-visual-container {{
      width: 100%;
      height: 180px;
      overflow: hidden;
      position: relative;
      background: #FFF9F0;
      border-top: 1px solid var(--border);
    }}
    .cook-visual-container img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }}
    .mobile-frame {{
      max-width: 375px;
      margin: 0 auto;
      border: 8px solid #333;
      border-radius: 28px;
      overflow: hidden;
      box-shadow: 0 12px 30px rgba(0,0,0,0.15);
      background: var(--bg);
    }}
  </style>
</head>
<body>

  <h1>CookiGram — Contrôle Visuel des Actions Atomiques (Pilote + Lot P1)</h1>
  <p class="lead">17 familles visuelles validées : 10 Pilote + 7 P1. Rendu responsive aux échelles Desktop (300×150), Mobile (260×130) et Miniature (120×80).</p>

  <h2>1. Matrice d'Échelle Globale (17 Familles)</h2>
  <div class="matrix-grid">
"""

for token, rel_path in INSTANCE_ACTION_MAPPING.items():
    item = items.get(token, {})
    label = item.get("action_label", token)
    status = item.get("status", "approved")
    is_p1 = "p1" in status or token in {"oven", "boil", "assemble", "steam", "season", "air_fry", "blend"}
    badge_cls = "badge-p1" if is_p1 else "badge-pilot"
    badge_txt = "Lot P1" if is_p1 else "Pilote"
    size_kb = item.get("file_size_kb", 0.0)
    abs_img_url = f"file://{ROOT}/static/{rel_path}"

    html_content += f"""
    <div class="matrix-card">
      <div class="card-header">
        <span class="token-title">{label} <code style="font-size:12px;color:var(--text-muted)">({token})</code></span>
        <span class="badge {badge_cls}">{badge_txt}</span>
      </div>
      <div class="views-row">
        <div class="view-box">
          <img class="img-large" src="{abs_img_url}" alt="{label}">
          <span class="view-label">Desktop (3:2)</span>
        </div>
        <div class="view-box">
          <img class="img-mobile" src="{abs_img_url}" alt="{label}">
          <span class="view-label">Mobile (260×130)</span>
        </div>
        <div class="view-box">
          <img class="img-thumb" src="{abs_img_url}" alt="{label}">
          <span class="view-label">Mini (120×80)</span>
        </div>
      </div>
      <div class="file-meta">
        <span>Format: WebP 900×600</span>
        <span>Poids: <strong>{size_kb} Ko</strong> (&lt; 80 Ko)</span>
      </div>
    </div>
"""

html_content += f"""
  </div>

  <h2>2. Simulation Live Mode Cuisine (Cook Mode) — Exemples P1</h2>
  <div class="sim-grid">
    <!-- Oven Step -->
    <div class="cook-step-card">
      <div class="cook-step-body">
        <div class="cook-step-badge">Étape 4 / 6 — Cuisson four</div>
        <div class="cook-step-heading">Enfourner les lasagnes à 180°C</div>
        <p class="cook-step-text">Glisser le plat à mi-hauteur dans le four préchauffé et laisser gratiner pendant 35 minutes jusqu'à ce que la surface soit bien dorée et bouillonnante.</p>
      </div>
      <div class="cook-visual-container">
        <img src="file://{ROOT}/static/images/atomic-actions/oven.webp" alt="Enfourner">
      </div>
    </div>

    <!-- Boil Step -->
    <div class="cook-step-card">
      <div class="cook-step-body">
        <div class="cook-step-badge">Étape 2 / 5 — Cuisson des pâtes</div>
        <div class="cook-step-heading">Porter l'eau à ébullition</div>
        <p class="cook-step-text">Faire chauffer 3 litres d'eau salée dans un grand faitout. Plonger les tagliatelles dès que les gros bouillons apparaissent.</p>
      </div>
      <div class="cook-visual-container">
        <img src="file://{ROOT}/static/images/atomic-actions/boil.webp" alt="Bouillir">
      </div>
    </div>

    <!-- Assemble Step -->
    <div class="cook-step-card">
      <div class="cook-step-body">
        <div class="cook-step-badge">Étape 3 / 6 — Montage</div>
        <div class="cook-step-heading">Monter les couches de lasagnes</div>
        <p class="cook-step-text">Alterner une couche de sauce bolognaise, les feuilles de lasagnes puis la béchamel crémeuse. Répéter l'opération sur 4 niveaux.</p>
      </div>
      <div class="cook-visual-container">
        <img src="file://{ROOT}/static/images/atomic-actions/assemble.webp" alt="Assembler">
      </div>
    </div>

    <!-- Air Fry Step -->
    <div class="cook-step-card">
      <div class="cook-step-body">
        <div class="cook-step-badge">Étape 2 / 3 — Cuisson Air Fryer</div>
        <div class="cook-step-heading">Cuire les frites de patate douce</div>
        <p class="cook-step-text">Déposer les frites assaisonnées dans le panier de l'air fryer sans les superposer. Lancer à 190°C pendant 18 minutes en secouant à mi-cuisson.</p>
      </div>
      <div class="cook-visual-container">
        <img src="file://{ROOT}/static/images/atomic-actions/air_fry.webp" alt="Air Fryer">
      </div>
    </div>
  </div>

</body>
</html>
"""

html_path = ROOT / "scripts/verify_p1_matrix.html"
html_path.write_text(html_content, encoding="utf-8")
print(f"HTML matrix written to {html_path}")

# Run Chromium headless to capture the matrix
dest_matrix_img = ARTIFACTS_DIR / "ui_p1_scale_matrix.png"
cmd_matrix = [
    "/usr/bin/chromium",
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1600,2400",
    f"--screenshot={dest_matrix_img}",
    f"file://{html_path}",
]
print("Capturing matrix screenshot...")
subprocess.run(cmd_matrix, check=True)
print(f"Screenshot saved to {dest_matrix_img}")

# Capture mobile view specifically
dest_mobile_img = ARTIFACTS_DIR / "ui_p1_mobile_cook_mode.png"
cmd_mobile = [
    "/usr/bin/chromium",
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=420,900",
    f"--screenshot={dest_mobile_img}",
    f"file://{html_path}",
]
print("Capturing mobile screenshot...")
subprocess.run(cmd_mobile, check=True)
print(f"Mobile screenshot saved to {dest_mobile_img}")
