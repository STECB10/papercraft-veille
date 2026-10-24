# film.json : la partition d'une vidéo

Exemple complet (pilote, ancien format court) : `serie/exemple/film.json`. Le moteur `serie/moteur/build.py` le
transforme en animation. Format 1080 × 1350. Deux mondes : la **nuit** (une feuille imprimée inclinée, la caméra la
descend : le problème, le contexte) puis, après un **pivot** sur noir et un pli, le **papier** plein cadre (l'étude,
les groupes, les résultats), puis la **fin** (promesse, logo, bouton Suivre). Sous-titres mot à mot automatiques.

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

- `pause_apres` : 2.5 après la phrase où commence le moment muet (si gag), 1.4 sur la phrase du pivot (obligatoire,
  1.0 à 2.0), 0.3 sur la dernière phrase avant la promesse.
- Les deux dernières phrases sont toujours `"Une étude par jour, vérifiée à la source."` (mode none) puis
  `"Papercraft."` (mode none).
- Un sous-titre affiche 30 caractères au plus par morceau : phrases courtes.

## Stations de la nuit (y croissants, sur une feuille de 780 px de large)

- `hook_number` (y 0, `cam_at` 0) : `header` (mono, ex. « Essai randomisé · Tanzanie · 2023–2024 »), `number`
  (« 18,2 »), `unit` (« % »), `caption`, `caption_at`, `people` (5), `lit` (index de la silhouette allumée), `lit_at`,
  `footnote`.
- `gag_waiting` (moment muet, salle d'attente) : `door` (texte de la porte), `chairs` (6), `occupied` (2), `cam_at`.
- `gag_clock` (moment muet, horloge qui tourne) : `label` (ex. « des semaines »), `cam_at`.
- `steps` (parcours en 2 à 4 étapes) : `title`, `cam_at`, `mark_at`, `steps`: [`{icon, label, at, note?, note_at?,
  alert?, chips?}`]. Une étape occupe 330 px.
Espacements minimum : après `hook_number` +980, après un gag +660.

## Stations du papier (y croissants)

Choisis-les selon le type d'étude (tableau de REGLES-CONTENU.md) : `two_groups` / `population_split` /
`result_dots` pour des groupes comparés ; `metric` pour une performance ; `studies_stack` + `key_points` pour une
méta-analyse ou une revue. `id_card` et `ai_scan` servent à toutes les études.

- `id_card` « L'étude en bref » : `title`, `cam_at`, `rows`: [`{label, value, at, accent?}`] (4 à 6 lignes : type
  d'étude, lieu, patients, durée, critère principal…). Hauteur +1100.
- Noms de groupes (`label` dans `two_groups`, `population_split`, `result_dots`, `result_bars`) : courts et explicites,
  22 caractères au plus, les mêmes d'une station à l'autre (« Sans IA » / « Avec IA », ou « Suivi habituel » / « Avec
  l'IA »). Jamais de sigle ni de libellé technique.
- `two_groups` les groupes comparés : `cam_at`, `groups`: 2 × `{label, sub?, accent?, at, steps: [{icon, text, at}]}`
  (2 à 4 étapes, texte de 40 caractères au plus ; le groupe testé a `accent: true`). Hauteur ≥ 1100.
- `ai_scan` **ce que fait l'IA (obligatoire, une fois, juste après `id_card` ou `two_groups`)** : `input_icon`
  (ce qui entre : fundus, xray, ecg, skin, eye, camera, doc, message, mic, heart, brain…), `input_label` (ex. « Photo du
  fond de l'œil », 40 caractères au plus), `ai_label` (ce que l'IA fait, verbe d'action : « repère les signes de
  rétinopathie », 45 caractères au plus), `output_label` (ce qui sort : « Résultat en 1 minute », 30 caractères au
  plus), `output_note?`, `ai_name?` (nom du logiciel s'il est dit), `title?` (défaut « Ce que fait l'IA »), `at` (au
  mot qui nomme l'entrée), `scan_at?`, `core_at?` (au mot qui nomme l'IA), `out_at?` (au mot qui nomme le résultat),
  `cam_at`. Hauteur +1180.
- `population_split` des points-patients qui se partagent : `total`, `total_label`, `dot_value` (10 si > 600),
  `count_at`, `count_end`, `split_at`, `groups`: [`{label, n}`, `{label, n, accent: true, accent_at}`], `cam_at`. +1250.
- `result_dots` résultat en proportion (n patients, k « oui ») : `title`, `groups`: [`{label, n, k, value, at, accent?}`]
  ×2, `diff`, `diff_at`, `cam_at`. +1270.
- `result_bars` résultat continu (moyennes, scores, délais) : `title`, `unit`, `groups`: [`{label, value (texte
  affiché, ex. « 12,4 »), num (nombre), at, accent?}`] ×2 ou 3, `diff?`, `diff_at?`, `cam_at`. +1150.
- `face_to_face` deux personnes et une carte : `card_title`, `card_value`, `card_note`, `label`, `at`, `card_at`,
  `label_at`, `check_at`, `cam_at`. +1100.
- `studies_stack` **méta-analyse ou revue** : les études regroupées, une feuille par étude (par lot au-delà de 40) :
  `n_studies`, `label?` (défaut « études »), `n_patients?`, `sub?` (ex. « 2015–2025 · 14 pays »), `title?`, `at` (au
  nombre d'études), `patients_at?`, `cam_at`. Hauteur +1150.
- `metric` **mesures de performance ou résultat regroupé** (sensibilité, spécificité, AUC, précision, risque
  relatif…) : `title`, `metrics`: 1 à 3 × `{label (« Sensibilité »), value (texte affiché, « 92,4 »), num (nombre),
  max? (100 par défaut ; 1 pour une AUC), unit? (« % »), note? (ex. « IC 95 % : 89–95 »), at, accent?}`, `caption?`,
  `caption_at?`, `cam_at`. Les jauges se remplissent jusqu'à num/max. Hauteur +1050.
- `key_points` **constats numérotés** (revue, cohorte, étude qualitative, limites) : `title?` (défaut « Ce qu'il
  faut retenir »), `points`: 2 à 4 × `{text (70 caractères au plus), at}`, `cam_at`. Hauteur 260 + 226 par constat.
- `typo` phrase de nuance en grande typo : `text` (= une phrase de mode type), `italic`, `cam_at`. +680.
- `flow_door` du résultat vers la porte : `from_label`, `to_label`, `at`, `card_at`, `door_at`, `walk_at`, `cam_at`. +850.
- `remaining_dots` ce qui reste à faire : `n`, `k`, `value`, `label`, `at`, `group_label`, `cam_at`. +1100.

Icônes permises : camera, magnifier, phone, chair, door, check, fundus, doc, clock, calendar, chart, chip, heart,
pill, hospital, eye, brain, stethoscope, user, users, message, xray, ecg, skin, mic.

## end

`{"fold_at": "<dernière phrase avant la promesse>.e+0.2", "promise": "Une étude par jour, vérifiée à la source.",
"promise_italic": "vérifiée", "wordmark_at": "s<Papercraft>", "button": "Suivre", "button_at": "s<Papercraft>+0.6",
"click_at": "s<Papercraft>+1.6", "source": "Auteur et al. · Revue · mois année", "doi": "doi:10.…",
"source_at": "s<promesse>:vérifiée-0.2"}`
