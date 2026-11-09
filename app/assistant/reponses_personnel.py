"""Réponses de l'assistant du personnel : mêmes données que celles du client, à la 3e personne."""
from datetime import date
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.assistant.reponses import MODES, _credits_en_cours, _jours, date_longue, fcfa
from app.historique import niveau_antecedent
from app.models import Client, Credit, Paiement
from app.routers.moi import ma_prochaine_echeance

AIDE = ("Une fois le client choisi, je peux indiquer :\n"
        "- sa prochaine échéance\n"
        "- ce qu'il lui reste à payer\n"
        "- ses retards éventuels\n"
        "- ses derniers paiements\n"
        "- sa situation pour une nouvelle demande de crédit")
SALUTATION = "Bonjour ! Quelle information souhaitez-vous sur ce client ?"
REMERCIEMENT = "Avec plaisir."
NON_COMPRIS = ("Je n'ai pas compris la question. Je peux renseigner sur la prochaine échéance, "
               "le solde restant, les retards, les derniers paiements et la situation pour un "
               "nouveau crédit.")


def _cible(client: Client) -> SimpleNamespace:
    """Les fonctions de l'espace client n'utilisent que `client_id` : on les réutilise telles quelles."""
    return SimpleNamespace(client_id=client.id)


def reponse_prochaine_echeance(session: Session, client: Client) -> str:
    p = ma_prochaine_echeance(session=session, utilisateur=_cible(client))
    if p is None:
        return "Aucune échéance à payer : les crédits sont soldés ou le client n'en a pas en cours."
    if p.en_retard:
        return (f"L'échéance n°{p.numero}, de {fcfa(p.reste_du)}, était due le "
                f"{date_longue(p.date_echeance)} : elle est en retard de {_jours(p.jours)}.")
    quand = "aujourd'hui" if p.jours == 0 else f"dans {_jours(p.jours)}"
    return (f"La prochaine échéance (n°{p.numero}) est de {fcfa(p.reste_du)}, "
            f"due le {date_longue(p.date_echeance)}, soit {quand}.")


def reponse_solde(session: Session, client: Client) -> str:
    en_cours = _credits_en_cours(session, _cible(client))
    if not en_cours:
        return "Aucun crédit en cours : il ne reste rien à payer."
    reste = sum(s["reste_a_payer"] for s in en_cours)
    capital = sum(s["capital_restant"] for s in en_cours)
    debut = ("Reste à payer" if len(en_cours) == 1
             else f"{len(en_cours)} crédits en cours. Reste à payer au total")
    return f"{debut} : {fcfa(reste)} (dont {fcfa(capital)} de capital)."


def reponse_retard(session: Session, client: Client) -> str:
    en_retard = [s for s in _credits_en_cours(session, _cible(client))
                 if s["nb_echeances_en_retard"] > 0]
    if not en_retard:
        return "Le client est à jour : aucune échéance n'est en retard."
    nombre = sum(s["nb_echeances_en_retard"] for s in en_retard)
    montant = sum(s["montant_en_retard"] for s in en_retard)
    jours = max(s["jours_retard_max"] for s in en_retard)
    pluriel = "s" if nombre > 1 else ""
    return (f"{nombre} échéance{pluriel} en retard, pour {fcfa(montant)}. "
            f"La plus ancienne l'est depuis {_jours(jours)}.")


def reponse_historique(session: Session, client: Client) -> str:
    paiements = session.scalars(
        select(Paiement).join(Credit, Credit.id == Paiement.credit_id)
        .where(Credit.client_id == client.id)
        .order_by(Paiement.date_paiement.desc(), Paiement.cree_le.desc()).limit(5)).all()
    if not paiements:
        return "Aucun paiement enregistré pour les crédits de ce client."
    lignes = []
    for p in paiements:
        mode = getattr(p.mode, "value", p.mode)
        lignes.append(f"- {date_longue(p.date_paiement)} : {fcfa(p.montant)} ({MODES.get(mode, mode)})")
    return "Derniers paiements :\n" + "\n".join(lignes)


def reponse_nouveau_credit(session: Session, client: Client) -> str:
    """Situation du client pour une nouvelle demande. La décision reste celle du directeur."""
    en_retard = [s for s in _credits_en_cours(session, _cible(client))
                 if s["nb_echeances_en_retard"] > 0]
    antecedent = niveau_antecedent(session, client.id, date.today())
    if antecedent == "en_cours":
        return ("Le client a un crédit en retard de plus de 90 jours : une nouvelle demande "
                "recevrait une recommandation de refus tant qu'il n'est pas régularisé.")
    if en_retard:
        return ("Le client a des échéances en retard : il doit les régulariser avant de déposer "
                "une nouvelle demande.")
    if antecedent == "regularise":
        return ("Le client a un antécédent de défaut régularisé : une nouvelle demande serait "
                "étudiée avec un seuil plus prudent. La décision revient au directeur.")
    return ("Aucun retard ni antécédent de défaut : le client peut déposer une nouvelle "
            "demande. La décision revient au directeur.")


DYNAMIQUES = {
    "prochaine_echeance": reponse_prochaine_echeance,
    "solde": reponse_solde,
    "retard": reponse_retard,
    "historique": reponse_historique,
    "nouveau_credit": reponse_nouveau_credit,
}
STATIQUES = {"aide": AIDE, "salutation": SALUTATION, "remerciement": REMERCIEMENT}


def repondre_personnel(intention: str, session: Session, client: Client) -> str:
    if intention in DYNAMIQUES:
        return DYNAMIQUES[intention](session, client)
    return STATIQUES.get(intention, NON_COMPRIS)
