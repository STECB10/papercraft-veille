# Étude du jour : prévoir la pneumonie sous respirateur avec l'apprentissage automatique (cohorte)

Peltekian et al., *Critical Care Explorations*, novembre 2026. Cohorte prospective (507 adultes ventilés) avec validation externe. DOI : 10.1097/cce.0000000000001506. Source : texte intégral.

**Raison du choix** : un vrai usage clinique en réanimation, des résultats concrets (validation externe, comparaison au score SOFA) et une limite honnête ; thème nouveau (réanimation, infection) après la méta-analyse sur la sarcopénie. Écartés : essai GPT-4o et étudiants (résumé seul, 12 articles, effets non significatifs), microdiscectomie (texte non libre), revues sans résultat clinique, extraction de dossiers neurochirurgicaux.

**Rôle de l'IA** : des modèles d'apprentissage automatique lisent chaque jour 36 données de réanimation et estiment le risque de pneumonie sous ventilation à 3, 5 ou 7 jours.

## Texte dit

0. (accroche) Peut-on voir venir une pneumonie sous respirateur plusieurs jours avant le diagnostic ?

1. (contexte) En réanimation, un patient sous respirateur peut développer une pneumonie.

2. (contexte) Elle pèse lourd : vingt-huit jours de réanimation en médiane, contre neuf sans pneumonie.

3. (probleme) Le problème, c'est que les premiers signes se noient dans la maladie : on repère la pneumonie trop tard.

4. (probleme) Résultat : les antibiotiques démarrent souvent après la dégradation.

5. (ia) Une équipe a donc entraîné des modèles d'apprentissage automatique sur les données quotidiennes.

6. (question) Ces modèles peuvent-ils prévoir la pneumonie avant le diagnostic ?

7. (etude) Pour le savoir, ils ont suivi cinq cent sept adultes sous respirateur, de juin deux mille dix-huit à juillet deux mille vingt-trois, pour prévoir la pneumonie.

8. (methode) Un lavage bronchique confirmait ou écartait la pneumonie : deux cent soixante et un l'ont eue, deux cent quarante-six non.

9. (methode) Chaque jour, trente-six données entrent dans le modèle, qui estime le risque de pneumonie.

10. (resultat) Résultat : sept jours avant le diagnostic, l'aire sous la courbe atteint zéro virgule huit cent soixante-six, sur une échelle qui s'arrête à un.

11. (resultat) Et à cinq jours, un autre modèle repère quatre-vingt-deux virgule quatre pour cent des cas et écarte soixante et onze virgule quatre pour cent des autres.

12. (resultat) Dans un autre hôpital, sur deux mille six cent quatre-vingt-un patients, l'aire reste à zéro virgule huit cent dix-sept.

13. (concret) En revanche, la variation du score de gravité SOFA ne prévoit presque rien : zéro virgule cinq cent vingt-huit.

14. (concret) Et le meilleur indice, c'est la durée de ventilation, avant la pression du respirateur et l'inflammation.

15. (limite) Attention : dans un essai à neuf données sur trente-six, l'aire tombe à zéro virgule six cent sept.

16. (retenir) À retenir : ces modèles pourraient aider à surveiller les patients à risque, mais il faudra les tester en temps réel.

17. (fin) Une étude par jour, vérifiée à la source.

18. (fin) Papercraft.

## Fiche des faits

| id | valeur | citation |
|---|---|---|
| f1 | 507 | In 507 mechanically ventilated adults |
| f2 | 2018 | from June 2018 to July 2023 |
| f3 | 2023 | from June 2018 to July 2023 |
| f4 | 261 | 261 (51.5%) experienced a BAL-confirmed episode of VAP |
| f5 | 246 | while 246 patients (48.5%) underwent BAL for suspected pneumonia |
| f6 | 36 | We extracted 36 day-level clinical features |
| f7 | 3 | predict VAP within 3, 5, or 7 days before BAL-confirmed diagnosis |
| f8 | 5 | predict VAP within 3, 5, or 7 days before BAL-confirmed diagnosis |
| f9 | 7 | predict VAP within 3, 5, or 7 days before BAL-confirmed diagnosis |
| f10 | 0.866 | LSTM (binned) | 0.866 (0.820–0.909 ) |
| f11 | 0.82 | LSTM (binned) | 0.866 (0.820–0.909 ) |
| f12 | 0.909 | LSTM (binned) | 0.866 (0.820–0.909 ) |
| f13 | 82.4 | the 5-day raw-feature random forest achieved 82.4% sensitivity, 71.4% specificity |
| f14 | 71.4 | the 5-day raw-feature random forest achieved 82.4% sensitivity, 71.4% specificity |
| f15 | 2681 | (n = 2681) |
| f16 | 0.817 | On external validation in MIMIC-IV, the best model achieved an AUROC of 0.817 for predicting VAP within 5 days |
| f17 | 0.528 | (area under the curve [AUC], 0.528 |
| f18 | 0.607 | resulted in a 0.607 (0.579–0.634) AUC for predicting VAP within 3 days |
| f19 | 28 | longer ICU stays (28.0 vs. 9.0 d) |
| f20 | 9 | longer ICU stays (28.0 vs. 9.0 d) |

Type d'étude : cohorte prospective avec développement temporel et validation externe (MIMIC-IV) ; l'intervalle de confiance du résultat principal vient du tableau 2 (bootstrap).

## Relecture

- Chaque « problème » dit-il pourquoi c'en est un ? Oui : les premiers signes se noient dans la gravité de la maladie (cause), donc la pneumonie est repérée tard et les antibiotiques démarrent après la dégradation (conséquence).
- Quels résultats concrets, de terrain ? Le score de gravité SOFA seul ne prévoit presque rien (0,528) ; le meilleur indice est la durée de ventilation, avant la pression du respirateur et l'inflammation ; la performance tient dans un autre hôpital (0,817) mais tombe à 0,607 dans un essai à 9 données sur 36.
- Le fil : chaque partie une seule fois, dans l'ordre (contexte, problème, IA, question, étude, méthode, résultats, concret, limite, à retenir) ; la phrase à retenir dit ce que ça change (surveiller les patients à risque après test en temps réel) sans redire un résultat.
- Les connecteurs disent-ils vrai ? « Résultat » introduit une conséquence ou un résultat, « En revanche » l'opposition du score SOFA, « Attention » la limite.
- Un auditeur non spécialiste comprend-il chaque chiffre ? L'aire sous la courbe est située sur une échelle qui s'arrête à 1 ; sensibilité et spécificité sont dites en pour cent des cas repérés et des autres écartés ; les effectifs sont des personnes (507, 261, 246, 2 681).
- L'image suit-elle la voix ? Oui : la question s'écrit pendant qu'elle est dite ; respirateur, pneumonie et séjour de 28 jours apparaissent sur leurs phrases ; signes discrets, retard, antibiotiques ; la fiche se remplit de haut en bas ; l'entonnoir 507, 261, 246 suit le lavage ; ce qui entre, le modèle, le risque ; puis un chiffre par phrase.
