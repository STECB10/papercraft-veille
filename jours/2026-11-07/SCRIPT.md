# An interpretable machine learning model integrating mucosal and cellular immunity to predict SARS-CoV-2 reinfection: a multicenter cohort study

Ran et al., Emerging Microbes & Infections, octobre 2026 · https://doi.org/10.1080/22221751.2026.2746253

**Type d'étude** : cohorte prospective avec modèle prédictif validé en interne et en externe (texte intégral lu).

**Raison du choix** : un modèle d'apprentissage automatique central dans l'étude, avec des résultats chiffrés complets (AUC, sensibilité, spécificité) et une validation externe. Les cinq autres candidats étaient soit des revues sans chiffres propres, soit un résumé seul sans résultats chiffrés exploitables (enquête sur la confiance envers l'IA), soit une revue dentaire d'accès restreint.

**Rôle de l'IA** : un modèle XGBoost combine des mesures cliniques et immunitaires (surtout les IgA nasales et les lymphocytes T CD4 mémoire centraux) pour prédire une réinfection symptomatique.

## Texte dit
Votre immunité contre le Covid peut-elle annoncer une réinfection ?
Le Covid est devenu endémique, et les réinfections touchent surtout les personnes fragiles.
Dans cette étude, onze virgule un pour cent des adultes suivis ont été réinfectés.
Pour cibler la prévention, il faudrait savoir qui est le plus à risque.
Or la protection repose sur plusieurs défenses : les anticorps du sang, ceux du nez et les lymphocytes T.
Une équipe chinoise a donc confié ces mesures à un algorithme d'apprentissage automatique.
Cet algorithme peut-il prédire qui sera réinfecté ?
Il s'agit d'une cohorte prospective, menée à Wuxi et Nantong, en Chine.
Mille cent cinquante-six adultes ont été suivis dix mois, en médiane, pour repérer les réinfections avec symptômes.
Dix-huit données entrent dans l'algorithme, les unes cliniques, les autres immunitaires.
Il en retient deux : les anticorps du nez et un lymphocyte T.
Il en tire un risque de réinfection pour chaque personne.
Ils l'ont d'abord entraîné sur quatre cents personnes de Wuxi, puis vérifié sur cent soixante-dix autres.
Enfin, ils l'ont éprouvé sur cinq cent quatre-vingt-six personnes de Nantong, une autre ville.
En vérification interne, l'aire sous la courbe atteint zéro virgule huit cent trente-cinq.
Autrement dit, le modèle distingue assez bien les réinfectés des autres.
À Nantong, l'aire sous la courbe monte à zéro virgule neuf cent quatre-vingt-seize.
La sensibilité atteint cent pour cent, la spécificité quatre-vingt-dix-sept virgule un pour cent.
Cette étude montre une bonne prédiction, pas une réduction des réinfections.
Mais les deux cohortes viennent de la même province : il faut confirmer ces résultats ailleurs.
Retenez que l'immunité du nez compte : plus elle est forte, moins le risque prédit est élevé.
Une étude par jour, vérifiée à la source.
Papercraft.

## Fiche des faits

| id | valeur | source |
|---|---|---|
| f1 | 570 | Participants from the Wuxi site ( n  = 570) |
| f2 | 586 | Participants from the Nantong site ( n  = 586) |
| f3 | 1156 | calcul : f1 + f2 |
| f4 | 128 | 128 (11.1%) experienced SARS-CoV-2 reinfection |
| f5 | 11.1 | 128 (11.1%) experienced SARS-CoV-2 reinfection |
| f6 | 10 | during a median follow-up of 10 months |
| f7 | 18 | A total of 18 demographic, clinical, and immune variables were considered for model development |
| f8 | 400 | training cohort ( n  = 400) |
| f9 | 170 | internal validation cohort ( n  = 170) |
| f10 | 0.835 | achieving an AUC of 0.835 in the internal validation cohort |
| f11 | 0.996 | XGB achieved the highest AUC of 0.996 among the evaluated models |
| f12 | 1 | a sensitivity of 1.000 |
| f13 | 0.971 | a specificity of 0.971 |
| f14 | 100 | calcul : f12 * 100 |
| f15 | 97.1 | calcul : f13 * 100 |
| f16 | 2024 | Between May 2024 and February 2025 |
| f17 | 2025 | Between May 2024 and February 2025 |

**Limite** : l'AUC externe (0,996) dépasse l'AUC interne (0,835) ; les deux cohortes viennent de la même province, avec le même variant (JN.1) et seulement des cas symptomatiques.
