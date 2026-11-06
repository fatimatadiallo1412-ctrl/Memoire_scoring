import pandas as pd

from src.features import PLAFOND_RATIO_CREDIT

SEUIL_DEFAUT = 0.15        # probabilité maximale de défaut acceptée (politique de l'IMF)
ENDETTEMENT_MAX = 0.40     # mensualité maximale, en part du revenu mensuel


def mensualite(montant, duree, taux_annuel=0.0):
    """Mensualité constante avec intérêts. Sans taux : montant / durée."""
    r = taux_annuel / 12
    if r == 0:
        return montant / duree
    return montant * r / (1 - (1 + r) ** -duree)


def taux_endettement(montant, duree, revenu, taux_annuel=0.0):
    return mensualite(montant, duree, taux_annuel) / revenu


def construire_ligne(profil, montant, duree, revenu, colonnes, taux_annuel=0.0):
    """Une ligne au format du modèle, pour un montant donné."""
    annuite = mensualite(montant, duree, taux_annuel)
    ligne = dict(profil)
    ligne["credit_sur_revenu"] = min(montant / revenu, PLAFOND_RATIO_CREDIT)
    ligne["annuite_sur_revenu"] = min(annuite / revenu, 1)
    ligne["duree_implicite"] = montant / annuite
    return pd.DataFrame([ligne])[colonnes]


def probabilite_defaut(modele, profil, montant, duree, revenu, colonnes, taux_annuel=0.0):
    ligne = construire_ligne(profil, montant, duree, revenu, colonnes, taux_annuel)
    return float(modele.predict_proba(ligne)[0, 1])


def suggerer_montant(modele, profil, montant_demande, duree, revenu, colonnes,
                     seuil=SEUIL_DEFAUT, pas=50_000, montant_min=50_000,
                     ratio_min=0.5, taux_annuel=0.0, endettement_max=ENDETTEMENT_MAX):
    p_demande = probabilite_defaut(modele, profil, montant_demande, duree, revenu,
                                   colonnes, taux_annuel)
    endett_demande = taux_endettement(montant_demande, duree, revenu, taux_annuel)

    # Pourquoi le montant demandé n'est pas accordable tel quel
    motifs = []
    if p_demande > seuil:
        motifs.append("risque_modele")
    if endett_demande > endettement_max:
        motifs.append("endettement")
    base = {"p_demande": p_demande, "endettement_demande": endett_demande, "motifs": motifs}

    if not motifs:
        return {"decision": "accord", "montant": montant_demande,
                "p_defaut": p_demande, **base}

    # On descend sur des multiples du pas (montants "ronds")
    montant = (montant_demande // pas) * pas
    if montant >= montant_demande:
        montant -= pas

    # Plancher : le plus élevé entre le minimum du produit et la part minimale du montant demandé
    plancher = max(montant_min, ratio_min * montant_demande)

    while montant >= plancher:
        if taux_endettement(montant, duree, revenu, taux_annuel) <= endettement_max:
            p = probabilite_defaut(modele, profil, montant, duree, revenu, colonnes, taux_annuel)
            if p <= seuil:
                return {"decision": "accord_reduit", "montant": montant,
                        "p_defaut": p, **base}
        montant -= pas

    return {"decision": "refus", "montant": None, "p_defaut": None, **base}