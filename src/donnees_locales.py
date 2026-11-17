"""Jeu de données local : un crédit décaissé = une ligne, avec sa cible observée.

C'est la matière première de la recalibration, du réentraînement et du suivi de performance.

Variables : le profil du client tel que le modèle l'a reçu au moment du score (ml.score.variables_entree,
via decision.score_id), et les trois ratios RECALCULÉS sur le montant, la durée et le taux réellement
accordés (un accord réduit change le risque).

Cible : défaut = retard de plus de 90 jours (même seuil que app/historique.py) pendant la fenêtre
d'observation. Fenêtre : min(durée, 12 mois) après le décaissement, plus 90 jours pour que le défaut
puisse se constater. Seuls les crédits « mûrs » (fenêtre terminée) ont une cible : un crédit récent
n'a pas encore eu le temps de faire défaut, l'inclure ferait croire à un risque trop faible.

    python -m src.donnees_locales            # résumé par cohorte
"""
from datetime import date

import pandas as pd
from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.historique import SEUIL_JOURS_DEFAUT, pire_retard_jours
from app.models import Client, Credit, Decision, Echeance, Paiement, Score
from src.modeling import COLONNES
from src.suggestion import construire_ligne

HORIZON_MOIS = 12           # fenêtre de performance maximale
PROFIL = [c for c in COLONNES
          if c not in ("credit_sur_revenu", "annuite_sur_revenu", "duree_implicite")]


def fin_observation(date_decaissement: date, duree_mois: int) -> date:
    """Date à partir de laquelle la cible d'un crédit est définitive."""
    return (date_decaissement + relativedelta(months=min(duree_mois, HORIZON_MOIS))
            + relativedelta(days=SEUIL_JOURS_DEFAUT))


def construire(session: Session, jour: date, murs_seulement: bool = True) -> pd.DataFrame:
    """Une ligne par crédit décaissé avant `jour`. Colonnes : COLONNES du modèle, `defaut`
    (0/1, vide si le crédit n'est pas mûr), `mur`, et des colonnes d'audit (sexe, agence, cohorte)."""
    requete = (
        select(Credit, Client, Score)
        .join(Client, Client.id == Credit.client_id)
        .join(Decision, Decision.demande_id == Credit.demande_id)
        .join(Score, Score.id == Decision.score_id)
        .where(Credit.date_decaissement <= jour,
               Decision.decision.in_(["accorder", "accorder_modifie"]))
        .order_by(Credit.date_decaissement))
    # Une demande peut avoir plusieurs décisions (ajournée puis accordée) : on garde la dernière
    lignes = {credit.id: (credit, client, score) for credit, client, score in session.execute(requete)}

    echeances, paiements = {}, {}
    for e in session.scalars(select(Echeance).where(Echeance.credit_id.in_(lignes))):
        echeances.setdefault(e.credit_id, []).append(e)
    for p in session.scalars(select(Paiement).where(Paiement.credit_id.in_(lignes))):
        paiements.setdefault(p.credit_id, []).append((p.date_paiement, p.montant))

    enregistrements = []
    for credit, client, score in lignes.values():
        fin = fin_observation(credit.date_decaissement, credit.duree_mois)
        mur = fin <= jour
        if murs_seulement and not mur:
            continue
        borne = min(fin, jour)
        payes = [(d, m) for d, m in paiements.get(credit.id, []) if d <= borne]
        dues = [e for e in echeances.get(credit.id, [])
                if e.date_echeance <= credit.date_decaissement + relativedelta(months=HORIZON_MOIS)]
        retard = pire_retard_jours(dues, payes, borne)

        profil = {c: score.variables_entree.get(c) for c in PROFIL}
        ligne = construire_ligne(profil, credit.montant_accorde, credit.duree_mois,
                                 client.revenu_mensuel, COLONNES, float(credit.taux_annuel))
        enreg = ligne.iloc[0].to_dict()
        enreg.update({
            "credit_id": credit.id, "demande_id": credit.demande_id, "client_id": client.id,
            "date_decaissement": credit.date_decaissement,
            "cohorte": credit.date_decaissement.strftime("%Y-%m"),
            "sexe": client.sexe, "agence_id": client.agence_id,
            "version_score": score.version_modele, "p_score": float(score.p_defaut),
            "duree_mois": credit.duree_mois, "fin_observation": fin,
            "pire_retard_jours": retard, "mur": mur,
            "defaut": int(retard > SEUIL_JOURS_DEFAUT) if mur else None,
        })
        enregistrements.append(enreg)
    return pd.DataFrame(enregistrements)


if __name__ == "__main__":
    from app.db import SessionLocal

    with SessionLocal() as s:
        df = construire(s, date.today(), murs_seulement=False)
    print(f"{len(df)} crédits décaissés, dont {int(df['mur'].sum())} mûrs")
    murs = df[df["mur"]]
    if len(murs):
        print(f"Taux de défaut observé (crédits mûrs) : {murs['defaut'].mean():.3f}")
        print(murs.groupby("cohorte")["defaut"].agg(["size", "mean"]).round(3).to_string())
