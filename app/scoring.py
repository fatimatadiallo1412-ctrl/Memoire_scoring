import json
import os
from functools import lru_cache

import joblib
from dotenv import load_dotenv

from app import referentiels as R
from app.explication import contributions
from src.features import PLAFOND_ENFANTS, PLAFOND_FAMILLE
from src import recours as RC
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


def evaluer_dossier(client, demande, produit, parametres, antecedent="aucun", historique=None,
                    avec_recours=True):
    """Renvoie la recommandation (accord / accord_reduit / refus) et les variables d'entrée.

    antecedent (voir app/historique.py) :
      "aucun"      : aucun incident, évaluation normale
      "regularise" : défaut passé régularisé, seuil d'acceptation resserré
      "en_cours"   : crédit en retard de plus de 90 jours, recommandation de refus
    La probabilité du modèle n'est jamais modifiée.
    avec_recours : calcule aussi les conseils au client (src/recours.py) ; désactivé pour les
    simulations de masse, qui n'en ont pas besoin.
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
    if avec_recours:
        recommandation["recours"] = recours_dossier(
            modele, profil, client, demande, produit, parametres, recommandation, seuil, antecedent,
            historique)

    ligne = construire_ligne(profil, demande.montant_demande, demande.duree_mois,
                             client.revenu_mensuel, COLONNES, taux)
    # Explication du score du montant demandé : poids de chaque variable (valeurs de Shapley)
    recommandation["contributions"] = contributions(modele, ligne, demande)
    variables = json.loads(ligne.to_json(orient="records"))[0]
    variables["antecedent_defaut"] = antecedent
    variables["complements"] = variables_complementaires(client, demande, historique)
    return recommandation, variables

def recours_dossier(modele, profil, client, demande, produit, parametres, recommandation, seuil,
                    antecedent="aucun", historique=None) -> dict:
    """Pourquoi la demande n'est pas accordée telle quelle, et ce que le client peut changer
    pour sa prochaine demande (src/recours.py). Calculé à chaque score et enregistré avec lui.

    Les conseils de l'institution sont calculés même pour un accord : ils servent si le directeur
    refuse contre l'avis du modèle (le motif est alors celui qu'il écrit pour le client)."""
    taux = float(produit.taux_annuel) / 100
    revenu = client.revenu_mensuel
    m_demandee = mensualite(demande.montant_demande, demande.duree_mois, taux)
    endettement_max = float(parametres["endettement_max"])
    reglages = {
        "mois_epargne": int(parametres.get("recours_mois_epargne", RC.MOIS_EPARGNE)),
        "part_nantie": float(parametres.get("recours_part_nantie", RC.PART_NANTIE)),
        "hausse_revenu_max": float(parametres.get("recours_hausse_revenu_max", RC.HAUSSE_REVENU_MAX)),
        "attente_max": int(parametres.get("recours_attente_max", RC.ATTENTE_MAX_MOIS)),
    }
    motifs = RC.motifs_client(
        recommandation["motifs"], mensualite_demandee=m_demandee, antecedent=antecedent,
        endettement=taux_endettement(demande.montant_demande, demande.duree_mois, revenu, taux),
        endettement_max=endettement_max)
    if antecedent == "en_cours":
        # Un seul conseil possible : régulariser avant toute nouvelle demande.
        return {"motifs": motifs, "plans": [], "institution": RC.regulariser(), "bloque": True,
                "reglages": reglages}

    plans = []
    if recommandation["decision"] != "accord":
        plans = RC.chercher_plans(
            modele, profil, demande.montant_demande, demande.duree_mois, revenu, COLONNES,
            taux_annuel=taux, seuil=seuil, endettement_max=endettement_max,
            montant_min=produit.montant_min, duree_min=produit.duree_min_mois,
            duree_max=produit.duree_max_mois, pas=int(parametres["pas_montant"]),
            # Accord réduit : comment obtenir la totalité du montant la prochaine fois
            montant_fixe=recommandation["decision"] == "accord_reduit",
            hausse_revenu_max=reglages["hausse_revenu_max"], attente_max=reglages["attente_max"])
    plan_reduit = next((p for p in plans if p["leviers"] and set(p["leviers"]) <= {"montant", "duree"}), None)
    # Épargne conseillée = mensualité d'un crédit réellement envisageable : celle du plan le plus proche
    # de la demande, sinon la mensualité maximale permise par la politique (jamais plus que la demande).
    if plans:
        m_visee, montant_vise = plans[-1]["mensualite"], plans[-1]["montant"]
    else:
        m_visee, montant_vise = min(m_demandee, endettement_max * revenu), demande.montant_demande
    institution = RC.recommandations_institution(
        client, demande, mensualite_visee=round(m_visee), historique=historique,
        plan_reduit=plan_reduit, montant_vise=montant_vise, mois_epargne=reglages["mois_epargne"],
        part_nantie=reglages["part_nantie"])
    return {"motifs": motifs if recommandation["decision"] != "accord" else [], "plans": plans,
            "institution": institution, "bloque": False, "mensualite_visee": round(m_visee),
            "reglages": reglages}
