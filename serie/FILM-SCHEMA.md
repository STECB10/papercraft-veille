# film.json : la partition d'une vidéo

La charte visuelle est `serie/frame.md` : lis d'abord sa section « Choisir la mise en scène » (quelle planche selon le
type d'étude, ce que dit la voix et ce que lit l'IA) et ses « Règles de fond ». Chaque planche est jouée en animation
dans `serie/reference/planches.html`. Le moteur `serie/moteur/build.py` transforme film.json en animation, format
1080 × 1350. Trois temps : **la table** (`night` : une feuille imprimée posée sur une table kraft, la caméra la descend :
le problème, le contexte), puis, après le **pivot** (la question, en grande typo) et un pli, **la feuille** plein cadre
(`paper` : l'étude, une planche par écran), puis **la fin** (promesse, logo, bouton Suivre). Sous-titres mot à mot
automatiques. **Tu ne places rien** : pas de `y`, le moteur espace lui-même les planches (un `y` éventuel est ignoré).

## Temps : toujours des ancres sur la voix

Jamais de secondes écrites à la main (sauf `0` pour le début). Le moteur ajoute seul 0,8 s d'entrée muette avant le
premier mot (la feuille est posée, l'en-tête s'écrit) : `0` veut dire « quand la voix commence », rien à compter. Ancres :
`"s3"` début de la phrase 3 (index dans `sentences`, à partir de 0) · `"s3.e"` fin de la phrase 3 ·
`"s3:photo"` début du mot « photo » dans la phrase 3 (casse et ponctuation ignorées) · `"s3:photo.e"` fin de ce mot ·
`"s3.w2"` 3e mot de la phrase · décalage : `"s3-0.2"`, `"s3:photo+0.3"`.
Règle : un élément apparaît au mot qui le nomme ; la caméra (`cam_at`) part 0,2 à 0,3 s avant la phrase de la station.

## Champs racine

```json
{"id": "<date>", "sentences": [...], "night": {"start": 0, "end": "<ancre>", "stations": [...]},
 "pivot": {"text": "<phrase exacte>", "italic": "<un mot>", "fold_at": "sN.e+0.12"},
 "paper": {"stations": [...]}, "end": {...}}
```
`duration`, `audio`, `words_file` sont remplis par la chaîne. `night.end` = fin de la dernière phrase du problème + 0,25.
`edition` (facultatif) force une édition de `serie/moteur/editions.json` ; sinon le moteur fait tourner les éditions
(palette, papier des planches, style du mot-clé des sous-titres, façon dont les planches arrivent) d'un jour à
l'autre : ne la fixe pas sans raison. Les planches de l'étude ne reprennent jamais exactement la suite de la veille.

## sentences

`{"text": "phrase dite, chiffres EN LETTRES, dite comme à l'oral (voir REGLES-CONTENU.md, « Parler comme un humain »)",
"display": "phrase affichée, chiffres en chiffres (facultatif)",
"box": "mot affiché encadré (un par phrase)", "peak": "1 ou 2 mots soulignés (3 à 4 fois par film)",
"mode": "sub" (défaut) | "type" (pivot ou nuance : grande typo, pas de sous-titre) | "none" (fin),
"pause_apres": secondes de silence ajoutées après la phrase}`

- `pause_apres` : **peu**, sinon la voix devient hachée. 0,3 à 0,5 aux seuls changements de partie (après le contexte,
  après la méthode, après le résultat principal : 2 à 7 par film) ; 1.4 sur la phrase du pivot (obligatoire, 1.0 à
  2.0) ; 2.5 après la phrase où commence le moment muet (si gag) ; 0.3 sur la dernière phrase avant la promesse. Entre
  deux phrases ordinaires, rien : la voix respire seule.
- Les deux dernières phrases sont toujours `"Une étude par jour, vérifiée à la source."` (mode none) puis
  `"Papercraft."` (mode none).
- Un sous-titre affiche 30 caractères au plus par morceau : phrases courtes.

## Planches de la table (`night.stations`, dans l'ordre)

**1. L'accroche (toujours la première station, `cam_at` 0).** Cinq mises en scène : choisis celle qui sert le mieux
l'étude, et **jamais la même que la veille** (le vérificateur refuse). Toutes ont un `header` mono (type d'étude ·
lieu · années, 60 caractères au plus) et une `footnote?` mono (60 caractères au plus). Le moteur calcule seul les
tailles : un chiffre ou un titre prend la plus grande taille qui tient, aucun texte ne déborde.

