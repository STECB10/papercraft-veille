# Étude du jour : une IA qui lit l'ECG aux urgences pour repérer l'infarctus (validation externe en Europe)

Champetier et al., *The Lancet Regional Health Europe*, novembre 2026. Étude diagnostique, analyse secondaire de deux cohortes prospectives (APACE, APACE-Light). Source : texte intégral.

**Raison du choix** : une étude prospective sur 12 630 patients, avec une vraie comparaison de l'IA à la troponine et aux urgentistes, un résultat nuancé et utile en pratique (l'IA seule ne suffit pas, combinée elle aide à trier). Thème cœur/urgences, type d'étude différent des dernières vidéos (essai tiré au sort, tuberculose).

**Rôle de l'IA** : AiTiA MI, un algorithme d'apprentissage profond, estime une probabilité d'infarctus à partir du tracé brut du premier ECG aux urgences.

## Texte dit

0. [accroche] Aux urgences, une IA lit un ECG : repère-t-elle un infarctus ?
1. [contexte] Devant une douleur thoracique, il faut vite savoir s'il s'agit d'un infarctus : plus on traite tôt, mieux le patient s'en sort.
2. [contexte] Alors on fait d'abord un ECG, puis on dose la troponine.
3. [probleme] Mais la lecture de l'ECG dépend de l'expérience de chacun.
4. [probleme] Et la troponine met souvent plus d'une heure à revenir du laboratoire central.
5. [probleme] Résultat : la confirmation de l'infarctus arrive en retard.
6. [ia] C'est là qu'entre AiTiA, un algorithme coréen qui lit le tracé brut de l'ECG et donne une probabilité d'infarctus.
7. [question] L'IA fonctionne-t-elle aussi en Europe, face à la troponine ?
8. [etude] Pour le savoir, ils ont repris deux cohortes prospectives européennes.
9. [etude] Douze mille six cent trente patients venus aux urgences avec une douleur thoracique.
10. [methode] Concrètement, le premier ECG de chaque patient passe dans l'IA, et les médecins ne voient pas son score.
11. [methode] Puis ils comparent son score à la troponine et au jugement des urgentistes.
12. [resultat] Résultat : l'aire sous la courbe de l'IA atteint zéro virgule soixante-dix-huit, pour un maximum de un.
13. [resultat] Mais, à quatre-vingt-dix minutes, les urgentistes font mieux, avec zéro virgule quatre-vingt-six, et la troponine encore mieux : zéro virgule quatre-vingt-quatorze.
14. [resultat] Et pour écarter un infarctus, elle en repère quatre-vingt-dix-sept virgule six pour cent, mais ne rassure que quatorze pour cent des patients.
15. [concret] Quant aux vingt-trois infarctus ratés dans la première cohorte, treize sont de type deux.
16. [concret] Enfin, combinée à la troponine, elle trie d'emblée cinquante-sept pour cent des patients, en repérant quatre-vingt-dix-sept virgule cinq pour cent des infarctus.
17. [limite] Attention : ses résultats baissent chez les patients âgés, et rien ne justifie un usage hors de l'hôpital.
18. [retenir] À retenir : l'IA pourrait aider les urgentistes en complément de la troponine, pas la remplacer.
19. [fin] Une étude par jour, vérifiée à la source.
20. [fin] Papercraft.

## Fiche des faits

| id | valeur | preuve |
|---|---|---|
| f16 | 5047 | (5047 in APACE and 7583 in APACE-Light) |
| f17 | 7583 | (5047 in APACE and 7583 in APACE-Light) |
| f2 | 2006 | from 04/2006 to 09/2020 |
| f3 | 2021 | from 01/2019 to 01/2021 |
| f4 | 2 | 57% (13/23) were identified as type 2 MI |
| f5 | 0.78 | the AI-ECG achieved an AUC of 0.78 (95% CI: 0.77–0.80) |
| f6 | 90 | integrated physician judgment at 90 min |
| f7 | 0.86 | had higher diagnostic performance than the AI-ECG, with an AUC of 0.86 |
| f8 | 0.94 | The diagnostic performance of the AI-ECG model was inferior to hs-cTnT: AUC of 0.94 |
| f9 | 97.6 | achieving a sensitivity of 97.6% |
| f10 | 14 | the AI-ECG model ruled out 14% (706/5031) |
| f11 | 23 | all 23 false negatives were NSTEMIs, and 57% (13/23) were identified as type 2 MI |
| f12 | 13 | 57% (13/23) were identified as type 2 MI |
| f13 | 57 | triaged 2877 patients (57%) |
| f14 | 97.5 | with a sensitivity of 97.5% (95% CI: 96.4–98.4%) |
| f15 | 1 | often exceeds 1 h |
| f1 | 12630 | calcul : f16 + f17 |

## Relecture

- Chaque « problème » dit-il pourquoi c'en est un ? Oui : la lecture de l'ECG dépend de l'expérience de chacun, et la troponine du laboratoire central dépasse souvent une heure, d'où une confirmation de l'infarctus retardée alors que traiter tôt améliore l'issue.
- Quels résultats concrets, de terrain, au-delà des performances ? Sur les 23 infarctus ratés dans la première cohorte, 13 sont de type 2 ; combinée à la troponine, l'IA trie d'emblée 57 % des patients en repérant 97,5 % des infarctus.
- Le fil : chaque partie une seule fois, dans l'ordre ? Oui : accroche, contexte, problème, IA, question, étude, méthode, résultats, concret, limite, à retenir ; la phrase à retenir dit le rôle d'appoint de l'IA sans redire un chiffre.
- Les connecteurs disent-ils vrai ? « Résultat » introduit une conséquence ou un résultat, « Mais » oppose l'IA aux urgentistes et à la troponine, « Quant aux » reprend les ratés, « Enfin » clôt les constats.
- Un auditeur non spécialiste comprend-il chaque chiffre ? L'aire sous la courbe est située (maximum de un) et comparée à deux repères ; la sensibilité est dite en pour cent d'infarctus repérés et la part de patients écartés en pour cent ; les ratés sont dits « treize sur vingt-trois » en chiffres.
- L'image suit-elle la voix ? Oui : le tracé d'ECG se verrouille sur « infarctus » ; les étapes (douleur, ECG, troponine) puis ce qui coince (expérience, heure) puis AiTiA (tracé, probabilité) arrivent sur leurs mots ; la fiche, l'IA, la comparaison, les barres, les jauges et les constats suivent chacun leur phrase.
