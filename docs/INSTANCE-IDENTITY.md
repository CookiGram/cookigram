# Identité d'instance (#391)

## Source canonique

[`site-config.yaml`](../site-config.yaml) est la seule source de l'identité
de l'instance CookiGram. Elle est lue par le builder Core
(`generator/instance.py`, contrat `docs/INSTANCE_IDENTITY.md` côté Core) ;
aucune donnée Core n'est déplacée ici et aucun changement Core n'est requis.

Contenu strictement identitaire : `site` (name, tagline, url), `branding`
(logo, favicon), `theme` (default, available), `illustrations` (style).
Ni navigation, ni URLs métier, ni contenu, ni comportement PWA, ni réglage
fonctionnel : le test `test_no_general_site_config_sprawl` l'interdit.

## Cohérence vérifiée automatiquement

`tests/test_instance_identity.py` contrôle :

- validité du YAML et des champs (url https, theme.default ∈ available,
  IDs de thème connus du contrat Core, chemins d'assets existants) ;
- `static/manifest.webmanifest` (graine PWA) : `name` et `short_name`
  égaux à `site.name`, couleurs égales à la couleur effective du thème
  par défaut, icônes existantes.

Note : le builder réécrit name, description, couleurs, `start_url` et
icônes du manifest au build depuis `site-config.yaml`. La graine versionnée
reste alignée sur ces valeurs effectives au lieu de prétendre le contraire.
La table des couleurs par thème dans le test est un miroir volontaire du
contrat Core : si Core change une couleur, le test échoue pour forcer un
suivi explicite, jamais une dérive silencieuse.
