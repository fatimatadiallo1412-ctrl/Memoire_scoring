from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Parametre

# clé : (valeur par défaut, description, minimum, maximum)
PARAMETRES_DEFAUT = {
    "seuil_defaut": (0.15, "Probabilité maximale de défaut acceptée", 0.01, 0.60),
    "endettement_max": (0.40, "Mensualité maximale, en part du revenu mensuel", 0.10, 0.80),
    "ratio_min": (0.50, "Part minimale du montant demandé proposable en réduction", 0.10, 1.00),
    "pas_montant": (10_000, "Pas de réduction du montant (FCFA)", 1_000, 1_000_000),
    "facteur_prudence_antecedent": (0.80, "Facteur appliqué au seuil de défaut si le client a un incident passé regularisé(1 = règle désactivée)", 0.10, 1.00),
}


def lire_parametres(session: Session) -> dict:
    """Valeurs en vigueur : celles de la base, à défaut les valeurs par défaut."""
    valeurs = {cle: v[0] for cle, v in PARAMETRES_DEFAUT.items()}
    for p in session.scalars(select(Parametre)):
        if p.cle in valeurs:
            valeurs[p.cle] = float(p.valeur)
    return valeurs