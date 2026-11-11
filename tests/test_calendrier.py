"""Calendrier de remboursement à mensualités constantes."""
from datetime import date

import pytest

from app.calendrier import ajouter_mois, generer_calendrier, mensualite_constante
from src.suggestion import mensualite


@pytest.mark.parametrize("depart, n, attendu", [
    (date(2026, 1, 15), 1, date(2026, 2, 15)),
    (date(2026, 1, 31), 1, date(2026, 2, 28)),     # février non bissextile
    (date(2028, 1, 31), 1, date(2028, 2, 29)),     # année bissextile
    (date(2026, 11, 30), 3, date(2027, 2, 28)),    # changement d'année
    (date(2026, 12, 10), 12, date(2027, 12, 10)),
])
def test_ajouter_mois(depart, n, attendu):
    assert ajouter_mois(depart, n) == attendu


def test_mensualite_sans_interet():
    assert mensualite_constante(600_000, 6, 0.0) == 100_000


def test_mensualite_formule_des_annuites():
    # 500 000 FCFA sur 12 mois à 24 % l'an : 47 280 FCFA par mois
    assert mensualite_constante(500_000, 12, 0.24) == 47_280


def test_mensualite_coherente_avec_le_scoring():
    """Le scoring et le calendrier doivent calculer la même mensualité."""
    assert mensualite_constante(800_000, 18, 0.22) == round(mensualite(800_000, 18, 0.22))


@pytest.mark.parametrize("montant, duree, taux", [(500_000, 12, 0.24), (310_000, 6, 0.24),
                                                   (25_000_000, 60, 0.20), (50_000, 3, 0.18),
                                                   (1_000_000, 10, 0.0)])
def test_calendrier_rembourse_exactement_le_capital(montant, duree, taux):
    lignes = generer_calendrier(montant, duree, taux, date(2026, 1, 31))
    assert len(lignes) == duree
    assert sum(l["capital"] for l in lignes) == montant
    assert [l["numero"] for l in lignes] == list(range(1, duree + 1))
    for l in lignes:
        assert l["montant_du"] == l["capital"] + l["interet"]
        assert l["capital"] > 0 and l["interet"] >= 0
    # Les échéances sont strictement croissantes, un mois d'écart
    dates = [l["date_echeance"] for l in lignes]
    assert dates == sorted(dates) and len(set(dates)) == duree


def test_interets_decroissants():
    """Avec l'amortissement, la part d'intérêts baisse à chaque échéance."""
    interets = [l["interet"] for l in generer_calendrier(1_000_000, 24, 0.24, date(2026, 3, 1))]
    assert interets == sorted(interets, reverse=True)
