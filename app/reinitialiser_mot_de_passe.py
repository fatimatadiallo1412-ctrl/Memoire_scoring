"""Remplace le mot de passe d'un compte existant.

Usage :
    python -m app.reinitialiser_mot_de_passe --email awa.niass@client.test
"""
import argparse
import getpass
import sys

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Utilisateur
from app.security import hasher_mot_de_passe


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--email", required=True)
    args = parseur.parse_args()

    nouveau = getpass.getpass("Nouveau mot de passe : ")
    confirmation = getpass.getpass("Confirme le mot de passe : ")
    if nouveau != confirmation:
        sys.exit("Les deux saisies sont différentes.")
    if len(nouveau) < 8:
        sys.exit("Mot de passe trop court (8 caractères minimum).")

    with SessionLocal() as session:
        utilisateur = session.scalars(
            select(Utilisateur).where(Utilisateur.email == args.email)).first()
        if utilisateur is None:
            sys.exit("Aucun compte avec cet email.")
        utilisateur.mot_de_passe_hash = hasher_mot_de_passe(nouveau)
        session.commit()
        print(f"Mot de passe mis à jour pour {args.email}")


if __name__ == "__main__":
    main()