- `hook_number` **un chiffre clé** : `number` (« 11,1 », « 185 », 7 caractères au plus), `unit` (« % », « mm »,
  ou un mot : « études », « patients » ; 14 caractères au plus), `caption` (ce que veut dire le chiffre, 75 caractères
  au plus), `caption_at`, `lit_at?`, `icon?`, `visual?`, `ratio?`. Sous le chiffre, une **figure qui dit ce chiffre**,
  choisie seule par le moteur (ou forcée par `visual`) :
  `grid` pour un pourcentage (100 points, les k % passent à l'accent au mot `lit_at`) · `sheets` pour un nombre
  d'études (autant de petites feuilles jusqu'à 48, une pile au-delà) · `people` pour « k sur n » (`ratio`:
  `{"k": 1, "n": 4}`, deux faits ; k silhouettes s'allument sur n) ou pour un petit effectif de personnes (24 au plus)
  · `icon` grand dessin au trait de l'objet de l'étude (`icon` : heart, brain, eye, xray, fundus, ecg, skin, pill…) ·
  `none`. Plus jamais « 5 silhouettes dont une allumée » : `people` et `lit` sont ignorés.
- `hook_question` **la question en grande typo** : `text` (= la phrase 0 de `sentences`, mot pour mot, 95 caractères
  au plus), `italic` (le mot clé, souligné à la main au moment où il est dit), `icon?`. Les mots s'écrivent avec la
  voix ; pas de sous-titre pendant ce temps.
- `hook_image` **ce que l'étude regarde, redessiné au trait** : `image` (fundus, xray, skin, mammo, ct, `ecg` pour un
  tracé qui défile, ou une icône : heart, brain, eye, mic…), `title` (une phrase sans chiffre, 60 caractères au plus),
  `title_at`, `scan_at?`, `lock_at?` (au mot qui nomme ce qu'on cherche : les repères se verrouillent).
- `hook_versus` **deux chiffres face à face** : `left` et `right` = `{label (24 caractères au plus), number?, unit?,
  note?, at}` ; `left` porte un chiffre, `right` peut rester sans chiffre (un grand « ? » : le résultat viendra),
  `caption?` (90 caractères au plus), `caption_at?`. Pour : avant / avec l'IA, deux groupes, IA / soignants.
- `hook_headline` **le titre de l'étude sur une coupure de papier** : `headline` (le titre traduit en français
  simple, 120 caractères au plus, aucun chiffre hors fiche), `journal?` (« Revue · mois année »), `mark` (des mots qui
  se suivent dans `headline`, surlignés au feutre), `mark_at`.

Choisir : un chiffre frappant et parlant → `hook_number` ; une question qui concerne le spectateur → `hook_question` ;
une IA qui lit une image, un tracé ou un organe → `hook_image` ; une comparaison → `hook_versus` ; un titre qui dit
tout ou une étude sans chiffre d'accroche → `hook_headline`. Varie aussi d'un jour à l'autre.

