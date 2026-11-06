"""Crée un compte de connexion (rôle client) rattaché à une fiche client existante.

Usage :
    python -m app.creer_compte_client --client-id 3 --email awa.niass@client.test --nom "Awa Niass"
Le mot de passe est demandé en saisie masquée (il n'apparaît pas dans l'historique).
"""
import argparse
import getpass
import sys

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Client, Utilisateur
from app.models.enums import Role
from app.security import hasher_mot_de_passe


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--client-id", type=int, required=True)
    parseur.add_argument("--email", required=True)
    parseur.add_argument("--nom", required=True, help="Nom complet affiché")
    args = parseur.parse_args()

    mot_de_passe = getpass.getpass("Mot de passe du compte client : ")
    if len(mot_de_passe) < 8:
        sys.exit("Mot de passe trop court (8 caractères minimum).")

    with SessionLocal() as session:
        if session.get(Client, args.client_id) is None:
            sys.exit(f"Aucun client avec l'id {args.client_id}.")
        if session.scalars(select(Utilisateur).where(
                Utilisateur.client_id == args.client_id)).first():
            sys.exit("Ce client a déjà un compte.")
        if session.scalars(select(Utilisateur).where(
                Utilisateur.email == args.email)).first():
            sys.exit("Cet email est déjà utilisé.")

        session.add(Utilisateur(
            email=args.email, nom_complet=args.nom,
            mot_de_passe_hash=hasher_mot_de_passe(mot_de_passe),
            role=Role.CLIENT, client_id=args.client_id))
        session.commit()
        print(f"Compte créé : {args.email} (client {args.client_id})")


if __name__ == "__main__":
    main()