# Règles de contenu de la série (retour de Steven sur le pilote, 24 octobre 2026)

Le pilote manquait de détails : on ne comprenait ni le sens de l'étude, ni la différence entre les groupes, et les
résultats étaient trop maigres. Le motion design, la musique et la voix sont validés tels quels.

## Durée et densité

- Durée cible : 85 à 105 s, soit environ 230 à 300 mots dits (les connecteurs sont courts : ils remplacent des mots, ils n'ajoutent pas de phrases) (retour du 24 octobre : prendre plus de temps
  au début pour que le contexte soit bien compris).
- Chaque phrase porte une information. Pas de phrase d'ambiance sans fait.

## Parler comme un humain (retour de Steven du 7 novembre 2026)

La voix doit sonner comme quelqu'un qui **explique une étude à un collègue**, pas comme une fiche lue à voix haute.
Les vidéos d'avant enchaînaient des constats posés l'un après l'autre (« Il s'agit d'une cohorte. Mille adultes ont
été suivis. Dix-huit données entrent dans l'algorithme. ») : c'est exactement ce qu'il ne faut plus faire.

- **Chaque phrase s'accroche à la précédente.** Au moins 6 phrases sur 10 commencent par un connecteur ou une tournure
  orale, et jamais trois phrases de suite sans lien (le vérificateur refuse). Varie : aucun connecteur n'ouvre plus de
  deux phrases.
  - enchaîner : « Et », « Alors », « Du coup » (rare), « À partir de là », « C'est là qu'… », « Pour le savoir »
  - opposer : « Mais », « Or », « Pourtant », « Le problème, c'est que… », « En revanche »
  - expliquer : « Concrètement », « Autrement dit », « En clair », « Par exemple »
  - ordonner : « D'abord », « Puis », « Ensuite », « Enfin », « Au départ », « Au final »
  - conclure : « Résultat : », « Bonne nouvelle : », « Attention quand même : », « À retenir : »
- **Le registre de l'oral, en restant exact** : « ils ont suivi… » plutôt que « … ont été suivis » ; « il n'en garde que
  deux » plutôt que « il en retient deux » ; des questions qu'on pose au spectateur (« Et le résultat ? ») ; des mots
  de tous les jours. Jamais d'emphase gratuite (« incroyable », « révolution »), jamais de familiarité appuyée.
- **Des phrases qui respirent** : 9 à 20 mots en moyenne, longueurs variées (une courte après deux longues), une
  phrase de moins de 6 mots seulement pour un effet voulu (2 au plus par film). Une virgule ou deux-points là où l'on
  ferait une pause en parlant.
- **L'intro raconte** : qui est concerné, quel est le problème, pourquoi c'est important, avant tout chiffre isolé.
  Le premier chiffre arrive dans une phrase qui l'explique.
- **Expliquer la méthode et les résultats pas à pas**, quitte à ralentir : ce qu'on a mesuré, comment, chez qui, puis
  ce que veut dire le chiffre (« autrement dit, sur dix patients… »).
- **Peu de silences ajoutés** : `pause_apres` 0,3 à 0,5 s aux seuls changements de partie (2 à 7 par film), en plus
  des pauses imposées (moment muet, pivot, avant la promesse). Entre deux phrases ordinaires, la voix respire seule :
  des silences partout donnent une lecture hachée.
- **Nombres** : dans le texte dit, toujours en toutes lettres (« zéro virgule huit cent quarante-cinq »,
  « dix-huit virgule deux pour cent »). `pipeline/nombres.py` convertit automatiquement s'il reste des chiffres.

Avant / après (même étude, mêmes faits) :

