import os

from dotenv import load_dotenv
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Agence, ProduitCredit, Utilisateur
from app.models.enums import Role
from app.security import hasher_mot_de_passe

load_dotenv()

AGENCES = [
    ("DKR01", "Agence Dakar Plateau", "Dakar"),
    ("THS01", "Agence Thiès", "Thiès"),
    ("STL01", "Agence Saint-Louis", "Saint-Louis"),
]

# Valeurs de démonstration, à valider avec une IMF
PRODUITS = [
    # code, libellé, montant min, montant max, durée min, durée max (mois), taux annuel (%)
    ("MICRO", "Microcrédit commerce", 50_000, 1_000_000, 3, 12, 24.0),
    ("PME", "Crédit petite entreprise", 500_000, 5_000_000, 6, 24, 22.0),
    ("SALARIE", "Crédit salarié", 100_000, 2_000_000, 6, 24, 18.0),
]


def get_or_create(session, modele, filtre, **valeurs):
    """Renvoie l'objet s'il existe déjà, sinon le crée : le script peut être relancé sans doublon."""
    objet = session.scalar(select(modele).filter_by(**filtre))
    if objet is None:
        objet = modele(**filtre, **valeurs)
        session.add(objet)
        session.flush()
    return objet


def main():
    mot_de_passe = os.environ.get("SEED_PASSWORD")
    if not mot_de_passe:
        raise SystemExit("Définis SEED_PASSWORD dans le fichier .env")

    with SessionLocal() as session:
        agences = [get_or_create(session, Agence, {"code": code}, nom=nom, zone=zone)
                   for code, nom, zone in AGENCES]

        for code, libelle, mn, mx, dmin, dmax, taux in PRODUITS:
            get_or_create(session, ProduitCredit, {"code": code}, libelle=libelle,
                          montant_min=mn, montant_max=mx, duree_min_mois=dmin,
                          duree_max_mois=dmax, taux_annuel=taux)

        comptes = [
            ("agent1@imf-demo.test", "Awa Ndiaye", Role.AGENT_CREDIT, agences[0]),
            ("directeur@imf-demo.test", "Moussa Diop", Role.DECIDEUR, agences[0]),
            ("admin@imf-demo.test", "Administrateur", Role.ADMINISTRATEUR, None),
        ]
        for email, nom, role, agence in comptes:
            get_or_create(session, Utilisateur, {"email": email}, nom_complet=nom, role=role,
                          agence_id=agence.id if agence else None,
                          mot_de_passe_hash=hasher_mot_de_passe(mot_de_passe))

        session.commit()
    print("Données de base créées.")


if __name__ == "__main__":
    main()