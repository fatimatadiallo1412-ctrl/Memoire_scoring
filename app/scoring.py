import json
import os
from functools import lru_cache

import joblib
from dotenv import load_dotenv

from app import referentiels as R
from app.explication import contributions
from src.features import PLAFOND_ENFANTS, PLAFOND_FAMILLE
from src.modeling import COLONNES, RACINE
from src.suggestion import (construire_ligne, mensualite, probabilite_defaut, suggerer_montant,
                            taux_endettement)

load_dotenv()
# Version en production. Une nouvelle version n'est promue qu'après la comparaison
# champion / challenger (src/champion_challenger.py) et la décision de la direction :
# on renseigne alors MODELE_VERSION dans .env, sans toucher au code.
VERSION_MODELE = os.environ.get("MODELE_VERSION", "xgb_home_credit_v4")

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


def seuil_applicable(parametres, antecedent="aucun") -> float:
    """Seuil de risque de la politique, resserré si le client a un incident passé régularisé."""
    seuil = float(parametres["seuil_defaut"])
    if antecedent == "regularise":
        seuil *= float(parametres.get("facteur_prudence_antecedent", FACTEUR_PRUDENCE_DEFAUT))
    return seuil


def evaluer_montant(client, demande, produit, parametres, montant, duree, antecedent="aucun") -> dict:
    """Risque et endettement d'un montant et d'une durée donnés (par exemple un accord modifié).
    Ne modifie rien : sert à éclairer la décision du directeur."""
    modele = charger_modele()
    profil = profil_client(client, demande.date_demande)
    taux = float(produit.taux_annuel) / 100
    revenu = client.revenu_mensuel
    seuil = seuil_applicable(parametres, antecedent)
    endettement_max = float(parametres["endettement_max"])
    p = probabilite_defaut(modele, profil, montant, duree, revenu, COLONNES, taux)
    endettement = taux_endettement(montant, duree, revenu, taux)
    motifs = []
    if antecedent == "en_cours":
        motifs.append("antecedent_en_cours")
    if p > seuil:
        motifs.append("risque_modele")
    if endettement > endettement_max:
        motifs.append("endettement")
    return {"montant": montant, "duree_mois": duree, "p_defaut": p, "seuil": seuil,
            "mensualite": round(mensualite(montant, duree, taux)), "endettement": endettement,
            "endettement_max": endettement_max, "dans_politique": not motifs, "motifs": motifs}


# Variables enregistrées avec chaque score sans être données au modèle v4 : elles alimenteront
# les modèles appris sur les données de l'institution (src/donnees_locales.py).
VARIABLES_MICROFINANCE = ["epargne_mensuelle", "membre_groupement", "usage_mobile_money",
                          "activite_saisonniere"]


def variables_complementaires(client, demande, historique: dict | None = None) -> dict:
    complements = {v: getattr(client, v, None) for v in VARIABLES_MICROFINANCE}
    complements["garantie"] = getattr(demande, "garantie", None)
    complements["revenu_mensuel"] = client.revenu_mensuel
    complements.update(historique or {})
    return complements


def evaluer_dossier(client, demande, produit, parametres, antecedent="aucun", historique=None):
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
    seuil = seuil_applicable(parametres, antecedent)

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
    # Explication du score du montant demandé : poids de chaque variable (valeurs de Shapley)
    recommandation["contributions"] = contributions(modele, ligne, demande)
    variables = json.loads(ligne.to_json(orient="records"))[0]
    variables["antecedent_defaut"] = antecedent
    variables["complements"] = variables_complementaires(client, demande, historique)
    return recommandation, variables