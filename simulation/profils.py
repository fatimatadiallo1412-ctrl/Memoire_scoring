"""Génération de profils de clients de microfinance (contexte sénégalais).

Données SIMULÉES : elles servent à faire vivre le système d'information
(entrepôt, tableau de bord, assistant), pas à valider le modèle de scoring.
Toutes les proportions ci-dessous sont des HYPOTHÈSES à valider avec une IMF.
"""
from datetime import date, timedelta

import numpy as np

DATE_REFERENCE = date(2026, 11, 1)     # date fixe : même âge à chaque exécution

# --- Poids des professions, par type de revenu (hypothèses) ---------------
PROFESSIONS = {
    "independant": {
        "commercant": 40, "artisan": 15, "agriculteur_eleveur_pecheur": 15,
        "chauffeur_transporteur": 10, "restauration_cuisine": 8,
        "services_personne": 6, "ouvrier_manoeuvre": 6,
    },
    "salarie_prive": {
        "ouvrier_manoeuvre": 20, "securite": 15, "nettoyage": 10, "serveur": 8,
        "technicien": 12, "comptable": 8, "secretaire": 8, "informatique": 5,
        "sante": 6, "cadre_gerant": 4, "commercant": 4,
    },
    "fonctionnaire": {
        "enseignant_employe_administratif": 50, "sante": 18, "secretaire": 10,
        "comptable": 6, "cadre_gerant": 6, "securite": 5, "technicien": 5,
    },
    "retraite": {          # profession exercée avant la retraite
        "enseignant_employe_administratif": 35, "commercant": 20, "artisan": 10,
        "securite": 10, "chauffeur_transporteur": 10, "comptable": 5, "sante": 10,
    },
}

# --- Revenu mensuel (FCFA) : loi log-normale (médiane, sigma) par type -----
REVENU = {
    "independant": (150_000, 0.60),
    "salarie_prive": (120_000, 0.50),
    "fonctionnaire": (220_000, 0.40),
    "retraite": (100_000, 0.40),
}
# Effet de la profession sur le revenu (1 = neutre)
MULT_PROFESSION = {
    "cadre_gerant": 1.8, "comptable": 1.4, "informatique": 1.5, "technicien": 1.3,
    "sante": 1.2, "agriculteur_eleveur_pecheur": 0.85, "nettoyage": 0.75,
    "ouvrier_manoeuvre": 0.75, "serveur": 0.75, "securite": 0.80,
}
REVENU_MIN, REVENU_MAX = 60_000, 1_500_000

# --- Noms fictifs (combinaisons aléatoires : d'éventuels homonymes sont fortuits)
NOMS = ["Diop", "Ndiaye", "Fall", "Sow", "Ba", "Diallo", "Sy", "Gueye", "Faye",
        "Sarr", "Mbaye", "Niang", "Cissé", "Thiam", "Seck", "Ndoye", "Diouf",
        "Kane", "Sène", "Camara", "Badji", "Mendy", "Tall", "Wade", "Samb",
        "Dione", "Lô", "Bâ", "Kébé", "Sall", "Gaye", "Mané"]
PRENOMS_F = ["Fatou", "Awa", "Aminata", "Khady", "Mariama", "Rokhaya", "Coumba",
             "Ndeye", "Aïssatou", "Mame", "Bineta", "Sokhna", "Astou", "Dieynaba",
             "Adja", "Marième", "Ramatoulaye", "Yacine", "Seynabou", "Penda"]
PRENOMS_M = ["Moussa", "Mamadou", "Ibrahima", "Ousmane", "Cheikh", "Abdoulaye",
             "Modou", "Alioune", "Pape", "Serigne", "Babacar", "Omar", "Samba",
             "Idrissa", "Lamine", "Boubacar", "Assane", "Mor", "Demba", "Saliou"]
PREFIXES_TEL = ["77", "78", "76", "70", "75"]


def _choisir(rng, poids: dict) -> str:
    cles = list(poids)
    p = np.array([poids[c] for c in cles], dtype=float)
    return str(rng.choice(cles, p=p / p.sum()))


