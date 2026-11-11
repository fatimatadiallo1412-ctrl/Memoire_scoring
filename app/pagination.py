"""Pagination des listes : nombre total transmis dans l'en-tête X-Total-Count."""
from fastapi import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

EN_TETE_TOTAL = "X-Total-Count"


def paginer(session: Session, requete, reponse: Response, limite: int, decalage: int):
    """Compte les lignes de la requête filtrée, place le total dans l'en-tête et renvoie la page demandée."""
    total = session.scalar(select(func.count()).select_from(requete.order_by(None).subquery()))
    reponse.headers[EN_TETE_TOTAL] = str(total)
    return session.scalars(requete.limit(limite).offset(decalage)).all()
