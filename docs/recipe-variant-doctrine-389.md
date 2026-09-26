# Doctrine variante / compatibilité — issue #389

Parent : https://github.com/CookiGram/cookigram/issues/389.
Socle : `docs/equipment-contract-495.md` (Equipment v2, inchangé), décision PO
titre-vs-métadonnées (commentaire #389 du 2026-09-20).

## 1. Règle : 1 plat = 1 fiche canonique = N variantes techniques

Le **titre porte l'identité culinaire du plat**. Le mode d'exécution, l'appareil,
la compatibilité marque/modèle et les propriétés pratiques sont des **métadonnées
structurées** (`variants`, `appliances`, tags utiles) présentées en contrôles
accessibles sur la fiche — jamais injectés dans le titre.

## 2. Variante technique vs compatibilité marque-modèle

- **Variante technique** : divergence procédurale utile (temps/pression, ordre
  d'étapes, quantité de liquide, accessoire ou contrainte spécifique). Exprimée
  en bloc `variants:` avec `id`, `name`, `description`, `prep_time`,
  `total_time`, `appliances` canoniques et `steps.replace` ciblés.
- **Compatibilité** : un appareil/modèle accepté **sans** divergence procédurale.
  Exprimée en valeur de la clé canonique (`pressure_cooker: [instant_pot,
  cookeo]`, `pizza_oven: [ooni, koda, …]`), jamais en variante distincte.
- **Une marque différente ne suffit pas à justifier une variante distincte.**

## 3. Contre-exemple anti-sur-normalisation

`One pot pasta épinards saumon` : `one pot` participe à l'identité culinaire et
technique du plat → **conservé dans le titre**. À l'inverse, `express`/`rapide`
est une **propriété** (représentée par la durée / un indicateur dédié), et
`Thermomix`/`Cookeo`/`Air Fryer` sont des **appareils** → candidats à sortir du
titre dès qu'ils sont représentés proprement ailleurs (variante ou compatibilité).

## 4. Compatibilités différées (arbitrage Human Owner 2026-09-26)

**Ninja Foodi** : zéro usage dans le corpus, les tests et le prototype. Restée
**hors du vocabulaire fermé** Equipment v2 — documentée ici comme compatibilité
différée, sans extension du contrat ni des tests #495. Réévaluer via
`docs/equipment-add-appliance.md` le jour d'un usage réel.

## 5. Référence : fiche Riz vapeur (pilote #389)

`Riz vapeur`, titre canonique sans appareil. Quatre variantes :
Casserole (`riz-blanc-long-casserole`), Thermomix (`riz-thermomix-mode-rice-cooker`,
TM5–TM7), Rice cooker (`riz-rice-cooker`, `[standard]`), Autocuiseur
(`pressure_cooker: [instant_pot, cookeo]` + `standard` traditionnel si procédure
validée). Marques au second niveau uniquement.
