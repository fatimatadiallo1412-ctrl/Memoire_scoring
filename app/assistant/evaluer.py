"""Évaluation du classifieur d'intentions.

Usage : python -m app.assistant.evaluer
            diagnostic complet sur le jeu de validation
        python -m app.assistant.evaluer --final --fichier data/assistant/phrases_test_final.csv
            évaluation finale : paramètres figés, aucun balayage
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from app.assistant.classifieur import (C_DEFAUT, FICHIER_PHRASES, SEUIL_AUTRE, SEUIL_SERVICE,
                                       SERVICES, charger_phrases, construire_pipeline, entrainer)

FICHIER_TEST = FICHIER_PHRASES.with_name("phrases_test.csv")
SEUILS = (0.30, 0.40, 0.50, 0.60, 0.70)
VALEURS_C = (1, 3, 10, 30, 100)
SEUIL_BALAYAGE = 0.40


def _predire(modele, phrases):
    proba = modele.predict_proba(phrases)
    return modele.classes_[proba.argmax(axis=1)], proba.max(axis=1)


def bilan(vrai, predit, confiance, seuil_service, seuil_autre=None) -> dict:
    """Ce que devient chaque phrase pour des seuils donnés (hors_sujet compte comme « non compris »)."""
    if seuil_autre is None:
        seuil_autre = seuil_service
    vrai, predit, confiance = map(np.asarray, (vrai, predit, confiance))
    est_service = np.isin(predit, list(SERVICES))
    seuil = np.where(est_service, seuil_service, seuil_autre)
    rejete = (confiance < seuil) | (predit == "hors_sujet")
    dans = vrai != "hors_sujet"
    return {
        "bonne réponse": (dans & ~rejete & (predit == vrai)).sum() / dans.sum(),
        "réponse erronée": (dans & ~rejete & (predit != vrai)).sum() / dans.sum(),
        "non compris": (dans & rejete).sum() / dans.sum(),
        "hors-sujet écarté": ((~dans) & rejete).sum() / max((~dans).sum(), 1),
        "donnée erronée": int((est_service & ~rejete & (predit != vrai)).sum()),
    }


def tableau_seuils(vrai, predit, confiance) -> pd.DataFrame:
    lignes = [{"seuil": s, **bilan(vrai, predit, confiance, s)} for s in SEUILS]
    return pd.DataFrame(lignes).set_index("seuil").round(3)


def balayage_c(entrainement, test) -> pd.DataFrame:
    vrai = test["intention"].to_numpy()
    lignes = []
    for c in VALEURS_C:
        modele = entrainer(entrainement, c=c)
        predit, confiance = _predire(modele, test["phrase"])
        lignes.append({"C": c, "exactitude": (predit == vrai).mean(),
                       "confiance moyenne": confiance.mean(),
                       **bilan(vrai, predit, confiance, SEUIL_BALAYAGE)})
    return pd.DataFrame(lignes).set_index("C").round(3)


def main():
    analyse = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analyse.add_argument("--fichier", default=str(FICHIER_TEST), help="fichier de phrases à évaluer")
    analyse.add_argument("--final", action="store_true", help="évaluation finale, paramètres figés")
    args = analyse.parse_args()

    pd.set_option("display.width", 160)
    entrainement = charger_phrases()
    print(f"Phrases d'entraînement : {len(entrainement)}")
    print(entrainement["intention"].value_counts().to_string())

    if not args.final:
        # Validation croisée sur l'entraînement : indicatif, plutôt optimiste
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        proba = cross_val_predict(construire_pipeline(), entrainement["phrase"],
                                  entrainement["intention"], cv=cv, method="predict_proba")
        classes = np.unique(entrainement["intention"])
        predit = classes[proba.argmax(axis=1)]
        exactitude = (predit == entrainement["intention"].to_numpy()).mean()
        print(f"\nValidation croisée (5 plis) : exactitude {exactitude:.3f} "
              f"(optimiste : phrases d'un même auteur)")

    chemin = Path(args.fichier)
    if not chemin.exists():
        print(f"\nPas de fichier : {chemin}")
        return
    test = charger_phrases(chemin)
    if test.empty:
        print("\nLe fichier est vide : ajoute des phrases.")
        return
    inconnues = set(test["intention"]) - set(entrainement["intention"])
    if inconnues:
        print(f"\nATTENTION : intentions absentes de l'entraînement : {sorted(inconnues)}")

    modele = entrainer(entrainement)
    predit, confiance = _predire(modele, test["phrase"])
    vrai = test["intention"].to_numpy()
    nom = "TEST FINAL" if args.final else "Validation"
    print(f"\n{nom} ({chemin.name}) : {len(test)} phrases, exactitude {(predit == vrai).mean():.3f}")
    print(classification_report(vrai, predit, zero_division=0))
    etiquettes = sorted(set(vrai) | set(predit))
    print("Matrice de confusion (lignes : vrai ; colonnes : prédit)")
    print(pd.DataFrame(confusion_matrix(vrai, predit, labels=etiquettes),
                       index=etiquettes, columns=etiquettes).to_string())

    retenu = bilan(vrai, predit, confiance, SEUIL_SERVICE, SEUIL_AUTRE)
    print(f"\nRéglage retenu : C = {C_DEFAUT}, seuil service {SEUIL_SERVICE}, seuil autre {SEUIL_AUTRE}")
    print(pd.Series(retenu).round(3).to_string())

    if not args.final:
        print("\nEffet d'un seuil unique")
        print(tableau_seuils(vrai, predit, confiance).to_string())
        print(f"\nEffet du paramètre C (seuil unique fixé à {SEUIL_BALAYAGE})")
        print(balayage_c(entrainement, test).to_string())

    erreurs = test[predit != vrai].assign(predit=predit[predit != vrai])
    if len(erreurs):
        print("\nPhrases mal classées :")
        print(erreurs.to_string(index=False))


if __name__ == "__main__":
    main()