# Optimisation des hyperparamètres : validation croisée à 5 blocs

Script : `src/experiences.py` · journal complet : `experience_hyperparametres.json` / `.log`

Protocole : 16 configurations (celle de v4, puis 15 tirages aléatoires sur la profondeur, `min_child_weight`, le sous-échantillonnage, `gamma` et la régularisation L1/L2). Chaque configuration est évaluée par validation croisée stratifiée sur 80 % des données, avec arrêt anticipé. Le test (20 %, même graine que `src/modeling.py`) n'est consulté qu'une fois par variante.

| Variante | AUC CV (moyenne ± écart-type) | AUC test |
|---|---|---|
| v4 en production (réglage d'origine) | 0,6441 ± 0,0028 | 0,6423 |
| v4, meilleure configuration trouvée | 0,6442 ± 0,0028 | 0,6428 |
| Sans durée | 0,6359 | 0,6347 |
| Durée sans contrainte (type v3) | 0,6917 | 0,6971 |

## Conclusions

1. **Le réglage des hyperparamètres n'apporte rien.** Les 16 configurations de v4 se tiennent entre 0,642 et 0,644. Le gain du meilleur réglage (+0,0005) est six fois plus petit que l'écart-type de la validation croisée. Le modèle en production est **conservé tel quel**.
2. **La durée doit rester dans le modèle.** La retirer coûte environ 0,008 d'AUC.
3. **Les 5 points d'écart avec la variante libre viennent du motif en dents de scie** propre à Home Credit (12 mois favorisés, 18 mois pénalisés ; voir notebook 03). Il est écarté parce qu'il n'est pas transposable : ce gain n'existe que sur Home Credit.
4. **Les gains futurs viendront des données, pas du réglage.** Il s'agit des crédits locaux (recalibration, puis réentraînement : `src/recalibration.py`) et de variables propres à la microfinance (historique de remboursement interne, épargne, mobile money, saisonnalité de l'activité).
