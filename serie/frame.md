---
version: 2
name: "Papercraft.AI · Une étude par jour : charte de la série"
description: >
  Charte commune à toutes les vidéos quotidiennes de la page LinkedIn Papercraft.AI : une étude IA & santé expliquée
  en 80 à 100 s, en français, en 4:5. Direction validée le 26 octobre 2026 : « La Revue papier ». La rigueur d'une
  figure de revue scientifique qui se dessine devant le spectateur (piste A), les gestes de papier découpé aux
  moments forts (piste B : silhouettes qui se lèvent, bandes et étiquettes qui se déplient, déchirure), et le
  vocabulaire « instrument » pour montrer ce que l'IA lit (piste C : onde, balayage, particules, jauges), le tout
  sur papier. Plus aucun fond nuit. Un seul accent, le carbone #5D68FF.
  Références animées : serie/reference/planches.html (chaque planche de cette charte, jouée sur de vrais chiffres).
unit: 1080×1350 (4:5), 30 i/s
principle: >
  lisible sans le son · une seule planche à l'écran, qui remplit le cadre · une idée dite = un geste · tout se trace,
  rien ne se pose en fondu · un accent · chaque chiffre vient de la fiche des faits, avec son intervalle s'il existe

colors:
  table: "#E3DBCB"           # la table (kraft clair) : le monde du constat, sous la feuille, et la carte de fin
  table-2: "#D6CCB8"         # ombre portée sur la table
  paper: "#ECE6DA"           # la feuille, et le sol plein cadre du monde de l'étude
  paper-lift: "#F4EFE6"      # une feuille posée sur une autre (relief), languettes, cartes
  paper-hi: "#F7F3EC"        # texte dans la boîte d'accent, étiquettes suspendues, bulles
  paper-2: "#DCD4C4"         # aplat secondaire, hachures du groupe témoin, bulle « patient »
  paper-3: "#C7BDA9"         # coin plié, verso révélé par la déchirure
  ink: "#16171C"             # encre : texte, traits, et SEULEMENT de petites surfaces (carte « noyau IA », bulle IA)
  ink-dim: "#57544E"         # encre secondaire, groupe témoin, étiquettes
  ink-faint: "rgba(22,23,28,.16)"  # points et silhouettes inactifs, grilles
  accent: "#5D68FF"          # LE carbone : boîte du mot-clé, groupe IA, barre IA, point de l'écart, balayage
  accent-deep: "#3A44D6"     # carbone pour du texte et des traits fins sur papier (annotations, « Fig. 3 »)
  accent-soft: "#A3A9FF"     # carbone sur une petite surface encre uniquement
  hairline: "rgba(22,23,28,.16)"

# woff2 locaux uniquement (assets/fonts/), jamais d'@import réseau. Toutes SIL OFL (@fontsource).
fonts:
  Bodoni Moda: { files: ["assets/fonts/BodoniModa-400.woff2 (400)", "assets/fonts/BodoniModa-500.woff2 (500)", "assets/fonts/BodoniModa-400-italic.woff2 (400 italic)"] }
  Schibsted Grotesk: { files: ["assets/fonts/SchibstedGrotesk-400.woff2 (400)", "assets/fonts/SchibstedGrotesk-500.woff2 (500)", "assets/fonts/SchibstedGrotesk-600.woff2 (600)", "assets/fonts/SchibstedGrotesk-700.woff2 (700)"] }
  IBM Plex Mono: { files: ["assets/fonts/IBMPlexMono-400.woff2 (400)", "assets/fonts/IBMPlexMono-500.woff2 (500)"] }

layout:
  canvas: "1080 × 1350"
  side-margins: "72 px à gauche et à droite"
  kicker: "y 66 : étiquette mono de la planche (« Fig. 3 · Progrès du score global »), filet d'encre à y 114 sur toute la largeur utile"
  title: "y 150 : titre Bodoni de la planche s'il y en a un (une ligne)"
  stage: "zone utile y 150 à 1060 : la planche l'occupe à 60 % au moins de sa hauteur (jamais une carte en haut et le vide en dessous)"
  subtitle-band: "y 1108 à 1196 : le sous-titre seul, rien d'autre"
  bottom-safe: "y 1210 à 1350 : aucune information (l'interface LinkedIn mobile s'y superpose)"
  one-plate: "une seule planche dans le cadre : la précédente est entièrement sortie avant que la suivante ne commence (jamais un bout de texte coupé en haut)"
  no-collision: "aucun élément n'en recouvre un autre au repos : icône à côté de son étiquette, jamais dessus ; 24 px d'air au moins entre deux blocs de texte"

