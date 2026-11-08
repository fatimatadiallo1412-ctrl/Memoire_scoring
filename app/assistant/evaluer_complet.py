"""Évaluation du pipeline complet tel qu'il est déployé : politesse + découpage + classifieur.

Une étiquette peut contenir plusieurs intentions séparées par « + » (ordre indifférent).
Usage : python -m app.assistant.evaluer_complet [--fichier data/assistant/phrases_test.csv]
"""
import argparse

import pandas as pd

from app.assistant.classifieur import SERVICES
from app.assistant.evaluer import FICHIER_TEST
from app.assistant.politesse import analyser


def ensemble(etiquette: str) -> frozenset:
    return frozenset(etiquette.split("+"))


def main():
    analyse = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analyse.add_argument("--fichier", default=str(FICHIER_TEST))
    args = analyse.parse_args()

    pd.set_option("display.width", 170)
    pd.set_option("display.max_colwidth", 80)
    test = pd.read_csv(args.fichier, sep=";", encoding="utf-8")
    test["final"] = ["+".join(i for i, _ in analyser(p)[0]) for p in test["phrase"]]

    lignes = []
    for _, ligne in test.iterrows():
        vrai, final = ensemble(ligne["intention"]), ensemble(ligne["final"])
        hors = vrai == {"hors_sujet"}
        rejete = final == {"non_compris"}
        lignes.append({
            "dans": not hors,
            "bonne": (not hors) and final == vrai,
            "partielle": (not hors) and final < vrai and not rejete,   # une question sur deux
            "rejete": (not hors) and rejete,
            "erronee": (not hors) and not rejete and not final <= vrai,
            "hors_ecarte": hors and rejete,
            "donnee_erronee": bool((final & SERVICES) - vrai),
        })
    res = pd.DataFrame(lignes)
    dans = res["dans"].sum()
    hors_n = (~res["dans"]).sum()

    print(f"Pipeline complet : {len(test)} phrases ({args.fichier})")
    print(f"  bonne réponse (toutes les questions) : {res['bonne'].sum() / dans:.3f}")
    print(f"  réponse partielle (une question sur deux) : {res['partielle'].sum() / dans:.3f}")
    print(f"  non compris                          : {res['rejete'].sum() / dans:.3f}")
    print(f"  réponse erronée                      : {res['erronee'].sum() / dans:.3f}")
    print(f"  hors-sujet écarté                    : {res['hors_ecarte'].sum() / max(hors_n, 1):.3f}")
    print(f"  données erronées (nb)                : {int(res['donnee_erronee'].sum())}")

    ko = test[~(res["bonne"] | res["hors_ecarte"])]
    if len(ko):
        print("\nPhrases où la réponse finale diffère de l'étiquette :")
        print(ko[["intention", "phrase", "final"]].to_string(index=False))


if __name__ == "__main__":
    main()