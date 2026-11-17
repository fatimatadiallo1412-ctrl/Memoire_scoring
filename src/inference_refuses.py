"""Inférence des refusés : corriger le biais de sélection du réentraînement.

Le problème : on n'observe le remboursement que des crédits ACCORDÉS. Un modèle réentraîné sur
ces seuls crédits ne voit jamais les profils que l'institution refuse ; au fil des cycles il
devient trop optimiste sur eux (il n'a jamais appris qu'ils étaient risqués).

La méthode retenue, l'augmentation « floue » (fuzzy augmentation) : chaque dossier refusé est
ajouté DEUX fois au jeu d'apprentissage, une fois comme défaut et une fois comme bon payeur,
avec des poids égaux à la probabilité de défaut estimée et à son complément :

    défaut        poids = POIDS × p'
    bon payeur    poids = POIDS × (1 − p')         avec p' = min(FACTEUR × p, 1)

  p        probabilité du modèle en service pour le montant demandé
  FACTEUR  prudence : les refusés sont supposés plus risqués que le modèle ne l'estime
           (1,5 par défaut ; à confronter aux résultats des accords encadrés, voir README)
  POIDS    poids total d'un refusé par rapport à un crédit observé (0,5 par défaut : une
           cible inférée vaut moins qu'une cible observée)

Les refusés ne servent qu'au réentraînement des arbres. La recalibration reste faite sur les
seuls crédits observés.
"""
from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modeling import COLONNES

FACTEUR_PRUDENCE = 1.5
POIDS_REFUSES = 0.5


def refuses(session: Session, jour: date) -> pd.DataFrame:
    """Dossiers refusés jusqu'à `jour`, avec les variables du score sur lequel le refus s'est fondé."""
    from app.models import Decision, DemandeCredit, Score
    lignes = session.execute(
        select(Decision.demande_id, DemandeCredit.date_demande, Score.variables_entree)
        .join(DemandeCredit, DemandeCredit.id == Decision.demande_id)
        .join(Score, Score.id == Decision.score_id)
        .where(Decision.decision == "refuser", DemandeCredit.date_demande <= jour)).all()
    if not lignes:
        return pd.DataFrame(columns=["demande_id", "date_decaissement", *COLONNES])
    df = pd.DataFrame([{"demande_id": d, "date_decaissement": jd,
                        **{c: v.get(c) for c in COLONNES}} for d, jd, v in lignes])
    return df.drop_duplicates("demande_id", keep="last")


def augmenter(modele, observes: pd.DataFrame, refus: pd.DataFrame,
              facteur: float = FACTEUR_PRUDENCE, poids: float = POIDS_REFUSES):
    """Jeu d'apprentissage augmenté : (X, y, poids). Les crédits observés ont un poids de 1."""
    X_obs = observes[COLONNES]
    y_obs = observes["defaut"].astype(int).to_numpy()
    if refus.empty:
        return X_obs, y_obs, np.ones(len(y_obs))
    p = np.clip(facteur * modele.predict_proba(refus[COLONNES])[:, 1], 0, 1)
    X = pd.concat([X_obs, refus[COLONNES], refus[COLONNES]], ignore_index=True)
    y = np.concatenate([y_obs, np.ones(len(refus), dtype=int), np.zeros(len(refus), dtype=int)])
    w = np.concatenate([np.ones(len(y_obs)), poids * p, poids * (1 - p)])
    return X, y, w