**2. Un moment muet (facultatif, jamais le même que la veille)** :
- `gag_clock` (horloge qui tourne) : `label` (ex. « des semaines »), `cam_at`.
- `gag_calendar` (page de calendrier dont les jours se barrent) : `label` (ex. « des mois d'attente »), `cam_at`.
- `gag_pile` (dossiers qui s'empilent : la charge, le retard) : `label` (ex. « trop de dossiers »), `cam_at`.
- `gag_waiting` (salle d'attente) : `door` (texte de la porte), `chairs` (6), `occupied` (2), `cam_at`.

**3. `steps`** (parcours en 2 à 4 étapes) : `title`, `cam_at`, `mark_at`, `steps`: [`{icon, label, at, note?,
note_at?, alert?, chips?}`]. `note` complète `label` sans le répéter (jamais « cher » puis « chère »), 28 caractères au
plus. `alert` s'affiche dans l'écran pour l'icône `phone`, sinon en étiquette sous la note.

## Planches de la feuille (`paper.stations`, dans l'ordre, une par écran)

Choisis-les avec le tableau « Choisir la mise en scène » de `serie/frame.md`. `id_card` et `ai_scan` servent à toutes
les études. Noms de groupes (`label`) : courts et explicites, 22 caractères au plus, les mêmes d'une planche à l'autre
(« Sans IA » / « Avec IA », ou « Suivi habituel » / « Avec l'IA »). Le groupe testé a `accent: true`.

**Intervalle de confiance** : chaque fois que la source en donne un pour un écart, mets-le dans `ci` :
`{"value": "+0,09" (texte affiché), "num": 0.09, "low": 0.04, "high": 0.14, "null": 0 (1 pour un rapport : RR, OR,
HR), "at": "<ancre>"}`. Le moteur dessine l'écart annoté et la figure de l'intervalle avec la ligne « aucun effet ».

- `id_card` « L'étude en bref » : `title`, `cam_at`, `rows`: [`{label, value, at, accent?}`] (4 à 6 lignes : type
  d'étude, lieu, patients, durée, critère principal…).
- `ai_scan` **ce que fait l'IA (obligatoire, une fois)** : `input_icon` (fundus, xray, ecg, skin, eye, camera, doc,
  message, mic, heart, brain…), `input_label` (40 caractères au plus), `ai_label` (verbe d'action, 45 caractères au
  plus), `output_label` (30 caractères au plus), `output_note?`, `ai_name?`, `title?`, `modality?` (ce que l'IA lit :
  `image`, `voix`, `texte`, `signal`, `donnees` ; déduit de l'icône sinon), `at` (au mot qui nomme l'entrée),
  `scan_at?`, `core_at?` (au mot qui nomme l'IA), `out_at?` (au mot qui nomme le résultat), `cam_at`.
- `population_split` tirage au sort : `total`, `total_label`, `dot_value` (1 ; 10 au-delà de 600), `count_at`,
  `count_end`, `split_at`, `groups`: [`{label, n}`, `{label, n, accent_at}`] (le 2e est le groupe testé), `cam_at`.
  Jusqu'à 60 personnes, des silhouettes se lèvent ; au-delà, des points.
- `two_groups` ce que vit chaque groupe : `cam_at`, `groups`: 2 × `{label, sub?, accent?, at, steps: [{icon, text,
  at}]}` (2 à 4 étapes, texte de 40 caractères au plus).
- `result_bars` résultat continu (moyennes, scores, délais) en figure : `title`, `unit?`, `groups`: [`{label, value
  (texte affiché, « 12,4 »), num, at, accent?}`] ×2 ou 3, `ci?` (ou `diff` + `diff_at` si pas d'intervalle), `cam_at`.
- `result_strips` même contenu que `result_bars`, en bandes de papier qui se déplient d'une fente, l'écart sur une
  étiquette suspendue : `title`, `groups` ×2 ou 3, `ci?` ou `diff`/`diff_at`, `cam_at`. Une fois par film au plus.
- `result_dots` résultat en proportion (n patients, k « oui ») : `title`, `unit?` (« % »), `groups`: [`{label, n, k,
  value, num, at, accent?}`] ×2, `ci` (ou `diff` + `diff_at`), `cam_at`.
- `metric` mesures (sensibilité, spécificité, AUC, score sur 5…) en jauges : `title`, `metrics`: 1 à 3 × `{label,
  value, num, max? (100 par défaut ; 1 pour une AUC ; 5 pour un score sur 5), unit?, note? (ex. « IC 95 % : 0,85–0,90 » :
  l'intervalle est aussi dessiné sur la jauge), at, accent?}`, `caption?`, `caption_at?`, `cam_at`.
- `diagnostic_grid` précision diagnostique : `total` (100 au plus : l'effectif exact, ou une représentation « pour
  100 patients » dont chaque nombre est un fait calculé), `sick` (malades), `found` (malades repérés), `false_alarms`,
  `legend?`, `at`, `sick_at?`, `scan_at?`, `sens?` et `spec?` : `{value, num, label (ex. « Sensibilité · 18 sur 20 »),
  at}`, `cam_at`.
- `roc_curve` courbe ROC d'un modèle : `auc`: `{value, num, at, note? (ex. « IC 95 % : 0,85 à 0,90 »)}`,
  `curve_at?`, `x_label?`, `y_label?`, `cam_at`. La courbe est un schéma tiré de l'AUC (le moteur l'écrit).
- `survival_curves` suivi dans le temps, SEULEMENT si la source donne les valeurs à chaque temps : `title?`, `times`
  (ex. [0, 6, 12, 18, 24]), `x_label`, `groups`: 2 × `{label, values (une par temps, en %), at, accent?}`, `note?`:
  `{text, time, at}` (l'écart annoté à un temps), `cam_at`.
- `forest_plot` méta-analyse, SEULEMENT si la source donne l'effet de chaque étude : `title?`, `null` (0 pour une
  différence, 1 pour un rapport), `studies`: 2 à 12 × `{label (« Martin 2021 »), value, low, high, weight?}`, `pooled`:
  `{label?, value, low, high, at, text? (ex. « RR 0,84 · IC 95 % : 0,77 à 0,91 »)}`, `at` (première étude),
  `left_label?`, `right_label?`, `cam_at`.
- `studies_stack` méta-analyse ou revue, quand le détail par étude manque : `n_studies`, `label?`, `n_patients?`,
  `sub?`, `title?`, `at`, `patients_at?`, `cam_at`.
- `chat` IA conversationnelle : `title?`, `messages`: 1 à 4 × `{from: patient | ia | soignant | question, lines (2 à
  5 lignes muettes), at, label?}`, `rating?`: `{value (« 4/5 »), label, at}`, `cam_at`. Jamais de texte dans les
  bulles : pas de dialogue inventé.
- `image_scan` l'IA lit une image : `image` (fundus, xray, skin, mammo, ct), `title?`, `at`, `scan_at?`, `lock_at?`
  (au mot qui nomme ce qui est trouvé), `out_at?`, `found_label` (ex. « Signes de rétinopathie »), `result_label?`
  (ex. « Résultat en 1 minute »), `cam_at`. L'image est redessinée au trait (mention « schéma »).
- `flow_chart` **le parcours des participants**, en entonnoir (comme le diagramme de flux de l'article) : `title?`,
  `stages`: 2 à 5 × `{label (40 caractères au plus), n (effectif affiché, « 2 378 »), at, accent?}` (de l'effectif de
  départ à celui qui est analysé ; la dernière étape passe à l'accent sauf si une autre porte `accent`),
  `excluded?`: [`{after (index de l'étape après laquelle on sort), label (26 caractères au plus), n, at}`], `cam_at`.
  Pour un essai, une cohorte ou un dépistage dont la source donne les effectifs de chaque étape.
- `big_stat` **LE résultat, en grand** : `title?`, `value` (« 35,9 », « 6 sur 10 », 9 caractères au plus), `num?`,
  `unit?` (« % » : un anneau se trace jusqu'à la valeur), `label` (ce que dit le chiffre, 90 caractères au plus),
  `label_at?`, `compare?`: `{value, unit?, label, at}` (le groupe comparé : son anneau se trace à l'intérieur), `at`,
  `cam_at`. Une fois par film au plus, pour le résultat qu'on doit retenir.
- `timeline` **la chronologie de l'étude** : `title?`, `events`: 2 à 5 × `{when (« Mars 2023 », « 10 mois », 16
  caractères au plus), label (60 au plus), at, accent?}`, `cam_at`. Pour une cohorte, un suivi, des inclusions sur
  plusieurs années (chaque date doit être un fait).
- `key_points` constats numérotés (revue, cohorte, limites) : `title?`, `points`: 2 à 4 × `{text (70 caractères au
  plus), at}`, `cam_at`.
- `typo` phrase en grande typo : `text` (= une phrase de `sentences`, mot pour mot), `italic`, `cam_at`. Deux au plus :
  la nuance (la première arrive par une déchirure qui révèle le verso) puis la phrase à retenir. Le sous-titre est
  masqué pendant ce temps.

Icônes permises : camera, magnifier, phone, chair, door, check, fundus, doc, clock, calendar, chart, chip, heart,
pill, hospital, eye, brain, stethoscope, user, users, message, xray, ecg, skin, mic.

## end

`{"fold_at": "<dernière phrase avant la promesse>.e+0.2", "promise": "Une étude par jour, vérifiée à la source.",
"promise_italic": "vérifiée", "wordmark_at": "s<Papercraft>", "button": "Suivre", "button_at": "s<Papercraft>+0.6",
"click_at": "s<Papercraft>+1.6", "source": "Auteur et al. · Revue · mois année", "doi": "doi:10.…",
"source_at": "s<promesse>:vérifiée-0.2"}`
