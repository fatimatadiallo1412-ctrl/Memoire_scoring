"""Comparaison champion / challenger sur un découpage HORS PÉRIODE.

Les challengers sont ajustés sur les crédits décaissés avant la date de coupure. Tous les modèles
sont ensuite évalués sur les crédits décaissés APRÈS, comme en production réelle. Les variables
d'entrée de chaque dossier étant conservées (ml.score), l'évaluation rejoue l'historique à
l'identique : c'est un fonctionnement « en parallèle » sans risque pour les clients.

Challengers construits automatiquement :
  recalibre    arbres du champion + recalibration sur les données locales
  reentraine   arbres ajoutés sur les données locales, puis recalibration
               (tenté seulement à partir de MIN_DEFAUTS_REENTRAINEMENT défauts, sauf --forcer)
On peut aussi comparer une version enregistrée : --challenger <version>.

Règle de promotion (toutes les conditions) :
  - au moins MIN_DEFAUTS_EVALUATION défauts dans la période d'évaluation ;
  - Brier score meilleur que celui du champion (probabilités plus justes) ;
  - AUC pas inférieure de plus de TOLERANCE_AUC (classement au moins aussi bon) ;
  - écart hommes / femmes de la part des dossiers au-dessus du seuil pas accru de plus de
    TOLERANCE_EQUITE.
La promotion reste une décision humaine : le script propose, la direction valide, puis on
renseigne MODELE_VERSION dans .env.

    python -m src.champion_challenger --jour 2026-11-06
    python -m src.champion_challenger --jour 2026-11-06 --enregistrer   # enregistre le gagnant
"""
import argparse
import json
from datetime import date

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score

from src.modeling import COLONNES, RACINE
from src.recalibration import continuer_entrainement, recalibrer

MIN_DEFAUTS_EVALUATION = 30
MIN_DEFAUTS_REENTRAINEMENT = 200
TOLERANCE_AUC = 0.01
TOLERANCE_EQUITE = 0.02
PART_APPRENTISSAGE = 0.7


def ks(y, p) -> float:
    ordre = np.argsort(p)
    y = np.asarray(y)[ordre]
    cum_bons = np.cumsum(1 - y) / max((1 - y).sum(), 1)
    cum_mauvais = np.cumsum(y) / max(y.sum(), 1)
    return float(np.max(np.abs(cum_bons - cum_mauvais)))


def mesurer(p, y, sexe, seuil) -> dict:
    y = np.asarray(y, dtype=int)
    m = {"n": int(len(y)), "n_defauts": int(y.sum()), "taux_observe": float(y.mean()),
         "taux_prevu": float(np.mean(p)), "brier": float(brier_score_loss(y, p)),
         "logloss": float(log_loss(y, np.clip(p, 1e-6, 1 - 1e-6), labels=[0, 1]))}
    if 0 < y.sum() < len(y):
        m.update(auc=float(roc_auc_score(y, p)), pr_auc=float(average_precision_score(y, p)),
                 ks=ks(y, p))
    au_dessus = pd.Series(np.asarray(p) > seuil).groupby(np.asarray(sexe)).mean()
    m["au_dessus_seuil"] = {str(k): float(v) for k, v in au_dessus.items()}
    m["ecart_equite"] = (float(abs(au_dessus.get("M", 0) - au_dessus.get("F", 0)))
                         if {"M", "F"} <= set(au_dessus.index) else None)
    return m


def decouper(df: pd.DataFrame, coupure: date | None):
    df = df.sort_values("date_decaissement")
    if coupure is None:
        coupure = df["date_decaissement"].iloc[int(len(df) * PART_APPRENTISSAGE)]
    return df[df["date_decaissement"] < coupure], df[df["date_decaissement"] >= coupure], coupure


def verdict(champion: dict, challenger: dict) -> tuple[bool, list[str]]:
    raisons = []
    if challenger["n_defauts"] < MIN_DEFAUTS_EVALUATION:
        return False, [f"{challenger['n_defauts']} défauts dans la période d'évaluation : "
                       f"au moins {MIN_DEFAUTS_EVALUATION} sont nécessaires pour conclure"]
    ok = True
    if challenger["brier"] >= champion["brier"]:
        ok = False
        raisons.append("Brier pas meilleur que le champion")
    if "auc" in challenger and "auc" in champion and challenger["auc"] < champion["auc"] - TOLERANCE_AUC:
        ok = False
        raisons.append(f"AUC en baisse de plus de {TOLERANCE_AUC}")
    if (challenger["ecart_equite"] is not None and champion["ecart_equite"] is not None
            and challenger["ecart_equite"] > champion["ecart_equite"] + TOLERANCE_EQUITE):
        ok = False
        raisons.append(f"écart hommes / femmes accru de plus de {TOLERANCE_EQUITE * 100:.0f} points")
    if ok:
        raisons.append("toutes les conditions de promotion sont remplies")
    return ok, raisons


