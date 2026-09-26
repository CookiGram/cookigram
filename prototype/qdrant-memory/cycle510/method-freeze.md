# Cycle 510 — gel méthodologique avant dev

Statut : **method-freeze + split pré-enregistré**. Aucun dev, gold holdout,
calibration ou mesure n'est inclus dans ce commit.

Autorisation Human Owner : `ANCHOR_DISJOINT_GO`, propre à
`CookiGram/cookigram#510`.

## Périmètre et précédent

Ce cycle explore l'ancrage et la décision retrieval, distinctement de #508.
Il reprend le formalisme durable de cycle2b (#508) : corpus fermé, golds
adossés à des preuves source, split fixé avant génération, artefacts versionnés
et tests déterministes sans Qdrant. Il ne copie, ne modifie et n'utilise aucun
gold de cycle2b comme donnée de réglage. Les cycles #508 restent gelés.

Dérogation locale à #510 : les documents peuvent être partagés entre dev et
holdout, mais les ancres/golds ne le peuvent pas. Le split ci-dessous choisit
des documents disjoints, plus strictement que l'autorisation, pour garantir
l'étanchéité sans examiner de gold holdout. Cette dérogation ne change pas le
contrat méthodologique standing.

## Documents admissibles

Liste fermée (libellé corrigé par réparation arbitrée
`FREEZE_REPAIR_GO` : la mention « non golds » était fausse —
voir section Réparation). Le chevauchement documentaire avec
#508 est autorisé ; l'interdiction porte sur les ancres :

| Document | Sections `##` | Affectation pré-enregistrée |
|---|---:|---|
| `AGENTS.md` | 5 | dev |
| `README.en.md` | 9 | dev |
| `GEMINI.md` | 10 | réserve holdout |
| `.agents/roles/README.md` | 3 | réserve holdout |

Total structurel : 27 slots de section, 14 côté dev et 13 côté réserve.
Le compte provient uniquement des titres `##`; aucun contenu ni gold holdout
n'a été consulté pour choisir le split. Aucune autre source n'est admissible.
Slots utilisables après exclusion des sections contaminées par des ancres
#508 (voir Réparation) : dev 13 (`AGENTS.md::h2:2` exclu), réserve 12
(`.agents/roles/README.md::h2:3` exclu).

## Réparation arbitrée FREEZE_REPAIR_GO (Human Owner)

Constat : `AGENTS.md` et `.agents/roles/README.md` ONT été des golds
mesurés du holdout cycle2b (`H2-V-direct`, `H2-W-para`), contrairement
au libellé « non golds » initial. Règle appliquée : le partage de
chemins documentaires avec #508 est autorisé, mais aucune ancre/gold
#508 ne peut être réutilisée ; la disjonction porte sur l'ancre, pas
sur le document. Méthode déterministe : `forbidden_508.json` liste les
75 ancres consommées/mesurées des items dev+holdout #508 (7 fichiers,
cycles 1/2/2b) ; toute section `##` des 4 docs contenant l'une d'elles
est exclue (`AGENTS.md::h2:2` via `Standard des recettes`,
`.agents/roles/README.md::h2:3` via `Spécialités de l'équipe`) ; toute
réutilisation verbatim ou reformulation équivalente de ces cibles est
interdite. Le dev-set perd `510-dev-002` sans remplacement (aucune
section propre libre côté dev) : 13 items. La réserve garde 12 slots
exploitables. Négatifs/abstain : le protocole pré-enregistré ne définit
aucune calibration tau/delta ni politique ; 0 négatif requis à ce stade.
Une future calibration de politique exigerait amendement + négatifs + GO.

## Définition exacte d'une ancre/gold

Un gold answerable est une question dont la réponse est une proposition
atomique, vérifiable dans une preuve contiguë à l'intérieur d'une seule
section `##` d'un document admissible. Le gold contient la question, la réponse
attendue, le chemin source, le chemin complet des titres jusqu'à `##`, et la
citation de preuve. Maximum : un gold par section `##`.

L'identité canonique d'ancre est le localisateur de section
`<path POSIX>::h2:<ordinal>` (ordinal `##` à base 1, dans le fichier au commit
pré-enregistré). Le chemin est relatif POSIX, normalisé Unicode NFC, sensible à
la casse. Cet identifiant ne dépend ni de la formulation de la question, ni du
texte du titre, ni d'un identifiant de ligne : reformuler ou ré-IDer le même
gold dans la même section ne peut pas créer une autre ancre. Le chemin complet
des titres est conservé pour la citation lisible.

Chaque gold a aussi un `proposition_key` sémantique stable, défini avant la
rédaction de la question et normalisé NFC, casefold, espaces Unicode repliés
et ponctuation périphérique retirée. Toute formulation triviale/paraphrase de
la même proposition doit garder cette clé, même si un auteur choisit un autre
document ou identifiant. Les gates rejettent l'intersection des clés
sémantiques entre les splits lorsqu'un holdout sera autorisé. La section
source est l'identité mécanique de l'ancre ; cette clé bloque les doublons
sémantiques d'une même réponse sous un autre localisateur.

## Pré-enregistrement du split

Le split est déterminé ici, avant tout gold dev :

- dev : toutes les sections `##` d'`AGENTS.md` et `README.en.md` ;
- réserve holdout : toutes les sections `##` de `GEMINI.md` et
  `.agents/roles/README.md` ;
- chaque emplacement de section peut fournir au plus un gold answerable ;
- les documents et emplacements sont disjoints : 14 slots dev, 13 slots de
  réserve ; le pool structurel utile reste non vide et équilibré ;
- le holdout ne sera construit qu'après un nouveau GO. Aucune question,
  réponse, preuve, proposition key, ancre ou fichier holdout ne figure dans ce
  commit.

Pendant la construction/calibration dev, il est interdit de lire, inspecter,
générer ou utiliser un gold holdout, y compris une question, réponse, preuve,
label ou clé sémantique. La réserve reste scellée ; seuls son périmètre de
fichiers et ses nombres de sections sont pré-enregistrés. Toute candidate
holdout qui, lors d'un GO ultérieur, partage une proposition key avec le dev
sera éliminée avant génération du holdout. Aucune calibration ne peut accéder
à des champs ou chemins holdout.

## Garde-fous anti-fuite

- liste blanche des quatre documents et rôles de split figés dans
  `split_preregistration.json` ;
- identifiant canonique indépendant de la formulation et des identifiants de
  lignes ;
- rejet de toute répétition de clé canonique ou `proposition_key` dans un
  même set ;
- test de disjonction des documents, slots de sections et ancres canoniques ;
- aucun artefact de holdout n'est créé durant ce GO ;
- aucune ancre/gold #508 n'est réutilisée : les 75 ancres de
  `forbidden_508.json` sont bannies verbatim (question/réponse/preuve)
  et toute section `##` en contenant une est exclue (`AGENTS.md::h2:2`,
  `.agents/roles/README.md::h2:3`) ; les reformulations équivalentes
  des cibles `H2-V`/`H2-W` sont interdites par revue ; le partage de
  chemins documentaires reste autorisé ;
- les 7 fichiers items #508 sont épinglés par SHA dans les tests
  (tripwire anti-mutation) ;
- aucune mesure, conclusion expérimentale ou intégration produit.

Cette exception de split vaut exclusivement pour #510. Le contrat standing
global demeure inchangé.
