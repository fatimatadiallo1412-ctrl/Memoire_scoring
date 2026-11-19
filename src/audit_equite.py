"""Audit d'équité du modèle v4 sur l'échantillon de VALIDATION (le test n'est pas ouvert).

    python -m src.audit_equite | tee docs/suivi_modele/audit_equite_validation.txt


1. Test de proxy : un modèle apprend à deviner le sexe à partir des 14 variables du scoring
   (appris sur l'apprentissage, évalué sur la validation). AUC + IC 95 % par bootstrap.
2. Égalité des chances : parmi les bons payeurs (TARGET = 0), part acceptée (p <= seuil),
   par sexe et par tranche d'âge. IC 95 % de Wilson pour chaque taux, IC bootstrap pour
   l'écart et le rapport.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from app.scoring import charger_modele
from src.modeling import CAT, COLONNES, DONNEES, NUM, separer

RNG = np.random.default_rng(42)
B = 1000
SEUILS = (0.12, 0.15)


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


df = pd.read_parquet(DONNEES)
train, val, _ = separer(df)            # le test n'est jamais utilisé ici
train = train[train.CODE_GENDER.isin(["F", "M"])]
val = val[val.CODE_GENDER.isin(["F", "M"])].copy()

# ---- 1. Test de proxy --------------------------------------------------------------------
prep = ColumnTransformer([
    ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), NUM),
    ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
proxy = Pipeline([("prep", prep), ("clf", XGBClassifier(
    n_estimators=300, learning_rate=0.05, max_depth=4, subsample=0.8, colsample_bytree=0.8,
    tree_method="hist", n_jobs=-1, random_state=42))])
y_tr = (train.CODE_GENDER == "F").astype(int)
y_va = (val.CODE_GENDER == "F").astype(int)
proxy.fit(train[COLONNES], y_tr)
s = proxy.predict_proba(val[COLONNES])[:, 1]
auc = roc_auc_score(y_va, s)
idx = np.arange(len(val))
boot = []
for _ in range(B):
    i = RNG.choice(idx, len(idx))
    if y_va.iloc[i].nunique() == 2:
        boot.append(roc_auc_score(y_va.iloc[i], s[i]))
lo, hi = np.percentile(boot, [2.5, 97.5])
print(f"PROXY  AUC validation = {auc:.4f}  IC95 [{lo:.4f} ; {hi:.4f}]  (n = {len(val)}, femmes {y_va.mean():.3f})")

imp = permutation_importance(proxy, val[COLONNES], y_va, scoring="roc_auc", n_repeats=5,
                             random_state=42, n_jobs=-1)
ordre = np.argsort(-imp.importances_mean)
print("Perte d'AUC quand on brouille la variable :")
for k in ordre:
    print(f"   {COLONNES[k]:<24} {imp.importances_mean[k]:.4f} ± {imp.importances_std[k]:.4f}")

# Sans les deux variables les plus porteuses
for retire in [[COLONNES[ordre[0]]], [COLONNES[ordre[0]], COLONNES[ordre[1]]]]:
    cols = [c for c in COLONNES if c not in retire]
    pr = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]),
         [c for c in NUM if c in cols]),
        ("cat", OneHotEncoder(handle_unknown="ignore"), [c for c in CAT if c in cols])])
    m = Pipeline([("prep", pr), ("clf", XGBClassifier(
        n_estimators=300, learning_rate=0.05, max_depth=4, subsample=0.8, colsample_bytree=0.8,
        tree_method="hist", n_jobs=-1, random_state=42))]).fit(train[cols], y_tr)
    print(f"   AUC proxy sans {retire} : {roc_auc_score(y_va, m.predict_proba(val[cols])[:, 1]):.4f}")

# ---- 2. Égalité des chances ----------------------------------------------------------------
val["p"] = charger_modele().predict_proba(val[COLONNES])[:, 1]
val["tranche_age"] = pd.cut(val.age_ans, [0, 30, 40, 50, 60, 200],
                            labels=["< 30 ans", "30-39 ans", "40-49 ans", "50-59 ans", "60 ans et +"],
                            right=False)
bons = val[val.TARGET == 0]
print(f"\nBons payeurs en validation : {len(bons)}")


def taux_par_groupe(d, groupe, seuil):
    out = []
    for g, x in d.groupby(groupe, observed=True):
        k, n = int((x.p <= seuil).sum()), len(x)
        lo, hi = wilson(k, n)
        out.append((g, n, k / n, lo, hi))
    return out


def boot_ecart(d, groupe, seuil, ref, autre):
    a = (d.loc[d[groupe] == ref, "p"] <= seuil).to_numpy()
    b = (d.loc[d[groupe] == autre, "p"] <= seuil).to_numpy()
    ecarts, rapports = [], []
    for _ in range(B):
        ma, mb = RNG.choice(a, len(a)).mean(), RNG.choice(b, len(b)).mean()
        ecarts.append(mb - ma)
        rapports.append(mb / ma)
    return (b.mean() - a.mean(), *np.percentile(ecarts, [2.5, 97.5]),
            b.mean() / a.mean(), *np.percentile(rapports, [2.5, 97.5]))


for seuil in SEUILS:
    print(f"\n=== Seuil {seuil:.0%} : part des bons payeurs acceptés ===")
    for groupe, ref in [("CODE_GENDER", "F"), ("tranche_age", "40-49 ans")]:
        rows = taux_par_groupe(bons, groupe, seuil)
        meilleur = max(rows, key=lambda r: r[2])[0]
        for g, n, t, lo, hi in rows:
            print(f"  {str(g):<12} n={n:>6}  {t * 100:6.2f} %  IC95 [{lo * 100:.2f} ; {hi * 100:.2f}]")
        for g, *_ in rows:
            if g == meilleur:
                continue
            e, elo, ehi, r, rlo, rhi = boot_ecart(bons, groupe, seuil, meilleur, g)
            print(f"    {g} vs {meilleur} : écart {e * 100:+.2f} pts IC95 [{elo * 100:+.2f} ; {ehi * 100:+.2f}]"
                  f" | rapport {r:.3f} IC95 [{rlo:.3f} ; {rhi:.3f}]")
