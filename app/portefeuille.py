"""Portefeuilles : qui a le droit de voir quel client.

Un gestionnaire (agent de crédit) ne voit que les clients qui lui sont rattachés,
ainsi que leurs dossiers et leurs crédits. Le directeur et l'administrateur voient tout.
"""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Client, Credit, DemandeCredit, Utilisateur
from app.models.enums import Role

VOIT_TOUT = (Role.DECIDEUR,)


def voit_tout(utilisateur: Utilisateur) -> bool:
    return utilisateur.role in VOIT_TOUT


def client_accessible(session: Session, client_id: int, utilisateur: Utilisateur) -> bool:
    client = session.get(Client, client_id)
    if client is None:
        return False
    return voit_tout(utilisateur) or client.gestionnaire_id == utilisateur.id


def credit_accessible(session: Session, credit_id: int, utilisateur: Utilisateur) -> bool:
    credit = session.get(Credit, credit_id)
    return credit is not None and client_accessible(session, credit.client_id, utilisateur)


def exiger_client(session: Session, client_id: int, utilisateur: Utilisateur) -> Client:
    """Renvoie le client s'il est dans le portefeuille ; sinon 404 (on ne révèle rien)."""
    if not client_accessible(session, client_id, utilisateur):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client introuvable")
    return session.get(Client, client_id)


def filtrer_clients(requete, utilisateur: Utilisateur):
    if voit_tout(utilisateur):
        return requete
    return requete.where(Client.gestionnaire_id == utilisateur.id)


def filtrer_demandes(requete, utilisateur: Utilisateur):
    if voit_tout(utilisateur):
        return requete
    return requete.where(DemandeCredit.client_id.in_(
        select(Client.id).where(Client.gestionnaire_id == utilisateur.id)))
