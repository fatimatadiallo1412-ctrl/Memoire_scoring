# Champion / challenger — champion : xgb_home_credit_v4

Coupure hors période : 2025-09-18 · apprentissage 190 crédits (18 défauts) · évaluation 82 crédits · seuil 0.12

| Modèle | Défauts | Prévu | Observé | AUC | KS | Brier | Écart H/F > seuil |
|---|---|---|---|---|---|---|---|
| champion | 2 | 0.070 | 0.024 | 0.388 | 0.412 | 0.0271 | 0.086 |
| recalibre | 2 | 0.082 | 0.024 | 0.388 | 0.412 | 0.0286 | 0.013 |
| reentraine | 2 | 0.082 | 0.024 | 0.388 | 0.412 | 0.0286 | 0.013 |

## Challengers
- **recalibre** : decalage (18 défauts) : logit(p') = 1.000 × logit(p) +0.164
- **reentraine** : 100 arbres ajoutés ; decalage (18 défauts) : logit(p') = 1.000 × logit(p) -0.002
- recalibre non promouvable : 2 défauts dans la période d'évaluation : au moins 30 sont nécessaires pour conclure
- reentraine non promouvable : 2 défauts dans la période d'évaluation : au moins 30 sont nécessaires pour conclure

**Proposition : garder le champion**