def comparer(df: pd.DataFrame, champion, seuil: float, coupure=None, forcer=False,
             autres: dict | None = None) -> dict:
    app, ev = decouper(df, coupure)[:2]
    coupure = decouper(df, coupure)[2]
    y_app, y_ev = app["defaut"].astype(int), ev["defaut"].astype(int)

    modeles = {"champion": champion}
    notes = {}
    if y_app.sum() > 0:
        modeles["recalibre"] = recalibrer(champion, app, y_app)
        notes["recalibre"] = modeles["recalibre"].calibrateur_.description()
    if y_app.sum() >= MIN_DEFAUTS_REENTRAINEMENT or (forcer and y_app.sum() > 0):
        continue_ = continuer_entrainement(champion, app, y_app)
        modeles["reentraine"] = recalibrer(continue_, app, y_app)
        notes["reentraine"] = "100 arbres ajoutés ; " + modeles["reentraine"].calibrateur_.description()
    else:
        notes["reentraine"] = (f"non tenté : {int(y_app.sum())} défauts en apprentissage, "
                               f"{MIN_DEFAUTS_REENTRAINEMENT} requis")
    modeles.update(autres or {})

    resultats = {nom: mesurer(m.predict_proba(ev[COLONNES])[:, 1], y_ev, ev["sexe"], seuil)
                 for nom, m in modeles.items()}
    decisions = {nom: verdict(resultats["champion"], r)
                 for nom, r in resultats.items() if nom != "champion"}
    gagnants = [n for n, (ok, _) in decisions.items() if ok]
    meilleur = min(gagnants, key=lambda n: resultats[n]["brier"]) if gagnants else None
    return {"coupure": str(coupure), "n_apprentissage": int(len(app)),
            "defauts_apprentissage": int(y_app.sum()), "n_evaluation": int(len(ev)),
            "seuil": seuil, "resultats": resultats, "notes": notes,
            "verdicts": {n: {"promouvable": ok, "raisons": r} for n, (ok, r) in decisions.items()},
            "proposition": meilleur}


def fmt(v, chiffres=4):
    return "–" if v is None else f"{v:.{chiffres}f}"


def en_markdown(c: dict, version: str) -> str:
    l = [f"# Champion / challenger — champion : {version}", "",
         f"Coupure hors période : {c['coupure']} · apprentissage {c['n_apprentissage']} crédits "
         f"({c['defauts_apprentissage']} défauts) · évaluation {c['n_evaluation']} crédits · "
         f"seuil {c['seuil']}", "",
         "| Modèle | Défauts | Prévu | Observé | AUC | KS | Brier | Écart H/F > seuil |",
         "|---|---|---|---|---|---|---|---|"]
    for nom, r in c["resultats"].items():
        l.append(f"| {nom} | {r['n_defauts']} | {r['taux_prevu']:.3f} | {r['taux_observe']:.3f} | "
                 f"{fmt(r.get('auc'), 3)} | {fmt(r.get('ks'), 3)} | {r['brier']:.4f} | "
                 f"{fmt(r['ecart_equite'], 3)} |")
    l += ["", "## Challengers"]
    for nom, note in c["notes"].items():
        l.append(f"- **{nom}** : {note}")
    for nom, v in c["verdicts"].items():
        l.append(f"- {nom} {'promouvable' if v['promouvable'] else 'non promouvable'} : "
                 + " ; ".join(v["raisons"]))
    l += ["", f"**Proposition : {c['proposition'] or 'garder le champion'}**"]
    return "\n".join(l) + "\n"


def main():
    from app.db import SessionLocal
    from app.parametres import lire_parametres
    from app.scoring import VERSION_MODELE, charger_modele
    from src import registre
    from src.donnees_locales import construire

    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("--jour", type=date.fromisoformat, default=date.today())
    parseur.add_argument("--coupure", type=date.fromisoformat)
    parseur.add_argument("--challenger", action="append", default=[],
                         help="version enregistrée à comparer (répétable)")
    parseur.add_argument("--forcer", action="store_true",
                         help="tenter le réentraînement même avec peu de défauts (démonstration)")
    parseur.add_argument("--enregistrer", action="store_true",
                         help="ré-ajuster le gagnant sur toutes les données mûres et l'enregistrer")
    args = parseur.parse_args()

    with SessionLocal() as s:
        df = construire(s, args.jour)
        seuil = float(lire_parametres(s)["seuil_defaut"])
    champion = charger_modele()
    autres = {v: registre.charger(v) for v in args.challenger}
    c = comparer(df, champion, seuil, args.coupure, args.forcer, autres)

    texte = en_markdown(c, VERSION_MODELE)
    print(texte)
    dossier = RACINE / "docs" / "suivi_modele"
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / f"champion_challenger_{args.jour}.md").write_text(texte, encoding="utf-8")
    (dossier / f"champion_challenger_{args.jour}.json").write_text(
        json.dumps(c, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    if args.enregistrer:
        nom = c["proposition"]
        if nom not in ("recalibre", "reentraine"):
            print("Aucun challenger construit n'est promouvable : rien n'est enregistré.")
            return
        y = df["defaut"].astype(int)
        modele = continuer_entrainement(champion, df, y) if nom == "reentraine" else champion
        modele = recalibrer(modele, df, y)
        version = f"{VERSION_MODELE}_{nom}_{args.jour:%Y%m%d}"
        registre.enregistrer(modele, {
            "version": version, "parent": VERSION_MODELE,
            "type": f"{nom} sur données locales ({modele.calibrateur_.description()})",
            "donnees": f"{len(df)} crédits locaux mûrs au {args.jour} ({int(y.sum())} défauts)",
            "performances": {k: c["resultats"][nom].get(k) for k in
                             ("auc", "ks", "brier", "taux_observe", "taux_prevu")}
                            | {"AUC": c["resultats"][nom].get("auc"),
                               "echantillon": f"hors période après le {c['coupure']}"},
            "equite": {"au_dessus_seuil": c["resultats"][nom]["au_dessus_seuil"]},
            "validation": "champion / challenger hors période ; promotion à valider par la direction",
        })
        print(f"Enregistré : models/{version}.joblib. Pour le mettre en service après validation :"
              f"\n  MODELE_VERSION={version}   (dans .env, puis redémarrer l'API)")


if __name__ == "__main__":
    main()
