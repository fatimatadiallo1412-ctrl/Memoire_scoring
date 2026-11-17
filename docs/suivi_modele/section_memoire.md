# Cycle de vie du modèle en production

*Proposition de section pour le mémoire. Les chiffres viennent de `experience_hyperparametres.md` et des rapports produits sur la base simulée.*

## 1. Pourquoi un modèle de scoring se dégrade

Un modèle de scoring résume les relations observées entre le profil d'un emprunteur et son remboursement **à un moment donné et sur une population donnée**. En production, deux phénomènes l'éloignent peu à peu de la réalité :

- **La dérive de la population.** Les clients qui se présentent changent : de nouvelles activités apparaissent, des agences ouvrent dans d'autres zones, l'inflation modifie les montants demandés. Le modèle reçoit alors des profils qu'il a peu ou pas vus.
- **La dérive de la relation.** À profil égal, le risque change avec le contexte économique : mauvaise saison agricole, choc sur les prix, crise sanitaire. Un même score ne correspond plus au même taux de défaut.

Le cas de cette plateforme ajoute une difficulté de départ. Le modèle a été appris sur les données publiques Home Credit et non sur des clients sénégalais. Il constitue donc un **point de départ** qu'il faut adapter aux données de l'institution dès qu'elles existent.

## 2. Optimiser le modèle : ce que montre la validation croisée

Avant de parler de suivi, nous avons vérifié si le modèle pouvait être amélioré sur les données disponibles. Le modèle v4 avait été réglé sur une seule séparation entre apprentissage et validation. Nous avons repris ce réglage par **validation croisée stratifiée à 5 blocs**, sur 16 configurations d'hyperparamètres : profondeur, taille minimale des feuilles, sous-échantillonnage, régularisation.

| Variante | AUC en validation croisée | AUC sur le test |
|---|---|---|
| v4 en production | 0,6441 ± 0,0028 | 0,6423 |
| v4, meilleure configuration | 0,6442 ± 0,0028 | 0,6428 |
| Sans la durée | 0,6359 | 0,6347 |
| Durée sans contrainte de monotonie | 0,6917 | 0,6971 |

Trois enseignements :

1. **Le réglage n'apporte rien de mesurable.** Le gain de la meilleure configuration (+0,0005) est six fois plus petit que l'écart-type de la validation croisée. Le modèle en production est conservé.
2. **La durée doit rester dans le modèle.** La retirer coûte près d'un point d'AUC.
3. **Le gain de la variante sans contrainte n'est pas transposable.** Ses cinq points d'avance viennent d'un motif en dents de scie propre à Home Credit (crédits de 12 mois très favorisés, de 18 mois pénalisés), qui n'a pas de justification économique pour une institution sénégalaise. Nous préférons un modèle légèrement moins performant sur Home Credit, mais dont le comportement reste explicable.

### Ni surapprentissage, ni sous-apprentissage

Nous avons comparé les performances du modèle v4 sur les trois jeux de données. La séparation est stratifiée à 60 / 20 / 20.

| Jeu | Dossiers | AUC | KS | Brier | Défaut prévu | Défaut observé |
|---|---|---|---|---|---|---|
| Apprentissage | 166 938 | 0,6585 | 0,229 | 0,0745 | 8,34 % | 8,35 % |
| Validation | 55 647 | 0,6424 | 0,213 | 0,0749 | 8,38 % | 8,35 % |
| Test | 55 647 | 0,6423 | 0,203 | 0,0749 | 8,33 % | 8,35 % |

**Le modèle ne surapprend pas.**

- L'AUC ne perd que 0,016 entre l'apprentissage et la validation.
- Le test, qui n'a servi à aucun réglage, donne le même résultat que la validation.
- La validation croisée varie peu d'un bloc à l'autre (écart-type 0,0028).
- Le défaut prévu reste égal au défaut observé sur chaque jeu.

Pour situer le modèle, nous avons fait varier sa capacité, c'est-à-dire la profondeur des arbres, toutes choses égales par ailleurs :

| Profondeur | AUC apprentissage | AUC validation | Écart |
|---|---|---|---|
| 2 | 0,6506 | 0,6415 | 0,009 |
| **3 (v4)** | 0,6585 | **0,6424** | 0,016 |
| 5 | 0,6824 | 0,6398 | 0,043 |
| 7 | 0,7158 | 0,6353 | 0,081 |

Au-delà de la profondeur 3, le modèle progresse sur l'apprentissage mais recule en validation : il commence à apprendre le bruit des données. La profondeur retenue est celle qui généralise le mieux.

**Le modèle ne sous-apprend pas non plus.** Un modèle plus riche ne fait pas mieux sur des données nouvelles, et les 16 réglages testés plafonnent tous autour de 0,643. Le niveau d'AUC s'explique par deux choix délibérés :

1. Le modèle se limite aux informations qu'un agent de microfinance peut recueillir, sans bureau de crédit ni historique bancaire.
2. La contrainte de monotonie sur la durée lui retire les cinq points d'AUC de la variante libre, qui ne sont pas transposables.

Le plafond vient donc de l'information disponible, pas de l'algorithme. Les progrès viendront **des données** et non du réglage : les crédits de l'institution, et des variables propres à la microfinance.

## 3. Collecter les données qui amélioreront le modèle

La fiche client comporte maintenant des informations facultatives propres à la microfinance :

- l'épargne mensuelle ;
- l'appartenance à une tontine ou à un groupement ;
- l'usage du mobile money ;
- le caractère saisonnier de l'activité.

