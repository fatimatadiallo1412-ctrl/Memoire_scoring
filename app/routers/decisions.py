from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import exiger_roles
from app.historique import niveau_antecedent
from app.models import Client, Decision, Journal, ProduitCredit, Utilisateur
from app.models.enums import Role, StatutDossier, TypeDecision
from app.routers.demandes import (LECTURE, charger_demande, exiger_score_valide,
                                  verifier_produit)
from app.parametres import lire_parametres
from app.schemas import DecisionIn, DecisionOut
from app.scoring import evaluer_montant
from app.workflow import changer_statut, est_concordante

router = APIRouter(prefix="/demandes", tags=["décisions"])

STATUT_APRES = {
    TypeDecision.ACCORDER: StatutDossier.ACCORDE,
    TypeDecision.ACCORDER_MODIFIE: StatutDossier.ACCORDE_MODIFIE,
    TypeDecision.REFUSER: StatutDossier.REFUSE,
    TypeDecision.AJOURNER: StatutDossier.AJOURNE,
}


def _simuler(session: Session, demande, montant: int, duree: int) -> dict:
    client = session.get(Client, demande.client_id)
    produit = session.get(ProduitCredit, demande.produit_id)
    return evaluer_montant(client, demande, produit, lire_parametres(session), montant, duree,
                           antecedent=niveau_antecedent(session, client.id, demande.date_demande))


@router.get("/{demande_id}/simuler")
def simuler(demande_id: int, montant: int = Query(gt=0), duree: int = Query(gt=0, le=120),
            session: Session = Depends(get_session),
            utilisateur: Utilisateur = Depends(exiger_roles(Role.DECIDEUR))):
    """Risque et endettement d'un montant et d'une durée envisagés pour un accord modifié (lecture seule)."""
    demande = charger_demande(session, demande_id, utilisateur)
    verifier_produit(session, demande.produit_id, montant, duree)
    return _simuler(session, demande, montant, duree)


@router.post("/{demande_id}/decider", response_model=DecisionOut,
             status_code=status.HTTP_201_CREATED)
def decider(demande_id: int, donnees: DecisionIn, session: Session = Depends(get_session),
            utilisateur: Utilisateur = Depends(exiger_roles(Role.DECIDEUR))):
    demande = charger_demande(session, demande_id, utilisateur)
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
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT,
                                "Montant et durée accordés obligatoires pour un accord avec modification")
        montant, duree = donnees.montant_accorde, donnees.duree_accordee
        verifier_produit(session, demande.produit_id, montant, duree)

    a_un_motif = bool(donnees.commentaire and donnees.commentaire.strip())
    concordance = est_concordante(choix, score.recommandation, score.montant_suggere, montant)
    if not concordance and not a_un_motif:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Un motif est obligatoire quand la décision diffère de la recommandation du modèle")

    # Accord modifié : le risque du montant réellement accordé est recalculé et tracé.
    simulation = None
    if choix == TypeDecision.ACCORDER_MODIFIE:
        simulation = _simuler(session, demande, montant, duree)
        if not simulation["dans_politique"] and not a_un_motif:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                f"Un motif est obligatoire : le montant accordé sort de la politique de crédit "
                f"(risque {simulation['p_defaut']:.1%} pour un seuil de {simulation['seuil']:.1%}, "
                f"endettement {simulation['endettement']:.0%} pour un maximum de {simulation['endettement_max']:.0%})")

    decision = Decision(
        demande_id=demande.id, score_id=score.id, decideur_id=utilisateur.id,
        decision=choix, montant_accorde=montant, duree_accordee=duree,
        commentaire=donnees.commentaire, recommandation_modele=score.recommandation,
        concordance=concordance)
    session.add(decision)
    changer_statut(demande, STATUT_APRES[choix])
    session.add(Journal(utilisateur_id=utilisateur.id, action="decision",
                        entite="demande_credit", entite_id=demande_id,
                        details={"decision": choix.value, "concordance": concordance,
                                 **({"simulation_montant_accorde": {
                                     k: (round(v, 4) if isinstance(v, float) else v)
                                     for k, v in simulation.items()}} if simulation else {})}))
    session.commit()
    session.refresh(decision)
    return decision


@router.get("/{demande_id}/decisions", response_model=list[DecisionOut])
def historique_decisions(demande_id: int, session: Session = Depends(get_session),
                         utilisateur: Utilisateur = Depends(exiger_roles(*LECTURE))):
    charger_demande(session, demande_id, utilisateur)
    return session.scalars(select(Decision).where(Decision.demande_id == demande_id)
                           .order_by(Decision.decide_le)).all()