typography:
  subtitle:  { fontFamily: "Schibsted Grotesk", px: 54, weight: 600, lineHeight: 66, tracking: "-0.015em", note: "la phrase de la voix, centrée dans la bande du bas, mot à mot, 32 caractères au plus par morceau ; encre sur papier" }
  title:     { fontFamily: "Bodoni Moda", px: 57, weight: 400, tracking: "-0.02em", note: "titre de planche (« Six études, un effet regroupé »)" }
  type:      { fontFamily: "Bodoni Moda", px: 72, weight: 400, lineHeight: 1.12, tracking: "-0.025em", note: "la nuance et la phrase à retenir, centrées ; italique carbone pour le mot qui porte ; PAS de sous-titre pendant ce temps (le texte n'est jamais affiché deux fois)" }
  numeral:   { fontFamily: "Bodoni Moda", px: "140 à 260", weight: 400, tracking: "-0.03em", note: "chiffre clé seul ; virgule décimale française ; % à 0,5 em ; chiffres tabulaires pendant le roulement" }
  numeral-mid: { fontFamily: "Bodoni Moda", px: "60 à 110", weight: 400, note: "valeurs au-dessus des barres, sensibilité, AUC, valeurs de l'intervalle" }
  annotation: { fontFamily: "Bodoni Moda", px: "45 à 63", style: italic, color: accent-deep, note: "l'écart annoté (« +0,09 »), « À 12 mois : 9 points d'écart »" }
  body:      { fontFamily: "Schibsted Grotesk", px: "42 à 48", weight: "500 à 600", lineHeight: 1.3, note: "texte d'un schéma ou d'une carte, rare" }
  label:     { fontFamily: "IBM Plex Mono", px: "27 (26 minimum)", weight: 400, tracking: "0.14em", upper: true, note: "kicker, axes, groupes, notes d'annotation, source. Rien n'est écrit en dessous de 26 px : sur un téléphone, 26 px font 9 px." }

camera:
  rig: "#stage (1080×1350, overflow hidden, perspective 1600px) > #drift > #cam > #world"
  drift: "le monde respire toujours : échelle 1,035 → 1 sur la durée de la planche (sans arrêt), ou 1 → 1,04 sur une planche de silhouettes"
  cran: "sur la table, la caméra descend la feuille par crans (1 s power3.inOut)"
  feuilles: "dans l'étude, chaque planche est une nouvelle feuille posée par-dessus la précédente (0,85 s power3.out, du bas puis de la droite en alternance) ; la précédente s'enfonce (échelle 0,93) et s'assombrit"
  table: "dans le monde du constat, la table est vue en légère plongée (rotationX 8 à 14°, perspective 900) : la feuille posée dessus a une ombre portée réelle"
  never: "pas d'aller-retour, pas de zoom décoratif, pas de secousse"
---

# Papercraft.AI · Une étude par jour : charte de la série

## L'idée

