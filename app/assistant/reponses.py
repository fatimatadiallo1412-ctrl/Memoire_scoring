"""Réponses de l'assistant : textes construits à partir des données du client connecté."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Credit, Paiement, Utilisateur
from app.routers.credits import _situation
from app.routers.moi import ma_prochaine_echeance

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
MODES = {"especes": "espèces", "mobile_money": "mobile money", "virement": "virement"}

AIDE = ("Je peux vous renseigner sur vos remboursements :\n"
        "- votre prochaine échéance\n"
        "- ce qu'il vous reste à payer\n"
        "- vos retards éventuels\n"
        "- vos derniers paiements\n"
        "Posez votre question simplement.")
SALUTATION = "Bonjour ! Je suis l'assistant de remboursement. Que souhaitez-vous savoir ?"
REMERCIEMENT = "Avec plaisir. N'hésitez pas à me poser une autre question."
NON_COMPRIS = ("Je n'ai pas compris votre question. Je peux répondre sur vos remboursements "
               "(prochaine échéance, solde restant, retards, derniers paiements). "
               "Pour toute autre demande, rapprochez-vous de votre agence.")


def fcfa(montant: int) -> str:
    return f"{montant:,}".replace(",", " ") + " FCFA"


def date_longue(jour: date) -> str:
    return f"{jour.day} {MOIS[jour.month - 1]} {jour.year}"


def _jours(n: int) -> str:
    return f"{n} jour" + ("s" if n > 1 else "")


def _credits_en_cours(session: Session, utilisateur: Utilisateur) -> list[dict]:
    credits = session.scalars(select(Credit).where(
        Credit.client_id == utilisateur.client_id)).all()
    situations = [_situation(session, c) for c in credits]
    return [s for s in situations if not s["solde"]]


def reponse_prochaine_echeance(session: Session, utilisateur: Utilisateur) -> str:
    p = ma_prochaine_echeance(session=session, utilisateur=utilisateur)
    if p is None:
        return "Vous n'avez aucune échéance à payer : vos crédits sont soldés ou vous n'en avez pas en cours."
    if p.en_retard:
        return (f"Votre échéance n°{p.numero}, de {fcfa(p.reste_du)}, était due le "
                f"{date_longue(p.date_echeance)} : elle est en retard de {_jours(p.jours)}. "
                f"Merci de régulariser rapidement.")
    quand = "aujourd'hui" if p.jours == 0 else f"dans {_jours(p.jours)}"
    return (f"Votre prochaine échéance (n°{p.numero}) est de {fcfa(p.reste_du)}, "
            f"due le {date_longue(p.date_echeance)}, soit {quand}.")


def reponse_solde(session: Session, utilisateur: Utilisateur) -> str:
    en_cours = _credits_en_cours(session, utilisateur)
    if not en_cours:
        return "Vous n'avez aucun crédit en cours : il ne vous reste rien à payer."
    reste = sum(s["reste_a_payer"] for s in en_cours)
    capital = sum(s["capital_restant"] for s in en_cours)
    debut = ("Il vous reste" if len(en_cours) == 1
             else f"Vous avez {len(en_cours)} crédits en cours. Il vous reste au total")
    return f"{debut} {fcfa(reste)} à payer (dont {fcfa(capital)} de capital)."


def reponse_retard(session: Session, utilisateur: Utilisateur) -> str:
    en_retard = [s for s in _credits_en_cours(session, utilisateur)
                 if s["nb_echeances_en_retard"] > 0]
    if not en_retard:
        return "Vous êtes à jour : aucune échéance n'est en retard."
    nombre = sum(s["nb_echeances_en_retard"] for s in en_retard)
    montant = sum(s["montant_en_retard"] for s in en_retard)
    jours = max(s["jours_retard_max"] for s in en_retard)
    pluriel = "s" if nombre > 1 else ""
    return (f"Vous avez {nombre} échéance{pluriel} en retard, pour {fcfa(montant)}. "
            f"La plus ancienne l'est depuis {_jours(jours)}. "
            f"Merci de régulariser rapidement ou de contacter votre agence.")


def reponse_historique(session: Session, utilisateur: Utilisateur) -> str:
    paiements = session.scalars(
        select(Paiement).join(Credit, Credit.id == Paiement.credit_id)
        .where(Credit.client_id == utilisateur.client_id)
        .order_by(Paiement.date_paiement.desc(), Paiement.cree_le.desc()).limit(5)).all()
    if not paiements:
        return "Je ne trouve aucun paiement enregistré pour vos crédits."
    lignes = []
    for p in paiements:
        mode = getattr(p.mode, "value", p.mode)
        lignes.append(f"- {date_longue(p.date_paiement)} : {fcfa(p.montant)} ({MODES.get(mode, mode)})")
    return "Vos derniers paiements :\n" + "\n".join(lignes)


def reponse_nouveau_credit(session: Session, utilisateur: Utilisateur) -> str:
    """Aucune date n'est promise : la décision revient au directeur."""
    en_retard = [s for s in _credits_en_cours(session, utilisateur)
                 if s["nb_echeances_en_retard"] > 0]
    if en_retard:
        return ("Vous avez des échéances en retard : régularisez-les d'abord, car cela pèse "
                "sur l'étude d'une nouvelle demande. La décision revient au directeur ; "
                "rapprochez-vous de votre agence.")
    return ("Toute nouvelle demande de crédit est étudiée par votre agence, et la décision "
            "revient au directeur. Rapprochez-vous de votre agence pour déposer votre demande.")


DYNAMIQUES = {
    "prochaine_echeance": reponse_prochaine_echeance,
    "solde": reponse_solde,
    "retard": reponse_retard,
    "historique": reponse_historique,
    "nouveau_credit": reponse_nouveau_credit,
}
STATIQUES = {"aide": AIDE, "salutation": SALUTATION, "remerciement": REMERCIEMENT}


def repondre(intention: str, session: Session, utilisateur: Utilisateur) -> str:
    if intention in DYNAMIQUES:
        return DYNAMIQUES[intention](session, utilisateur)
    return STATIQUES.get(intention, NON_COMPRIS)