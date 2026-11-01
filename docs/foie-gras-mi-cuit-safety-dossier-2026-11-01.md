# Dossier de qualification sanitaire — foies gras mi-cuits en bocal

**État : BLOCKED — dossier de préparation, pas une recette ni une autorisation de cuisson/publication.**
État des fichiers vérifié contre le HEAD exact de la PR #534 :
`34a604411bd7d316ac265ab857f60855127eb793` (`feat/issue-533-agent-e0f6c4a3`), le 1 novembre 2026.
La PR est ouverte. Le contrôle public de publication de ce dépôt exclut les cinq slugs
ci-dessous de `recipes/`; il est réversible après qualification indépendante documentée.

## Décision et limites des éléments disponibles

Aucune source examinée n'établit un procédé sûr pour les charges décrites, dans le bocal
de 500 ml décrit, avec mesure au point froid, valeur létale ciblée, refroidissement validé
et durée de vie réfrigérée spécifique. Le couple `55 °C / ~80 min` des `.gram` et le
couple `65 °C / 150 min` de la description de PR ne sont donc pas conservés ou proposés
comme substituts. La mention de « terrine 500 g » sur une source de recette ne prouve pas
l'équivalence de contenant, de charge ou de profil thermique.

L'ANSES décrit des facteurs de maîtrise propres au foie gras et précise que le traitement
mi-cuit n'est pas le traitement destiné à inactiver la toxine botulinique; sa conclusion
insiste sur la chaîne du froid. Ce rapport éclaire les dangers, mais ne qualifie aucun des
deux barèmes CookiGram. [Rapport ANSES 2019-SA-0114, § 3.4.2.2, pp. 70–71](https://www.anses.fr/fr/system/files/BIORISK2019SA0114Ra-1.pdf#page=70).

Le NCHFP explique que la position du point froid et la pénétration de chaleur varient avec
la forme et taille du bocal, la texture et taille des morceaux, le ratio solide/liquide,
l'empilement et la température initiale. Il décrit des essais de pénétration instrumentés,
suivis d'une détermination de létalité et d'une confirmation microbiologique pour une
conserve peu acide. C'est un cadre méthodologique, pas un barème transposable au foie gras
réfrigéré. [NCHFP, Heat Processing of Home-canned Foods](https://nchfp.uga.edu/resources/entry/backgrounder-heat-processing-of-home-canned-foods).

Le FDA Food Code est un modèle de règles pour le commerce alimentaire américain; ses
critères ne constituent pas une recette domestique. Il documente toutefois que le
refroidissement d'aliments nécessitant un contrôle temps/température est défini par une
trajectoire mesurée et non par un bain glacé d'une durée présumée. [FDA Food Code 2022,
§§ 3-501.14 et 3-502.12](https://www.fda.gov/food/fda-food-code/food-code-2022).

## Matrice des variantes et des données manquantes

Les faits de charge ci-dessous sont relevés dans le contenu de la PR #534. Les champs
marqués **à mesurer / documenter** ne sont pas déductibles du volume nominal du bocal.
Les masses arithmétiques ci-dessous additionnent les quantités explicitement données dans
les `.gram`; elles ne remplacent pas la pesée de la charge finale après marinade et pertes.

| Variante | Charge documentée au niveau des Gram | Masse totale / géométrie | Bocal, fermeture, joint, dimensions, espace de tête | Inclusions pertinentes | Procédé thermique instrumenté requis | Cible microbiologique et preuves requises |
|---|---|---|---|---|---|---|
| Nature au sel | 450 g foie cru + 4,5 g sel | **454,5 g** avant pertes; volume tassé, hauteur de remplissage et poche d'air **à documenter** | 500 ml annoncé; type/référence du verre, compatibilité thermique, type de couvercle, état/matériau du joint, diamètre/hauteur intérieurs **inconnus**; headspace « 1–2 cm » est une consigne déclarée, non mesurée/validée | Sel; mélange foie/gras et lobes non homogène | Courbe bain et produit depuis départ réel, montée, maintien, inertie et refroidissement; emplacement du point froid à déterminer par thermocouples | Spécialiste à définir dangers pertinents (dont *C. botulinum* selon chaîne du froid/emballage réduit en oxygène, *Listeria monocytogenes*, *Salmonella*); cible de réduction, modèle/valeur létale et confirmation microbiologique **à établir** |
| Poivre vert | 450 g foie + 4,5 g sel + 4,5 g poivre vert égoutté | **459 g** avant pertes; déplacement volumique, tassement, hauteur de remplissage **à mesurer** | Même spécification manquante que nature; aucun plan coté fourni | Grains concassés répartis dans les lobes; effet sur homogénéité/point froid **non étudié** | Profil complet au point froid, avec inclusion et charge exacte | Cible, challenge/justification de réduction et durée de vie **à établir** pour cette matrice |
| Armagnac / quatre-épices | 450 g foie + 4,5 g sel + 4,7 g quatre-épices + 13,5 ml Armagnac | **459,2 g de solides + 13,5 ml de liquide** avant pertes; masse finale, liquide retenu/égoutté, tassement et volume final **à mesurer** (densité non renseignée) | Même spécification manquante que nature | Liquide alcoolisé et épices; effet sur la matrice et la chaleur **non validé** | Profil complet au point froid; composition réelle de départ et géométrie fixées | Cible, effet de formulation et durée de vie **à établir** |
| Truffe noire | 450 g foie + 4,5 g sel + 11 g truffe | **465,5 g** avant pertes; volume des lamelles, tassement et hauteur de remplissage **à mesurer** | Même spécification manquante que nature | Lamelles intercalées entre lobes; points de contact et poches éventuelles **non étudiés** | Profil complet au point froid dans configuration finale | Cible, protocole microbio et durée de vie **à établir** |
| Sauternes / figue sèche | **350 g foie + 127 g figues + 3,5 g sel + 10,5 ml Sauternes** | **480,5 g de solides + 10,5 ml de liquide** avant pertes; masse finale, déplacement volumique, tassement/porosité et hauteur de remplissage **à mesurer** (densité non renseignée). Ce n'est pas la charge de 450 g foie seul. | Même spécification manquante que nature; headspace indiqué mais non vérifié | Figue en bâtonnets intercalée, Sauternes; ratio solide/liquide et positionnement au froid **non qualifiés** | Étude distincte ou démonstration expérimentale de représentativité; ne pas transférer le résultat des quatre autres variantes | Cible et durée de vie **à établir séparément**; valider le pire cas compositionnel et géométrique |

Dans les cinq fiches, la méthode réellement écrite est un bocal **ouvert** dans un sac
extérieur scellé, plongé dans un bain. La description de la PR annonce au contraire un
bocal **fermé directement** dans le bain, sans sac. Ces montages ne sont pas interchangeables
par présomption. Le modèle exact du bocal, du couvercle et du joint n'est pas identifié.

## Profil, bain et conservation : protocole à demander à l'expert

Le dossier de qualification devra spécifier, sans extrapolation :

1. La référence commerciale, les plans/dimensions intérieures, le matériau/fermeture/joint,
   la compatibilité fabricant avec le cycle, le headspace mesuré et la méthode de fermeture.
2. Le poids net final et la géométrie de chaque charge, le départ froid/chaud, le tassement,
   l'orientation, le ratio solide/liquide et le placement dans le bain.
3. L'étalonnage traçable du thermoplongeur et de sondes indépendantes sur la plage concernée,
   l'uniformité du bain, sa récupération après immersion, la profondeur/espacement des pots,
   et les conditions de charge maximale/minimale.
4. Des essais de pénétration de chaleur multi-points pour localiser le point froid, puis des
   enregistrements indépendants de température en ce point pendant la montée, l'éventuel
   maintien, l'inertie après arrêt et toute la phase de refroidissement. Résolution,
   exactitude, fréquence d'acquisition, incertitude et répétitions devront être documentées.
5. La décision d'un spécialiste sur les dangers, la cible microbiologique, la réduction
   requise et la méthode de calcul/validation; confirmation en laboratoire ou challenge test
   si indiqué. Ne pas déduire de cible d'un autre produit, d'un autre emballage ou d'une
   recette en ligne.
6. Une étude de durée de vie réfrigérée sur le produit et l'emballage retenus, avec limites
   de température réalistes, critères microbiologiques/sensoriels, dates d'échantillonnage,
   nombre de lots et justification statistique. Jusqu'à cette preuve, **aucun nombre de jours
   n'est établi**. La chaîne du froid et toute instruction de refroidissement doivent être
   rédigées par l'expert après examen des profils mesurés.

Le rapport ANSES souligne l'importance de la chaîne du froid pour le foie gras mi-cuit; cela
ne suffit pas à démontrer une durée de trois jours pour cette formulation et ce procédé.
Le repère de bain glacé de 30 min est également non vérifié comme critère de température à
cœur. Une durée fixe seule ne prouve pas le refroidissement.

## Proposition éditoriale minimale pour les cinq `.gram`

Patch ciblé à appliquer à la branche de recettes après examen indépendant; aucune instruction
de cuisson de remplacement :

- Supprimer les lignes exécutables `régler à 55 °C et cuire ~80 min`, la phrase d'observation
  qui présente cette cuisson comme aboutie, et la référence de barème importée d'une terrine.
- Supprimer le bain glacé `~30 min` comme garantie de refroidissement; remplacer le macro
  d'exécution par une mention de statut **« préparation suspendue — procédé et refroidissement
  non qualifiés; ne pas exécuter »** uniquement si le schéma Gram permet une étape non
  exécutable. Sinon, garder les fichiers hors du répertoire `recipes/`.
- Retirer `conservation.fridge_days: 3`, la consigne « consommer dans les 3 jours » et le
  total de cuisson/maturation qui suggère une durée de procédé complète. Ne pas introduire
  de nouveau délai ou de nouvelle température.
- Ne pas substituer `65 °C / 150 min` de la description PR. Harmoniser source, auteur,
  contenant, fermeture et équipement seulement après choix et qualification du procédé réel.
- Garder ingrédients, provenance, prompts et images existants; la barrière de catalogue
  n'efface ni les fichiers sources éventuels ni les actifs visuels.

L'exclusion est réversible après qu'une preuve indépendante couvre la formule, la charge, le
contenant, le cycle complet, le refroidissement et toute durée revendiquée. Le script exige
la liste de slugs complète codée en dur; retirer un slug du JSON seul échoue. Une recette
exclue ne doit pas apparaître dans le catalogue public ou l'aperçu construit.

## Barrière et responsabilités

`.gram/publication-exclusions.json` liste les cinq slugs et `scripts/check-publication-exclusions.py`
impose cette liste ainsi que l'identité canonique `foie-gras-de-canard-cru`, codées dans le
script pour que le JSON ne puisse pas les retirer. L'entrée canonique et ses trois alias source
sont également exigés dans `.gram/ingredients.yaml`; leur suppression, renommage ou collision
avec un autre ID fait échouer le contrôle. Le garde lit les mentions d'ingrédients `@...{}` et
résout chaque nom/alias via le registre. Pour couvrir un ID alternatif ajouté à un duplicata
intégral, il reconnaît aussi la signature étroite du procédé #534 : bocal 500 ml ouvert dans
sac sous vide, bain à 55 °C et 80 min. Un foie de canard frais sauté avec l'alias générique
`foie de canard` reste autorisé; il n'a ni l'ID bloqué ni cette signature. Les mots en prose,
description ou source ne suffisent pas à déclencher le garde. Un manifeste ou registre manquant
ou malformé fait échouer le contrôle.

La CI publique l'exécute avant validation, build, aperçu et déploiement Pages. Les tests
injectent une copie complète renommée et réécrite, un alias paraphrasé résolu au même ID,
un nouvel ID canonique avec la méthode d'origine, un manifeste/registre incomplet et des
contrôles négatifs (foie de volaille, foie de canard frais sauté, magret sous vide avec mention
éditoriale, gras de canard et pâté végétal). C'est une barrière catalogue contre l'ajout à
`main`, pas une nouvelle capacité de filtre à la volée dans Core. Un moteur qui ingère un
répertoire fourni par un tiers doit respecter sa propre configuration de filtrage; cette
capacité reste à établir dans `cookigram-core` si nécessaire.

**Déblocage de #534 :** la PR reste BLOCKED indépendamment du statut CI. Il faut une qualification
indépendante, une revue de la matrice et des fiches corrigées, puis vérifier la barrière,
le catalogue et tout chemin d'aperçu/build avant toute décision de publication.
