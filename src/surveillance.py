"""Suivi du modèle en production : stabilité (sans attendre les remboursements) et performance
(sur les crédits arrivés à maturité). Produit un rapport daté avec un niveau d'alerte par indicateur.

    # 1. Une fois, après quelques mois de production : figer la population de référence
    python -m src.surveillance figer-reference --debut 2025-01-01 --fin 2025-06-30
    # 2. Chaque mois (le planificateur le fait le 1er du mois) : rapport du mois écoulé
    python -m src.surveillance rapport --debut 2026-10-01 --fin 2026-10-31

Indicateurs
  Stabilité   PSI des scores et de chaque variable, part des modalités inconnues du modèle
  Décisions   taux d'acceptation, taux de dérogation (décision contraire à la recommandation)
  Performance AUC, calibration (défaut prévu / observé) des crédits mûrs des 12 derniers mois
"""
import argparse
import json
from datetime import date, timedelta

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score
from sqlalchemy import select

from src.modeling import CAT, COLONNES, NUM, RACINE

# ---- Seuils d'alerte (usage courant en scoring ; à valider par la direction des risques) ------
PSI_ORANGE, PSI_ROUGE = 0.10, 0.25
INCONNUES_ORANGE, INCONNUES_ROUGE = 0.05, 0.15     # part des dossiers avec une modalité inconnue
DEROGATION_ORANGE, DEROGATION_ROUGE = 0.15, 0.25
BAISSE_AUC_ORANGE, BAISSE_AUC_ROUGE = 0.03, 0.05
CALIBRATION_ORANGE, CALIBRATION_ROUGE = 1.25, 1.50  # rapport observé / prévu (ou son inverse)
MIN_DEFAUTS_PERFORMANCE = 30                        # en dessous, la performance n'est pas jugée

DOSSIER_RAPPORTS = RACINE / "docs" / "suivi_modele"
EPS = 1e-4
NIVEAUX = ["vert", "orange", "rouge"]


# ---- Population Stability Index ------------------------------------------------------------

def bornes_quantiles(valeurs, n=10) -> list[float]:
    """Bornes intérieures des classes (déciles), sans doublon."""
    q = np.nanquantile(np.asarray(valeurs, dtype=float), np.linspace(0, 1, n + 1)[1:-1])
    return sorted(set(float(x) for x in q))


def repartition_numerique(valeurs, bornes) -> list[float]:
    """Part de chaque classe ; la dernière case compte les valeurs manquantes."""
    v = np.asarray(valeurs, dtype=float)
    manquants = np.isnan(v)
    classes = np.digitize(v[~manquants], bornes)
    comptes = np.bincount(classes, minlength=len(bornes) + 1).tolist() + [int(manquants.sum())]
    total = max(len(v), 1)
    return [c / total for c in comptes]


def repartition_categorielle(valeurs, modalites) -> dict[str, float]:
    s = pd.Series(valeurs).fillna("(vide)").astype(str)
    parts = s.value_counts(normalize=True)
    res = {m: float(parts.get(m, 0.0)) for m in modalites}
    res["(autre)"] = float(parts[~parts.index.isin(modalites)].sum())
    return res


def psi(reference, actuelle) -> float:
    r = np.clip(np.asarray(reference, dtype=float), EPS, None)
    a = np.clip(np.asarray(actuelle, dtype=float), EPS, None)
    return float(np.sum((a - r) * np.log(a / r)))


def bruit_psi(n_classes: int, n_reference: int, n_actuel: int) -> float:
    """PSI attendu par le seul hasard de l'échantillonnage, sans aucune dérive :
    environ (classes - 1) x (1/n_ref + 1/n_act). Sur un petit mois (130 dossiers), il atteint
    déjà 0,08 : on juge donc l'excès de PSI au-delà de ce bruit."""
    return (n_classes - 1) * (1 / max(n_reference, 1) + 1 / max(n_actuel, 1))


def niveau(valeur, orange, rouge) -> str:
    if valeur is None or (isinstance(valeur, float) and np.isnan(valeur)):
        return "n/a"
    return "rouge" if valeur >= rouge else "orange" if valeur >= orange else "vert"


