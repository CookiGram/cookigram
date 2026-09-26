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

Liste fermée, issue des documents réservés (non golds) dans le précédent
cycle2b :

| Document | Sections `##` | Affectation pré-enregistrée |
|---|---:|---|
| `AGENTS.md` | 5 | dev |
| `README.en.md` | 9 | dev |
| `GEMINI.md` | 10 | réserve holdout |
| `.agents/roles/README.md` | 3 | réserve holdout |

Total structurel : 27 slots de section, 14 côté dev et 13 côté réserve.
Le compte provient uniquement des titres `##`; aucun contenu ni gold holdout
n'a été consulté pour choisir le split. Aucune autre source n'est admissible.

## Définition exacte d'une ancre/gold

Un gold answerable est une question dont la réponse est une proposition
atomique, vérifiable dans une preuve contiguë à l'intérieur d'une seule
section `##` d'un document admissible. Le gold contient la question, la réponse
attendue, le chemin source, le chemin complet des titres jusqu'à `##`, et la
citation de preuve. Maximum : un gold par section `##`.

L'identité canonique d'ancre est
`sha256("cookigram-anchor-v1\n" + path + "\n" + normalized_heading_path +
"\n" + proposition_key)`. Les chemins sont relatifs POSIX et sensibles à la
casse. Les titres et proposition keys sont normalisés NFC, casefold, espaces
Unicode repliés et ponctuation périphérique retirée. `proposition_key` est un
identifiant sémantique stable, défini avant rédaction de la question ; il ne
dépend jamais de la formulation. Reformuler la question ou changer son
identifiant de ligne ne crée donc pas une nouvelle ancre. Une répétition ou
paraphrase du même fait garde la même proposition key et doit être exclue du
split opposé.

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
- aucun gold de #508 n'est copié ou utilisé comme tuning data ;
- aucune mesure, conclusion expérimentale ou intégration produit.

Cette exception de split vaut exclusivement pour #510. Le contrat standing
global demeure inchangé.
