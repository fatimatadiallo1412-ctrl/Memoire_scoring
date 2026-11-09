from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import exiger_roles
from app.models import Client, DemandeCredit, Journal, ProduitCredit, Score, Utilisateur
from app.models.enums import Role, StatutDossier
from app.schemas import DemandeIn, DemandeOut, InstructionIn, ScoreOut
from app.scoring import VERSION_MODELE, evaluer_dossier
from app.workflow import changer_statut
from app.portefeuille import client_accessible, filtrer_demandes
from app.parametres import lire_parametres
from app.historique import niveau_antecedent


router = APIRouter(prefix="/demandes", tags=["demandes"])

SAISIE = (Role.AGENT_CREDIT, Role.ADMINISTRATEUR)
LECTURE = (Role.AGENT_CREDIT, Role.DECIDEUR, Role.ADMINISTRATEUR)
MODIFIABLES = (StatutDossier.BROUILLON, StatutDossier.COMPLET,
               StatutDossier.SCORE, StatutDossier.INSTRUIT)


def verifier_produit(session: Session, produit_id: int, montant: int, duree: int) -> None:
    produit = session.get(ProduitCredit, produit_id)
    if produit is None or not produit.actif:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Produit inconnu ou inactif")
    if not produit.montant_min <= montant <= produit.montant_max:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Montant hors limites du produit ({produit.montant_min} à {produit.montant_max} FCFA)")
    if not produit.duree_min_mois <= duree <= produit.duree_max_mois:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Durée hors limites du produit ({produit.duree_min_mois} à {produit.duree_max_mois} mois)")


def _charger_demande_brut(session: Session, demande_id: int) -> DemandeCredit:
    demande = session.get(DemandeCredit, demande_id)
    if demande is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dossier introuvable")
    return demande


@router.post("", response_model=DemandeOut, status_code=status.HTTP_201_CREATED)
def creer_demande(donnees: DemandeIn, session: Session = Depends(get_session),
                  utilisateur: Utilisateur = Depends(exiger_roles(*SAISIE))):
    if not client_accessible(session, donnees.client_id, utilisateur):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Client inconnu")
    verifier_produit(session, donnees.produit_id, donnees.montant_demande, donnees.duree_mois)

    prochain_id = session.scalar(text("SELECT nextval(pg_get_serial_sequence('ops.demande_credit', 'id'))"))
    jour = donnees.date_demande or date.today()
    demande = DemandeCredit(
        id=prochain_id,
        numero=f"DC{jour.year}-{prochain_id:06d}",
        client_id=donnees.client_id,
        produit_id=donnees.produit_id,
        instructeur_id=utilisateur.id,
        montant_demande=donnees.montant_demande,
        duree_mois=donnees.duree_mois,
        objet=donnees.objet,
        date_demande=jour,
    )
    session.add(demande)
    session.add(Journal(utilisateur_id=utilisateur.id, action="dossier_cree",
                        entite="demande_credit", entite_id=prochain_id))
    session.commit()
    session.refresh(demande)
    return demande


@router.get("", response_model=list[DemandeOut])
def lister_demandes(
    statut: StatutDossier | None = None,
    client_id: int | None = None,
    limite: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
    utilisateur: Utilisateur = Depends(exiger_roles(*LECTURE)),
):
    requete = select(DemandeCredit).order_by(DemandeCredit.id.desc()).limit(limite)
    requete = filtrer_demandes(requete, utilisateur)
    if statut:
        requete = requete.where(DemandeCredit.statut == statut)
    if client_id:
        requete = requete.where(DemandeCredit.client_id == client_id)
    return session.scalars(requete).all()


@router.get("/{demande_id}", response_model=DemandeOut)
def lire_demande(demande_id: int, session: Session = Depends(get_session),
                 utilisateur: Utilisateur = Depends(exiger_roles(*LECTURE))):
    return charger_demande(session, demande_id, utilisateur)


@router.put("/{demande_id}", response_model=DemandeOut)
def modifier_demande(demande_id: int, donnees: DemandeIn, session: Session = Depends(get_session),
                     utilisateur: Utilisateur = Depends(exiger_roles(*SAISIE))):
    demande = charger_demande(session, demande_id, utilisateur)
    if demande.statut not in MODIFIABLES:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"Un dossier au statut {demande.statut.value} ne peut plus être modifié")
    verifier_produit(session, donnees.produit_id, donnees.montant_demande, donnees.duree_mois)

    demande.produit_id = donnees.produit_id
    demande.montant_demande = donnees.montant_demande
    demande.duree_mois = donnees.duree_mois
    demande.objet = donnees.objet
    demande.donnees_modifiees_le = text("now()")   # le score éventuel devient périmé
    if demande.statut in (StatutDossier.SCORE, StatutDossier.INSTRUIT):
        changer_statut(demande, StatutDossier.COMPLET)

    session.add(Journal(utilisateur_id=utilisateur.id, action="dossier_modifie",
                        entite="demande_credit", entite_id=demande_id))
    session.commit()
    session.refresh(demande)
    return demande


