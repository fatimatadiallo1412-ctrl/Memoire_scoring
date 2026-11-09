"""Répartit les clients entre les gestionnaires de LEUR agence.

Chaque client est confié à l'agent de rang (identifiant du client modulo nombre d'agents
de l'agence). Par défaut, seuls les clients sans gestionnaire sont affectés ; avec --refaire,
tous les clients sont réaffectés.
Usage : python -m app.repartir_portefeuilles [--refaire]
"""
import argparse

from sqlalchemy import func, select, update

from app.db import SessionLocal
from app.models import Agence, Client, Journal, Utilisateur
from app.models.enums import Role


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--refaire", action="store_true",
                         help="réaffecte aussi les clients déjà affectés")
    args = parseur.parse_args()

    with SessionLocal() as session:
        bilan = {}
        for agence in session.scalars(select(Agence).order_by(Agence.id)).all():
            agents = session.scalars(
                select(Utilisateur)
                .where(Utilisateur.role == Role.AGENT_CREDIT, Utilisateur.actif.is_(True),
                       Utilisateur.agence_id == agence.id)
                .order_by(Utilisateur.id)).all()
            if not agents:
                print(f"{agence.code} : aucun gestionnaire, clients laissés tels quels")
                continue

            nombre = len(agents)
            for rang, agent in enumerate(agents):
                requete = update(Client).where(Client.agence_id == agence.id,
                                               Client.id % nombre == rang)
                if not args.refaire:
                    requete = requete.where(Client.gestionnaire_id.is_(None))
                session.execute(requete.values(gestionnaire_id=agent.id))
            bilan[agence.code] = nombre
        session.add(Journal(utilisateur_id=None, action="portefeuilles_repartis",
                            entite="client", entite_id=None,
                            details={"refaire": args.refaire, "agents_par_agence": bilan}))
        session.commit()

        lignes = session.execute(
            select(Agence.code, Utilisateur.email, func.count(Client.id))
            .join(Utilisateur, Utilisateur.agence_id == Agence.id)
            .outerjoin(Client, Client.gestionnaire_id == Utilisateur.id)
            .where(Utilisateur.role == Role.AGENT_CREDIT)
            .group_by(Agence.code, Utilisateur.email)
            .order_by(Agence.code, Utilisateur.email)).all()
        for code, email, total in lignes:
            print(f"{code}  {email} : {total} clients")
        sans = session.scalar(select(func.count()).select_from(Client)
                              .where(Client.gestionnaire_id.is_(None)))
        print(f"Sans gestionnaire : {sans}")


if __name__ == "__main__":
    main()
