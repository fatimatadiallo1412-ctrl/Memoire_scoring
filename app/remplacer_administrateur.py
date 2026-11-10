"""Remplace l'administrateur unique de la plateforme.

Usage : python -m app.remplacer_administrateur --email nouvel.admin@imf-demo.test --nom "Nom Complet"
Option --essai : montre ce qui serait fait sans rien enregistrer.

L'ancien compte est désactivé (il reste en base pour l'historique d'audit) et le nouveau est créé
dans la même opération : on ne peut pas se retrouver sans administrateur ni avec deux.
Le mot de passe est demandé en saisie masquée.
"""
import argparse
import getpass
import sys

from sqlalchemy import select, text

from app.db import SessionLocal
from app.models import Journal, Utilisateur
from app.models.enums import Role
from app.security import hasher_mot_de_passe


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--email", required=True)
    parseur.add_argument("--nom", required=True, help="Nom complet affiché")
    parseur.add_argument("--essai", action="store_true", help="Ne rien enregistrer")
    args = parseur.parse_args()

    mot_de_passe = getpass.getpass("Mot de passe du nouvel administrateur : ")
    if len(mot_de_passe) < 8:
        sys.exit("Mot de passe trop court (8 caractères minimum).")
    if getpass.getpass("Confirmez le mot de passe : ") != mot_de_passe:
        sys.exit("Les deux mots de passe sont différents.")

    with SessionLocal() as session:
        if session.scalars(select(Utilisateur).where(Utilisateur.email == args.email)).first():
            sys.exit("Cet email est déjà utilisé.")

        ancien_id = session.execute(text(
            "SELECT id FROM ops.utilisateur WHERE role = 'administrateur' AND actif LIMIT 1")).scalar()
        if ancien_id is not None:
            session.execute(text("UPDATE ops.utilisateur SET actif = false WHERE id = :i"), {"i": ancien_id})
            session.flush()

        nouveau = Utilisateur(
            email=args.email, nom_complet=args.nom,
            mot_de_passe_hash=hasher_mot_de_passe(mot_de_passe),
            role=Role.ADMINISTRATEUR)
        session.add(nouveau)
        session.flush()
        session.add(Journal(
            utilisateur_id=nouveau.id, action="administrateur_remplace", entite="utilisateur",
            entite_id=nouveau.id, details={"ancien_id": ancien_id}))

        if args.essai:
            session.rollback()
            print(f"ESSAI : l'ancien compte (id {ancien_id}) serait désactivé et {args.email} deviendrait "
                  "administrateur. Rien n'a été enregistré.")
            return
        session.commit()
        print(f"Nouvel administrateur : {args.email}. Ancien compte (id {ancien_id}) désactivé.")


if __name__ == "__main__":
    main()
