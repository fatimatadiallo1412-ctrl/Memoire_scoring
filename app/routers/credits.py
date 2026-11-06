from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.calendrier import generer_calendrier, mensualite_constante
from app.db import get_session
from app.deps import exiger_roles
from app.models import Credit, Decision, Echeance, Journal, ProduitCredit, Utilisateur
from app.models.enums import Role, StatutDossier
from app.routers.demandes import LECTURE, charger_demande
from app.schemas import CreditOut, DecaissementIn, EcheanceOut
from app.workflow import changer_statut

router = APIRouter(tags=["crédits"])


@router.post("/demandes/{demande_id}/decaisser", response_model=CreditOut,
             status_code=status.HTTP_201_CREATED)
def decaisser(demande_id: int, donnees: DecaissementIn | None = None,
              session: Session = Depends(get_session),
              utilisateur: Utilisateur = Depends(
                  exiger_roles(Role.AGENT_CREDIT, Role.ADMINISTRATEUR))):
    demande = charger_demande(session, demande_id)
    if demande.statut not in (StatutDossier.ACCORDE, StatutDossier.ACCORDE_MODIFIE):
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Seul un dossier accordé peut être décaissé")

    # Les conditions du crédit sont celles de la dernière décision du directeur
    decision = session.scalars(
        select(Decision).where(Decision.demande_id == demande_id)
        .order_by(Decision.decide_le.desc()).limit(1)).first()
    if decision is None or decision.montant_accorde is None:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Aucune décision d'accord trouvée pour ce dossier")

    produit = session.get(ProduitCredit, demande.produit_id)
    taux = float(produit.taux_annuel) / 100          # 24.00 (%) -> 0.24
    montant, duree = decision.montant_accorde, decision.duree_accordee
    jour = (donnees.date_decaissement if donnees and donnees.date_decaissement
            else date.today())

    credit = Credit(
        demande_id=demande.id, client_id=demande.client_id,
        montant_accorde=montant, duree_mois=duree, taux_annuel=taux,
        mensualite=mensualite_constante(montant, duree, taux),
        date_decaissement=jour, decaisse_par=utilisateur.id)
    session.add(credit)
    session.flush()          # attribue credit.id sans valider la transaction

    for ligne in generer_calendrier(montant, duree, taux, jour):
        session.add(Echeance(credit_id=credit.id, **ligne))

    changer_statut(demande, StatutDossier.DECAISSE)
    changer_statut(demande, StatutDossier.EN_REMBOURSEMENT)
    session.add(Journal(utilisateur_id=utilisateur.id, action="decaissement",
                        entite="credit", entite_id=credit.id,
                        details={"demande_id": demande.id, "montant": montant,
                                 "duree_mois": duree}))
    session.commit()
    session.refresh(credit)
    return credit


@router.get("/demandes/{demande_id}/credit", response_model=CreditOut)
def credit_du_dossier(demande_id: int, session: Session = Depends(get_session),
                      utilisateur: Utilisateur = Depends(exiger_roles(*LECTURE))):
    charger_demande(session, demande_id)
    credit = session.scalars(select(Credit).where(Credit.demande_id == demande_id)).first()
    if credit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ce dossier n'a pas de crédit décaissé")
    return credit


@router.get("/credits/{credit_id}/echeances", response_model=list[EcheanceOut])
def echeances_du_credit(credit_id: int, session: Session = Depends(get_session),
                        utilisateur: Utilisateur = Depends(exiger_roles(*LECTURE))):
    if session.get(Credit, credit_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Crédit introuvable")
    return session.scalars(select(Echeance).where(Echeance.credit_id == credit_id)
                           .order_by(Echeance.numero)).all()