from fastapi import HTTPException, status

from app.models.enums import StatutDossier as S

TRANSITIONS = {
    S.BROUILLON: {S.COMPLET},
    S.COMPLET: {S.BROUILLON, S.SCORE},
    S.SCORE: {S.COMPLET, S.INSTRUIT},
    S.INSTRUIT: {S.COMPLET, S.SOUMIS},
    S.SOUMIS: {S.ACCORDE, S.ACCORDE_MODIFIE, S.REFUSE, S.AJOURNE},
    S.AJOURNE: {S.SOUMIS},
    S.ACCORDE: {S.DECAISSE},
    S.ACCORDE_MODIFIE: {S.DECAISSE},
    S.REFUSE: set(),
    S.DECAISSE: {S.EN_REMBOURSEMENT},
    S.EN_REMBOURSEMENT: {S.SOLDE, S.CONTENTIEUX},
    S.CONTENTIEUX: {S.EN_REMBOURSEMENT, S.SOLDE},
    S.SOLDE: set(),
}


def changer_statut(demande, cible: S) -> None:
    """Change le statut du dossier si la transition est autorisée, sinon renvoie 409."""
    if cible not in TRANSITIONS[demande.statut]:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Transition interdite : {demande.statut.value} vers {cible.value}")
    demande.statut = cible