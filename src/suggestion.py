import pandas as pd

from src.features import PLAFOND_RATIO_CREDIT

SEUIL_DEFAUT = 0.15      # probabilité maximale de défaut acceptée (politique de l'IMF)


def mensualite(montant, duree, taux_annuel=0.0):
    """Mensualité constante avec intérêts. Sans taux : montant / durée."""
    r = taux_annuel / 12
    if r == 0:
        return montant / duree
    return montant * r / (1 - (1 + r) ** -duree)


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
                     ratio_min=0.5, taux_annuel=0.0):
    p_demande = probabilite_defaut(modele, profil, montant_demande, duree, revenu,
                                   colonnes, taux_annuel)

    if p_demande <= seuil:
        return {"decision": "accord", "montant": montant_demande,
                "p_defaut": p_demande, "p_demande": p_demande}

    # On descend sur des multiples du pas (montants "ronds")
    montant = (montant_demande // pas) * pas
    if montant >= montant_demande:
        montant -= pas

    # Plancher : le plus élevé entre le minimum du produit et la part minimale du montant demandé
    plancher = max(montant_min, ratio_min * montant_demande)

    while montant >= plancher:
        p = probabilite_defaut(modele, profil, montant, duree, revenu, colonnes, taux_annuel)
        if p <= seuil:
            return {"decision": "accord_reduit", "montant": montant,
                    "p_defaut": p, "p_demande": p_demande}
        montant -= pas

    return {"decision": "refus", "montant": None,
            "p_defaut": None, "p_demande": p_demande}