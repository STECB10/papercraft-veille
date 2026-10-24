---
name: etude-du-jour
description: Choisit l'étude IA & santé du jour parmi jours/<date>/candidats.json, en tire une fiche des faits prouvés, écrit le script, film.json et le post LinkedIn de la série Papercraft.AI, puis les fait valider par pipeline/verifier.py. Lancé chaque matin par GitHub Actions.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# L'étude du jour (série Papercraft.AI)

Tu travailles seul, sans humain à qui poser une question. La date est dans la variable d'environnement `DATE_DU_JOUR`
(dossier `jours/$DATE_DU_JOUR/`). Lis d'abord : `serie/REGLES-CONTENU.md`, `serie/FILM-SCHEMA.md`,
`serie/exemple/film.json` (pilote validé pour le style, mais trop court en contenu) et `serie/exemple/SCRIPT.md`.

## 1. Choisir

Lis `candidats.json` (6 études, déjà notées). Choisis celle qui parle le plus à des soignants, kinés, chercheurs
français : un vrai résultat chiffré sur des patients, une comparaison claire, de préférence un essai tiré au sort ou
une étude prospective. Évite les études purement techniques (précision d'un modèle sans patient) sauf si le résultat
est frappant et concret. Puis : `python3 pipeline/texte_integral.py <rang>` (rang à partir de 1). Il écrit
`source.txt` (le seul texte dont tu tires des chiffres) et `etude.json`.

## 2. Fiche des faits : `faits.json`

Liste de faits : `{"id": "f1", "valeur": 2378, "citation": "<extrait copié MOT POUR MOT de source.txt contenant la
valeur>"}` ou, pour un chiffre calculé, `{"id": "f9", "valeur": 64.1, "calcul": "100 - f8"}`. Chaque chiffre du film
et du post (années comprises) doit venir d'ici. Ne jamais arrondir au-delà de ce que dit la source ; un arrondi affiché
(« 64 % » pour 64,1) est accepté par le vérificateur. Si la source ne donne pas un chiffre, ne l'invente pas : change
la phrase. Note honnêtement le type d'étude (essai tiré au sort, cohorte, rétrospective, préprint non relu).

## 3. Script et `film.json`

Suis `serie/REGLES-CONTENU.md` à la lettre : 60 à 85 s, 170 à 230 mots dits, dans l'ordre contexte → question de
l'étude → carte d'identité (`id_card`) → les deux groupes décrits concrètement (`two_groups`) → résultats (valeur des
deux groupes, écart, intervalle de confiance s'il existe) → 1 résultat secondaire utile → portée et limite (une
phrase `typo`) → phrase à retenir → promesse → « Papercraft. ».
Français simple, phrases courtes (8 à 14 mots), vouvoiement implicite, aucun anglicisme évitable, jamais « l'IA bat
les médecins » si l'étude ne le teste pas, jamais un avant/après pour deux groupes tirés au sort.
Texte dit : chiffres en lettres (« trente-six pour cent ») ; `display` : chiffres (« 36 % »). Sigles lisibles :
écris « IA », jamais « I.A. ». Choisis des stations qui montrent chaque idée au moment où elle est dite, avec des
ancres sur les mots (voir FILM-SCHEMA.md). La nuit montre le problème (`hook_number`, un moment muet `gag_clock` ou
`gag_waiting`, `steps`) ; le papier montre l'étude. Respecte les espacements y.

## 4. Post : `post.txt`

Ligne 1 : une phrase d'accroche (le résultat clé en langage simple, 160 caractères au plus). Puis 2 à 3 phrases : la
question, les groupes, le résultat principal. Puis « Source : Auteur et al., Revue, mois année. » suivi du lien
exact de `etude.json` (`https://doi.org/…`). Puis 3 à 4 hashtags. 1 500 caractères au plus. Aucun chiffre hors fiche.

## 5. Garder une trace : `SCRIPT.md`

Le titre de l'étude, la raison du choix, le texte dit complet, et la fiche des faits sous forme de tableau.

## 6. Valider

`python3 pipeline/verifier.py`. S'il répond REFUSÉ, corrige chaque point et relance, jusqu'à VALIDÉ. Tu as fini
quand il répond VALIDÉ. Ne lance ni la voix, ni le rendu, ni la publication : la suite de la chaîne s'en charge.
