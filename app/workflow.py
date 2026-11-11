from fastapi import HTTPException, status

from app.models.enums import StatutDossier as S
from app.models.enums import TypeDecision as D

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


# Ce que la recommandation du modèle signifie, en termes de décision humaine
EQUIVALENT_MODELE = {
    "accord": D.ACCORDER,
    "accord_reduit": D.ACCORDER_MODIFIE,
    "refus": D.REFUSER,
}


def est_concordante(choix: D, recommandation: str, montant_suggere: int | None = None,
                    montant_accorde: int | None = None) -> bool:
    """La décision du directeur suit-elle la recommandation du modèle ?

    Un accord modifié n'est concordant avec un « accord réduit » que si le montant accordé
    ne dépasse pas le montant suggéré par le modèle : accorder davantage revient à contredire le modèle.
    """
    if choix != EQUIVALENT_MODELE[recommandation]:
        return False
    if choix == D.ACCORDER_MODIFIE and montant_suggere is not None and montant_accorde is not None:
        return montant_accorde <= montant_suggere
    return True
