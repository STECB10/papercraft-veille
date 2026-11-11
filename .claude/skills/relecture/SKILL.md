---
name: relecture
description: Relit en vérificateur indépendant le film du jour (jours/<date>/) contre source.txt - sens des résultats, causalité, population, mesure, limite, clarté - corrige le strict nécessaire, fait revalider par pipeline/verifier.py et écrit relecture.json. Lancé par GitHub Actions après /etude-du-jour.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# La relecture indépendante (le vérificateur du binôme)

Tu n'as pas écrit ce film. Un autre agent l'a écrit ; `pipeline/verifier.py` a déjà prouvé que chaque **chiffre** vient
de la source. Toi, tu vérifies ce qu'un programme ne sait pas vérifier : que les **phrases disent ce que l'étude dit**.
Tu travailles seul, sans humain à qui poser une question. La date est dans `DATE_DU_JOUR` (dossier `jours/$DATE_DU_JOUR/`).

Règle d'or : **ne cherche pas à améliorer le style, cherche les erreurs.** Si tout est juste, tu ne modifies rien et tu
le dis. Une relecture qui invente des problèmes est pire qu'une relecture qui n'en trouve pas.

## 1. Lire

Dans cet ordre : `source.txt` (le résumé, puis Méthodes, Résultats, et la partie Limites de la Discussion),
`faits.json`, puis `film.json` (les `sentences`, puis les planches de `night` et `paper`), enfin `post.txt`.
Ne lis pas `SCRIPT.md` avant d'avoir fini : sa section « Relecture » est l'avis de l'auteur, pas le tien.

## 2. Contrôler, phrase par phrase

Pour chaque phrase dite et chaque planche, retrouve dans `source.txt` le passage qui la porte, et pose-toi :

1. **Le sens de l'effet.** Qui fait mieux, plus, moins ? Le groupe mis en accent est-il bien le groupe testé ? Un
   « plus de complications » n'est pas devenu « moins » ; les groupes ne sont pas inversés sur une planche.
2. **La force de la preuve.** Un verbe de cause (« réduit », « améliore », « permet », « fait baisser ») seulement pour
   un essai tiré au sort dont l'intervalle exclut l'absence d'effet. Sinon : « est associé à », « s'accompagne de ».
   « Significatif » seulement si la source le dit. Un résultat dont l'intervalle contient l'absence d'effet est dit
   comme tel (« pas de différence démontrée »), pas comme une baisse ou une hausse.
3. **Qui et contre quoi.** L'effectif, la population (âge, pays, critères), le comparateur réel (soins habituels,
   témoin actif, médecins seuls…). Un résultat de sous-groupe est présenté comme un sous-groupe.
4. **Ce qui est mesuré.** L'unité, l'échelle, le moment (« à douze mois »). Le résultat présenté comme principal est
   bien le critère principal de l'étude ; un critère secondaire ou exploratoire est dit comme tel.
5. **Ce que fait l'IA.** Ce qui entre, ce qu'elle produit, qui décide à la fin : comme dans la méthode, sans lui prêter
   un rôle qu'elle n'a pas (« l'IA diagnostique » alors qu'elle alerte un soignant).
6. **La limite.** C'est une limite que les auteurs écrivent, et elle est fidèle.
7. **Le post.** Mêmes exigences ; la première ligne ne promet pas plus que l'étude.
8. **La clarté.** Une phrase qu'un auditeur ne comprendrait pas à la première écoute (tournure bancale, sigle jamais
   expliqué, mot de jargon).

Classe chaque problème :
- **bloquant** : contresens, surinterprétation, erreur de population, de comparateur ou de mesure (points 1 à 7) ;
- **mineur** : clarté (point 8).

## 3. Corriger le strict nécessaire

- Corrige **tous les bloquants**. Corrige un mineur seulement si une retouche d'une phrase suffit.
- Quatre phrases modifiées au plus. Au-delà, c'est que le film est à réécrire : ne touche à rien, verdict
  « à réécrire », et décris les problèmes.
- Garde la même longueur à quelques mots près : le film doit rester entre 210 et 300 mots dits.
- Quand tu changes le texte d'une phrase dans `film.json`, mets à jour **tout ce qui en dépend** : son `display`
  (mot pour mot, chiffres en chiffres), son `box` et son `peak` s'ils citent un mot disparu, les ancres `"sN:mot"` qui
  visaient un mot que tu as retiré (choisis le mot qui nomme maintenant la même chose), le `text` du `pivot` ou d'une
  planche `typo` si c'est cette phrase, la `source` de la phrase, et le texte dit recopié dans `SCRIPT.md`.
- Aucun chiffre nouveau sans son fait dans `faits.json` (avec sa citation mot pour mot).
- Ne change ni le choix de l'étude, ni l'ordre du récit, ni les planches (sauf un libellé faux ou des groupes inversés).

## 4. Revalider

`python3 pipeline/nombres.py` puis `python3 pipeline/verifier.py`. S'il répond REFUSÉ, corrige et relance (trois essais
au plus). S'il refuse toujours, remets les fichiers d'origine :
`cp jours/$DATE_DU_JOUR/.avant-relecture/* jours/$DATE_DU_JOUR/` et note le verdict « abandonnée ».

## 5. Rendre compte : `relecture.json`

Écris `jours/$DATE_DU_JOUR/relecture.json` :

```json
{"verdict": "rien à corriger | corrigé | à réécrire | abandonnée",
 "resume": "une phrase pour l'humain qui valide (120 caractères au plus) : ce que tu as vérifié ou changé",
 "points": [{"gravite": "bloquant | mineur", "ou": "phrase 12 | planche paper 3 | post",
             "probleme": "ce qui n'allait pas, en une phrase",
             "preuve": "l'extrait de source.txt, mot pour mot, qui le montre",
             "avant": "le texte d'origine", "apres": "le texte corrigé (ou null si tu n'as pas corrigé)"}]}
```

`points` est vide quand le verdict est « rien à corriger ». Tu as fini quand `relecture.json` est écrit et que
`pipeline/verifier.py` répond VALIDÉ. Ne lance ni la voix, ni le rendu, ni la publication.
