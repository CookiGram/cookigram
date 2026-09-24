"""Instance identity contract (#391).

`site-config.yaml` is the single canonical source for the instance
identity consumed by the Core builder (generator/instance.py). The PWA
seed `static/manifest.webmanifest` must stay coherent with it. No Core
change, no general site config.
"""

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# Mirror of the Color Theme Contract owned by Core
# (cookigram-core generator/instance.py THEMES). If Core changes a color,
# this test fails on purpose: the seed manifest must follow deliberately,
# never drift silently.
CORE_THEME_COLORS = {
    "light": "#fffaf1",
    "dark": "#161514",
    "halloween": "#1e1a20",
    "christmas": "#fbf6ea",
}


def _config() -> dict:
    data = yaml.safe_load((ROOT / "site-config.yaml").read_text(encoding="utf-8"))
    assert isinstance(data, dict), "site-config.yaml must contain a mapping"
    return data


def _manifest() -> dict:
    data = json.loads((ROOT / "static/manifest.webmanifest").read_text(encoding="utf-8"))
    assert isinstance(data, dict), "manifest seed must be a JSON object"
    return data


def _resolve_asset(path: str) -> Path:
    assert isinstance(path, str) and path.strip(), "asset path must be a non-empty string"
    clean = path.strip().replace("\\", "/")
    assert not clean.startswith("/") and ".." not in Path(clean).parts, f"asset path must be relative: {path}"
    candidate = ROOT / "static" / clean.removeprefix("static/").removeprefix("assets/")
    assert candidate.is_file(), f"asset referenced but missing: {path}"
    return candidate


def test_site_config_is_valid() -> None:
    config = _config()
    site = config.get("site", {})
    assert isinstance(site.get("name"), str) and site["name"].strip()
    assert isinstance(site.get("tagline"), str) and site["tagline"].strip()
    assert isinstance(site.get("url"), str) and site["url"].startswith("https://")

    branding = config.get("branding", {})
    _resolve_asset(branding.get("logo", ""))
    _resolve_asset(branding.get("favicon", ""))

    theme = config.get("theme", {})
    available = theme.get("available", [])
    assert isinstance(available, list) and available, "theme.available must be non-empty"
    assert set(available) <= set(CORE_THEME_COLORS), f"unknown theme IDs: {set(available) - set(CORE_THEME_COLORS)}"
    assert theme.get("default") in available, "theme.default must be listed in theme.available"

    illustrations = config.get("illustrations", {})
    assert isinstance(illustrations.get("style"), str) and illustrations["style"].strip()


def test_manifest_seed_matches_identity() -> None:
    config = _config()
    manifest = _manifest()
    name = config["site"]["name"]
    assert manifest.get("name") == name
    assert manifest.get("short_name") == name

    expected_color = CORE_THEME_COLORS[config["theme"]["default"]]
    assert manifest.get("theme_color") == expected_color
    assert manifest.get("background_color") == expected_color

    icons = manifest.get("icons", [])
    assert isinstance(icons, list) and icons, "seed manifest must declare icons"
    for icon in icons:
        _resolve_asset(icon.get("src", ""))


def test_no_general_site_config_sprawl() -> None:
    config = _config()
    allowed = {"site", "branding", "theme", "illustrations", "typography"}
    assert set(config) <= allowed, f"site-config.yaml must stay identity-only: {set(config) - allowed}"
    assert set(config.get("site", {})) <= {"name", "tagline", "url"}, "site section must stay identity-only"