| Avant (liste de constats) | Après (quelqu'un qui explique) |
|---|---|
| Il s'agit d'une cohorte prospective, menée à Wuxi et Nantong, en Chine. | Pour le savoir, les chercheurs ont mené une cohorte prospective à Wuxi et à Nantong, en Chine. |
| Mille cent cinquante-six adultes ont été suivis dix mois, en médiane, pour repérer les réinfections avec symptômes. | Concrètement, ils ont suivi mille cent cinquante-six adultes pendant dix mois, en médiane, en notant les réinfections avec symptômes. |
| Dix-huit données entrent dans l'algorithme, les unes cliniques, les autres immunitaires. Il en retient deux : … | Au départ, dix-huit données entrent dans l'algorithme, cliniques ou immunitaires. Mais il n'en garde que deux : … |
| En vérification interne, l'aire sous la courbe atteint zéro virgule huit cent trente-cinq. | Résultat : en vérification interne, l'aire sous la courbe atteint zéro virgule huit cent trente-cinq. |
| À Nantong, l'aire sous la courbe monte à zéro virgule neuf cent quatre-vingt-seize. | À Nantong, c'est encore mieux : l'aire sous la courbe monte à zéro virgule neuf cent quatre-vingt-seize. |
| Cette étude montre une bonne prédiction, pas une réduction des réinfections. | Attention : l'étude montre une bonne prédiction, pas moins de réinfections. |

Le script complet de cet exemple est dans `serie/exemple/SCRIPT-NATUREL.md`.

## Un récit qui se tient (retour de Steven du 8 novembre 2026)

Sur la vidéo du trouble bipolaire : « le problème, c'est que le diagnostic repose sur un entretien avec le psychiatre »
(ah bon ? pourquoi est-ce un problème ?), des performances de modèle mais presque aucun résultat concret (« c'est la
façon de parler qui trahit la maladie » : mais quoi exactement ?), et une fin décousue (la voix, puis les limites, puis
de nouveau la voix). Quatre règles, toutes contrôlées par `pipeline/verifier.py` :

1. **Un problème annoncé est un problème expliqué.** Dire pourquoi c'en est un pour les patients : sa cause (« aucune
   mesure objective n'existe ») et sa conséquence (« trois patients sur quatre sont d'abord pris pour des dépressifs,
   d'où six ans de retard alors que le traitement dépend de la phase »). Deux phrases au moins dans la partie
   « probleme », ou une phrase qui dit la cause ou la conséquence. Chaque phrase du problème cite sa preuve (`source`).
   Si l'auditeur peut demander « et alors ? » ou « pourquoi ? », la réponse est dans la phrase suivante.
2. **Des résultats concrets, de terrain**, après les performances (partie « concret », 2 à 5 phrases) : ce que l'IA
   repère exactement (quels indices, avec des exemples), ce qui diffère entre les groupes, ce que ça change pour un
   patient ou un soignant. Cherche-les dans les Résultats et la Discussion du texte intégral, pas seulement dans le
   résumé. Chaque phrase concrète cite l'extrait de `source.txt` qui la prouve (`source`, mot pour mot). Si la source
   ne donne vraiment rien de concret, dis-le et choisis une autre étude.
3. **Un seul fil, dans l'ordre**, chaque partie dite une fois (champ `partie` de chaque phrase) : accroche → contexte →
   problème → ce que fait l'IA → question → l'étude → méthode → résultats et concret (ils peuvent alterner) → limite →
   à retenir → fin. Jamais de retour en arrière. La phrase à retenir ne redit pas un résultat : elle dit ce que
   l'étude change, ou pourrait changer, en pratique, en tenant compte de la limite.
4. **Des connecteurs qui disent vrai et des chiffres qu'on comprend.** Le connecteur décrit la vraie relation (« Le
   problème » annonce un problème, « Résultat : » une conséquence ou un résultat, « Autrement dit » reformule la phrase
   d'avant, jamais « En prime » devant un intervalle de confiance). Sensibilité et spécificité se disent en « x sur y »
   ou en pour cent, jamais en « zéro virgule » ; l'aire sous la courbe est située une fois (« tout près du maximum de
   un ») ; un effectif se traduit en personnes (« sur soixante patients, cinquante-six repérés »).

