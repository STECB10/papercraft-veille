---
name: etude-du-jour
description: Choisit l'étude IA & santé du jour parmi jours/<date>/candidats.json, en tire une fiche des faits prouvés, écrit le script, film.json et le post LinkedIn de la série Papercraft.AI, puis les fait valider par pipeline/verifier.py. Lancé chaque matin par GitHub Actions.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# L'étude du jour (série Papercraft.AI)

Tu travailles seul, sans humain à qui poser une question. La date est dans la variable d'environnement `DATE_DU_JOUR`
(dossier `jours/$DATE_DU_JOUR/`). Lis d'abord : `serie/REGLES-CONTENU.md`, `serie/FILM-SCHEMA.md`,
`serie/frame.md` (la charte visuelle : sections « Les accroches », « Choisir la mise en scène » et « Règles de fond »),
`serie/exemple/SCRIPT-NATUREL.md` et `serie/exemple/film-naturel.json` (**la référence** : un humain qui explique, des
phrases reliées par des connecteurs, un problème expliqué, des résultats concrets, un seul fil). `serie/exemple/film.json` (le pilote) ne sert plus que pour la
forme du fichier : son texte haché est justement ce qu'il ne faut plus écrire.
Regarde aussi le `film.json` de la veille (le dernier dossier de `jours/` avant aujourd'hui) : **l'accroche et le
moment muet d'aujourd'hui doivent être différents des siens** (le vérificateur refuse sinon).

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
connecteurs logiques, intro qui raconte, méthode et résultats expliqués pas à pas, respirations) : 85 à 105 s, 230 à 300 mots dits, dans l'ordre accroche (1 phrase
qui capte, la toute première) → contexte (4 à 5 phrases : la situation, qui est concerné, comment on fait
aujourd'hui, ce qui coince, ce que fait l'IA testée) → question de
l'étude → carte d'identité (`id_card`) → ce que fait l'IA (`ai_scan` : ce qui entre, ce que l'IA en fait, ce qui
sort, chaque bloc apparaît au mot qui le nomme ; `modality` selon ce que l'IA lit) → méthode puis résultats **adaptés
au type d'étude et à ce que dit la voix** (tableaux de `serie/frame.md`, section « Choisir la mise en scène », et de
REGLES-CONTENU.md : par exemple `population_split` puis `two_groups` et `result_bars` avec `ci` pour un essai,
`diagnostic_grid` ou `roc_curve` pour une performance, `forest_plot` ou `studies_stack` pour une méta-analyse, `chat`
pour une IA conversationnelle, `image_scan` quand l'IA lit une image ; et pour varier : `flow_chart` quand la source
donne les effectifs de chaque étape, `big_stat` pour LE résultat à retenir, `timeline` pour un suivi dans le temps ;
jamais exactement la même suite de planches que la veille) → 1 résultat secondaire utile → portée et limite
(une phrase `typo`) → phrase à retenir (une phrase `typo`) → promesse → « Papercraft. ». Dès que la source donne un
intervalle de confiance pour le résultat principal, il est dans `ci`.
Le champ `type_etude` de candidats.json donne une première indication ; vérifie-le dans source.txt.
Écris comme on parle (section « Parler comme un humain » de REGLES-CONTENU.md) : chaque phrase s'accroche à la
précédente par un connecteur (« Et », « Mais », « Alors », « Concrètement », « Résultat : », « Autrement dit »…),
le registre de l'oral (« ils ont suivi… », « il n'en garde que deux »), peu de `pause_apres` (2 à 7, aux changements de
partie). Relis le texte dit à voix haute dans ta tête : s'il sonne comme une liste, réécris-le.
Français simple, phrases de 9 à 20 mots, vouvoiement implicite, aucun anglicisme évitable, jamais « l'IA bat
les médecins » si l'étude ne le teste pas, jamais un avant/après pour deux groupes tirés au sort, jamais de « deux groupes » inventés pour une étude qui n'en
compare pas.
Texte dit : chiffres en lettres (« trente-six pour cent ») ; `display` : chiffres (« 36 % »), et sinon le
texte dit **mot pour mot, en entier** (le vérificateur refuse tout mot retiré ou reformulé). Sigles lisibles :
écris « IA », jamais « I.A. ». Choisis des stations qui montrent chaque idée au moment où elle est dite, avec des
ancres sur les mots (voir FILM-SCHEMA.md). La table montre le problème : d'abord **une accroche choisie pour cette étude** parmi `hook_number`,
`hook_question`, `hook_image`, `hook_versus`, `hook_headline` (FILM-SCHEMA.md dit laquelle selon l'étude ; jamais celle
de la veille), puis éventuellement un moment muet (`gag_clock`, `gag_calendar`, `gag_pile`, `gag_waiting`, jamais celui
de la veille), puis `steps` ; la feuille montre l'étude, une planche par écran. Textes courts dans l'accroche
(caption 75 caractères au plus, header 60) : le moteur ajuste les tailles, mais un texte bref se lit mieux. N'écris pas de `y` : le moteur place les
planches. N'écris jamais un chiffre dans une planche s'il n'est pas dans la fiche des faits (une courbe de suivi ou un
forest plot seulement si la source donne chaque valeur).