Chaque étude est une feuille de papier : l'article lui-même. Le film commence **sur la table** (kraft clair), où la
feuille est posée en légère plongée, imprimée à l'encre comme une figure de revue : c'est le **constat** (le
problème, qui est concerné, comment on fait aujourd'hui). Au **pivot**, la feuille se plie et l'on entre **dans la
feuille**, papier plein cadre : c'est **l'étude** (carte d'identité, ce que fait l'IA, méthode, résultats). La
**nuance** arrive par une déchirure qui révèle le verso. La **fin** revient sur la table : la feuille se replie en
glyphe Papercraft, la promesse, le bouton « Suivre ».

Tout est papier : aucune planche n'a de fond nuit. L'encre ne couvre que de petites surfaces (la carte « noyau IA »,
la bulle de l'IA, une pastille), jamais un fond de scène.

## Les trois familles de gestes

Un geste montre une idée **au moment où la voix la dit** (ancre sur le mot qui la nomme). Deux gestes au plus à la
fois. Aucun élément n'arrive en simple fondu : il se trace, se lève, se déplie ou se dépose.

### Tracer (la figure de revue)

| Geste | Mouvement | Quand |
|---|---|---|
| `tracer` | trait révélé par son tiret (`strokeDashoffset`), 0,4 à 0,8 s power2.out ; les axes avant les données | axes, flèches de schéma, courbes, contours d'image |
| `barre` | `scaleY` 0 → 1 depuis la ligne de base, 0,7 à 0,8 s power3.out ; la valeur roule en même temps jusqu'à son chiffre exact | une valeur par groupe |
| `annoter` | un seul geste : marqueur (boucle, soulignement ou crochet) 0,6 s, puis trait de liaison 0,3 s, puis note mono 0,3 s | l'écart, le mot qui compte, une note de méthode (« 3 modules · 30 min au total ») |
| `intervalle` | ligne d'échelle tracée, ligne « aucun effet » en pointillé (0, ou 1 pour un rapport), la moustache grandit depuis son centre (0,6 s), le point carbone se pose (0,25 s), les bornes s'impriment | chaque fois que la source donne un intervalle de confiance : il est TOUJOURS montré |
| `schéma` | blocs de haut en bas reliés par des flèches tracées, chacun au mot qui le nomme | ce que fait l'IA, un parcours de soin |

### Plier (le papier découpé)

| Geste | Mouvement | Quand |
|---|---|---|
| `se lever` | silhouettes (tête ronde + corps en pilule) qui se dressent depuis la feuille : `scaleY` 0 → 1 depuis leurs pieds, 0,32 s, décalage 0,02 s | un effectif de personnes (60 au plus ; au-delà, points-patients) |
| `répartir` | les silhouettes ou les points rejoignent leur groupe (0,7 s power3.inOut, ordre tiré au sort mais fixe), puis le groupe IA passe au carbone une à une | le tirage au sort, une répartition |
| `déplier` | charnière 3D : `rotationX` −90° → 0 (perspective 520), depuis le bas pour une bande, depuis le haut pour une languette ou une étiquette, 0,5 à 0,8 s power3.out | languettes de groupes, bandes-résultats, étiquette suspendue |
| `suspendre` | une punaise se pose, la ficelle descend, l'étiquette se déplie et se penche (−6° → −2°) | l'écart et son intervalle, sur une planche « bandes » |
| `poser` | une nouvelle feuille glisse par-dessus la précédente et se pose, avec son ombre ; la précédente s'enfonce et s'assombrit | chaque nouvelle planche de l'étude |
| `plier` | le pli de la feuille (mécanisme signature) : reflet qui glisse le long de la diagonale 0,25 s, puis la moitié se rabat 0,45 s expo.inOut | le pivot (une fois) et la fin (une fois) |
| `déchirer` | tension 0,25 s, puis les deux moitiés partent (haut vers le haut, bas vers le bas, 0,8 s power3.in) avec un bord fibreux blanc de 3 px ; révèle le verso paper-3 | la nuance ou la limite (une fois par film au plus) |

### Mesurer (l'instrument, sur papier)

| Geste | Mouvement | Quand |
|---|---|---|
| `onde` | 40 barres d'encre qui vibrent (images clés tirées d'une graine fixe), puis s'aplatissent quand la voix s'arrête | l'IA écoute une voix |
| `balayer` | une bande carbone translucide traverse l'image ou le noyau (0,8 à 1,2 s, linéaire), puis des repères d'angle se verrouillent (échelle 1,7 → 1, 0,4 s power3.out) sur ce qui est trouvé | l'IA lit une image |
| `flux` | des points arrivent d'un peu partout et se rangent en grille (0,8 s power3.out, décalage 0,015 s) | des données qui entrent, une population en points |
| `jauge` | filet fin + trait de 11 px qui se remplit jusqu'à valeur ÷ maximum, en même temps que le chiffre roule | sensibilité, spécificité, score sur 5, pourcentage |
| `noyau IA` | carte encre : nœuds carbone qui apparaissent, liens tracés, le nœud central pulse trois fois | le moment où l'IA travaille |
| `conversation` | bulles qui se posent (échelle 0,96 → 1, y 24 px), points de saisie, lignes qui s'écrivent | une IA conversationnelle |

## Les planches

Chaque planche a un nom de moteur (entre crochets) que `film.json` utilise ; ses champs sont dans
`serie/FILM-SCHEMA.md`. Le moteur (`serie/moteur/`) les dessine toutes ; la référence animée est
`serie/reference/planches.html`, et `python3 serie/moteur/essai.py serie/moteur/essai-planches.json <dossier>` les
rejoue toutes (données fictives) avec une voix simulée.

### Sur la table (le constat)

| Planche | Ce qu'elle montre | Gestes |
|---|---|---|
| Accroche chiffrée [`hook_number`] | le chiffre qui pose le problème, en Bodoni, et des silhouettes dont une passe au carbone | `barre` ou roulement, `se lever` |
| Moment muet [`gag_clock`, `gag_waiting`] | l'attente, sans voix | horloge, salle d'attente |
| Parcours actuel [`steps`] | 2 à 4 étapes du soin d'aujourd'hui | `schéma`, `annoter` sur l'étape qui coince |

### Dans la feuille (l'étude)

| Planche | Ce qu'elle montre | Gestes |
|---|---|---|
| L'étude en bref [`id_card`] | fiche bristol scotchée : marge carbone, une ligne réglée par information (type, lieu, effectif, durée, critère) | `déplier`, valeurs qui s'impriment |
| Ce que fait l'IA [`ai_scan`] | Fig. : ce qui entre → noyau IA → ce qui sort, le mot clé annoté | `schéma`, `noyau IA`, `annoter`, plus le geste de la modalité (tableau plus bas) |
| Tirage au sort [`population_split`] | l'effectif exact qui se lève puis se partage sous deux languettes | `se lever`, `déplier`, `répartir` |
| Deux groupes [`two_groups`] | ce que vit chaque groupe, côte à côte, marges égales | `schéma` en deux colonnes |
| Résultat en barres [`result_bars`] | Fig. : axe gradué, une barre par groupe, l'écart annoté, puis l'intervalle | `tracer`, `barre`, `annoter`, `intervalle` |
| Résultat en bandes [`result_strips`] | variante papier : bandes qui se déplient d'une fente, étiquette de l'écart suspendue | `déplier`, `suspendre` |
| Résultat en points [`result_dots`] | une proportion par groupe en points-patients exacts, puis l'intervalle | `flux`, `répartir`, `jauge`, `intervalle` |
| Mesures [`metric`] | 1 à 3 mesures (score sur 5, sensibilité…) en jauges | `jauge` |
| Grille diagnostique [`diagnostic_grid`] | 100 patients (ou l'effectif exact s'il est sous 100) : malades cerclés, repérés en carbone, manqués vides, fausses alertes à l'encre | `flux`, `balayer`, `jauge` |
| Courbe ROC [`roc_curve`] | la courbe face à la diagonale du hasard, l'aire qui se remplit, l'AUC exacte | `tracer`, roulement |
| Courbes de suivi [`survival_curves`] | deux courbes en escalier dans le temps, l'écart annoté | `tracer`, `annoter` |
| Forest plot [`forest_plot`] | une ligne par étude (carré + moustache), puis le losange regroupé qui tombe, « ← favorise le témoin / favorise l'IA → » | `tracer`, `intervalle` |
| Études regroupées [`studies_stack`] | une petite feuille imprimée par étude (par lots au-delà de 40), lâchée sur la table | feuilles qui tombent et se posent |
| Conversation [`chat`] | l'échange patient ↔ IA et la note donnée par les évaluateurs | `conversation`, `annoter` |
| Imagerie [`image_scan`] | l'image redessinée au trait (fond d'œil, radio du thorax, peau, mammographie, coupe de scanner), balayée, les signes verrouillés, le délai de résultat | `tracer`, `balayer` |
| Constats [`key_points`] | 2 à 4 constats numérotés en Bodoni, qui remplissent la hauteur | lignes qui s'impriment |
| Nuance [`typo`] | la phrase de limite ou la phrase à retenir, seule, en grande typo | `déchirer` avant (une fois), texte qui monte |
| Source | auteur et al., revue en Bodoni italique, mois, année, DOI | s'imprime |

