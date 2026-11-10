import json
from functools import lru_cache

import joblib

from app import referentiels as R
from src.features import PLAFOND_ENFANTS, PLAFOND_FAMILLE
from src.modeling import COLONNES, RACINE
from src.suggestion import construire_ligne, suggerer_montant

VERSION_MODELE = "xgb_home_credit_v3"

# Facteur appliqué au seuil de défaut pour un client dont l'incident passé est régularisé
# (1.0 = règle désactivée). La valeur réelle vient de ops.parametre.
FACTEUR_PRUDENCE_DEFAUT = 0.8


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
        "OCCUPATION_TYPE": (getattr(client, "categorie_profession", None)
                            or R.PROFESSION.get(client.profession, "Non renseigné")),
        "FLAG_OWN_REALTY": "Y" if client.possede_bien_immobilier else "N",
        "FLAG_OWN_CAR": "Y" if client.possede_vehicule else "N",
    }


def evaluer_dossier(client, demande, produit, parametres, antecedent="aucun"):
    """Renvoie la recommandation (accord / accord_reduit / refus) et les variables d'entrée.

    antecedent (voir app/historique.py) :
      "aucun"      : aucun incident, évaluation normale
      "regularise" : défaut passé régularisé, seuil d'acceptation resserré
      "en_cours"   : crédit en retard de plus de 90 jours, recommandation de refus
    La probabilité du modèle n'est jamais modifiée.
    """
    modele = charger_modele()
    profil = profil_client(client, demande.date_demande)
    taux = float(produit.taux_annuel) / 100

    seuil_base = float(parametres["seuil_defaut"])
    facteur = float(parametres.get("facteur_prudence_antecedent", FACTEUR_PRUDENCE_DEFAUT))
    seuil = seuil_base * facteur if antecedent == "regularise" else seuil_base

    recommandation = suggerer_montant(
        modele, profil, demande.montant_demande, demande.duree_mois,
        client.revenu_mensuel, COLONNES,
        seuil=seuil, pas=int(parametres["pas_montant"]),
        montant_min=produit.montant_min, ratio_min=parametres["ratio_min"],
        taux_annuel=taux, endettement_max=parametres["endettement_max"])

    if antecedent == "en_cours":
        recommandation["decision"] = "refus"
        recommandation["montant"] = None
        recommandation["p_defaut"] = None
        recommandation["motifs"].append(
            "Crédit en retard de plus de 90 jours : à régulariser avant tout nouveau crédit")
    elif antecedent == "regularise":
        recommandation["motifs"].append(
            f"Incident de paiement passé, régularisé : seuil de risque resserré "
            f"({seuil:.3f} au lieu de {seuil_base:.3f})")
    recommandation["seuil_applique"] = seuil

    ligne = construire_ligne(profil, demande.montant_demande, demande.duree_mois,
                             client.revenu_mensuel, COLONNES, taux)
    variables = json.loads(ligne.to_json(orient="records"))[0]
    variables["antecedent_defaut"] = antecedent
    return recommandation, variables