from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import exiger_roles
from app.models import Credit, Echeance, Rappel, Utilisateur
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


class RappelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    credit_id: int
    type_rappel: str
    canal: str
    jour: date
    message: str
    lu_le: datetime | None


@router.get("/rappels", response_model=list[RappelOut])
def mes_rappels(non_lus: bool = False, limite: int = Query(default=50, ge=1, le=200),
                session: Session = Depends(get_session),
                utilisateur: Utilisateur = Depends(client_connecte)):
    """Les rappels du client connecté, les plus récents d'abord."""
    requete = select(Rappel).where(Rappel.client_id == utilisateur.client_id)
    if non_lus:
        requete = requete.where(Rappel.lu_le.is_(None))
    return session.scalars(requete.order_by(Rappel.jour.desc(), Rappel.id.desc())
                           .limit(limite)).all()


@router.get("/rappels/non-lus")
def nombre_rappels_non_lus(session: Session = Depends(get_session),
                           utilisateur: Utilisateur = Depends(client_connecte)):
    """Pour afficher une pastille « n rappels » dans l'interface."""
    nombre = session.scalar(select(func.count()).select_from(Rappel).where(
        Rappel.client_id == utilisateur.client_id, Rappel.lu_le.is_(None)))
    return {"non_lus": nombre}


@router.post("/rappels/{rappel_id}/lu", response_model=RappelOut)
def marquer_rappel_lu(rappel_id: int, session: Session = Depends(get_session),
                      utilisateur: Utilisateur = Depends(client_connecte)):
    # 404 (et non 403) si le rappel appartient à un autre client
    rappel = session.scalars(select(Rappel).where(
        Rappel.id == rappel_id, Rappel.client_id == utilisateur.client_id)).first()
    if rappel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rappel introuvable")
    if rappel.lu_le is None:
        rappel.lu_le = func.now()
        session.commit()
        session.refresh(rappel)
    return rappel