Chaque phrase porte sa `partie` (l'ordre du récit) ; les phrases du problème et des résultats concrets portent leur
`source` (l'extrait de source.txt qui les prouve). Avant d'écrire, lis les sections Résultats et Discussion du texte
intégral et note dans faits.json ce que l'étude montre concrètement (quels indices, quelles différences entre groupes,
quels exemples), pas seulement les performances du modèle. Pour la partie concrète, la planche `findings` est faite
pour ça. Un rapport de cotes ou de risques (OR, RR, HR) se montre avec la planche `ratio`, jamais en jauge `metric`.

**L'image suit la voix** (FILM-SCHEMA.md, « Les planches suivent la voix ») : pour chaque phrase, demande-toi ce qui
apparaît à l'écran pendant qu'elle est dite. Chaque élément est ancré sur le mot qui le nomme, dans la fenêtre de sa
planche (entre son `cam_at` et celui de la planche suivante), dans l'ordre où il est dessiné ; aucune phrase du contexte
ou du problème ne passe sur une accroche qui parle d'autre chose ; aucune planche figée plus de 8 s.

## 4. Post : `post.txt`

Ligne 1 : une phrase d'accroche (le résultat clé en langage simple, 160 caractères au plus). Puis 2 à 3 phrases : la
question, les groupes, le résultat principal. Puis **une question ouverte** d'une ligne, posée aux soignants, qui donne
envie de répondre en commentaire (« Et dans votre service, vous feriez confiance à cette alerte ? ») : pas de question
fermée vague (« Qu'en pensez-vous ? »). Puis « Source : Auteur et al., Revue, mois année. » suivi du lien
exact de `etude.json` (`https://doi.org/…`). Puis 3 à 4 hashtags. 1 500 caractères au plus. Aucun chiffre hors fiche.

## 5. Garder une trace : `SCRIPT.md`

Le titre de l'étude, la raison du choix, le rôle de l'IA en une phrase, le texte dit complet, et la fiche des faits sous forme de tableau.

## 6. Relire comme un auditeur

Relis le texte dit d'un bout à l'autre comme quelqu'un qui ne connaît pas le sujet, corrige, puis écris dans SCRIPT.md une
section `## Relecture` avec une puce par question et ta réponse :
- Chaque « problème » dit-il pourquoi c'en est un (cause, conséquence pour les patients) ?
- Quels résultats concrets, de terrain, au-delà des performances (ce que l'IA repère, exemples, ce qui change) ?
- Le fil : chaque partie une seule fois, dans l'ordre, et la phrase à retenir dit-elle ce que ça change sans redire un
  résultat ?
- Les connecteurs disent-ils vrai (« Le problème », « Résultat », « Autrement dit »…) ?
- Un auditeur non spécialiste comprend-il chaque chiffre (« x sur y », pour cent, aire sous la courbe située) ?
- L'image suit-elle la voix ? Phrase par phrase, qu'est-ce qui apparaît à l'écran, et est-ce bien ce qui est dit ?

## 7. Valider

`python3 pipeline/nombres.py` (écrit les nombres du texte dit en toutes lettres), puis `python3 pipeline/verifier.py`. S'il répond REFUSÉ, corrige chaque point et relance, jusqu'à VALIDÉ. Tu as fini
quand il répond VALIDÉ. Ne lance ni la voix, ni le rendu, ni la publication : la suite de la chaîne s'en charge.
