# film.json : la partition d'une vidéo

La charte visuelle est `serie/frame.md` : lis d'abord sa section « Choisir la mise en scène » (quelle planche selon le
type d'étude, ce que dit la voix et ce que lit l'IA) et ses « Règles de fond ». Chaque planche est jouée en animation
dans `serie/reference/planches.html`. Le moteur `serie/moteur/build.py` transforme film.json en animation, format
1080 × 1350. Trois temps : **la table** (`night` : une feuille imprimée posée sur une table kraft, la caméra la descend :
le problème, le contexte), puis, après le **pivot** (la question, en grande typo) et un pli, **la feuille** plein cadre
(`paper` : l'étude, une planche par écran), puis **la fin** (promesse, logo, bouton Suivre). Sous-titres mot à mot
automatiques. **Tu ne places rien** : pas de `y`, le moteur espace lui-même les planches (un `y` éventuel est ignoré).

## Temps : toujours des ancres sur la voix

Jamais de secondes écrites à la main (sauf `0` pour le début). Ancres :
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

## sentences

`{"text": "phrase dite, chiffres EN LETTRES", "display": "phrase affichée, chiffres en chiffres (facultatif)",
"box": "mot affiché encadré (un par phrase)", "peak": "1 ou 2 mots soulignés (3 à 4 fois par film)",
"mode": "sub" (défaut) | "type" (pivot ou nuance : grande typo, pas de sous-titre) | "none" (fin),
"pause_apres": secondes de silence ajoutées après la phrase}`

- `pause_apres` : 0.3 à 0.6 après chaque information clé (respiration) ; 2.5 après la phrase où commence le moment muet (si gag), 1.4 sur la phrase du pivot (obligatoire,
  1.0 à 2.0), 0.3 sur la dernière phrase avant la promesse.
- Les deux dernières phrases sont toujours `"Une étude par jour, vérifiée à la source."` (mode none) puis
  `"Papercraft."` (mode none).
- Un sous-titre affiche 30 caractères au plus par morceau : phrases courtes.

## Planches de la table (`night.stations`, dans l'ordre)

- `hook_number` (`cam_at` 0) : `header` (mono, ex. « Essai randomisé · Tanzanie · 2023–2024 »), `number`
  (« 18,2 »), `unit` (« % »), `caption`, `caption_at`, `people` (5), `lit` (index de la silhouette allumée), `lit_at`,
  `footnote`.
- `gag_waiting` (moment muet, salle d'attente) : `door` (texte de la porte), `chairs` (6), `occupied` (2), `cam_at`.
- `gag_clock` (moment muet, horloge qui tourne) : `label` (ex. « des semaines »), `cam_at`.
- `steps` (parcours en 2 à 4 étapes) : `title`, `cam_at`, `mark_at`, `steps`: [`{icon, label, at, note?, note_at?,
  alert?, chips?}`]. `note` complète `label` sans le répéter (jamais « cher » puis « chère »). `alert` s'affiche dans
  l'écran pour l'icône `phone`, sinon en étiquette carbone sous la note.

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