# ---- Référence ------------------------------------------------------------------------------

def construire_reference(X: pd.DataFrame, scores, description: str) -> dict:
    ref = {"description": description, "n": int(len(X)),
           "score": {"bornes": bornes_quantiles(scores)}, "variables": {}}
    ref["score"]["parts"] = repartition_numerique(scores, ref["score"]["bornes"])
    for c in NUM:
        bornes = bornes_quantiles(X[c])
        ref["variables"][c] = {"type": "num", "bornes": bornes,
                               "parts": repartition_numerique(X[c], bornes)}
    for c in CAT:
        modalites = sorted(X[c].fillna("(vide)").astype(str).unique().tolist())
        ref["variables"][c] = {"type": "cat", "parts": repartition_categorielle(X[c], modalites)}
    return ref


def comparer(reference: dict, X: pd.DataFrame, scores) -> dict:
    """PSI bruts et PSI en excès du bruit d'échantillonnage (c'est l'excès qui déclenche l'alerte)."""
    n_ref, n_act = reference["n"], len(X)
    res = {"score": psi(reference["score"]["parts"],
                        repartition_numerique(scores, reference["score"]["bornes"])),
           "variables": {}, "exces": {}}
    res["exces"]["score"] = max(
        res["score"] - bruit_psi(len(reference["score"]["parts"]), n_ref, n_act), 0.0)
    for c, r in reference["variables"].items():
        if r["type"] == "num":
            actuelle = repartition_numerique(X[c], r["bornes"])
            res["variables"][c] = psi(r["parts"], actuelle)
        else:
            modalites = [m for m in r["parts"] if m != "(autre)"]
            actuelle = repartition_categorielle(X[c], modalites)
            res["variables"][c] = psi([r["parts"][m] for m in actuelle],
                                      list(actuelle.values()))
        k = len(r["parts"])
        res["exces"][c] = max(res["variables"][c] - bruit_psi(k, n_ref, n_act), 0.0)
    return res


def chemin_reference(version: str):
    return RACINE / "models" / f"reference_{version}.json"


# ---- Modalités inconnues du modèle ---------------------------------------------------------

def modalites_inconnues(modele, X: pd.DataFrame) -> dict:
    """Le OneHotEncoder ignore en silence une modalité absente de l'entraînement : le dossier est
    alors scoré comme s'il n'avait pas de valeur. On compte ces cas, variable par variable."""
    encodeur = modele.named_steps["prep"].named_transformers_["cat"]
    parts, exemples = {}, {}
    masque_total = np.zeros(len(X), dtype=bool)
    for c, connues in zip(CAT, encodeur.categories_):
        inconnu = ~X[c].astype(str).isin(set(map(str, connues)))
        masque_total |= inconnu.to_numpy()
        parts[c] = float(inconnu.mean()) if len(X) else 0.0
        if inconnu.any():
            exemples[c] = X.loc[inconnu, c].astype(str).value_counts().head(5).to_dict()
    return {"part_dossiers": float(masque_total.mean()) if len(X) else 0.0,
            "par_variable": parts, "exemples": exemples}


# ---- Lecture de la production --------------------------------------------------------------

def scores_periode(session, debut: date, fin: date) -> pd.DataFrame:
    """Dernier score de chaque dossier scoré dans la période, avec ses variables d'entrée."""
    from app.models import Score
    lignes = session.execute(
        select(Score.demande_id, Score.variables_entree, Score.calcule_le)
        .where(Score.calcule_le >= debut, Score.calcule_le < fin + timedelta(days=1))
        .order_by(Score.calcule_le)).all()
    derniers = {d: v for d, v, _ in lignes}
    if not derniers:
        return pd.DataFrame(columns=["demande_id", *COLONNES])
    df = pd.DataFrame([{"demande_id": d, **v} for d, v in derniers.items()])
    return df[["demande_id", *COLONNES]]


