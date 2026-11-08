"""Grille de seuils à deux niveaux : un seuil strict pour les intentions qui affichent des
données du client, un seuil plus souple pour les autres.

Usage : python -m app.assistant.grille
"""
import numpy as np
import pandas as pd

from app.assistant.classifieur import charger_phrases, entrainer
from app.assistant.evaluer import FICHIER_TEST, SERVICES, _predire

VALEURS_C = (10, 30)
SEUILS_SERVICE = (0.40, 0.50, 0.60, 0.70)
SEUILS_AUTRE = (0.20, 0.30, 0.40)


def main():
    pd.set_option("display.width", 160)
    entrainement = charger_phrases()
    test = charger_phrases(FICHIER_TEST)
    vrai = test["intention"].to_numpy()
    dans = vrai != "hors_sujet"

    lignes = []
    for c in VALEURS_C:
        modele = entrainer(entrainement, c=c)
        predit, confiance = _predire(modele, test["phrase"])
        est_service = np.isin(predit, SERVICES)
        for s_service in SEUILS_SERVICE:
            for s_autre in SEUILS_AUTRE:
                seuil = np.where(est_service, s_service, s_autre)
                rejete = (confiance < seuil) | (predit == "hors_sujet")
                lignes.append({
                    "C": c, "seuil service": s_service, "seuil autre": s_autre,
                    "bonne réponse": (dans & ~rejete & (predit == vrai)).sum() / dans.sum(),
                    "non compris": (dans & rejete).sum() / dans.sum(),
                    "donnée erronée": int((est_service & ~rejete & (predit != vrai)).sum()),
                })
    print(pd.DataFrame(lignes).round(3).to_string(index=False))


if __name__ == "__main__":
    main()