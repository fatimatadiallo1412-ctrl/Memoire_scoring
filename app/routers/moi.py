from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import exiger_roles
from app.models import Credit, Echeance, Utilisateur
from app.models.enums import Role
from app.routers.credits import _situation
from app.schemas import (CreditOut, EcheanceOut, ProchaineEcheanceOut,
                         SituationOut)

router = APIRouter(prefix="/moi", tags=["espace client"])


def client_connecte(utilisateur: Utilisateur = Depends(exiger_roles(Role.CLIENT))) -> Utilisateur:
    if utilisateur.client_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Ce compte n'est rattaché à aucune fiche client")
    return utilisateur


def _credit_du_client(session: Session, credit_id: int, utilisateur: Utilisateur) -> Credit:
    """Le crédit n'est renvoyé que s'il appartient au client connecté.
    Sinon 404 (et non 403) : on ne révèle pas l'existence du crédit d'un autre."""
    credit = session.scalars(select(Credit).where(
        Credit.id == credit_id, Credit.client_id == utilisateur.client_id)).first()
    if credit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Crédit introuvable")
    return credit


@router.get("/credits", response_model=list[CreditOut])
def mes_credits(session: Session = Depends(get_session),
                utilisateur: Utilisateur = Depends(client_connecte)):
    return session.scalars(select(Credit).where(Credit.client_id == utilisateur.client_id)
                           .order_by(Credit.date_decaissement.desc())).all()


@router.get("/credits/{credit_id}/situation", response_model=SituationOut)
def ma_situation(credit_id: int, session: Session = Depends(get_session),
                 utilisateur: Utilisateur = Depends(client_connecte)):
    return _situation(session, _credit_du_client(session, credit_id, utilisateur))


@router.get("/credits/{credit_id}/echeances", response_model=list[EcheanceOut])
def mes_echeances(credit_id: int, session: Session = Depends(get_session),
                  utilisateur: Utilisateur = Depends(client_connecte)):
    credit = _credit_du_client(session, credit_id, utilisateur)
    return session.scalars(select(Echeance).where(Echeance.credit_id == credit.id)
                           .order_by(Echeance.numero)).all()


@router.get("/prochaine-echeance", response_model=ProchaineEcheanceOut | None)
def ma_prochaine_echeance(session: Session = Depends(get_session),
                          utilisateur: Utilisateur = Depends(client_connecte)):
    """L'échéance impayée la plus proche (ou la plus en retard), tous crédits confondus."""
    aujourdhui = date.today()
    candidates = []
    for credit in session.scalars(select(Credit).where(
            Credit.client_id == utilisateur.client_id)).all():
        situation = _situation(session, credit)
        if situation["solde"]:
            continue
        ligne = next(l for l in situation["echeances"] if l["reste_du"] > 0)
        candidates.append((ligne["date_echeance"], credit.id, ligne))
    if not candidates:
        return None

    jour, credit_id, ligne = min(candidates, key=lambda c: c[0])
    ecart = (jour - aujourdhui).days
    return ProchaineEcheanceOut(
        credit_id=credit_id, numero=ligne["numero"], date_echeance=jour,
        reste_du=ligne["reste_du"], en_retard=ecart < 0, jours=abs(ecart))