def decisions_periode(session, debut: date, fin: date) -> dict:
    from app.models import Decision
    decisions = session.scalars(
        select(Decision).where(Decision.decide_le >= debut,
                               Decision.decide_le < fin + timedelta(days=1))).all()
    finales = [d for d in decisions if d.decision in ("accorder", "accorder_modifie", "refuser")]
    n = len(finales)
    if not n:
        return {"n": 0}
    accords = sum(d.decision != "refuser" for d in finales)
    avec_reco = [d for d in finales if d.concordance is not None]
    derog = [d for d in avec_reco if d.concordance is False]
    sens = pd.Series([f"{d.recommandation_modele} -> {getattr(d.decision, 'value', d.decision)}"
                      for d in derog]).value_counts()
    return {"n": n, "taux_acceptation": accords / n,
            "taux_derogation": len(derog) / len(avec_reco) if avec_reco else None,
            "derogations_par_sens": sens.to_dict()}


# ---- Performance ---------------------------------------------------------------------------

def calibration_par_classe(p, y, n_classes=5) -> list[dict]:
    df = pd.DataFrame({"p": p, "y": y})
    df["classe"] = pd.qcut(df["p"].rank(method="first"), min(n_classes, len(df)), labels=False)
    return [{"classe": int(k), "n": int(len(g)), "prevu": float(g["p"].mean()),
             "observe": float(g["y"].mean())} for k, g in df.groupby("classe")]


def performance(modele, credits: pd.DataFrame, auc_reference: float | None) -> dict:
    """credits : sortie de src.donnees_locales.construire (crédits mûrs)."""
    if credits.empty:
        return {"n": 0, "verdict": "aucun crédit mûr"}
    y = credits["defaut"].astype(int).to_numpy()
    p = modele.predict_proba(credits[COLONNES])[:, 1]
    res = {"n": int(len(y)), "n_defauts": int(y.sum()), "taux_observe": float(y.mean()),
           "taux_prevu": float(p.mean()), "brier": float(brier_score_loss(y, p)),
           "calibration": calibration_par_classe(p, y)}
    rapport = res["taux_observe"] / max(res["taux_prevu"], EPS)
    res["rapport_observe_prevu"] = rapport
    if y.sum() < MIN_DEFAUTS_PERFORMANCE or y.sum() == len(y):
        res["verdict"] = (f"{int(y.sum())} défauts observés : moins de {MIN_DEFAUTS_PERFORMANCE}, "
                          "performance non jugée (trop peu de recul)")
        res["niveau_calibration"] = res["niveau_auc"] = "n/a"
        return res
    res["auc"] = float(roc_auc_score(y, p))
    ecart = max(rapport, 1 / max(rapport, EPS))
    res["niveau_calibration"] = niveau(ecart, CALIBRATION_ORANGE, CALIBRATION_ROUGE)
    if auc_reference:
        res["baisse_auc"] = auc_reference - res["auc"]
        res["niveau_auc"] = niveau(res["baisse_auc"], BAISSE_AUC_ORANGE, BAISSE_AUC_ROUGE)
    else:
        res["niveau_auc"] = "n/a"
    return res


# ---- Rapport -------------------------------------------------------------------------------

ACTIONS = {
    "vert": "Aucune action : le modèle reste en service tel quel.",
    "orange": "Analyser les indicateurs en orange avec la direction des risques ; "
              "préparer une recalibration si la situation persiste deux mois de suite.",
    "rouge": "Lancer la comparaison champion / challenger (python -m src.champion_challenger) "
             "et, si les données le permettent, recalibrer ou réentraîner. "
             "Renforcer la revue humaine des dossiers en attendant.",
}


