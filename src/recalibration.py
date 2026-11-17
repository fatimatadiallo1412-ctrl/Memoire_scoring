"""Adaptation du modèle Home Credit aux données de l'institution, en deux niveaux.

1. Recalibration : on garde le classement des clients (les arbres ne bougent pas) et on corrige
   seulement le NIVEAU des probabilités sur les crédits locaux mûrs. La méthode dépend du nombre
   de défauts observés, pour ne pas sur-ajuster un petit échantillon :
     < 30 défauts   décalage   : un seul paramètre, la moyenne prévue rejoint le taux observé
     30 à 199       Platt      : logistique sur le logit du score (pente et constante)
     ≥ 200          isotonique : correspondance croissante libre, par paliers
   Les trois corrections sont croissantes : le classement, les contraintes de monotonie et la
   recherche du montant accordable restent valides.

2. Réentraînement : on AJOUTE des arbres au modèle existant, appris sur les crédits locaux
   (le préprocesseur et les contraintes de monotonie sont conservés). À réserver aux volumes
   suffisants (plusieurs centaines de défauts), toujours suivi d'une recalibration.

Les explications SHAP (app/explication.py) restent calculées sur les arbres : elles expliquent
le score avant recalibration, dont l'ordre est le même.
"""
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import expit, logit
from sklearn.base import BaseEstimator
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from src.modeling import COLONNES

MIN_DEFAUTS_PLATT = 30
MIN_DEFAUTS_ISOTONIQUE = 200
P_MIN = 1e-4


def _logit(p):
    return logit(np.clip(p, P_MIN, 1 - P_MIN))


class Calibrateur(BaseEstimator):
    """Transformation croissante des probabilités brutes du modèle."""

    def __init__(self, methode: str = "auto"):
        self.methode = methode

    def fit(self, p, y):
        p, y = np.asarray(p, dtype=float), np.asarray(y, dtype=int)
        n_defauts = int(y.sum())
        methode = self.methode
        if methode == "auto":
            methode = ("isotonique" if n_defauts >= MIN_DEFAUTS_ISOTONIQUE
                       else "platt" if n_defauts >= MIN_DEFAUTS_PLATT else "decalage")
        z = _logit(p)
        if methode == "platt":
            lr = LogisticRegression(C=1e4).fit(z.reshape(-1, 1), y)
            self.pente_, self.constante_ = float(lr.coef_[0, 0]), float(lr.intercept_[0])
            if self.pente_ <= 0:          # pente non croissante : données trop bruitées
                methode = "decalage"
        if methode == "decalage":
            cible = y.mean()
            res = minimize_scalar(lambda d: (expit(z + d).mean() - cible) ** 2,
                                  bounds=(-5, 5), method="bounded")
            self.pente_, self.constante_ = 1.0, float(res.x)
        if methode == "isotonique":
            self.iso_ = IsotonicRegression(y_min=P_MIN, y_max=1 - P_MIN, out_of_bounds="clip")
            self.iso_.fit(p, y)
        self.methode_ = methode
        self.n_defauts_ = n_defauts
        return self

    def transform(self, p):
        p = np.asarray(p, dtype=float)
        if self.methode_ == "isotonique":
            return self.iso_.predict(p)
        return expit(self.pente_ * _logit(p) + self.constante_)

    def description(self) -> str:
        if self.methode_ == "isotonique":
            return f"isotonique ({self.n_defauts_} défauts)"
        return (f"{self.methode_} ({self.n_defauts_} défauts) : "
                f"logit(p') = {self.pente_:.3f} × logit(p) {self.constante_:+.3f}")


class PipelineRecalibre(Pipeline):
    """Le pipeline d'origine (prep + clf, utilisé tel quel par SHAP) suivi d'un calibrateur."""

    def predict_proba(self, X, **params):
        brut = super().predict_proba(X, **params)[:, 1]
        p = self.calibrateur_.transform(brut)
        return np.column_stack([1 - p, p])

    def predict_proba_brut(self, X):
        return super().predict_proba(X)[:, 1]


def recalibrer(modele, X, y, methode: str = "auto") -> PipelineRecalibre:
    """Nouveau modèle = arbres de `modele` + calibrateur appris sur (X, y) locaux."""
    base = modele.steps          # pour un modèle déjà recalibré : on repart des arbres seuls
    brut = Pipeline(base).predict_proba(X[COLONNES])[:, 1]
    nouveau = PipelineRecalibre(list(base))
    nouveau.calibrateur_ = Calibrateur(methode).fit(brut, y)
    return nouveau


def continuer_entrainement(modele, X, y, n_arbres: int = 100, taux: float = 0.02,
                           poids=None) -> Pipeline:
    """Ajoute `n_arbres` arbres appris sur les données locales au booster existant."""
    prep = modele.named_steps["prep"]
    ancien = modele.named_steps["clf"]
    params = ancien.get_params()
    params.update(n_estimators=n_arbres, learning_rate=taux)
    clf = XGBClassifier(**params)
    clf.fit(prep.transform(X[COLONNES]), y, sample_weight=poids, xgb_model=ancien.get_booster())
    return Pipeline([("prep", prep), ("clf", clf)])
