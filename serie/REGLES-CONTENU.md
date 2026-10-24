# Règles de contenu de la série (retour de Steven sur le pilote, 24 octobre 2026)

Le pilote manquait de détails : on ne comprenait ni le sens de l'étude, ni la différence entre les groupes, et les
résultats étaient trop maigres. Le motion design, la musique et la voix sont validés tels quels.

## Durée et densité

- Durée cible : 80 à 100 s, soit environ 210 à 280 mots dits (retour du 24 octobre : prendre plus de temps
  au début pour que le contexte soit bien compris).
- Chaque phrase porte une information. Pas de phrase d'ambiance sans fait.

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
| Essai tiré au sort, comparaison de groupes | qui reçoit quoi, par qui, quand, dans chaque groupe | valeur de chaque groupe (n/N), écart, IC | `two_groups`, `population_split`, `result_dots` ou `result_bars` |
| Performance d'un modèle (diagnostic, détection) | sur quelles données l'IA a été entraînée et testée, contre quelle référence | sensibilité, spécificité, AUC, comparaison aux soignants s'il y en a une | `metric`, `result_bars` |
| Cohorte, prédiction | qui a été suivi, combien de temps, quelles données entrent dans le modèle | ce que le modèle prédit et avec quelle précision, les facteurs qui comptent | `metric`, `key_points`, `result_bars` |
| Méta-analyse, revue systématique | combien d'études, de patients, sur quelle période, comment elles ont été choisies | le résultat regroupé (avec IC et hétérogénéité si elle est donnée), ce qui varie d'une étude à l'autre | `studies_stack`, `metric` ou `result_bars`, `key_points` |
| Revue de littérature | quel champ, combien de travaux, la question posée | les 3 ou 4 grands constats, ce qui manque encore | `studies_stack`, `key_points` |
| Autre (qualitative, enquête, économie…) | ce qui a été fait, concrètement | les constats principaux, chiffrés si possible | `key_points`, `result_bars`, `metric` |

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
- La source avec le lien de l'article (https://doi.org/<DOI>).
- 3 à 4 hashtags.
