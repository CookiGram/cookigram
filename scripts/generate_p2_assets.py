#!/usr/bin/env python3
"""Process, normalize, and generate P2 atomic action assets, SVGs, prompts, and manifest updates."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

P2_ASSETS = {
    "grate": {
        "source": "/home/pierrecsn/.gemini/antigravity-cli/brain/669261fb-cc64-49f5-a4b7-7842cf103d5e/action_grate_zest_1790021477264.jpg",
        "action_label": "Râper / Zester",
        "prompt": "Modern editorial culinary illustration of hands grating parmesan cheese with a stainless steel microplane grater over a wooden bowl, delicate cheese shavings falling, a yellow lemon with fresh zest nearby, clean culinary composition, warm cream background, terracotta linen accent, gentle gouache textures, soft organic lighting, simple harmonious color palette, high contrast silhouette for mobile readability, non-photorealistic, quiet kitchen atmosphere, no face, no text, no watermark, no digital UI icons.",
        "justification": "Hands using a microplane grater over a wooden bowl with falling shreds and fresh citrus zest. Instantly recognizable grating gesture, distinct from chopping or slicing.",
        "mutualized_tokens": ["zest", "microplane", "shred_cheese", "grater", "zester", "finely_grate"],
    },
    "roll_out": {
        "source": "/home/pierrecsn/.gemini/antigravity-cli/brain/669261fb-cc64-49f5-a4b7-7842cf103d5e/action_roll_out_dough_1790021494973.jpg",
        "action_label": "Abaisser / Étaler la pâte",
        "prompt": "Modern editorial culinary illustration of hands using a wooden rolling pin to roll out pastry dough into a smooth round sheet on a lightly floured countertop, delicate dusting of flour, clean culinary composition, warm cream background, sage green linen towel accent, gentle gouache textures, soft organic lighting, simple harmonious color palette, high contrast silhouette for mobile readability, non-photorealistic, quiet kitchen atmosphere, no face, no text, no watermark, no digital UI icons.",
        "justification": "Hands holding a rolling pin rolling dough flat on a floured board. Clear pastry archetype distinct from manual kneading.",
        "mutualized_tokens": ["roll_dough", "flatten_dough", "rolling_pin", "roll_flat", "sheet_dough", "abaisser"],
    },
    "peel": {
        "source": "/home/pierrecsn/.gemini/antigravity-cli/brain/669261fb-cc64-49f5-a4b7-7842cf103d5e/action_peel_vegetable_1790021510878.jpg",
        "action_label": "Éplucher / Peler",
        "prompt": "Modern editorial culinary illustration of hands holding a wooden-handled Y-peeler peeling a fresh carrot, thin curl of carrot peel coming off onto a wooden cutting board, clean culinary composition, warm cream background, terracotta linen napkin accent, gentle gouache textures, soft organic lighting, simple harmonious color palette, high contrast silhouette for mobile readability, non-photorealistic, quiet kitchen atmosphere, no face, no text, no watermark, no digital UI icons.",
        "justification": "Hands peeling a carrot with an économe/peeler with ribbon peel curls. Unmistakable peeling prep gesture distinct from knife chopping.",
        "mutualized_tokens": ["vegetable_peel", "skin_vegetables", "econome", "pare", "peeling"],
    },
}


def main():
    static_images_dir = ROOT / "static/images/atomic-actions"
    static_svg_dir = ROOT / "static/illustrations/cooking-actions/v1"
    prompts_dir = ROOT / "image-prompts/atomic-actions"
    manifest_path = ROOT / "assets/atomic-actions/manifest.json"

    static_images_dir.mkdir(parents=True, exist_ok=True)
    static_svg_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["updated_at"] = "2026-09-21T22:15:00+02:00"
    existing_tokens = {item["canonical_token"] for item in manifest["items"]}

    for token, info in P2_ASSETS.items():
        src_img = Image.open(info["source"]).convert("RGB")
        resized = src_img.resize((900, 600), Image.Resampling.LANCZOS)
        dest_webp = static_images_dir / f"{token}.webp"
        resized.save(dest_webp, format="WEBP", quality=82, method=6)

        data = dest_webp.read_bytes()
        size_kb = round(len(data) / 1024, 1)
        sha = hashlib.sha256(data).hexdigest()

        # Generate data-URI SVG wrapper
        b64_data = base64.b64encode(data).decode("ascii")
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 600" width="100%" height="100%">
  <title>{info['action_label']}</title>
  <image width="900" height="600" href="data:image/webp;base64,{b64_data}" />
</svg>
"""
        dest_svg = static_svg_dir / f"{token}.svg"
        dest_svg.write_text(svg_content, encoding="utf-8")

        # Generate prompt markdown file
        tokens_list = "\n".join(f"- `{t}`" for t in info["mutualized_tokens"])
        prompt_md = f"""# Prompt CookiGram — Action Culinaire : {info['action_label']} (`{token}`)

## Métadonnées
- **Action ID** : `{token}`
- **Token canonique** : `{token}`
- **Statut** : P2 validé
- **Dimensions source** : 900×600 (ratio 3:2)
- **Format** : WebP ({size_kb} Ko) + wrapper SVG data-URI
- **SHA256** : `{sha}`
- **Générateur** : Imagen 3 (`imagegeneration@006`)
- **Date** : 2026-09-21

## Contrat Visuel d'Instance
- **Style** : Gouache éditoriale douce / soft cel-shading culinaire
- **Palette** : Fonds lin crème `#FFF9F0` / grège `#F7EFE2`, accents terracotta `#E07A5F`, vert sauge `#819B88`, inox et bois clair
- **Cadrage** : Vue 3/4 plongeante ~40–45°, silhouette contrastée pour lisibilité mobile (260×130) et compact (120×80)
- **Présence humaine** : Mains / avant-bras en action active uniquement (aucun visage, aucun corps entier)
- **Interdictions** : Aucun texte, aucun chiffre, aucun minuteur/timer, aucune température, aucune icône UI

## Prompt Utilisé
```text
{info['prompt']}
```

## Negative Prompt
```text
photorealism, 3d render, photograph, cartoon, anime chibi, faces, full body, text, letters, watermarks, timer, clock, digital icons, kitchen chaos, blurry
```

## Justification Sémantique & Mutualisation
{info['justification']}

Tokens mutualisés :
{tokens_list}
"""
        dest_prompt = prompts_dir / f"{token}.md"
        dest_prompt.write_text(prompt_md, encoding="utf-8")

        # Update manifest
        if token not in existing_tokens:
            manifest["items"].append({
                "action_id": token,
                "action_label": info["action_label"],
                "canonical_token": token,
                "status": "p2_approved",
                "asset_path": f"images/atomic-actions/{token}.webp",
                "model_name": "Imagen 3",
                "model_version": "imagegeneration@006",
                "generation_date": "2026-09-21",
                "aspect_ratio": "3:2",
                "dimensions": "900x600",
                "file_size_bytes": len(data),
                "file_size_kb": size_kb,
                "sha256": sha,
                "contract_version": "1.0.0",
                "prompt": info["prompt"],
                "negative_prompt": "photorealism, 3d render, photograph, cartoon, anime chibi, faces, full body, text, letters, watermarks, timer, clock, digital icons, kitchen chaos, blurry",
                "mutualized_tokens": info["mutualized_tokens"],
                "justification": info["justification"],
            })

        print(f"Processed {token:12s}: WebP = {size_kb:5.1f} KB (budget < 80 KB), SVG = {len(dest_svg.read_bytes())/1024:5.1f} KB, SHA = {sha[:12]}...")

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nManifest updated. Total catalog items now: {len(manifest['items'])}")


if __name__ == "__main__":
    main()
