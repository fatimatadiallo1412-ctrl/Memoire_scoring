"""Audit d'inclusion : le modèle exclut-il des profils à revenu informel ?

Même demande type pour tout le monde (3 mois de revenu, 12 mois, produit MICRO à 24 %),
scorée par la fonction réelle de l'application avec la politique par défaut.
Les écarts observés ne peuvent donc venir que du PROFIL du client.
"""
from types import SimpleNamespace

import pandas as pd

from app.scoring import evaluer_dossier
from simulation.profils import DATE_REFERENCE, generer_profils
from src.modeling import RACINE

N_PROFILS = 2000
PARAMETRES = {"seuil_defaut": 0.15, "endettement_max": 0.40,
              "ratio_min": 0.50, "pas_montant": 10_000}
PRODUIT = SimpleNamespace(taux_annuel=24.0, montant_min=50_000, montant_max=1_000_000)
DUREE_MOIS = 12
MOIS_DE_REVENU = 3          # montant demandé = 3 × revenu mensuel (dans les limites du produit)


def scorer_profils() -> pd.DataFrame:
    lignes = []
    for p in generer_profils(N_PROFILS):
        montant = round(MOIS_DE_REVENU * p["revenu_mensuel"] / 10_000) * 10_000
        montant = int(min(max(montant, PRODUIT.montant_min), PRODUIT.montant_max))
        demande = SimpleNamespace(date_demande=DATE_REFERENCE,
                                  montant_demande=montant, duree_mois=DUREE_MOIS)
        reco, _ = evaluer_dossier(SimpleNamespace(**p), demande, PRODUIT, PARAMETRES)
        lignes.append({**p, "montant_demande": montant, "decision": reco["decision"],
                       "p_demande": reco["p_demande"],
                       "endettement": reco["endettement_demande"]})
    df = pd.DataFrame(lignes)
    df["accord"] = df["decision"] == "accord"
    df["reduit"] = df["decision"] == "accord_reduit"
    df["refus"] = df["decision"] == "refus"
    df["quartile_revenu"] = pd.qcut(df["revenu_mensuel"], 4,
                                    labels=["Q1 (bas)", "Q2", "Q3", "Q4 (haut)"])
    df["tranche_anciennete"] = pd.cut(
        df["anciennete_activite_mois"], [-1, 11, 35, 71, 10_000],
        labels=["< 1 an", "1 à 3 ans", "3 à 6 ans", "6 ans et +"])
    return df


def resume(df: pd.DataFrame, par: str, n_min: int = 30) -> pd.DataFrame:
    t = df.groupby(par, observed=True).agg(
        n=("decision", "size"), accord=("accord", "mean"), reduit=("reduit", "mean"),
        refus=("refus", "mean"), p_defaut_moy=("p_demande", "mean"))
    t[["accord", "reduit", "refus"]] = (t[["accord", "reduit", "refus"]] * 100).round(1)
    t["p_defaut_moy"] = (t["p_defaut_moy"] * 100).round(1)
    return t[t["n"] >= n_min]


if __name__ == "__main__":
    df = scorer_profils()
    print(f"{len(df)} profils scorés – % accord / accord réduit / refus, "
          f"probabilité de défaut moyenne (%)\n")
    print("GLOBAL\n", resume(df.assign(tous="tous"), "tous"), "\n")
    for critere in ["type_revenu", "profession", "sexe", "tranche_anciennete",
                    "quartile_revenu"]:
        print(f"PAR {critere.upper()}\n", resume(df, critere), "\n")

    # Comparaison à revenu égal : % de refus par quartile de revenu et type d'activité
    types = df[df["type_revenu"] != "retraite"]
    print("% DE REFUS – quartile de revenu × type d'activité (n ≥ 15 par case)")
    refus = types.pivot_table(index="quartile_revenu", columns="type_revenu",
                              values="refus", aggfunc="mean", observed=True) * 100
    effectifs = types.pivot_table(index="quartile_revenu", columns="type_revenu",
                                  values="refus", aggfunc="size", observed=True)
    print(refus.where(effectifs >= 15).round(1), "\n")
    print("Effectifs correspondants\n", effectifs, "\n")

    sortie = RACINE / "data" / "processed" / "audit_inclusion_profils.csv"
    df.drop(columns=["accord", "reduit", "refus"]).to_csv(sortie, index=False)
    print("Détail enregistré :", sortie)