#!/usr/bin/env python3
"""Process, normalize, and generate P1 atomic action assets, SVGs and prompts."""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

P1_ASSETS = {
    "oven": {
        "source": "/home/pierrecsn/.gemini/antigravity-cli/brain/669261fb-cc64-49f5-a4b7-7842cf103d5e/action_oven_bake_1790020498788.jpg",
        "action_label": "Enfourner / Cuisson au four",
        "prompt": "Modern editorial culinary illustration of sliding a ceramic baking dish into a warm oven using fabric kitchen oven mitts, gentle golden glow, clean culinary composition, warm cream background, terracotta linen accent, gentle gouache textures, soft organic lighting, simple harmonious color palette, high contrast silhouette for mobile readability, non-photorealistic, quiet kitchen atmosphere, no face, no text, no watermark, no digital UI icons.",
        "justification": "Hands in quilted oven mitts sliding a ceramic baking dish into the oven. Instantly readable as oven baking/roasting/preheating, distinct from stovetop cooking.",
        "mutualized_tokens": ["preheat", "bake", "roast", "broil", "gratin", "baking", "in_oven"],
    },
    "boil": {
        "source": "/home/pierrecsn/.gemini/antigravity-cli/brain/669261fb-cc64-49f5-a4b7-7842cf103d5e/action_boil_pot_1790020511814.jpg",
        "action_label": "Bouillir / Cuire à l'eau",
        "prompt": "Modern editorial culinary illustration of a stainless steel cooking pot with boiling water, rolling bubbles on the water surface and soft gentle steam rising, clean culinary composition, warm cream background, terracotta linen napkin accent, gentle gouache textures, soft organic lighting, simple harmonious color palette, high contrast silhouette for mobile readability, non-photorealistic, quiet kitchen atmosphere, no face, no text, no watermark, no digital UI icons.",
        "justification": "Stainless cooking pot with clear rolling boil bubbles and rising steam. Distinct from thick simmering sauce.",
        "mutualized_tokens": ["rolling_boil", "blanch", "poach", "pasta_boil", "water_cook"],
    },
    "assemble": {
        "source": "/home/pierrecsn/.gemini/antigravity-cli/brain/669261fb-cc64-49f5-a4b7-7842cf103d5e/action_assemble_layer_1790020524218.jpg",
        "action_label": "Assembler / Garnir",
        "prompt": "Modern editorial culinary illustration of assembling ingredients, hands using a spatula to spread a creamy layer and carefully arrange layers in a rectangular baking dish, clean culinary composition, warm cream background, terracotta linen napkin accent, gentle gouache textures, soft organic lighting, simple harmonious color palette, high contrast silhouette for mobile readability, non-photorealistic, quiet kitchen atmosphere, no face, no text, no watermark, no digital UI icons.",
        "justification": "Hands layering and spreading ingredients in a baking dish. Captures constructive building steps (lasagna, layered bakes, bowls) distinct from final plate presentation.",
        "mutualized_tokens": ["layer", "garnish_intermediate", "spread_layer", "mount", "stuff", "fill"],
    },
    "steam": {
        "source": "/home/pierrecsn/.gemini/antigravity-cli/brain/669261fb-cc64-49f5-a4b7-7842cf103d5e/action_steam_basket_1790020538848.jpg",
        "action_label": "Cuire à la vapeur",
        "prompt": "Modern editorial culinary illustration of a traditional bamboo steamer basket on a kitchen countertop, lid slightly lifted with gentle wisps of soft steam rising from tender green vegetables inside, clean culinary composition, warm cream background, sage green linen accent, gentle gouache textures, soft organic lighting, simple harmonious color palette, high contrast silhouette for mobile readability, non-photorealistic, quiet kitchen atmosphere, no face, no text, no watermark, no digital UI icons.",
        "justification": "Steaming tier basket with lid lifted and gentle steam. Immediately identifies steam/varoma cooking without immersion in liquid.",
        "mutualized_tokens": ["varoma", "bamboo_steam", "steam_cook", "steamer"],
    },
    "season": {
        "source": "/home/pierrecsn/.gemini/antigravity-cli/brain/669261fb-cc64-49f5-a4b7-7842cf103d5e/action_season_pinch_1790020553431.jpg",
        "action_label": "Assaisonner / Saupoudrer",
        "prompt": "Modern editorial culinary illustration of hands delicately pinching and sprinkling sea salt and aromatic herbs over ingredients on a plate, grains falling gently, small wooden salt cellar nearby, clean culinary composition, warm cream background, terracotta linen accent, gentle gouache textures, soft organic lighting, simple harmonious color palette, high contrast silhouette for mobile readability, non-photorealistic, quiet kitchen atmosphere, no face, no text, no watermark, no digital UI icons.",
        "justification": "Hand sprinkling salt and herbs from fingertips over food. Distinct seasoning gesture, not pouring liquid.",
        "mutualized_tokens": ["salt", "pepper", "spice", "sprinkle", "coat", "marinate_season"],
    },
    "air_fry": {
        "source": "/home/pierrecsn/.gemini/antigravity-cli/brain/669261fb-cc64-49f5-a4b7-7842cf103d5e/action_air_fry_basket_1790020567310.jpg",
        "action_label": "Cuire à l'air fryer",
        "prompt": "Modern editorial culinary illustration of a hand holding the handle of an air fryer basket, showing crispy golden roasted potatoes and vegetables inside the perforated drawer, clean culinary composition, warm cream background, sage green linen accent, gentle gouache textures, soft organic lighting, simple harmonious color palette, high contrast silhouette for mobile readability, non-photorealistic, quiet kitchen atmosphere, no face, no text, no watermark, no digital UI icons.",
        "justification": "Hand holding air fryer drawer basket with crispy golden ingredients. Clear modern appliance archetype.",
        "mutualized_tokens": ["crisp_air_fry", "airfryer_basket", "shake_basket"],
    },
    "blend": {
        "source": "/home/pierrecsn/.gemini/antigravity-cli/brain/669261fb-cc64-49f5-a4b7-7842cf103d5e/action_blend_soup_1790020584387.jpg",
        "action_label": "Mixer / Réduire en purée",
        "prompt": "Modern editorial culinary illustration of a hand holding an immersion stick blender inside a stainless cooking pot, blending a vibrant smooth carrot and pumpkin soup, gentle swirl in the puree, clean culinary composition, warm cream background, terracotta linen napkin accent, gentle gouache textures, soft organic lighting, simple harmonious color palette, high contrast silhouette for mobile readability, non-photorealistic, quiet kitchen atmosphere, no face, no text, no watermark, no digital UI icons.",
        "justification": "Hand holding an immersion stick blender pureeing soup in a pot. Unambiguous mechanical blending gesture, distinct from manual stirring.",
        "mutualized_tokens": ["puree", "crush_food", "immersion_blend", "liquidize", "smoothie_blend"],
    },
}