La demande de crédit indique la **garantie** proposée : caution solidaire, garant individuel ou épargne bloquée.

À chaque calcul de score, la plateforme enregistre aussi l'**historique de remboursement interne** du client : nombre de crédits antérieurs, nombre de crédits soldés, pire retard et nombre de défauts passés.

Le modèle actuel n'utilise aucune de ces variables, puisque Home Credit ne les contient pas, et elles ne modifient pas le score. Elles sont conservées avec chaque score, telles qu'elles étaient au moment de la décision. C'est la condition pour pouvoir, plus tard, entraîner un modèle sur les données de l'institution sans biais de reconstitution.

## 4. Surveiller sans attendre les remboursements

Le défaut ne se constate qu'après plusieurs mois. Il faut donc des indicateurs **avancés**, calculables dès le dépôt des dossiers. Le rapport de suivi est produit automatiquement le premier de chaque mois, sur les trois derniers mois. Il est consultable par l'administrateur sur la page « Santé du modèle ».

| Indicateur | Ce qu'il détecte | Seuils (à surveiller / action) |
|---|---|---|
| Indice de stabilité (PSI) des scores | La population scorée s'éloigne de la population de référence | 0,10 / 0,25 |
| PSI de chaque variable | Quelle caractéristique a changé (âge, profession, ratios…) | 0,10 / 0,25 |
| Valeurs inconnues du modèle | Catégories absentes de l'entraînement, ignorées silencieusement par l'encodeur | 5 % / 15 % des dossiers |
| Taux de dérogation | Le directeur s'écarte de plus en plus des recommandations | 15 % / 25 % |

**Une précaution méthodologique.** Le PSI d'un petit échantillon est élevé même sans aucune dérive, par le seul effet du hasard. Ce bruit vaut environ (k − 1)(1/n₁ + 1/n₂), pour k classes et deux échantillons de tailles n₁ et n₂. Sur 130 dossiers comparés à une référence de 480, il atteint 0,08, presque le seuil d'alerte. Un premier rapport mensuel sur la base simulée était ainsi en alerte « orange » sans qu'aucune dérive n'existe. L'alerte porte donc sur l'**excès** de PSI au-delà de ce bruit, et le rapport couvre trois mois pour disposer de volumes suffisants.

## 5. Mesurer la performance réelle

Pour les crédits arrivés à maturité, le rapport compare le défaut prévu au défaut observé. Un crédit est mûr quand sa fenêtre d'observation est terminée : sa durée, au plus 12 mois, plus 90 jours. Le rapport donne la **calibration** par classe de risque et l'**AUC**, comparée à celle de la fiche du modèle.

Un crédit encore en cours n'a pas eu le temps de faire défaut. L'inclure ferait croire à tort que le risque est faible. En dessous de 30 défauts observés, le rapport ne juge pas la performance : il le dit au lieu de produire un chiffre trompeur.

## 6. Adapter le modèle : recalibrer, réentraîner, comparer

Quand les données locales le permettent, deux niveaux d'adaptation sont prévus.

**La recalibration** conserve les arbres du modèle et corrige seulement le niveau des probabilités. La méthode dépend du nombre de défauts locaux, pour ne pas sur-ajuster un petit échantillon :

- moins de 30 : un simple décalage ;
- de 30 à 199 : la méthode de Platt ;
- 200 et plus : la régression isotonique.

Ces trois corrections sont croissantes. Elles conservent le classement des clients, les contraintes de monotonie et la logique de recherche du montant accordable.

**Le réentraînement** ajoute au modèle des arbres appris sur les crédits locaux. Il n'est tenté qu'à partir de 200 défauts locaux.

**L'inférence des refusés** corrige un biais structurel du réentraînement. On n'observe le remboursement que des crédits accordés. Un modèle réentraîné sur eux seuls n'apprend jamais que les profils refusés étaient risqués, et devient trop optimiste à leur égard au fil des cycles. Nous utilisons l'augmentation dite « floue » : chaque dossier refusé est ajouté deux fois au jeu d'apprentissage, comme défaut et comme bon payeur. Les deux lignes sont pondérées par la probabilité de défaut estimée, majorée par prudence (facteur 1,5), et par son complément. Une cible inférée valant moins qu'une cible observée, le poids total d'un refusé est réduit de moitié.

**La comparaison champion / challenger** décide si une nouvelle version remplace la version en service. Les challengers sont ajustés sur les crédits décaissés avant une date de coupure, puis évalués sur les crédits décaissés après, comme en production. Un challenger n'est proposé que s'il remplit toutes ces conditions :

- au moins 30 défauts dans la période d'évaluation ;
- un score de Brier meilleur que celui du modèle en service ;
- une AUC qui ne baisse pas de plus de 0,01 ;
- un écart entre hommes et femmes, dans la part des dossiers au-dessus du seuil, qui ne s'accroît pas de plus de 2 points.

La mise en service reste une **décision humaine**. Chaque version a une fiche (données, performances, équité, validation) et chaque score garde la version qui l'a produit.

## 7. Limites

- Les remboursements de la base de démonstration sont simulés et **ne dépendent pas du score**. Les rapports produits valident le fonctionnement des outils, pas la qualité du modèle.
- Le facteur de prudence de l'inférence des refusés (1,5) est une hypothèse. Pour le mesurer, il faudrait accorder, de manière encadrée, quelques petits crédits juste au-dessus du seuil. C'est une décision de politique de crédit qui revient à l'institution.
- Les seuils d'alerte sont des valeurs d'usage courant dans le métier du scoring. Ils doivent être validés par la direction des risques de l'institution.
