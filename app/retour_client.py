"""Retour au client après une décision : pourquoi sa demande n'a pas été accordée telle quelle,
et ce qu'il peut changer pour sa prochaine demande.

Le même contenu est montré au client (espace client), à l'agent et au directeur (fiches dossier
et client). La version client ne contient aucun chiffre de risque.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Decision, DemandeCredit, ProduitCredit, Score
from app.models.enums import TypeDecision

# Champs d'un plan montrés au client (ni probabilité de défaut, ni taux d'endettement)
CHAMPS_PLAN_CLIENT = ("texte", "montant", "duree_mois", "attente_mois", "revenu_vise", "mensualite")


def retour_decision(decision: Decision | None, score: Score | None, pour_client: bool = False) -> dict | None:
    """None si la décision n'appelle pas de retour (accord complet, ou dossier non décidé)."""
    if decision is None or decision.decision == TypeDecision.ACCORDER:
        return None
    recours = ((score.facteurs or {}).get("recours") if score else None) or {}
    reco_modele = decision.recommandation_modele
    motifs, plans, institution = [], [], []

    if decision.decision == TypeDecision.REFUSER:
        institution = recours.get("institution", [])
        if reco_modele == "refus":
            # Refus conforme au modèle : ses motifs et ses plans s'appliquent.
            motifs = recours.get("motifs", [])
            plans = recours.get("plans", [])
        # Refus contre l'avis du modèle : seul le motif écrit par le directeur, et les règles de l'institution.
    elif decision.decision == TypeDecision.ACCORDER_MODIFIE:
        institution = recours.get("institution", [])
        if reco_modele == "accord_reduit":
            # Plans calculés pour obtenir la totalité du montant demandé.
            motifs = recours.get("motifs", [])
            plans = recours.get("plans", [])
    # Ajournement : seul le message du directeur, s'il en a écrit un.

    if not (motifs or plans or institution or decision.motif_client):
        return None
    if pour_client:
        plans = [{k: p.get(k) for k in CHAMPS_PLAN_CLIENT} for p in plans]
    return {
        "decision": decision.decision.value,
        "decide_le": decision.decide_le,
        "montant_accorde": decision.montant_accorde,
        "duree_accordee": decision.duree_accordee,
        "message": decision.motif_client,
        "motifs": [m["texte"] for m in motifs],
        "plans": plans,
        "institution": [{"code": i["code"], "titre": i["titre"], "texte": i["texte"]} for i in institution],
        "bloque": bool(recours.get("bloque")),
        # Scores calculés avant l'ajout des recommandations : rien à proposer, on le dit.
        "calcule": bool(recours),
    }


def derniere_decision(session: Session, demande_id: int) -> Decision | None:
    return session.scalars(select(Decision).where(Decision.demande_id == demande_id)
                           .order_by(Decision.decide_le.desc(), Decision.id.desc())).first()


def retour_demande(session: Session, demande_id: int, pour_client: bool = False) -> dict | None:
    decision = derniere_decision(session, demande_id)
    if decision is None:
        return None
    score = session.get(Score, decision.score_id) if decision.score_id else None
    return retour_decision(decision, score, pour_client)


def demandes_avec_retour(session: Session, client_id: int, pour_client: bool = False) -> list[dict]:
    """Les demandes du client, de la plus récente à la plus ancienne, avec le retour de leur décision."""
    demandes = session.scalars(select(DemandeCredit).where(DemandeCredit.client_id == client_id)
                               .order_by(DemandeCredit.date_demande.desc(), DemandeCredit.id.desc())).all()
    produits = {p.id: p.libelle for p in session.scalars(select(ProduitCredit))}
    return [{
        "id": d.id, "numero": d.numero, "date_demande": d.date_demande, "produit": produits.get(d.produit_id),
        "montant_demande": d.montant_demande, "duree_mois": d.duree_mois, "statut": d.statut.value,
        "retour": retour_demande(session, d.id, pour_client),
    } for d in demandes]