def produire_rapport(session, debut: date, fin: date, jour: date | None = None) -> dict:
    from app.scoring import VERSION_MODELE, charger_modele
    from src.donnees_locales import construire
    from src.registre import lire_fiche

    jour = jour or fin
    modele = charger_modele()
    fiche = lire_fiche(VERSION_MODELE)
    rapport = {"version_modele": VERSION_MODELE, "periode": [debut.isoformat(), fin.isoformat()],
               "produit_le": date.today().isoformat(), "alertes": {}}

    X = scores_periode(session, debut, fin)
    rapport["dossiers_scores"] = int(len(X))
    if len(X):
        p = modele.predict_proba(X[COLONNES])[:, 1]
        rapport["score_moyen"] = float(p.mean())
        ref_chemin = chemin_reference(VERSION_MODELE)
        if ref_chemin.exists():
            ref = json.loads(ref_chemin.read_text(encoding="utf-8"))
            stab = comparer(ref, X, p)
            rapport["reference"] = ref["description"]
            rapport["psi"] = stab
            rapport["alertes"]["psi_score"] = niveau(stab["exces"]["score"], PSI_ORANGE, PSI_ROUGE)
            pire = max(((c, v) for c, v in stab["exces"].items() if c != "score"),
                       key=lambda kv: kv[1])
            rapport["alertes"]["psi_variables"] = niveau(pire[1], PSI_ORANGE, PSI_ROUGE)
            rapport["psi_variable_max"] = {"variable": pire[0], "exces_psi": pire[1]}
        else:
            rapport["reference"] = ("aucune : lancer `python -m src.surveillance figer-reference` "
                                    "sur les premiers mois de production")
        inconnues = modalites_inconnues(modele, X)
        rapport["modalites_inconnues"] = inconnues
        rapport["alertes"]["modalites_inconnues"] = niveau(
            inconnues["part_dossiers"], INCONNUES_ORANGE, INCONNUES_ROUGE)

    dec = decisions_periode(session, debut, fin)
    rapport["decisions"] = dec
    if dec.get("taux_derogation") is not None:
        rapport["alertes"]["derogations"] = niveau(
            dec["taux_derogation"], DEROGATION_ORANGE, DEROGATION_ROUGE)

    # Performance : crédits dont la fenêtre d'observation s'est terminée dans les 12 derniers mois
    credits = construire(session, jour)
    if not credits.empty:
        credits = credits[credits["fin_observation"] > jour - timedelta(days=365)]
    perf = performance(modele, credits, fiche.get("performances", {}).get("AUC"))
    rapport["performance"] = perf
    rapport["alertes"]["calibration"] = perf.get("niveau_calibration", "n/a")
    rapport["alertes"]["auc"] = perf.get("niveau_auc", "n/a")

    jugees = [n for n in rapport["alertes"].values() if n in NIVEAUX]
    rapport["niveau_global"] = max(jugees, key=NIVEAUX.index) if jugees else "n/a"
    rapport["action"] = ACTIONS.get(rapport["niveau_global"], "Données insuffisantes.")
    return rapport


def pct(x):
    return "–" if x is None else f"{100 * x:.1f} %"


def en_markdown(r: dict) -> str:
    l = [f"# Suivi du modèle {r['version_modele']}",
         f"Période : du {r['periode'][0]} au {r['periode'][1]} · produit le {r['produit_le']}", "",
         f"**Niveau global : {r['niveau_global'].upper()}** — {r['action']}", "",
         "| Indicateur | Niveau |", "|---|---|"]
    l += [f"| {k} | {v} |" for k, v in r["alertes"].items()]
    l += ["", "## Stabilité", f"Dossiers scorés : {r['dossiers_scores']}",
          f"Référence : {r.get('reference', '–')}"]
    if "psi" in r:
        ex = r["psi"]["exces"]
        l += [f"PSI des scores : {r['psi']['score']:.3f} (excès sur le bruit : {ex['score']:.3f})",
              "", "Seul l'excès au-delà du bruit d'échantillonnage déclenche une alerte "
              f"(orange ≥ {PSI_ORANGE}, rouge ≥ {PSI_ROUGE}).", "",
              "| Variable | PSI | Excès |", "|---|---|---|"]
        l += [f"| {k} | {v:.3f} | {ex[k]:.3f} |" for k, v in
              sorted(r["psi"]["variables"].items(), key=lambda kv: -ex[kv[0]])]
    if "modalites_inconnues" in r:
        mi = r["modalites_inconnues"]
        l += ["", f"Dossiers avec une modalité inconnue du modèle : {pct(mi['part_dossiers'])}"]
        l += [f"- {c} : {ex}" for c, ex in mi["exemples"].items()]
    d = r["decisions"]
    l += ["", "## Décisions", f"Décisions : {d['n']}"]
    if d["n"]:
        l += [f"Taux d'acceptation : {pct(d['taux_acceptation'])}",
              f"Taux de dérogation : {pct(d['taux_derogation'])}"]
        l += [f"- {k} : {v}" for k, v in d["derogations_par_sens"].items()]
    p = r["performance"]
    l += ["", "## Performance (crédits mûrs, 12 derniers mois)", f"Crédits : {p['n']}"]
    if p["n"]:
        l += [f"Défauts : {p['n_defauts']} · observé {pct(p['taux_observe'])} · "
              f"prévu {pct(p['taux_prevu'])} · Brier {p['brier']:.4f}"]
        if "auc" in p:
            l += [f"AUC : {p['auc']:.3f}" + (f" (baisse {p['baisse_auc']:+.3f} par rapport à la fiche)"
                                             if "baisse_auc" in p else "")]
        if "verdict" in p:
            l += [p["verdict"]]
        l += ["", "| Classe de risque | n | Prévu | Observé |", "|---|---|---|---|"]
        l += [f"| {c['classe'] + 1} | {c['n']} | {pct(c['prevu'])} | {pct(c['observe'])} |"
              for c in p["calibration"]]
    return "\n".join(l) + "\n"


