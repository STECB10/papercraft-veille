# Étude du jour : une IA qui lit la pression artérielle au doigt pour dépister la sténose aortique

Kassab et al., *JACC Advances*, novembre 2026. Cohorte prospective internationale, étude de performance diagnostique (décembre 2020 à juillet 2025). DOI : 10.1016/j.jacadv.2026.103475. Source : résumé seul (texte intégral non libre).

**Raison du choix** : un vrai résultat chiffré sur un dépistage cardiaque simple, utile aux soignants ; thème nouveau (cœur) après la rétine, et une étude prospective multicentrique avec échographie comme référence. Le résumé donne sensibilité, spécificité et valeurs prédictives avec leurs effectifs, donc un point de vigilance concret (les fausses alertes). Les autres candidats : essai de faisabilité sur 11 parents, étude rétrospective sur la rééducation ou prédiction de démoralisation sur dialyse, moins parlants ou moins solides.

**Rôle de l'IA** : un réseau de neurones lit la courbe de pression artérielle prise au doigt, sans geste invasif, et dit si une sténose aortique au moins modérée est probable.

## Texte dit

0. (accroche) Un brassard au doigt pourrait-il révéler un rétrécissement de la valve aortique ?

1. (contexte) La sténose aortique est un rétrécissement de cette valve, qui pèse lourd en santé publique.

2. (contexte) Pour la confirmer, on passe aujourd'hui par une échographie du cœur, qui sert de référence.

3. (probleme) Le problème, c'est que sans repérage précoce, la prise en charge arrive plus tard.

4. (probleme) Alors il faudrait un test de dépistage simple, pour savoir à qui proposer l'échographie.

5. (ia) C'est là qu'intervient l'IA : un réseau de neurones lit la pression artérielle prise au doigt, sans geste invasif.

6. (question) Cette IA sait-elle repérer une sténose aortique significative ?

7. (etude) Pour le savoir, une cohorte prospective internationale, de décembre deux mille vingt à juillet deux mille vingt-cinq.

8. (methode) Concrètement, chaque participant passe une échographie, avec en même temps sa pression artérielle au doigt.

9. (methode) Ensuite, chaque courbe passe dans l'IA, qui dit si la valve est rétrécie.

10. (methode) Elle s'entraîne d'abord sur trois mille six cent trente-quatre patients de la Cleveland Clinic.

11. (methode) Puis elle est testée sur mille trois cent trente-six autres, vus plus tard aux États-Unis, en Espagne et aux Pays-Bas.

12. (resultat) Résultat : l'IA repère quatre-vingt-douze virgule cinq pour cent des vraies sténoses.

13. (resultat) Autrement dit, sur deux cent quarante et un patients atteints, elle en repère deux cent vingt-trois et en rate dix-huit.

14. (concret) Mais côté patients sains, elle n'en écarte à raison que sept cent six sur mille quatre-vingt-quinze.

15. (concret) Autrement dit, sur six cent douze patients signalés, deux cent vingt-trois seulement sont vraiment atteints.

16. (concret) En revanche, quand elle ne signale rien, elle a raison dans sept cent six cas sur sept cent vingt-quatre.

17. (limite) Attention : c'est un test de dépistage, pas un diagnostic : l'échographie reste nécessaire.

18. (retenir) À retenir : ce test pourrait aider à choisir qui envoyer vers l'échographie, sans la remplacer.

19. (fin) Une étude par jour, vérifiée à la source.

20. (fin) Papercraft.

## Fiche des faits

| id | valeur | preuve |
|---|---|---|
| f1 | 2020 | from December 2020 through July 2025 |
| f2 | 2025 | from December 2020 through July 2025 |
| f3 | 3634 | 307 of 3,634 (8.4%) patients in the development cohort |
| f4 | 1336 | 241 of 1,336 (18.0%) in the validation cohort |
| f5 | 241 | 241 of 1,336 (18.0%) in the validation cohort |
| f6 | 223 | sensitivity of 92.5% (223/241; 95% CI: 88.5%-95.2%) |
| f7 | 92.5 | sensitivity of 92.5% (223/241; 95% CI: 88.5%-95.2%) |
| f8 | 18 | calcul : f5 - f6 |
| f9 | 706 | specificity of 64.5% (706/1,095; 95% CI: 61.6%-67.3%) |
| f10 | 1095 | specificity of 64.5% (706/1,095; 95% CI: 61.6%-67.3%) |
| f11 | 612 | positive predictive value of 36.4% (223/612; 95% CI: 32.7%-40.3%) |
| f12 | 724 | negative predictive value of 97.5% (706/724; 95% CI: 96.1%-98.4%) |

## Relecture

- Chaque « problème » dit-il pourquoi c'en est un ? Oui, dans la limite du résumé : sans repérage précoce, la prise en charge arrive plus tard ; d'où le besoin d'un dépistage simple avant l'échographie.
- Quels résultats concrets, de terrain ? Spécificité (706 sur 1 095), fausses alertes (223 vrais malades sur 612 signalés), valeur rassurante quand l'IA ne signale rien (706 sur 724).
- Le fil : chaque partie une fois, dans l'ordre ? Oui ; la limite (dépistage, pas diagnostic) précède la phrase à retenir, qui dit ce que le test pourrait changer (choisir qui passe l'échographie).
- Les connecteurs disent-ils vrai ? « Le problème » annonce un problème, « Résultat » un résultat, « Autrement dit » reformule, « Mais » et « En revanche » opposent.
- Un auditeur non spécialiste comprend-il chaque chiffre ? Oui : tout est en « x sur y » ou en pour cent, sans AUC.
- L'image suit-elle la voix ? Oui : titre de l'étude, puis valve et échographie, retard de prise en charge, dépistage simple et pression au doigt ; fiche, IA (courbe, IA, sténose), entraînement puis test, résultat en grand, trois constats un par phrase.