### La fin

Retour sur la table. La feuille se replie en glyphe Papercraft (le chemin M1.5 1.5H13L18.5 7V24.5H1.5Z, le coin et le
pli en carbone), « Papercraft.AI » en Bodoni, la promesse « Une étude par jour, vérifiée à la source. » en type, un
bouton « Suivre » (pilule encre, texte paper-hi) que le curseur clique en un seul geste, 2 à 3 s de tenue vivante.

## Les sons

Peu, au bon moment, jamais à la chaîne : des bruits de papier pour les gestes de papier (la feuille posée, le pli, la
déchirure), un « ping » quand arrive le résultat qui compte, un « pop » pour l'écart. Rien sur chaque élément qui
apparaît, jamais deux bruitages à moins de 1,2 s (le moteur trie lui-même). La musique et la voix restent devant.

## Choisir la mise en scène

Le récit est toujours le même (accroche → contexte → question → l'étude en bref → ce que fait l'IA → méthode →
résultats → portée et limite → phrase à retenir → promesse). Ce qui change, ce sont les planches de la méthode et des
résultats, et le geste qui montre ce que l'IA lit.

### Selon le type d'étude

| Type d'étude | Méthode | Résultats |
|---|---|---|
| Essai tiré au sort | Tirage au sort, Deux groupes | Résultat en barres (valeur continue) ou en points (proportion), Intervalle, Mesures pour un résultat secondaire |
| Précision diagnostique | Ce que fait l'IA (avec la référence comparée) | Grille diagnostique, Mesures (sensibilité, spécificité) |
| Modèle prédictif | Ce que fait l'IA (les données qui entrent) | Courbe ROC si une AUC est donnée, Mesures, Constats (facteurs qui comptent) |
| Cohorte, survie | Parcours, L'étude en bref (durée de suivi) | Courbes de suivi si la source donne des valeurs dans le temps, sinon Intervalle sur le rapport de risque |
| Méta-analyse | Études regroupées | Forest plot si la source donne l'effet de chaque étude, sinon Intervalle sur l'effet regroupé ; Constats |
| Revue de littérature | Études regroupées | Constats |
| IA conversationnelle | Conversation | Mesures (notes des évaluateurs), Résultat en barres si deux groupes |
| Qualitative, enquête | L'étude en bref | Constats, Mesures |