def ecrire_rapport(r: dict) -> str:
    DOSSIER_RAPPORTS.mkdir(parents=True, exist_ok=True)
    base = DOSSIER_RAPPORTS / f"suivi_{r['periode'][1]}"
    base.with_suffix(".json").write_text(json.dumps(r, ensure_ascii=False, indent=2, default=str),
                                         encoding="utf-8")
    base.with_suffix(".md").write_text(en_markdown(r), encoding="utf-8")
    return str(base.with_suffix(".md"))


def enregistrer_en_base(session, r: dict, utilisateur_id: int | None = None):
    """Conserve le rapport dans ml.rapport_suivi (page « Santé du modèle » de l'administrateur)."""
    from app.models import RapportSuivi
    rapport = RapportSuivi(
        version_modele=r["version_modele"], debut=date.fromisoformat(r["periode"][0]),
        fin=date.fromisoformat(r["periode"][1]), niveau_global=r["niveau_global"],
        contenu=json.loads(json.dumps(r, default=str)), produit_par=utilisateur_id)
    session.add(rapport)
    session.commit()
    session.refresh(rapport)
    return rapport


def trimestre_ecoule(jour: date) -> tuple[date, date]:
    """Les trois derniers mois complets : assez de dossiers pour un PSI fiable."""
    debut, fin = mois_precedent(jour)
    return mois_precedent(mois_precedent(debut)[0])[0], fin


def mois_precedent(jour: date) -> tuple[date, date]:
    fin = jour.replace(day=1) - timedelta(days=1)
    return fin.replace(day=1), fin


def figer_reference(session, debut: date, fin: date) -> str:
    from app.scoring import VERSION_MODELE, charger_modele
    X = scores_periode(session, debut, fin)
    if len(X) < 200:
        raise SystemExit(f"{len(X)} dossiers seulement sur la période : au moins 200 sont nécessaires.")
    p = charger_modele().predict_proba(X[COLONNES])[:, 1]
    ref = construire_reference(
        X, p, f"production du {debut} au {fin} ({len(X)} dossiers), modèle {VERSION_MODELE}")
    chemin = chemin_reference(VERSION_MODELE)
    chemin.write_text(json.dumps(ref, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(chemin)


def main():
    from app.db import SessionLocal

    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("action", choices=["rapport", "figer-reference"])
    parseur.add_argument("--debut", type=date.fromisoformat)
    parseur.add_argument("--fin", type=date.fromisoformat)
    parseur.add_argument("--jour", type=date.fromisoformat,
                         help="date d'observation des remboursements (défaut : --fin)")
    args = parseur.parse_args()
    debut, fin = (args.debut, args.fin) if args.debut and args.fin else mois_precedent(date.today())

    with SessionLocal() as s:
        if args.action == "figer-reference":
            print("Référence enregistrée :", figer_reference(s, debut, fin))
            return
        r = produire_rapport(s, debut, fin, args.jour)
        enregistrer_en_base(s, r)
    print(en_markdown(r))
    print("Rapport :", ecrire_rapport(r))


if __name__ == "__main__":
    main()
