"""Explication d'un score : contribution de chaque variable (valeurs de Shapley, TreeSHAP natif de XGBoost).

Les contributions sont exprimées en log-odds : positives, elles augmentent le risque ; négatives, elles le
diminuent. Les colonnes encodées (one-hot) sont regroupées par variable d'origine.
"""
import xgboost as xgb

LIBELLES = {
    "CNT_CHILDREN": "Nombre d'enfants",
    "CNT_FAM_MEMBERS": "Taille du ménage",
    "age_ans": "Âge",
    "anciennete_emploi_ans": "Ancienneté dans l'activité",
    "sans_emploi": "Sans activité déclarée",
    "credit_sur_revenu": "Montant demandé / revenu mensuel",
    "annuite_sur_revenu": "Mensualité / revenu mensuel",
    "duree_implicite": "Durée du crédit",
    "NAME_INCOME_TYPE": "Type de revenu",
    "NAME_FAMILY_STATUS": "Situation familiale",
    "NAME_HOUSING_TYPE": "Logement",
    "OCCUPATION_TYPE": "Profession",
    "FLAG_OWN_REALTY": "Bien immobilier",
    "FLAG_OWN_CAR": "Véhicule",
}


def _valeur_lisible(variable: str, ligne: dict, demande=None) -> str | None:
    """Valeur affichable pour les variables numériques (les catégories viennent de la fiche client)."""
    v = ligne.get(variable)
    if v is None:
        return None
    if variable == "age_ans":
        return f"{int(v)} ans"
    if variable == "anciennete_emploi_ans":
        return f"{v:.1f} an(s)".replace(".", ",")
    if variable == "annuite_sur_revenu":
        return f"{v * 100:.0f} %"
    if variable == "credit_sur_revenu":
        return f"{v:.1f} × le revenu".replace(".", ",")
    if variable == "duree_implicite" and demande is not None:
        return f"{demande.duree_mois} mois"
    if variable in ("CNT_CHILDREN", "CNT_FAM_MEMBERS"):
        return str(int(v))
    return None


def contributions(modele, ligne_df, demande=None, nombre: int = 6) -> list[dict]:
    """Les `nombre` variables qui pèsent le plus sur le score de ce dossier, de la plus forte à la plus faible."""
    prep = modele.named_steps["prep"]
    booster = modele.named_steps["clf"].get_booster()
    valeurs = booster.predict(xgb.DMatrix(prep.transform(ligne_df)), pred_contribs=True)[0][:-1]

    noms = prep.get_feature_names_out()
    cat = sorted(next(colonnes for nom, _, colonnes in prep.transformers_ if nom == "cat"), key=len, reverse=True)
    totaux: dict[str, float] = {}
    for nom, valeur in zip(noms, valeurs):
        brut = nom.split("__", 1)[1]
        origine = brut if nom.startswith("num__") else next(c for c in cat if brut.startswith(c + "_"))
        totaux[origine] = totaux.get(origine, 0.0) + float(valeur)

    ligne = ligne_df.iloc[0].to_dict()
    tries = sorted(totaux.items(), key=lambda kv: abs(kv[1]), reverse=True)[:nombre]
    return [{"variable": var, "libelle": LIBELLES.get(var, var), "contribution": round(val, 4),
             "valeur": _valeur_lisible(var, ligne, demande)} for var, val in tries]
