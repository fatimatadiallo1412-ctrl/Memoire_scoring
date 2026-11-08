"""Classifieur d'intentions de l'assistant : TF-IDF sur caractères + régression logistique."""
from functools import lru_cache
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

RACINE = Path(__file__).resolve().parents[2]
FICHIER_PHRASES = RACINE / "data" / "assistant" / "phrases.csv"

C_DEFAUT = 10.0

# Intentions qui affichent des données personnelles du client : une erreur y est grave.
SERVICES = frozenset({"prochaine_echeance", "solde", "retard", "historique", "nouveau_credit"})

# Probabilité minimale pour répondre ; en dessous, « je n'ai pas compris ».
# Choisis sur le jeu de validation (voir docs/grille_seuils_assistant.txt).
SEUIL_SERVICE = 0.50    # intentions qui affichent des données : seuil strict
SEUIL_AUTRE = 0.30      # aide, salutation, remerciement : seuil souple


def charger_phrases(chemin: Path = FICHIER_PHRASES) -> pd.DataFrame:
    phrases = pd.read_csv(chemin, sep=";", dtype=str, encoding="utf-8").dropna()
    phrases["phrase"] = phrases["phrase"].str.strip()
    return phrases[phrases["phrase"] != ""].reset_index(drop=True)


def construire_pipeline(c: float = C_DEFAUT):
    return make_pipeline(
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), strip_accents="unicode",
                        lowercase=True, sublinear_tf=True),
        LogisticRegression(C=c, max_iter=1000),
    )


def entrainer(phrases: pd.DataFrame | None = None, c: float = C_DEFAUT):
    if phrases is None:
        phrases = charger_phrases()
    modele = construire_pipeline(c)
    modele.fit(phrases["phrase"], phrases["intention"])
    return modele


@lru_cache(maxsize=1)
def modele_assistant():
    """Entraîné une seule fois au premier appel (quelques dizaines de millisecondes)."""
    return entrainer()


def comprendre(texte: str) -> tuple[str, float]:
    """Renvoie (intention, confiance). Hors sujet ou confiance sous le seuil : 'non_compris'."""
    modele = modele_assistant()
    proba = modele.predict_proba([texte])[0]
    indice = int(proba.argmax())
    intention, confiance = str(modele.classes_[indice]), float(proba[indice])
    seuil = SEUIL_SERVICE if intention in SERVICES else SEUIL_AUTRE
    if intention == "hors_sujet" or confiance < seuil:
        return "non_compris", confiance
    return intention, confiance