Avant de valider, relis le script comme un auditeur qui ne connaît pas le sujet et écris tes réponses dans SCRIPT.md
(section « ## Relecture », une puce par question, voir la skill).

## Ce que chaque script doit dire, dans cet ordre

0. **L'accroche** (la première phrase, 8 à 14 mots) : une question ou un constat qui parle directement au
   spectateur et lui donne envie de rester (« Votre radio a peut-être déjà été lue par une IA. »). Pas de chiffre
   qui ne soit pas dans la fiche des faits.
1. **Le contexte** (4 à 5 phrases, sans se presser) : ce qu'est la maladie ou la situation en mots simples, qui est
   concerné (un chiffre sourcé), comment on fait aujourd'hui, pourquoi ça coince, puis ce que fait l'IA testée,
   concrètement (ce qu'elle regarde, ce qu'elle produit, qui l'utilise).
2. **La question de l'étude** en une phrase claire : « Les chercheurs ont voulu savoir si… ».
3. **La carte d'identité de l'étude** : type (essai tiré au sort, méta-analyse, revue, cohorte, étude diagnostique,
   rétrospective, préprint non relu), lieu, nombre de patients (ou d'études), durée ou période, ce qui est mesuré.
4. **La méthode, expliquée concrètement**, et 5. **les résultats** : leur forme dépend du type d'étude (tableau
   ci-dessous). Toujours le résultat principal avec sa valeur exacte, son intervalle de confiance s'il existe, puis 1
   ou 2 résultats secondaires utiles.
6. **La portée et les limites** : ce que l'étude montre, ce qu'elle ne montre pas, 1 limite concrète.
7. **La phrase à retenir**, puis la signature « Une étude par jour, vérifiée à la source. Papercraft. »

## La trame s'adapte au type d'étude

Le récit (accroche → contexte → question → carte d'identité → ce que fait l'IA → méthode → résultats → portée →
phrase à retenir) est le même pour tous ; ce qui change, c'est la méthode, les résultats et les stations qui les
montrent. Ne jamais forcer une étude dans une trame qui ne lui va pas (pas de « deux groupes » s'il n'y en a pas).

| Type d'étude | Méthode à expliquer | Résultats | Stations conseillées |
|---|---|---|---|
| Essai tiré au sort, comparaison de groupes | qui reçoit quoi, par qui, quand, dans chaque groupe | valeur de chaque groupe (n/N), écart, IC | `population_split`, `two_groups`, `result_bars`, `result_strips` ou `result_dots` (avec `ci`), `metric` |
| Précision diagnostique (détection) | sur quelles données l'IA a été testée, contre quelle référence | sensibilité, spécificité, comparaison aux soignants s'il y en a une | `image_scan` si l'IA lit une image, `diagnostic_grid`, `metric` |
| Modèle prédictif, cohorte | qui a été suivi, combien de temps, quelles données entrent dans le modèle | AUC, ce que le modèle prédit, les facteurs qui comptent | `roc_curve` (AUC), `survival_curves` (valeurs dans le temps), `metric`, `key_points` |
| Méta-analyse, revue systématique | combien d'études, de patients, sur quelle période, comment elles ont été choisies | le résultat regroupé (avec IC et hétérogénéité si elle est donnée), ce qui varie d'une étude à l'autre | `studies_stack`, `forest_plot` (effet de chaque étude), `metric`, `key_points` |
| Revue de littérature | quel champ, combien de travaux, la question posée | les 3 ou 4 grands constats, ce qui manque encore | `studies_stack`, `key_points` |
| IA conversationnelle (chatbot, patient virtuel) | qui parle à l'IA, de quoi, qui juge les réponses | notes des évaluateurs, comparaison de groupes s'il y en a | `chat`, `metric`, `result_bars` |
| Autre (qualitative, enquête, économie…) | ce qui a été fait, concrètement | les constats principaux, chiffrés si possible | `key_points`, `result_bars`, `metric` |

La mise en scène détaillée (quelle planche selon ce que dit la voix et ce que lit l'IA, quels gestes) est dans
`serie/frame.md`, section « Choisir la mise en scène ».

## L'IA au centre

La page parle d'IA en santé. L'étude choisie doit avoir **un vrai lien avec l'IA ou le machine learning** : un
outil d'IA testé sur des patients, un modèle qui prédit, détecte ou classe, un assistant conversationnel, une
comparaison IA / soignants, etc. Seule une étude où l'IA n'est qu'une mention en passant est hors sujet.

## Sous-titres

Le sous-titre (`display`) reprend le texte dit **mot pour mot et en entier** ; seuls les nombres passent en
chiffres (« trente-six pour cent » → « 36 % »). Jamais de mot retiré, ajouté ou reformulé.

## Écran

- Une station « carte d'identité » (type, lieu, n, durée, critère) après la question.
- Une station « ce que fait l'IA » (`ai_scan`) : ce qui entre, l'IA qui analyse, ce qui sort. Obligatoire.
- Des noms de groupes explicites et courts (« Sans IA » / « Avec IA »), lisibles sur un téléphone.
- Les stations de méthode et de résultats suivent le tableau ci-dessus : « deux groupes » seulement s'il y a des
  groupes comparés ; « études regroupées », « mesures » ou « constats » sinon.
- Une station « résultats » : les deux valeurs, les points-patients, l'écart et son IC 95 %.
- Les chiffres restent ceux de la fiche des faits, tirée du texte intégral quand il est accessible (sinon du résumé,
  et la vidéo le dit en source).

## Post LinkedIn

- Ligne 1 : une phrase d'accroche (le résultat clé en langage simple).
- 2 à 3 phrases : la question, la méthode (les groupes, les études regroupées…), le résultat principal.
- Une question ouverte d'une ligne aux soignants, pour lancer les commentaires (« Et vous, dans votre pratique… ? »).
- La source avec le lien de l'article (https://doi.org/<DOI>).
- 3 à 4 hashtags.
