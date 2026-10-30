# Étude du jour — 30 octobre 2026

**Titre** : Artificial Intelligence for Rupture Risk Stratification of Small Unruptured Intracranial Aneurysms (≤ 7 mm): A Systematic Review and Meta-analysis. (Kamandi et al., Journal of Imaging Informatics in Medicine, 27 octobre 2026, DOI 10.1007/s10278-026-02419-8)

**Type d'étude** : méta-analyse (revue systématique, enregistrée PROSPERO). Source : résumé seul (texte intégral non accessible).

**Raison du choix** : seule méta-analyse du lot avec un résultat chiffré complet (AUC regroupée avec intervalle, sensibilité, spécificité, comparaison des familles de modèles) sur une décision clinique concrète (opérer ou surveiller un petit anévrisme). Les autres candidats étaient des revues narratives sans chiffre regroupé ou hors soin direct.

**Rôle de l'IA** : des modèles d'apprentissage automatique estiment le risque de rupture d'un petit anévrisme à partir de données d'imagerie et cliniques.

## Texte dit

Faut-il opérer un petit anévrisme cérébral, ou simplement le surveiller ?
Ces anévrismes cérébraux de sept millimètres ou moins portent un risque de rupture important.
Pour décider, les médecins s'appuient sur des scores de risque, comme PHASES ou ELAPSS.
Pourtant, pour ces petits anévrismes, ces scores ne font guère mieux que le hasard.
Des chercheurs ont donc testé des modèles d'IA, qui apprennent à prédire la rupture à partir de données de patients.
Ces modèles d'IA prédisent-ils vraiment mieux le risque de rupture ?
Les auteurs ont réalisé une méta-analyse, c'est-à-dire une synthèse chiffrée de plusieurs études.
Ils ont regroupé dix études, publiées entre deux mille dix-neuf et deux mille vingt-cinq.
Elles portent sur cinq mille quatre cent neuf patients, sept mille cinquante-sept anévrismes et soixante-deux modèles.
Les données d'un anévrisme entrent dans le modèle, qui estime son risque de rupture.
Pour comparer ces modèles, ils ont retenu l'aire sous la courbe, qui mesure la qualité de la prédiction.
Résultat : en regroupant les études, l'aire sous la courbe regroupée atteint zéro virgule sept cent quatre-vingt-treize.
L'intervalle de confiance à quatre-vingt-quinze pour cent va de zéro virgule sept cent cinquante-quatre à zéro virgule huit cent vingt-sept.
La sensibilité est de soixante et onze pour cent, et la spécificité de soixante-dix-huit pour cent.
Selon la famille, l'apprentissage automatique classique obtient le meilleur score, avec zéro virgule huit cent vingt-sept.
Les modèles statistiques atteignent zéro virgule sept cent soixante-dix-neuf, et l'apprentissage profond zéro virgule sept cent quarante et un.
En revanche, neuf études sur dix présentent un risque élevé de biais.
Ces résultats restent à confirmer dans des registres prospectifs.
L'IA semble prédire mieux que les scores classiques, mais la preuve reste fragile.
Une étude par jour, vérifiée à la source.
Papercraft.

## Fiche des faits

| id | valeur | source |
|---|---|---|
| f1 | 7 | Small unruptured intracranial aneurysms (UIAs; ≤ 7 mm) |
| f2 | 10 | calcul : 10 |
| f3 | 2019 | Ten studies (2019-2025) |
| f4 | 2025 | Ten studies (2019-2025) |
| f5 | 5409 | 5409 patients |
| f6 | 7057 | 7057 aneurysms |
| f7 | 62 | 62 models |
| f8 | 0.793 | Pooled AUC was 0.793 |
| f9 | 0.754 | 95% CI 0.754-0.827 |
| f10 | 0.827 | 95% CI 0.754-0.827 |
| f11 | 95 | 95% CI 0.754-0.827 |
| f12 | 0.713 | sensitivity of 0.713 |
| f13 | 0.78 | specificity of 0.780 |
| f14 | 71.3 | calcul : f12*100 |
| f15 | 78 | calcul : f13*100 |
| f16 | 0.779 | statistical models (0.779) |
| f17 | 0.741 | DL (0.741) |
| f18 | 9 | calcul : 9 |

Note : « dix études » et « neuf sur dix » sont écrits en lettres dans le résumé (Ten studies, Nine of ten).
