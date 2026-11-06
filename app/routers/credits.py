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
from sqlalchemy import func, select
from app.models import Credit, Decision, DemandeCredit, Echeance, Journal, Paiement, ProduitCredit, Utilisateur
from app.schemas import (CreditOut, DecaissementIn, EcheanceOut, PaiementIn,
                         PaiementOut, SituationOut)
from app.suivi import situation_credit
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
def _credit_ou_404(session: Session, credit_id: int) -> Credit:
    credit = session.get(Credit, credit_id)
    if credit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Crédit introuvable")
    return credit


def _situation(session: Session, credit: Credit) -> dict:
    echeances = session.scalars(select(Echeance).where(Echeance.credit_id == credit.id)).all()
    total_paye = session.scalar(
        select(func.coalesce(func.sum(Paiement.montant), 0))
        .where(Paiement.credit_id == credit.id))
    return situation_credit(echeances, int(total_paye), date.today())


@router.post("/credits/{credit_id}/paiements", response_model=PaiementOut,
             status_code=status.HTTP_201_CREATED)
def enregistrer_paiement(credit_id: int, donnees: PaiementIn,
                         session: Session = Depends(get_session),
                         utilisateur: Utilisateur = Depends(
                             exiger_roles(Role.AGENT_CREDIT, Role.ADMINISTRATEUR))):
    credit = _credit_ou_404(session, credit_id)
    demande = session.get(DemandeCredit, credit.demande_id)
    if demande.statut not in (StatutDossier.EN_REMBOURSEMENT, StatutDossier.CONTENTIEUX):
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Ce crédit n'accepte plus de paiement")

    jour = donnees.date_paiement or date.today()
    if jour > date.today():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "La date de paiement ne peut pas être dans le futur")
    if jour < credit.date_decaissement:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "La date de paiement précède le décaissement")

    situation = _situation(session, credit)
    if donnees.montant > situation["reste_a_payer"]:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Le montant dépasse le reste à payer ({situation['reste_a_payer']})")

    paiement = Paiement(credit_id=credit.id, montant=donnees.montant,
                        date_paiement=jour, mode=donnees.mode,
                        enregistre_par=utilisateur.id)
    session.add(paiement)
    session.flush()

    # Si ce paiement solde le crédit, le dossier passe à "solde"
    if donnees.montant == situation["reste_a_payer"]:
        changer_statut(demande, StatutDossier.SOLDE)

    session.add(Journal(utilisateur_id=utilisateur.id, action="paiement",
                        entite="credit", entite_id=credit.id,
                        details={"montant": donnees.montant, "mode": donnees.mode}))
    session.commit()
    session.refresh(paiement)
    return paiement


@router.get("/credits/{credit_id}/paiements", response_model=list[PaiementOut])
def historique_paiements(credit_id: int, session: Session = Depends(get_session),
                         utilisateur: Utilisateur = Depends(exiger_roles(*LECTURE))):
    _credit_ou_404(session, credit_id)
    return session.scalars(select(Paiement).where(Paiement.credit_id == credit_id)
                           .order_by(Paiement.date_paiement, Paiement.id)).all()


@router.get("/credits/{credit_id}/situation", response_model=SituationOut)
def situation_du_credit(credit_id: int, session: Session = Depends(get_session),
                        utilisateur: Utilisateur = Depends(exiger_roles(*LECTURE))):
    return _situation(session, _credit_ou_404(session, credit_id))