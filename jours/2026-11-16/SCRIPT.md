# Étude du jour : 16 novembre 2026

**Titre** : Imaging-Based AI for Predicting Pathological Complete Response in Esophageal Cancer After Neoadjuvant Therapy: Systematic Review and Meta-Analysis.
Li et al., *Journal of Medical Internet Research*, novembre 2026. Méta-analyse de 33 études (diagnostic, PRISMA-DTA). Source : texte intégral.

**Pourquoi ce choix** : seul candidat en accès libre avec texte intégral et vrai résultat chiffré, très parlant pour les soignants (oncologie, radiologie : chirurgie ou surveillance). L'essai tiré au sort sur la tuberculose (rang 2) est en accès fermé : résumé seul, la partie « concret » aurait manqué. Thème « imagerie » déjà traité il y a deux jours, mais le sujet (cancer de l'œsophage, validation externe, preuves fragiles) et le type d'étude (méta-analyse) diffèrent de la veille (cohorte, urgences) ; accroche titre de presse (la veille : chiffre), pas de moment muet.

**Rôle de l'IA** : des modèles lisent un scanner ou une IRM après traitement et prédisent si la tumeur a totalement disparu (réponse complète pathologique).

## Texte dit

0. (accroche) Une IA peut-elle voir, sur un scanner, qu'un cancer de l'œsophage a disparu ?
1. (contexte) Ce cancer tue plus de cinq cent mille personnes par an.
2. (contexte) Après le traitement, il ne reste parfois aucune cellule tumorale vivante : c'est la réponse complète.
3. (probleme) Le problème, c'est que le scanner montre souvent des résidus, de la cicatrice et non une tumeur vivante.
4. (probleme) Résultat : on ne sait pas à coup sûr qui répond complètement, ce qui pourrait ouvrir la voie à une surveillance.
5. (ia) Des chercheurs ont donc évalué les IA qui prédisent cette réponse.
6. (question) Ces IA prédisent-elles bien la réponse complète, y compris dans d'autres hôpitaux ?
7. (etude) Pour le savoir, ils ont regroupé trente-trois études, publiées entre deux mille dix-neuf et deux mille vingt-six.
8. (methode) Dans chacune, l'IA lit un scanner ou une IRM, et sa prédiction est comparée à l'analyse du tissu.
9. (methode) D'abord, dans son centre d'origine : vingt-sept jeux de données, mille huit cent quatre-vingt-onze patients.
10. (methode) Ensuite, ailleurs : seize jeux, sept cent soixante-dix-sept patients.
11. (resultat) Résultat : dans le centre d'origine, l'aire sous la courbe atteint zéro virgule quatre-vingt-six, sur un maximum de un.
12. (resultat) Autrement dit, elle repère soixante-dix-sept pour cent des réponses complètes et écarte à raison quatre-vingt-deux pour cent des autres.
13. (resultat) Et ailleurs ? Presque pareil : zéro virgule quatre-vingt-quatre, avec soixante-treize pour cent des réponses repérées.
14. (concret) Mais dans un nouvel hôpital, les réponses repérées iraient de trente-quatre à quatre-vingt-treize pour cent.
15. (concret) Et presque toutes ces études viennent de Chine : trente-deux sur trente-trois.
16. (concret) Surtout, douze études sur trente-trois présentent un risque élevé de biais.
17. (limite) Attention : preuves de très faible certitude, l'IA ne doit pas décider seule d'éviter la chirurgie.
18. (retenir) À retenir : l'IA peut compléter le scanner, mais il faudra des tests en direct, dans d'autres pays.
19. (fin) Une étude par jour, vérifiée à la source.
20. (fin) Papercraft.

## Fiche des faits

| id | valeur | preuve |
|---|---|---|
| f1 | 500 | causing over 500,000 deaths annually |
| f2 | 500000 | calcul : f1*1000 |
| f3 | 33 | A total of 33 eligible studies |
| f4 | 27 | Thirty-three studies contributed 27 internal-validation datasets with 1891 patients and 16 external-validation datasets with 777 patients |
| f5 | 1891 | Thirty-three studies contributed 27 internal-validation datasets with 1891 patients and 16 external-validation datasets with 777 patients |
| f6 | 16 | Thirty-three studies contributed 27 internal-validation datasets with 1891 patients and 16 external-validation datasets with 777 patients |
| f7 | 777 | Thirty-three studies contributed 27 internal-validation datasets with 1891 patients and 16 external-validation datasets with 777 patients |
| f8 | 2019 | studies were published between 2019 and 2026 |
| f9 | 2026 | studies were published between 2019 and 2026 |
| f10 | 0.86 | area under the curve (AUC), 0.86 (95% CI 0.83-0.89) |
| f11 | 0.83 | area under the curve (AUC), 0.86 (95% CI 0.83-0.89) |
| f12 | 0.89 | area under the curve (AUC), 0.86 (95% CI 0.83-0.89) |
| f13 | 95 | area under the curve (AUC), 0.86 (95% CI 0.83-0.89) |
| f14 | 0.77 | Internal sensitivity was 0.77 |
| f15 | 0.82 | specificity 0.82 |
| f16 | 77 | calcul : f14*100 |
| f17 | 82 | calcul : f15*100 |
| f18 | 0.84 | AUC 0.84 (95% CI 0.79-0.89) |
| f19 | 0.73 | External sensitivity was 0.73 |
| f20 | 73 | calcul : f19*100 |
| f21 | 0.34 | PI 0.34-0.93 |
| f22 | 0.93 | PI 0.34-0.93 |
| f23 | 34 | calcul : f21*100 |
| f24 | 93 | calcul : f22*100 |
| f25 | 32 | Nearly all studies were conducted in China (32/33) |
| f26 | 12 | 12 had high validation risk of bias |

## Relecture

- Chaque « problème » dit-il pourquoi c'en est un ? Oui : le scanner montre des résidus (cicatrice, pas tumeur vivante), donc on ne sait pas à coup sûr qui répond complètement, alors que cela pourrait ouvrir la voie à une surveillance.
- Quels résultats concrets, de terrain, au-delà des performances ? Dans un nouvel hôpital, les réponses repérées iraient de 34 à 93 % (intervalle de prédiction) ; presque tout vient de Chine (32 sur 33) ; 12 études sur 33 ont un risque élevé de biais.
- Le fil : chaque partie une seule fois, dans l'ordre ? Oui : contexte, problème, IA, question, étude, méthode, résultats, concret, limite, à retenir ; la phrase à retenir dit ce qui manque (tests en direct), sans redire un résultat.
- Les connecteurs disent-ils vrai ? « Le problème » annonce un problème, « Résultat » une conséquence ou un résultat, « Autrement dit » reformule l'aire sous la courbe en sensibilité et spécificité, « Mais » oppose les moyennes aux écarts.
- Un auditeur non spécialiste comprend-il chaque chiffre ? L'aire sous la courbe est située (« sur un maximum de un ») ; sensibilité et spécificité sont dites en pour cent des réponses repérées et des autres cas écartés.
- L'image suit-elle la voix ? Oui : le titre s'affiche sur l'accroche ; les étapes (500 000 morts, traitement, réponse complète) puis (résidus, réponse jamais sûre, IA) suivent s1 à s5 ; la fiche se remplit sur la phrase de l'étude ; scanner, IA puis prédiction ; deux tests (origine, ailleurs) ; courbe, jauges 77 % et 82 %, 0,84 ; trois limites, une par phrase.
