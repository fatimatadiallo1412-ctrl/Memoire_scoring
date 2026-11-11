"""Suggestion de montant : recherche du plus grand montant acceptable.

Un modèle factice rend les tests indépendants du modèle réellement entraîné :
le risque y augmente avec la part de la mensualité dans le revenu.
"""
import numpy as np
import pytest

from src.modeling import COLONNES
from src.suggestion import construire_ligne, mensualite, suggerer_montant, taux_endettement

PROFIL = {c: 0 for c in COLONNES}


class ModeleFactice:
    """Risque = 2 % + 50 % × (mensualité / revenu)."""

    def predict_proba(self, ligne):
        p = 0.02 + 0.5 * float(ligne["annuite_sur_revenu"].iloc[0])
        return np.array([[1 - p, p]])


def _suggerer(montant, duree=12, revenu=150_000, **options):
    reglages = dict(seuil=0.15, pas=50_000, montant_min=50_000, ratio_min=0.5, taux_annuel=0.24,
                    endettement_max=0.40)
    reglages.update(options)
    return suggerer_montant(ModeleFactice(), PROFIL, montant, duree, revenu, COLONNES, **reglages)


def test_mensualite_et_endettement():
    assert mensualite(1_200_000, 12) == 100_000
    assert taux_endettement(1_200_000, 12, 400_000) == 0.25


def test_ligne_du_modele():
    ligne = construire_ligne(PROFIL, 600_000, 12, 150_000, COLONNES, 0.0)
    assert list(ligne.columns) == COLONNES
    assert ligne["credit_sur_revenu"].iloc[0] == 4
    assert ligne["annuite_sur_revenu"].iloc[0] == pytest.approx(50_000 / 150_000)
    assert ligne["duree_implicite"].iloc[0] == 12


def test_ratios_plafonnes():
    """Comme à l'entraînement, les ratios extrêmes sont plafonnés."""
    ligne = construire_ligne(PROFIL, 50_000_000, 3, 10_000, COLONNES, 0.0)
    assert ligne["credit_sur_revenu"].iloc[0] == 15
    assert ligne["annuite_sur_revenu"].iloc[0] == 1


def test_accord_du_montant_demande():
    r = _suggerer(200_000)       # mensualité ≈ 19 000, soit 13 % du revenu, risque ≈ 8 %
    assert r["decision"] == "accord" and r["montant"] == 200_000 and r["motifs"] == []


def test_accord_reduit_sur_un_montant_rond():
    r = _suggerer(500_000)       # mensualité ≈ 47 000, soit 32 % du revenu, risque ≈ 18 %
    assert r["decision"] == "accord_reduit"
    assert r["motifs"] == ["risque_modele"]
    assert r["montant"] < 500_000 and r["montant"] % 50_000 == 0
    assert r["p_defaut"] <= 0.15
    # C'est le plus grand montant acceptable : le palier suivant dépasse le seuil
    au_dessus = _suggerer(r["montant"] + 50_000)
    assert au_dessus["decision"] != "accord"


def test_motif_endettement():
    r = _suggerer(700_000, seuil=0.99)    # mensualité ≈ 66 000, soit 44 % du revenu
    assert "endettement" in r["motifs"] and "risque_modele" not in r["motifs"]
    assert r["decision"] == "accord_reduit"
    assert taux_endettement(r["montant"], 12, 150_000, 0.24) <= 0.40


def test_refus_sous_le_plancher():
    """On ne propose jamais moins de la moitié du montant demandé : au-delà, c'est un refus."""
    r = _suggerer(2_000_000)
    assert r["decision"] == "refus" and r["montant"] is None and r["p_defaut"] is None


def test_refus_si_le_minimum_du_produit_n_est_pas_atteignable():
    r = _suggerer(300_000, revenu=30_000, montant_min=250_000)
    assert r["decision"] == "refus"
