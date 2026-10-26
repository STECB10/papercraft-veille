---
name: etude-du-jour
description: Choisit l'étude IA & santé du jour parmi jours/<date>/candidats.json, en tire une fiche des faits prouvés, écrit le script, film.json et le post LinkedIn de la série Papercraft.AI, puis les fait valider par pipeline/verifier.py. Lancé chaque matin par GitHub Actions.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# L'étude du jour (série Papercraft.AI)

Tu travailles seul, sans humain à qui poser une question. La date est dans la variable d'environnement `DATE_DU_JOUR`
(dossier `jours/$DATE_DU_JOUR/`). Lis d'abord : `serie/REGLES-CONTENU.md`, `serie/FILM-SCHEMA.md`,
`serie/frame.md` (la charte visuelle : sections « Choisir la mise en scène » et « Règles de fond »),
`serie/exemple/film.json` (pilote validé pour le style, mais trop court en contenu) et `serie/exemple/SCRIPT.md`.

## 1. Choisir

Lis `candidats.json` (6 études, déjà notées). **L'étude doit avoir un vrai lien avec l'IA ou le machine
learning** : un outil d'IA testé sur des patients, un modèle qui prédit ou détecte quelque chose, un algorithme qui
classe des patients, un assistant conversationnel, etc. Écarte seulement les études où l'IA n'est qu'une mention en
passant (une phrase de perspective, un mot-clé). Parmi celles qui restent, choisis celle qui parle le plus à des soignants, kinés, chercheurs
français : un vrai résultat chiffré et utile en pratique, quel que soit le type d'étude (essai tiré au sort,
méta-analyse, revue, cohorte, performance d'un modèle…). À intérêt égal, préfère les preuves les plus solides (essai
tiré au sort, méta-analyse, étude prospective). Évite les études purement techniques sans lien avec le soin, sauf si
le résultat est frappant et concret. Puis : `python3 pipeline/texte_integral.py <rang>` (rang à partir de 1). Il écrit
`source.txt` (le seul texte dont tu tires des chiffres) et `etude.json`.

## 2. Fiche des faits : `faits.json`

Liste de faits : `{"id": "f1", "valeur": 2378, "citation": "<extrait copié MOT POUR MOT de source.txt contenant la
valeur>"}` ou, pour un chiffre calculé, `{"id": "f9", "valeur": 64.1, "calcul": "100 - f8"}`. Chaque chiffre du film
et du post (années comprises) doit venir d'ici. Ne jamais arrondir au-delà de ce que dit la source ; un arrondi affiché
(« 64 % » pour 64,1) est accepté par le vérificateur. Si la source ne donne pas un chiffre, ne l'invente pas : change
la phrase. Note honnêtement le type d'étude (essai tiré au sort, méta-analyse, revue, cohorte, étude diagnostique,
rétrospective, préprint non relu).

## 3. Script et `film.json`

Suis `serie/REGLES-CONTENU.md` à la lettre (surtout la section « Style » : phrases complètes reliées par des
connecteurs logiques, intro qui raconte, méthode et résultats expliqués pas à pas, respirations) : 80 à 100 s, 210 à 280 mots dits, dans l'ordre accroche (1 phrase
qui capte, la toute première) → contexte (4 à 5 phrases : la situation, qui est concerné, comment on fait
aujourd'hui, ce qui coince, ce que fait l'IA testée) → question de
l'étude → carte d'identité (`id_card`) → ce que fait l'IA (`ai_scan` : ce qui entre, ce que l'IA en fait, ce qui
sort, chaque bloc apparaît au mot qui le nomme ; `modality` selon ce que l'IA lit) → méthode puis résultats **adaptés
au type d'étude et à ce que dit la voix** (tableaux de `serie/frame.md`, section « Choisir la mise en scène », et de
REGLES-CONTENU.md : par exemple `population_split` puis `two_groups` et `result_bars` avec `ci` pour un essai,
`diagnostic_grid` ou `roc_curve` pour une performance, `forest_plot` ou `studies_stack` pour une méta-analyse, `chat`
pour une IA conversationnelle, `image_scan` quand l'IA lit une image) → 1 résultat secondaire utile → portée et limite
(une phrase `typo`) → phrase à retenir (une phrase `typo`) → promesse → « Papercraft. ». Dès que la source donne un
intervalle de confiance pour le résultat principal, il est dans `ci`.
Le champ `type_etude` de candidats.json donne une première indication ; vérifie-le dans source.txt.
Français simple, phrases courtes (8 à 14 mots), vouvoiement implicite, aucun anglicisme évitable, jamais « l'IA bat
les médecins » si l'étude ne le teste pas, jamais un avant/après pour deux groupes tirés au sort, jamais de « deux groupes » inventés pour une étude qui n'en
compare pas.
Texte dit : chiffres en lettres (« trente-six pour cent ») ; `display` : chiffres (« 36 % »), et sinon le
texte dit **mot pour mot, en entier** (le vérificateur refuse tout mot retiré ou reformulé). Sigles lisibles :
écris « IA », jamais « I.A. ». Choisis des stations qui montrent chaque idée au moment où elle est dite, avec des
ancres sur les mots (voir FILM-SCHEMA.md). La table montre le problème (`hook_number`, un moment muet `gag_clock` ou
`gag_waiting`, `steps`) ; la feuille montre l'étude, une planche par écran. N'écris pas de `y` : le moteur place les
planches. N'écris jamais un chiffre dans une planche s'il n'est pas dans la fiche des faits (une courbe de suivi ou un
forest plot seulement si la source donne chaque valeur).

## 4. Post : `post.txt`

Ligne 1 : une phrase d'accroche (le résultat clé en langage simple, 160 caractères au plus). Puis 2 à 3 phrases : la
question, les groupes, le résultat principal. Puis « Source : Auteur et al., Revue, mois année. » suivi du lien
exact de `etude.json` (`https://doi.org/…`). Puis 3 à 4 hashtags. 1 500 caractères au plus. Aucun chiffre hors fiche.

## 5. Garder une trace : `SCRIPT.md`

Le titre de l'étude, la raison du choix, le rôle de l'IA en une phrase, le texte dit complet, et la fiche des faits sous forme de tableau.

## 6. Valider

`python3 pipeline/nombres.py` (écrit les nombres du texte dit en toutes lettres), puis `python3 pipeline/verifier.py`. S'il répond REFUSÉ, corrige chaque point et relance, jusqu'à VALIDÉ. Tu as fini
quand il répond VALIDÉ. Ne lance ni la voix, ni le rendu, ni la publication : la suite de la chaîne s'en charge.
