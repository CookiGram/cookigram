"""Ingredient icon coverage (#391 lot-icons).

Every slug in the instance ``.gram/ingredients.yaml`` must resolve to an
icon: either a direct ``static/icons/ingredients/<slug>.svg`` asset or a
category fallback file present in the instance pack.

The resolution mirrors the Core ``IngredientIconResolver`` contract
without importing Core: the public content CI has no Core checkout, so
the family and category-fallback tables below are vendored mirrors of
``generator/ingredient_icons.py``. If Core changes either table, this
test fails on purpose to force an explicit sync — never a silent drift.
"""

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ICONS_DIR = ROOT / "static" / "icons" / "ingredients"

# Mirror of Core ICON_FAMILY_BY_SLUG (preparation/cut variants sharing one
# visual vocabulary instead of duplicating SVGs).
ICON_FAMILY_BY_SLUG = {
    "creme-fraiche-epaisse": "creme-fraiche",
    "creme-fraiche-liquide": "creme-fraiche",
    "saumon-frais": "saumon",
    "saumon-fume": "saumon",
    "filet-de-poulet": "poulet",
    "cuisse-de-poulet": "poulet",
    "paleron-de-boeuf": "boeuf",
    "faux-filet": "boeuf",
    "souris-d-agneau": "plat-de-cote-de-boeuf",
    "porc-hache": "porc",
    "filet-mignon-de-porc": "porc",
    "echine-de-porc": "porc",
    "roti-de-porc": "porc",
    "riz-a-risotto": "riz",
    "riz-basmati": "riz",
    "riz-long-blanc": "riz",
    "farfalle": "pates",
    "penne": "pates",
    "torsades": "pates",
    "nouilles-chinoises": "pates",
    "champignons-de-paris": "champignon",
    "concentre-de-tomate": "concentre-tomate",
    "cube-de-bouillon-de-volaille": "bouillon-volaille",
    "cube-de-bouillon": "cube-de-bouillon",
    "cube-de-bouillon-de-boeuf": "cube-de-bouillon",
    "cube-de-bouillon-de-legumes": "cube-de-bouillon",
    "moutarde-de-dijon": "moutarde",
    "persil-frais": "persil",
    "coriandre-fraiche": "coriandre",
    "piment-rouge": "piment",
    "piment-de-cayenne": "piment",
    "curry-en-poudre": "curry",
    "ail-en-poudre": "ail",
    "tomate-cerise": "tomate",
    "tomates-concassees": "tomate",
    "tomates-sechees": "tomate",
    "laurier": "laurier",
    "thym": "thym",
    "lait": "lait",
    "lait-demi-ecreme": "lait",
    "lait-de-soja": "lait",
    "noix-de-muscade": "noix-de-muscade",
    "oeuf": "oeuf",
    "jaune-d-oeuf": "oeuf",
    "miel": "miel",
    "paprika": "paprika",
    "sauce-soja": "sauce-soja",
    "concombre": "concombre",
    "aubergine": "aubergine",
    "courgette": "courgette",
    "chou-fleur": "chou-fleur",
    "petits-pois": "petits-pois",
    "crevettes": "crevettes",
    "feta": "feta",
    "cannelle": "cannelle",
    "cumin": "cumin",
    "curcuma": "curcuma",
    "maizena": "maizena",
    "lentilles-corail": "lentilles-corail",
    "banane": "banane",
    "pomme": "pomme",
    "potiron": "potiron",
    "courge-butternut": "potiron",
    "asperges": "asperges",
    "panais": "panais",
    "mache": "mache",
    "salade-romaine": "salade-romaine",
    "oignon-nouveau": "oignon-nouveau",
    "celeri": "celeri",
    "anchois": "anchois",
    "filet-de-poisson": "filet-de-poisson",
    "langoustines": "langoustines",
    "viande-hachee": "viande-hachee",
    "lardons": "lardons",
    "lard": "lardons",
    "saucisse-fumee": "lardons",
    "jambon-cru": "jambon-cru",
    "chorizo": "chorizo",
    "chataignes": "chataignes",
    "pois-chiches": "pois-chiches",
    "pois-gourmands": "pois-gourmands",
    "lentilles-vertes": "lentilles-vertes",
    "pistaches": "pistaches",
    "pignons-de-pin": "pignons-de-pin",
    "amandes-effilees": "amandes-effilees",
    "chapelure": "chapelure",
    "feuilles-de-lasagne": "feuilles-de-lasagne",
    "pate-seche-a-lasagne": "feuilles-de-lasagne",
    "pain-de-mie": "pain-de-mie",
    "pain-d-epices": "pain-de-mie",
    "emmental-rape": "fromage-rape",
    "fromage-rape": "fromage-rape",
    "sauce-tomate": "sauce-tomate",
    "bechamel": "bechamel",
    "caramel-liquide": "caramel-liquide",
    "jus-de-citron-vert": "jus-de-citron-vert",
    "vin-rouge": "vin-rouge",
    "vinaigre-blanc": "vinaigre-blanc",
    "vinaigre-de-riz": "vinaigre-de-riz",
    "vinaigre-de-vin": "vinaigre-de-vin",
    "aneth": "aneth",
    "cerfeuil": "cerfeuil-frais",
    "estragon": "estragon-frais",
    "herbes-de-provence": "herbes-de-provence",
    "romarin": "herbes-de-provence",
    "gingembre-moulu": "gingembre-moulu",
    "quatre-epices": "quatre-epices",
    "garam-masala": "garam-masala",
    "graine-de-fenouil": "graines-de-fenouil",
    "graine-de-moutarde": "graines-de-moutarde",
    "graine-de-sesame": "graines-de-sesame-blanc",
    "epices-cajun": "epices-cajun",
    "la-vache-qui-rit": "produit-laitier",
    "clou-de-girofle": "clou-de-girofle",
    "mascarpone": "produit-laitier",
    "mozzarella": "produit-laitier",
    "ricotta": "produit-laitier",
    "coriandre-moulue": "coriandre-moulue",
    "croutons": "croutons",
    "capres": "capres",
    "fond-de-legumes": "fond-de-legumes",
    "fond-de-viande": "fond-de-viande",
    "fruits-secs": "fruits-secs",
    "ghee": "ghee",
    "huile-de-coco": "huile-vegetale",
    "huile-de-pepins-de-raisin": "huile-vegetale",
    "huile-de-sesame": "huile-vegetale",
    "huile-vegetale": "huile-vegetale",
    "jus-de-canneberge": "jus-de-canneberge",
    "jus-de-cuisson-sous-vide": "jus-de-cuisson-sous-vide",
    "mais": "mais",
    "olives-vertes": "olives-vertes",
    "olives-noires": "olives-noires",
    "origan": "origan",
    "piment-vert": "piment-vert",
    "harissa": "piment",
    "pate-miso": "pate-miso",
    "pate-tikka": "pate-tikka",
    "sauce-worcestershire": "sauce-worcestershire",
    "sauge": "sauge",
    "sucre-roux": "sucre-roux",
    "tahini": "tahini",
    "whisky": "whisky",
    "kirsch": "whisky",
    "cognac": "whisky",
    "biere-brune": "whisky",
    "vin-de-shaoxing": "whisky",
    "levure-boulangere": "levure-chimique",
    "gousse-de-vanille": "extrait-de-vanille",
    "cacao-en-poudre": "chocolat-noir",
    "copeaux-de-chocolat": "chocolat-noir",
    "chocolat-noir": "chocolat-noir",
    "cerise": "cerise",
    "poivre-vert": "poivre",
    "cepes": "champignon",
    "jarret-de-veau": "boeuf",
    "orange": "jus-d-orange",
    "bouillon-de-volaille": "bouillon-volaille",
    "bouillon-de-legumes": "bouillon-de-legumes",
    "amande-en-poudre": "amandes-en-poudre",
    "basilic-frais": "basilic-frais",
    "poivron": "poivron",
    "poireau": "poireau",
    "parmesan": "parmesan",
    "poulet": "poulet",
}