@router.post("/{demande_id}/completer", response_model=DemandeOut)
def completer_demande(demande_id: int, session: Session = Depends(get_session),
                      utilisateur: Utilisateur = Depends(exiger_roles(*SAISIE))):
    demande = charger_demande(session, demande_id, utilisateur)
    client = session.get(Client, demande.client_id)

    manquants = []
    if client.revenu_mensuel <= 0:
        manquants.append("revenu mensuel du client")
    if manquants:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Dossier incomplet : " + ", ".join(manquants))

    changer_statut(demande, StatutDossier.COMPLET)
    session.add(Journal(utilisateur_id=utilisateur.id, action="dossier_complet",
                        entite="demande_credit", entite_id=demande_id))
    session.commit()
    session.refresh(demande)
    return demande
@router.post("/{demande_id}/scorer", response_model=ScoreOut)
def scorer_demande(demande_id: int, session: Session = Depends(get_session),
                   utilisateur: Utilisateur = Depends(exiger_roles(*SAISIE))):
    demande = charger_demande(session, demande_id, utilisateur)
    if demande.statut not in (StatutDossier.COMPLET, StatutDossier.SCORE):
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"Un dossier au statut {demande.statut.value} ne peut pas être scoré")
    client = session.get(Client, demande.client_id)
    produit = session.get(ProduitCredit, demande.produit_id)
    if client.revenu_mensuel <= 0:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Le revenu mensuel du client est nécessaire au scoring")

    parametres = lire_parametres(session)
    reco, variables = evaluer_dossier(
        client, demande, produit, parametres,
        antecedent=niveau_antecedent(session, client.id, demande.date_demande))

    if reco["decision"] == "accord":
        montant_suggere, p_suggere = demande.montant_demande, reco["p_defaut"]
    else:
        montant_suggere, p_suggere = reco["montant"], reco["p_defaut"]

    score = Score(
        demande_id=demande.id,
        version_modele=VERSION_MODELE,
        p_defaut=reco["p_demande"],
        seuil_applique=reco["seuil_applique"],
        recommandation=reco["decision"],
        montant_suggere=montant_suggere,
        p_montant_suggere=p_suggere,
        variables_entree=variables,
        facteurs={"motifs": reco["motifs"],
                  "endettement_demande": round(reco["endettement_demande"], 3),
                  "parametres": parametres},
    )
    session.add(score)
    if demande.statut == StatutDossier.COMPLET:
        changer_statut(demande, StatutDossier.SCORE)
    session.add(Journal(utilisateur_id=utilisateur.id, action="dossier_score",
                        entite="demande_credit", entite_id=demande_id,
                        details={"recommandation": reco["decision"],
                                 "p_defaut": round(reco["p_demande"], 4)}))
    session.commit()
    session.refresh(score)
    return score


@router.get("/{demande_id}/score", response_model=ScoreOut)
def dernier_score(demande_id: int, session: Session = Depends(get_session),
                  utilisateur: Utilisateur = Depends(exiger_roles(*LECTURE))):
    demande = charger_demande(session, demande_id, utilisateur)
    score = session.scalar(select(Score).where(Score.demande_id == demande_id)
                           .order_by(Score.calcule_le.desc()).limit(1))
    if score is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucun score pour ce dossier")
    resultat = ScoreOut.model_validate(score)
    resultat.valide = demande.donnees_modifiees_le <= score.calcule_le   # sinon : score périmé
    return resultat
def exiger_score_valide(session: Session, demande: DemandeCredit) -> Score:
    score = session.scalar(select(Score).where(Score.demande_id == demande.id)
                           .order_by(Score.calcule_le.desc()).limit(1))
    if score is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Le dossier n'a pas encore été scoré")
    if demande.donnees_modifiees_le > score.calcule_le:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Le score est périmé : les données ont changé, il faut le recalculer")
    return score


@router.post("/{demande_id}/instruire", response_model=DemandeOut)
def instruire_demande(demande_id: int, donnees: InstructionIn,
                      session: Session = Depends(get_session),
                      utilisateur: Utilisateur = Depends(exiger_roles(*SAISIE))):
    demande = charger_demande(session, demande_id, utilisateur)
    exiger_score_valide(session, demande)
    changer_statut(demande, StatutDossier.INSTRUIT)
    demande.avis_instruction = donnees.avis
    demande.avis_instruction_le = datetime.now(timezone.utc)
    session.add(Journal(utilisateur_id=utilisateur.id, action="dossier_instruit",
                        entite="demande_credit", entite_id=demande_id))
    session.commit()
    session.refresh(demande)
    return demande


@router.post("/{demande_id}/soumettre", response_model=DemandeOut)
def soumettre_demande(demande_id: int, session: Session = Depends(get_session),
                      utilisateur: Utilisateur = Depends(exiger_roles(*SAISIE))):
    demande = charger_demande(session, demande_id, utilisateur)
    exiger_score_valide(session, demande)
    changer_statut(demande, StatutDossier.SOUMIS)
    session.add(Journal(utilisateur_id=utilisateur.id, action="dossier_soumis",
                        entite="demande_credit", entite_id=demande_id))
    session.commit()
    session.refresh(demande)
    return demande


def charger_demande(session: Session, demande_id: int, utilisateur: Utilisateur) -> DemandeCredit:
    """Charge un dossier si son client est dans le portefeuille de l'utilisateur.
    Sinon 404 (et non 403) : on ne révèle pas l'existence du dossier."""
    demande = _charger_demande_brut(session, demande_id)
    if not client_accessible(session, demande.client_id, utilisateur):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dossier introuvable")
    return demande
