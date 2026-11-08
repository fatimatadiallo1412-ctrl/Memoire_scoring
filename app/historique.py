"""Historique interne : détection des incidents de paiement d'un client déjà connu."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Credit, Echeance, Paiement
from app.suivi import situation_credit

# Au-delà de ce nombre de jours de retard, un crédit est considéré comme ayant été en défaut
# (même seuil que l'indicateur est_contentieux du DWH).
SEUIL_JOURS_DEFAUT = 90


def pire_retard_jours(echeances, paiements, jour: date) -> int:
    """Pire retard (en jours) connu sur un crédit, à la date `jour`.

    echeances : objets avec numero, date_echeance, montant_du
    paiements : liste de (date_paiement, montant)

    Imputation dans l'ordre (comme app/suivi.py) : chaque échéance est couverte quand le
    cumul des paiements atteint le cumul des montants dus. Son retard est l'écart entre
    cette date de couverture et son échéance. Si elle n'est pas couverte, on compte
    jusqu'à `jour`.
    """
    paiements = sorted(paiements, key=lambda p: p[0])
    pire = 0
    du_cumule = 0
    for e in sorted(echeances, key=lambda e: e.numero):
        du_cumule += e.montant_du
        paye = 0
        date_couverture = None
        for date_p, montant in paiements:
            paye += montant
            if paye >= du_cumule:
                date_couverture = date_p
                break
        fin = date_couverture if date_couverture is not None else jour
        pire = max(pire, (fin - e.date_echeance).days)
    return pire


def antecedents(session: Session, client_id: int, jour: date) -> dict:
    """Crédits du client ayant dépassé le seuil de retard, en deux groupes :
    en_cours    : encore en retard au-delà du seuil et non soldés
    regularises : défaut passé, soldé ou revenu sous le seuil
    """
    resultat = {"en_cours": [], "regularises": []}
    credits = session.scalars(
        select(Credit).where(Credit.client_id == client_id,
                             Credit.date_decaissement <= jour)).all()

    for credit in credits:
        echeances = session.scalars(
            select(Echeance).where(Echeance.credit_id == credit.id)
            .order_by(Echeance.numero)).all()
        paiements = [(p.date_paiement, p.montant) for p in session.scalars(
            select(Paiement).where(Paiement.credit_id == credit.id,
                                   Paiement.date_paiement <= jour))]
        if pire_retard_jours(echeances, paiements, jour) <= SEUIL_JOURS_DEFAUT:
            continue

        total_paye = sum(m for _, m in paiements)
        situation = situation_credit(echeances, total_paye, jour)
        if not situation["solde"] and situation["jours_retard_max"] > SEUIL_JOURS_DEFAUT:
            resultat["en_cours"].append(credit.id)
        else:
            resultat["regularises"].append(credit.id)
    return resultat


def niveau_antecedent(session: Session, client_id: int, jour: date) -> str:
    """'en_cours', 'regularise' ou 'aucun' (un défaut en cours l'emporte)."""
    a = antecedents(session, client_id, jour)
    if a["en_cours"]:
        return "en_cours"
    if a["regularises"]:
        return "regularise"
    return "aucun"