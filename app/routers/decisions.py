from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import exiger_roles
from app.models import Decision, Journal, Utilisateur
from app.models.enums import Role, StatutDossier, TypeDecision
from app.routers.demandes import (LECTURE, charger_demande, exiger_score_valide,
                                  verifier_produit)
from app.schemas import DecisionIn, DecisionOut
from app.workflow import changer_statut

router = APIRouter(prefix="/demandes", tags=["décisions"])

# Ce que la recommandation du modèle signifie, en termes de décision humaine
EQUIVALENT_MODELE = {
    "accord": TypeDecision.ACCORDER,
    "accord_reduit": TypeDecision.ACCORDER_MODIFIE,
    "refus": TypeDecision.REFUSER,
}
STATUT_APRES = {
    TypeDecision.ACCORDER: StatutDossier.ACCORDE,
    TypeDecision.ACCORDER_MODIFIE: StatutDossier.ACCORDE_MODIFIE,
    TypeDecision.REFUSER: StatutDossier.REFUSE,
    TypeDecision.AJOURNER: StatutDossier.AJOURNE,
}


@router.post("/{demande_id}/decider", response_model=DecisionOut,
             status_code=status.HTTP_201_CREATED)
def decider(demande_id: int, donnees: DecisionIn, session: Session = Depends(get_session),
            utilisateur: Utilisateur = Depends(exiger_roles(Role.DECIDEUR))):
    demande = charger_demande(session, demande_id)
    if demande.statut != StatutDossier.SOUMIS:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Seul un dossier soumis à décision peut faire l'objet d'une décision")
    score = exiger_score_valide(session, demande)

    choix = donnees.decision
    montant = duree = None
    if choix == TypeDecision.ACCORDER:
        montant, duree = demande.montant_demande, demande.duree_mois
    elif choix == TypeDecision.ACCORDER_MODIFIE:
        if donnees.montant_accorde is None or donnees.duree_accordee is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                                "Montant et durée accordés obligatoires pour un accord avec modification")
        montant, duree = donnees.montant_accorde, donnees.duree_accordee
        verifier_produit(session, demande.produit_id, montant, duree)

    concordance = choix == EQUIVALENT_MODELE[score.recommandation]
    if not concordance and not (donnees.commentaire and donnees.commentaire.strip()):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Un motif est obligatoire quand la décision diffère de la recommandation du modèle")

    decision = Decision(
        demande_id=demande.id, score_id=score.id, decideur_id=utilisateur.id,
        decision=choix, montant_accorde=montant, duree_accordee=duree,
        commentaire=donnees.commentaire, recommandation_modele=score.recommandation,
        concordance=concordance)
    session.add(decision)
    changer_statut(demande, STATUT_APRES[choix])
    session.add(Journal(utilisateur_id=utilisateur.id, action="decision",
                        entite="demande_credit", entite_id=demande_id,
                        details={"decision": choix.value, "concordance": concordance}))
    session.commit()
    session.refresh(decision)
    return decision


@router.get("/{demande_id}/decisions", response_model=list[DecisionOut])
def historique_decisions(demande_id: int, session: Session = Depends(get_session),
                         utilisateur: Utilisateur = Depends(exiger_roles(*LECTURE))):
    charger_demande(session, demande_id)
    return session.scalars(select(Decision).where(Decision.demande_id == demande_id)
                           .order_by(Decision.decide_le)).all()