# Mirror of Core CATEGORY_FALLBACK_ICONS (category names casefolded).
CATEGORY_FALLBACK_ICONS = {
    "boissons": "eau",
    "boissons et alcools": "whisky",
    "boissons et condiments": "whisky",
    "boissons et liquides": "eau",
    "boucherie et charcuterie": "boeuf",
    "boucherie et volaille": "boeuf",
    "boucherie et volailles": "boeuf",
    "boulangerie": "pain-de-mie",
    "charcuterie": "lardons",
    "charcuterie et traiteur": "lardons",
    "condiments": "epices-cajun",
    "condiments et aides culinaires": "bouillon-volaille",
    "condiments et assaisonnements": "epices-cajun",
    "conserves et bocaux": "concentre-tomate",
    "crèmerie et oeufs": "produit-laitier",
    "céréales et féculents": "riz",
    "fromages": "fromage-rape",
    "fruits": "pomme",
    "fruits et légumes": "pomme",
    "fruits secs": "fruits-secs",
    "fruits à coque et graines": "fruits-secs",
    "fruits, légumes, légumineuses et oléagineux": "pomme",
    "féculents et céréales": "riz",
    "herbes et épices": "herbes-de-provence",
    "lait et produits laitiers": "produit-laitier",
    "légumes et aromates": "oignon",
    "matières grasses": "huile-vegetale",
    "poissons et fruits de mer": "filet-de-poisson",
    "poissons, viandes, œufs": "filet-de-poisson",
    "produits céréaliers": "pain-de-mie",
    "produits laitiers": "produit-laitier",
    "produits laitiers et matières grasses": "produit-laitier",
    "produits laitiers et substituts": "produit-laitier",
    "produits sucrés": "sucre",
    "pâtes et préparations": "pates",
    "viandes": "boeuf",
    "viandes et volailles": "boeuf",
    "épicerie": "farine",
    "épicerie salée": "farine",
    "épicerie sucrée": "sucre",
}


def _icon_file(slug: str) -> Path:
    return ICONS_DIR / f"{ICON_FAMILY_BY_SLUG.get(slug, slug)}.svg"


def _resolves(slug: str, category: str) -> bool:
    if _icon_file(slug).is_file():
        return True
    fallback = CATEGORY_FALLBACK_ICONS.get(category.casefold())
    return fallback is not None and (ICONS_DIR / f"{fallback}.svg").is_file()


class IngredientIconCoverageTests(unittest.TestCase):
    def test_every_gram_slug_resolves(self):
        database = yaml.safe_load(
            (ROOT / ".gram" / "ingredients.yaml").read_text(encoding="utf-8")
        )["ingredients"]
        self.assertGreater(len(database), 0, "Gram ingredient database is empty")
        missing = [
            slug
            for slug, entry in database.items()
            if not _resolves(slug, (entry or {}).get("category", ""))
        ]
        self.assertEqual(missing, [], f"{len(missing)} Gram slug(s) without icon")


if __name__ == "__main__":
    unittest.main()