### Selon ce que la voix dit ou montre

| La voix dit… | On montre… |
|---|---|
| un nombre de personnes | autant de silhouettes qui se lèvent (60 au plus), sinon autant de points ; au-delà de 600, 1 point = 10 patients et l'étiquette le dit |
| qu'on a tiré au sort | `répartir` sous deux languettes nommées comme les groupes |
| une valeur pour chaque groupe | une barre (ou une bande) par groupe, la valeur qui roule |
| un écart | `annoter` l'écart sur la figure |
| un intervalle de confiance | `intervalle`, avec la ligne « aucun effet » |
| une sensibilité, une spécificité | la grille diagnostique ou une jauge |
| une AUC | la courbe ROC |
| une durée, une attente | l'horloge ou le calendrier sur la table |
| une étape du soin | une ligne du parcours, au mot qui la nomme |
| une limite | la nuance, une fois précédée de la déchirure |
| le mot le plus important de la phrase | la boîte carbone du sous-titre, une par phrase |

### Selon ce que l'IA lit (planche « Ce que fait l'IA »)

| L'IA lit… | Geste d'entrée | Dessin |
|---|---|---|
| une image (photo, radio, scanner, peau) | `balayer` puis repères verrouillés | l'image redessinée au trait, jamais une image réelle |
| une voix | `onde` | micro au trait |
| un texte, une question | `conversation` | bulles, lignes qui s'écrivent |
| un signal (ECG, capteur, montre) | tracé d'oscilloscope qui défile | grille fine, tracé à l'encre |
| un dossier, des données | lignes de tableau qui défilent, les variables utiles surlignées | tableau au trait |

## Règles de fond (elles ne changent pas)

- Aucun chiffre, nom, date ou citation qui ne soit pas dans la fiche des faits. Les effectifs de points et de
  silhouettes sont exacts.
- Une forme dessinée sans donnée (une courbe ROC tracée à partir de la seule AUC, une image redessinée) porte la
  mention mono « schéma » ; jamais de courbe inventée présentée comme celle de l'article.
- Dans une conversation, les bulles ne contiennent que des phrases citées par la source (traduites et signalées
  comme telles) ou des lignes muettes ; jamais un dialogue inventé.
- Pas de « avant / après » pour deux groupes tirés au sort : deux groupes côte à côte, marges égales.
- Le groupe témoin est à l'encre (hachures pour une barre), le groupe IA en carbone. Pas d'autre teinte : pas de rouge
  « danger », pas de vert « succès ».
- La boîte du mot-clé est la seule façon de surligner un mot du sous-titre ; les annotations au marqueur sont sur la
  figure, jamais dans le sous-titre.
- Pas d'Inter, Space Grotesk, Geist, system-ui. Pas d'emoji. Pas d'icône dans une pastille ronde. Pas d'image
  médicale réelle, de logo d'hôpital ni de figure copiée de l'article : tout est redessiné au trait.
- Pas d'easing élastique ni rebondissant, pas de `repeat: -1`, pas de tween de `letterSpacing`. Tout est piloté par
  la timeline (rejouable à n'importe quelle image) : les tirages « au hasard » viennent d'une graine fixe.

## Blocs HyperFrames dont s'inspirer

Le moteur reste celui de la série (`serie/moteur/`) ; ces blocs du registre HyperFrames (`npx hyperframes add <nom>`)
servent de source pour les gestes : `chart-story` (barres aux valeurs exactes), `vox-annotate` (annoter),
`svg-stroke-trace` (tracer), `count-up` (roulement), `torn-paper-rip` (déchirer),
`paper-collage-reveal`, `focus-rack`, `scan-band` et `yt-circle-pointer` (balayer, repères), `mk-progress-stat`
(jauge), `oscilloscope-trace` (signal), `ai-chat-reveal` (conversation), `grain-overlay` (grain du papier).
