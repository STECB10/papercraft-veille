# Machine Learning Classification of Bipolar Disorder Across Mood States Using NLP and Speech Analysis

Yamaguchi et al., Journal of Medical Internet Research, novembre 2026. Étude observationnelle prospective (Japon, 2017–2024).

**Raison du choix** : vrai modèle d'IA (voix + langage) avec résultat chiffré et intervalle de confiance, utile aux soignants en psychiatrie ; texte intégral disponible ; accroche et moment muet différents de la veille.

**Rôle de l'IA** : un modèle d'apprentissage automatique analyse la voix et les mots d'un entretien pour estimer la probabilité d'un trouble bipolaire.

## Texte dit

0. Votre voix pourrait-elle trahir un trouble bipolaire ?
1. Le trouble bipolaire touche entre un et trois pour cent des adultes.
2. Et pourtant, il faut en moyenne six ans pour poser le bon diagnostic.
3. Le problème, c'est que le diagnostic repose sur un entretien avec le psychiatre.
4. Alors des chercheurs japonais ont confié la parole des patients à un algorithme d'apprentissage automatique.
5. Il écoute comment on parle, mais aussi ce qu'on dit.
6. Cette analyse de la parole peut-elle repérer un trouble bipolaire ?
7. Pour le savoir, ils ont mené une étude prospective, dans plusieurs centres du Japon.
8. Concrètement, ils ont recruté soixante et un patients bipolaires et quatre-vingt-dix-neuf témoins en bonne santé.
9. Chacun a passé un entretien de trente à soixante minutes.
10. Au départ, l'algorithme reçoit six mille trois cent soixante-treize mesures du son, et deux cent onze du langage.
11. Ensuite, il trie ces mesures et ne garde que les plus utiles.
12. À partir de là, il en tire une probabilité : patient bipolaire ou non.
13. Résultat : l'aire sous la courbe atteint zéro virgule neuf cent seize.
14. En prime, l'intervalle de confiance va de zéro virgule huit cent cinquante-quatre à zéro virgule neuf cent cinquante-huit.
15. Autrement dit, il repère cinquante-six patients sur soixante, soit une sensibilité de zéro virgule neuf cent trente-trois.
16. Et il reconnaît quatre-vingt-cinq témoins sur quatre-vingt-dix-neuf : la spécificité est de zéro virgule huit cent cinquante-neuf.
17. Mais qui porte le résultat, la voix ou les mots ?
18. Le son seul atteint zéro virgule neuf cent dix, contre zéro virgule six cent cinquante et un pour les mots.
19. Attention : pas de comparaison avec d'autres maladies psychiatriques, et les groupes restent petits.
20. À retenir : c'est surtout la façon de parler, plus que les mots, qui signale la maladie.
21. Une étude par jour, vérifiée à la source.
22. Papercraft.

## Fiche des faits

| id | valeur | source |
|---|---|---|
| f1 | 1 | 'affects 1% to 3% of adults worldwide' |
| f2 | 3 | 'affects 1% to 3% of adults worldwide' |
| f3 | 6 | 'diagnostic delays averaging 6 years' |
| f4 | 61 | '61 patients with BP and 99 healthy control (HC) individuals' |
| f5 | 99 | '61 patients with BP and 99 healthy control (HC) individuals' |
| f6 | 30 | 'Each interview lasted 30 to 60 minutes' |
| f7 | 60 | 'Each interview lasted 30 to 60 minutes' |
| f8 | 6373 | 'We extracted 6373 acoustic features' |
| f9 | 211 | '211 linguistic features' |
| f10 | 0.916 | 'AUC=0.916, 95% CI 0.854‐0.958' |
| f11 | 0.854 | 'AUC=0.916, 95% CI 0.854‐0.958' |
| f12 | 0.958 | 'AUC=0.916, 95% CI 0.854‐0.958' |
| f13 | 0.933 | 'sensitivity 0.933, specificity 0.859; n=60 vs 99' |
| f14 | 0.859 | 'sensitivity 0.933, specificity 0.859; n=60 vs 99' |
| f15 | 56 | '0.933 (56/60)' |
| f16 | 85 | '0.859 (85/99)' |
| f17 | 0.91 | 'The acoustic-only classification (AUC 0.910)' |
| f18 | 0.651 | 'linguistic-only classification (AUC 0.651)' |
| f19 | 2017 | 'This 7-year (2017‐2024) prospective observational study' |
| f20 | 2024 | 'This 7-year (2017‐2024) prospective observational study' |
| f23 | 60 | 'sensitivity 0.933, specificity 0.859; n=60 vs 99' |
| f22 | 14 | 'f5 - f16' |
| f21 | 159 | 'f23 + f5' |
