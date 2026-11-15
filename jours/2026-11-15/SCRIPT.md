# Étude du jour : 15 novembre 2026

**Titre** : Explainable Machine Learning for Predicting Hospital Admission at Emergency Department Triage: Retrospective Cohort Study.
Dave et al., *JMIR Medical Informatics*, novembre 2026. Cohorte rétrospective, 526 145 visites, deux hôpitaux de Montréal. Source : texte intégral.

**Pourquoi ce choix** : seul candidat portant sur un vrai outil d'aide à l'organisation des urgences, très concret pour les soignants français (lits, attente), avec résultats chiffrés et facteurs explicables. Thème nouveau (urgences) après le rein et l'imagerie ; accroche chiffrée (la veille : image) et moment muet (salle d'attente) différents. L'essai tiré au sort sur la tuberculose (rang 2) est en accès fermé : pas de texte intégral.

**Rôle de l'IA** : un algorithme (XGBoost) prédit, avec les données disponibles à la fin du triage, si le patient sera hospitalisé.

## Texte dit

0. (accroche) Et si l'IA savait, dès le triage, qui va être hospitalisé ?
1. (contexte) Aux urgences, une infirmière évalue d'abord la gravité de chaque patient : c'est le triage.
2. (contexte) Ensuite seulement, on sait qui sera hospitalisé.
3. (probleme) Le problème, c'est que les patients admis restent longtemps aux urgences, à attendre un lit.
4. (probleme) Résultat : ces retards s'accompagnent d'une baisse de la qualité des soins pour les patients.
5. (probleme) Or, repérer tôt les admissions permettrait de préparer les lits.
6. (ia) Des chercheurs canadiens ont donc entraîné un algorithme à prédire l'admission, avec les données du triage.
7. (question) Peut-on prédire une hospitalisation dès la fin du triage ?
8. (etude) Pour le savoir, ils ont analysé cinq cent vingt-six mille cent quarante-cinq visites d'adultes, dans deux hôpitaux de Montréal.
9. (etude) Ces visites vont de deux mille quinze à deux mille vingt-deux ; dix-sept virgule quatre pour cent ont mené à une admission.
10. (methode) Concrètement, il reçoit l'âge, les constantes vitales, le motif de consultation et la gravité du triage.
11. (methode) Il apprend sur soixante-dix pour cent des visites, puis il est testé sur vingt pour cent gardés à part.
12. (resultat) Résultat : l'aire sous la courbe atteint zéro virgule quatre-vingt-six, contre zéro virgule quatre-vingt-quatre pour un modèle classique.
13. (resultat) Autrement dit, il repère soixante-sept pour cent des admissions, et écarte à raison quatre-vingt-six pour cent des sorties.
14. (concret) Et ce qui pèse le plus : l'âge, la gravité au triage, le mode d'arrivée et les hospitalisations passées.
15. (concret) Par exemple, un patient arrivé à pied est moins souvent admis qu'un patient arrivé en ambulance.
16. (concret) Enfin, plus le seuil d'alerte monte, plus les alertes sont fiables, mais plus on rate d'admissions.
17. (limite) Attention : étude rétrospective, dans deux hôpitaux universitaires, pas encore testée en direct.
18. (retenir) À retenir : cet outil pourrait aider à anticiper les lits, une fois validé ailleurs.
19. (fin) Une étude par jour, vérifiée à la source.
20. (fin) Papercraft.

## Fiche des faits

| id | valeur | preuve |
|---|---|---|
| f1 | 526145 | The final cohort included 526 145 visits |
| f2 | 91363 | with 91 363 patients (17.4%) admitted |
| f3 | 17.4 | with 91 363 patients (17.4%) admitted |
| f4 | 0.86 | AUC-ROC of 0.86 (95% CI 0.858-0.864) |
| f5 | 0.858 | AUC-ROC of 0.86 (95% CI 0.858-0.864) |
| f6 | 0.864 | AUC-ROC of 0.86 (95% CI 0.858-0.864) |
| f7 | 0.67 | a sensitivity of 0.67, and a specificity of 0.86 |
| f8 | 0.86 | a sensitivity of 0.67, and a specificity of 0.86 |
| f9 | 67 | calcul : f7*100 |
| f10 | 86 | calcul : f8*100 |
| f11 | 0.84 | outperforming the LR baseline (AUC 0.84) |
| f12 | 2015 | between January 2015 and December 2022 |
| f13 | 2022 | between January 2015 and December 2022 |
| f14 | 2 | at 2 academic hospitals |
| f15 | 70 | training (70%), validation (10%), and testing (20%) |
| f16 | 20 | training (70%), validation (10%), and testing (20%) |
| f17 | 95 | AUC-ROC of 0.86 (95% CI 0.858-0.864) |

## Relecture

- Problème expliqué ? Oui : les admis attendent un lit aux urgences (cause), les soins se dégradent (conséquence), et prévoir tôt les admissions permettrait de préparer les lits.
- Résultats concrets ? Les prédicteurs (âge, gravité au triage, mode d'arrivée, hospitalisations passées), l'exemple ambulance contre arrivée à pied, et l'effet du seuil d'alerte.
- Fil ? Accroche, contexte, problème, IA, question, étude, méthode, résultats, concret, limite, à retenir, fin : chaque partie une fois, sans retour.
- Connecteurs ? « Le problème », « Résultat », « Autrement dit », « Par exemple », « Enfin », « Attention », « À retenir » disent la relation réelle.
- Chiffres compréhensibles ? Aire sous la courbe située face à un modèle classique ; sensibilité et spécificité en pour cent d'admissions repérées et de sorties écartées ; effectif en visites.
- L'image suit la voix ? Triage puis décision, salle d'attente sur la phrase de l'attente, parcours « anticiper les lits », fiche de l'étude, schéma des données, courbe, jauges, constats et seuil, chacun au mot dit.