def main():
    static_images_dir = ROOT / "static/images/atomic-actions"
    static_svg_dir = ROOT / "static/illustrations/cooking-actions/v1"
    prompts_dir = ROOT / "image-prompts/atomic-actions"

    static_images_dir.mkdir(parents=True, exist_ok=True)
    static_svg_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for token, info in P1_ASSETS.items():
        src_img = Image.open(info["source"]).convert("RGB")
        resized = src_img.resize((900, 600), Image.Resampling.LANCZOS)
        dest_webp = static_images_dir / f"{token}.webp"
        resized.save(dest_webp, format="WEBP", quality=82, method=6)

        data = dest_webp.read_bytes()
        size_kb = len(data) / 1024
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

        # Mutualized tokens bullets
        tokens_list = "\n".join(f"- `{t}`" for t in info["mutualized_tokens"])

        # Generate prompt markdown file
        prompt_md = f"""# Prompt CookiGram — Action Culinaire : {info['action_label']} (`{token}`)

## Métadonnées
- **Action ID** : `{token}`
- **Token canonique** : `{token}`
- **Statut** : P1 validé
- **Dimensions source** : 900×600 (ratio 3:2)
- **Format** : WebP ({size_kb:.1f} Ko) + wrapper SVG data-URI
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

        results[token] = {
            "size_kb": size_kb,
            "sha256": sha,
            "svg_bytes": len(dest_svg.read_bytes()),
        }
        print(f"Processed {token:12s}: WebP = {size_kb:5.1f} KB (budget: <80KB), SVG = {len(dest_svg.read_bytes())/1024:5.1f} KB, SHA = {sha[:12]}...")

    print("\nAll 7 P1 assets successfully normalized and written.")
    return results


if __name__ == "__main__":
    main()
