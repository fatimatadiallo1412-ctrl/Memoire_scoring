import json
from functools import lru_cache

import joblib

from app import referentiels as R
from src.features import PLAFOND_ENFANTS, PLAFOND_FAMILLE
from src.modeling import COLONNES, RACINE
from src.suggestion import SEUIL_DEFAUT, construire_ligne, suggerer_montant

VERSION_MODELE = "xgb_home_credit_v3"
PAS_MONTANT = 10_000


@lru_cache(maxsize=1)
def charger_modele():
    """Le modèle est chargé une seule fois, au premier appel."""
    return joblib.load(RACINE / "models" / f"{VERSION_MODELE}.joblib")


def profil_client(client, jour) -> dict:
    """Traduit la fiche client en variables du modèle (hors ratios)."""
    mois = client.anciennete_activite_mois
    # Dans les données d'entraînement, retraités et sans emploi ont sans_emploi = 1 et ancienneté 0
    sans_emploi = client.type_revenu == "retraite" or mois == 0
    age = (jour - client.date_naissance).days / 365.25
    return {
        "CNT_CHILDREN": min(client.nb_enfants, PLAFOND_ENFANTS),
        "CNT_FAM_MEMBERS": min(client.taille_menage, PLAFOND_FAMILLE),
        "age_ans": age,
        "anciennete_emploi_ans": 0.0 if sans_emploi else mois / 12,
        "sans_emploi": int(sans_emploi),
        "NAME_INCOME_TYPE": R.TYPE_REVENU[client.type_revenu],
        "NAME_FAMILY_STATUS": R.SITUATION_FAMILIALE[client.situation_familiale],
        "NAME_HOUSING_TYPE": R.TYPE_LOGEMENT[client.type_logement],
        "OCCUPATION_TYPE": R.PROFESSION.get(client.profession, "Non renseigné"),
        "FLAG_OWN_REALTY": "Y" if client.possede_bien_immobilier else "N",
        "FLAG_OWN_CAR": "Y" if client.possede_vehicule else "N",
    }


def evaluer_dossier(client, demande, produit, seuil=SEUIL_DEFAUT, ratio_min=0.5):
    """Renvoie la recommandation (accord / accord_reduit / refus) et les variables d'entrée."""
    modele = charger_modele()
    profil = profil_client(client, demande.date_demande)
    taux = float(produit.taux_annuel) / 100

    recommandation = suggerer_montant(
        modele, profil, demande.montant_demande, demande.duree_mois,
        client.revenu_mensuel, COLONNES, seuil=seuil, pas=PAS_MONTANT,
        montant_min=produit.montant_min, ratio_min=ratio_min, taux_annuel=taux)

    ligne = construire_ligne(profil, demande.montant_demande, demande.duree_mois,
                             client.revenu_mensuel, COLONNES, taux)
    variables = json.loads(ligne.to_json(orient="records"))[0]
    return recommandation, variables