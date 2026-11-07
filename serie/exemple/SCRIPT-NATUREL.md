# Exemple de script « comme un humain qui parle »

Étude : Ran et al., *Emerging Microbes & Infections*, octobre 2026 (prédire la réinfection au Covid à partir de l'immunité).
Mêmes faits que la vidéo du 7 novembre 2026, réécrits selon `serie/REGLES-CONTENU.md` (« Parler comme un humain »).
Accroche `hook_question`, moment muet `gag_calendar`. 300 mots ; le vérificateur répond VALIDÉ.

Repère les débuts de phrase : presque chacune s'accroche à la précédente, et les silences ajoutés (`pause_apres`) ne
tombent qu'aux changements de partie.

| # | Texte dit | pause_apres |
|---|---|---|
| 0 | Votre immunité contre le Covid peut-elle annoncer une réinfection ? |  |
| 1 | Le Covid circule désormais toute l'année, et les réinfections touchent surtout les personnes fragiles. |  |
| 2 | Dans cette étude, onze virgule un pour cent des adultes suivis ont été réinfectés. | 0.4 |
| 3 | Alors, pour cibler la prévention, il faudrait savoir qui est le plus à risque. |  |
| 4 | Or la protection repose sur plusieurs défenses : les anticorps du sang, ceux du nez et les lymphocytes T. |  |
| 5 | Une équipe chinoise a donc confié ces mesures à un algorithme d'apprentissage automatique. | 0.3 |
| 6 | Cet algorithme peut-il prédire qui sera réinfecté ? | 1.4 |
| 7 | Pour le savoir, les chercheurs ont mené une cohorte prospective à Wuxi et à Nantong, en Chine. |  |
| 8 | Concrètement, ils ont suivi mille cent cinquante-six adultes pendant dix mois, en médiane, en notant les réinfections avec symptômes. | 0.4 |
| 9 | Au départ, dix-huit données entrent dans l'algorithme, cliniques ou immunitaires. |  |
| 10 | Mais il n'en garde que deux : les anticorps du nez et un type de lymphocyte T. |  |
| 11 | Et il en tire un risque de réinfection pour chaque personne. |  |
| 12 | Ils l'ont d'abord entraîné sur quatre cents personnes de Wuxi, puis vérifié sur cent soixante-dix autres. |  |
| 13 | Enfin, ils l'ont testé sur cinq cent quatre-vingt-six personnes de Nantong, une autre ville. | 0.4 |
| 14 | Résultat : en vérification interne, l'aire sous la courbe atteint zéro virgule huit cent trente-cinq. |  |
| 15 | Autrement dit, le modèle repère plutôt bien les réinfectés. |  |
| 16 | À Nantong, c'est encore mieux : l'aire sous la courbe monte à zéro virgule neuf cent quatre-vingt-seize. |  |
| 17 | La sensibilité atteint cent pour cent, et la spécificité quatre-vingt-dix-sept virgule un pour cent. | 0.4 |
| 18 | Attention : l'étude montre une bonne prédiction, pas moins de réinfections. |  |
| 19 | Et les deux cohortes viennent de la même province : il faudra confirmer ailleurs. |  |
| 20 | À retenir : plus l'immunité du nez est forte, plus le risque prédit est faible. | 0.3 |
| 21 | Une étude par jour, vérifiée à la source. |  |
| 22 | Papercraft. |  |

Le `film.json` complet (planches et ancres) : `serie/exemple/film-naturel.json`.