def _profil(rng) -> dict:
    # Sexe : hypothèse de 60 % de femmes (public typique de la microfinance).
    # Il ne sert qu'à l'audit d'équité, jamais au scoring.
    sexe = "F" if rng.random() < 0.60 else "M"

    # Âge : loi normale (moyenne 38 ans, écart-type 10), bornée entre 21 et 70
    age = int(np.clip(rng.normal(38, 10), 21, 70))

    # Type de revenu : dépend d'abord de l'âge
    if age >= 60:
        type_revenu = "retraite" if rng.random() < 0.70 else "independant"
    else:
        type_revenu = _choisir(rng, {"independant": 0.68, "salarie_prive": 0.20,
                                     "fonctionnaire": 0.12})
    profession = _choisir(rng, PROFESSIONS[type_revenu])

    # Revenu : log-normal. mu = ln(médiane) ; sigma = dispersion (0,6 ≈ ±80 %)
    mediane, sigma = REVENU[type_revenu]
    mediane *= MULT_PROFESSION.get(profession, 1.0)
    revenu = rng.lognormal(mean=np.log(mediane), sigma=sigma)
    revenu = int(np.clip(round(revenu / 5_000) * 5_000, REVENU_MIN, REVENU_MAX))

    # Situation familiale : dépend de l'âge
    p_celib = (0.80 if age < 25 else 0.50 if age < 30 else 0.25 if age < 35
               else 0.10 if age < 45 else 0.05)
    p_veuf = float(np.clip(0.002 * (age - 40), 0, 0.12)) if age > 40 else 0.0
    p_divorce = 0.04
    p_marie = max(1 - p_celib - p_veuf - p_divorce, 0.05)
    situation = _choisir(rng, {"celibataire": p_celib, "marie": p_marie,
                               "divorce": p_divorce, "veuf": p_veuf + 1e-9})

    # Enfants : Poisson ; lambda croît avec l'âge (≈ 3 enfants vers 40 ans)
    if situation == "celibataire":
        lam = 0.4 if age >= 28 else 0.1
    else:
        lam = float(np.clip(0.15 * (age - 20) + 0.3, 0.3, 4.5))
    nb_enfants = int(min(rng.poisson(lam), 10))

    # Ménage : le client + conjoint + enfants + autres personnes à charge
    # (les ménages sénégalais sont grands : Poisson de moyenne 1,5 pour les autres)
    taille = 1 + (situation == "marie") + nb_enfants + int(rng.poisson(1.5))
    taille = int(min(taille, 20))

    # Ancienneté dans l'activité : exponentielle (moyenne 7 ans, 10 ans pour la fonction
    # publique), plafonnée par l'âge d'entrée dans la vie active (18 ans)
    if type_revenu == "retraite":
        anciennete = 0
    else:
        echelle = 120 if type_revenu == "fonctionnaire" else 84
        anciennete = int(min(3 + rng.exponential(echelle), (age - 18) * 12))

    # Logement
    poids_log = {"proprietaire": 30, "locataire": 42, "famille": 28}
    if type_revenu == "fonctionnaire":
        poids_log = {"proprietaire": 30, "locataire": 40, "famille": 10,
                     "logement_fonction": 20}
    if age < 28:
        poids_log["famille"] = poids_log["famille"] * 2
    type_logement = _choisir(rng, poids_log)

    possede_bien = bool(rng.random() < (0.85 if type_logement == "proprietaire" else 0.10))
    p_vehicule = float(np.clip(revenu / 1_000_000, 0.03, 0.60))
    if profession == "chauffeur_transporteur":
        p_vehicule = min(p_vehicule + 0.30, 0.90)
    possede_vehicule = bool(rng.random() < p_vehicule)

    prenom = str(rng.choice(PRENOMS_F if sexe == "F" else PRENOMS_M))
    naissance = DATE_REFERENCE - timedelta(days=int(age * 365.25 + rng.integers(0, 365)))
    telephone = f"{rng.choice(PREFIXES_TEL)}{int(rng.integers(0, 10_000_000)):07d}"

    return {
        "nom": str(rng.choice(NOMS)), "prenom": prenom, "sexe": sexe,
        "date_naissance": naissance, "telephone": telephone,
        # variables utilisées par le modèle (noms de la table ops.client)
        "type_revenu": type_revenu, "profession": profession,
        "situation_familiale": situation, "type_logement": type_logement,
        "anciennete_activite_mois": anciennete, "nb_enfants": nb_enfants,
        "taille_menage": taille, "possede_bien_immobilier": possede_bien,
        "possede_vehicule": possede_vehicule, "revenu_mensuel": revenu,
    }


def generer_profils(n: int, graine: int = 42) -> list[dict]:
    rng = np.random.default_rng(graine)
    return [_profil(rng) for _ in range(n)]


if __name__ == "__main__":
    import pandas as pd

    df = pd.DataFrame(generer_profils(2000))
    df["age"] = (pd.Timestamp(DATE_REFERENCE) - pd.to_datetime(df["date_naissance"])).dt.days // 365
    print("Âge :\n", df["age"].describe().round(1), "\n")
    print("Type de revenu (%) :\n", (df["type_revenu"].value_counts(normalize=True) * 100).round(1), "\n")
    print("Revenu mensuel par type :\n", df.groupby("type_revenu")["revenu_mensuel"]
          .describe()[["25%", "50%", "75%", "max"]].round(0), "\n")
    print("Situation familiale (%) :\n", (df["situation_familiale"].value_counts(normalize=True) * 100).round(1), "\n")
    print("Enfants / taille du ménage (moyenne) :", df["nb_enfants"].mean().round(2), "/", df["taille_menage"].mean().round(2))
    print("Logement (%) :\n", (df["type_logement"].value_counts(normalize=True) * 100).round(1), "\n")
    print("Ancienneté médiane (mois) :", df["anciennete_activite_mois"].median())
    print("Véhicule / bien immobilier (%) :", round(df["possede_vehicule"].mean() * 100, 1),
          "/", round(df["possede_bien_immobilier"].mean() * 100, 1))