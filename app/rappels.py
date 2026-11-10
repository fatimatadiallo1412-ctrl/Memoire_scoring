"""Génère les rappels de remboursement affichés dans l'espace client.

Usage :
    python -m app.rappels                       # rappels du jour
    python -m app.rappels --a-blanc             # compte sans rien enregistrer
    python -m app.rappels --jour 2026-11-20     # simule une autre date

Idempotent : une contrainte d'unicité (échéance, type) interdit les doublons.
"""
import argparse
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.assistant.reponses import _jours, date_longue, fcfa
from app.db import SessionLocal
from app.models import Credit, DemandeCredit, Echeance, Journal, Paiement, Rappel
from app.models.enums import StatutDossier
from app.suivi import situation_credit

# (écart en jours par rapport à la date d'échéance, type), du plus tôt au plus tard.
# Négatif = avant l'échéance. Choix de politique, modifiables ici.
PALIERS = [(-3, "avant_3j"), (0, "jour_j"), (1, "retard_1"),
           (7, "retard_7"), (14, "retard_14"), (30, "retard_30")]
STATUTS_SUIVIS = (StatutDossier.EN_REMBOURSEMENT, StatutDossier.CONTENTIEUX)


def palier(ecart: int) -> str | None:
    """Le palier le plus récent atteint (rattrapage : on ne rejoue pas les paliers manqués)."""
    atteints = [type_rappel for decalage, type_rappel in PALIERS if decalage <= ecart]
    return atteints[-1] if atteints else None


def texte(type_rappel: str, numero: int, montant: int, echeance: date, ecart: int) -> str:
    base = f"échéance n°{numero} de {fcfa(montant)}"
    if type_rappel == "avant_3j":
        return f"Rappel : votre {base} est due le {date_longue(echeance)}, dans {_jours(-ecart)}."
    if type_rappel == "jour_j":
        return f"Votre {base} est due aujourd'hui."
    message = (f"Votre {base} était due le {date_longue(echeance)} : "
               f"elle est en retard de {_jours(ecart)}.")
    if type_rappel == "retard_30":
        return message + " Merci de contacter votre agence au plus vite."
    return message + " Merci de régulariser rapidement."


def generer(session, jour: date) -> dict[str, int]:
    """Crée les rappels dus à la date `jour`. Renvoie le nombre créé par type."""
    credits = session.scalars(
        select(Credit).join(DemandeCredit, DemandeCredit.id == Credit.demande_id)
        .where(DemandeCredit.statut.in_(STATUTS_SUIVIS), Credit.date_decaissement <= jour)).all()

    crees: dict[str, int] = {}
    for credit in credits:
        echeances = session.scalars(select(Echeance).where(Echeance.credit_id == credit.id)).all()
        total_paye = session.scalar(
            select(func.coalesce(func.sum(Paiement.montant), 0))
            .where(Paiement.credit_id == credit.id, Paiement.date_paiement <= jour))
        identifiants = {e.numero: e.id for e in echeances}

        for ligne in situation_credit(echeances, int(total_paye), jour)["echeances"]:
            if ligne["reste_du"] == 0:
                continue
            ecart = (jour - ligne["date_echeance"]).days
            type_rappel = palier(ecart)
            if type_rappel is None:
                continue
            resultat = session.execute(
                insert(Rappel).values(
                    client_id=credit.client_id, credit_id=credit.id,
                    echeance_id=identifiants[ligne["numero"]], type_rappel=type_rappel,
                    jour=jour,
                    message=texte(type_rappel, ligne["numero"], ligne["reste_du"],
                                  ligne["date_echeance"], ecart))
                .on_conflict_do_nothing(index_elements=["echeance_id", "type_rappel"])
                .returning(Rappel.id))
            if resultat.first() is not None:
                crees[type_rappel] = crees.get(type_rappel, 0) + 1
    return crees


def executer(jour: date, a_blanc: bool = False) -> dict[str, int]:
    """Ouvre une session, génère, trace au journal et valide (sauf à blanc)."""
    with SessionLocal() as session:
        crees = generer(session, jour)
        if a_blanc:
            session.rollback()
        else:
            session.add(Journal(utilisateur_id=None, action="rappels_generes",
                                entite="rappel", entite_id=None,
                                details={"jour": jour.isoformat(), **crees}))
            session.commit()
        return crees


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("--jour", type=date.fromisoformat, default=date.today())
    parseur.add_argument("--a-blanc", action="store_true",
                         help="compte les rappels sans rien enregistrer")
    args = parseur.parse_args()

    crees = executer(args.jour, args.a_blanc)
    etat = "À BLANC (rien enregistré)" if args.a_blanc else "enregistrés"
    print(f"Rappels pour le {args.jour} : {sum(crees.values())} {etat}")
    for type_rappel in (t for _, t in PALIERS):
        if type_rappel in crees:
            print(f"  {type_rappel} : {crees[type_rappel]}")


if __name__ == "__main__":
    main()
