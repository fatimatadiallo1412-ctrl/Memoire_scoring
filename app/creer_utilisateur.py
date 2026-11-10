"""Crée un compte du personnel (gestionnaire par défaut).

Usage : python -m app.creer_utilisateur --email agent2@imf-demo.test --nom "Agent Deux"
Le mot de passe est demandé en saisie masquée (il n'apparaît pas dans l'historique).
"""
import argparse
import getpass
import sys

from sqlalchemy import select, text

from app.db import SessionLocal
from app.models import Agence, Utilisateur
from app.models.enums import Role
from app.security import hasher_mot_de_passe


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--email", required=True)
    parseur.add_argument("--nom", required=True, help="Nom complet affiché")
    parseur.add_argument("--role", default=Role.AGENT_CREDIT.value,
                         choices=[r.value for r in Role if r != Role.CLIENT])
    parseur.add_argument("--agence-id", type=int, default=None)
    args = parseur.parse_args()

    mot_de_passe = getpass.getpass("Mot de passe du compte : ")
    if len(mot_de_passe) < 8:
        sys.exit("Mot de passe trop court (8 caractères minimum).")

    with SessionLocal() as session:
        if args.agence_id is not None and session.get(Agence, args.agence_id) is None:
            sys.exit(f"Aucune agence avec l'id {args.agence_id}.")
        if session.scalars(select(Utilisateur).where(Utilisateur.email == args.email)).first():
            sys.exit("Cet email est déjà utilisé.")
        if args.role == Role.ADMINISTRATEUR.value and session.execute(text(
                "SELECT 1 FROM ops.utilisateur WHERE role = 'administrateur' AND actif LIMIT 1")).first():
            sys.exit("Il existe déjà un administrateur actif : il ne peut y en avoir qu'un. "
                     "Pour changer de titulaire : python -m app.remplacer_administrateur")
        session.add(Utilisateur(
            email=args.email, nom_complet=args.nom,
            mot_de_passe_hash=hasher_mot_de_passe(mot_de_passe),
            role=Role(args.role), agence_id=args.agence_id))
        session.commit()
        print(f"Compte créé : {args.email} ({args.role})")


if __name__ == "__main__":
    main()
