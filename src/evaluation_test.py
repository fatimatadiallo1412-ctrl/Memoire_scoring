"""Évaluation finale du modèle en service sur le jeu de TEST Home Credit (ouverture n° 10, 18/11/2026).

Aucun choix de conception ne découle de ce script : il mesure le modèle déjà retenu.
Sortie : docs/suivi_modele/evaluation_test_v4.json

    python -m src.evaluation_test

- Mesures globales (AUC avec IC95 bootstrap et DeLong, Gini, KS, Brier, PR-AUC).
- Matrice de confusion, rappel, précision, spécificité aux seuils 12 % (en service) et 15 %.
  Classe positive = défaut ; « refusé » = probabilité de défaut > seuil.
- Calibration : pente et intercept (Van Calster 2019), calibration dans l'ensemble.
"""
import json

import joblib
import numpy as np
import pandas as pd
from scipy import optimize, stats
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score, roc_curve

from src.modeling import COLONNES, DONNEES, RACINE, separer

SORTIE = RACINE / "docs" / "suivi_modele" / "evaluation_test_v4.json"
B = 1000


def delong_ic(y, p, z=1.96):
    """IC de l'AUC par la méthode de DeLong (variance par composantes structurelles)."""
    y = np.asarray(y)
    pos, neg = p[y == 1], p[y == 0]
    rang = stats.rankdata(np.concatenate([pos, neg]))
    m, n = len(pos), len(neg)
    auc = (rang[:m].sum() - m * (m + 1) / 2) / (m * n)
    v10 = (rang[:m] - stats.rankdata(pos)) / n
    v01 = 1 - (rang[m:] - stats.rankdata(neg)) / m
    se = np.sqrt(np.var(v10, ddof=1) / m + np.var(v01, ddof=1) / n)
    return round(auc - z * se, 4), round(auc + z * se, 4)


def logistique(y, X, offset=0.0):
    """Régression logistique sans pénalité (maximum de vraisemblance) ; renvoie coefficients et covariance."""
    def nll(beta):
        eta = X @ beta + offset
        return np.sum(np.logaddexp(0, eta) - y * eta)

    def grad(beta):
        return X.T @ (1 / (1 + np.exp(-(X @ beta + offset))) - y)

    beta = optimize.minimize(nll, np.zeros(X.shape[1]), jac=grad, method="BFGS").x
    mu = 1 / (1 + np.exp(-(X @ beta + offset)))
    cov = np.linalg.inv(X.T @ (X * (mu * (1 - mu))[:, None]))
    return [float(x) for x in beta], cov


def ic(valeur, variance, z=1.96):
    e = z * np.sqrt(variance)
    return [round(valeur - e, 4), round(valeur + e, 4)]


def main():
    df = pd.read_parquet(DONNEES)
    _, _, test = separer(df)
    y = test["TARGET"].to_numpy()
    p = joblib.load(RACINE / "models" / "xgb_home_credit_v4.joblib").predict_proba(test[COLONNES])[:, 1].astype(float)

    fpr, tpr, _ = roc_curve(y, p)
    auc = roc_auc_score(y, p)
    rng = np.random.default_rng(42)
    boot = []
    for _ in range(B):
        i = rng.integers(0, len(y), len(y))
        boot.append(roc_auc_score(y[i], p[i]))
    res = {"jeu": f"test Home Credit ({len(y)} dossiers, défaut {y.mean():.4f})",
           "modele": "models/xgb_home_credit_v4.joblib",
           "global": {"AUC": round(auc, 4), "AUC_IC95_bootstrap": [round(x, 4) for x in np.percentile(boot, [2.5, 97.5])],
                      "AUC_IC95_DeLong": delong_ic(y, p), "Gini": round(2 * auc - 1, 4),
                      "KS": round(float((tpr - fpr).max()), 4), "Brier": round(brier_score_loss(y, p), 5),
                      "Brier_reference_taux_constant": round(brier_score_loss(y, np.full(len(y), y.mean())), 5),
                      "PR_AUC": round(average_precision_score(y, p), 4), "taux_defaut": round(y.mean(), 4)}}

    for s in (0.12, 0.15):
        refuse = p > s
        vp = int((refuse & (y == 1)).sum())     # défaillant refusé
        fp = int((refuse & (y == 0)).sum())     # bon payeur refusé
        fn = int((~refuse & (y == 1)).sum())    # défaillant accepté
        vn = int((~refuse & (y == 0)).sum())    # bon payeur accepté
        res[f"seuil_{s:.2f}"] = {
            "matrice": {"defaillant_refuse_VP": vp, "bon_payeur_refuse_FP": fp,
                        "defaillant_accepte_FN": fn, "bon_payeur_accepte_VN": vn},
            "rappel_defauts_detectes": round(vp / (vp + fn), 4),
            "precision_refus_justifies": round(vp / (vp + fp), 4),
            "specificite_bons_payeurs_acceptes": round(vn / (vn + fp), 4),
            "taux_acceptation": round((vn + fn) / len(y), 4),
            "defaut_chez_acceptes": round(fn / (vn + fn), 4),
            "defaut_chez_refuses": round(vp / (vp + fp), 4)}

    # Calibration (Van Calster et al., 2019) : logit(P(y=1)) = a + b * logit(p)
    lp = np.log(p / (1 - p))
    (a, b), cov = logistique(y, np.column_stack([np.ones_like(lp), lp]))
    (a0,), cov0 = logistique(y, np.ones((len(y), 1)), offset=lp)
    res["calibration"] = {
        "pente": round(b, 4), "pente_IC95": ic(b, cov[1, 1]),
        "intercept_calibration_dans_l_ensemble": round(a0, 4), "intercept_IC95": ic(a0, cov0[0, 0]),
        "prevu_moyen": round(float(p.mean()), 4), "observe": round(float(y.mean()), 4),
        "lecture": "pente 1 et intercept 0 = calibration parfaite ; pente < 1 = scores trop dispersés"}

    SORTIE.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
