"""Circuit du dossier et concordance entre le directeur et le modèle."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.enums import StatutDossier as S
from app.models.enums import TypeDecision as D
from app.workflow import TRANSITIONS, changer_statut, est_concordante


def _dossier(statut):
    return SimpleNamespace(statut=statut)


@pytest.mark.parametrize("depart, cible", [
    (S.BROUILLON, S.COMPLET), (S.COMPLET, S.SCORE), (S.SCORE, S.INSTRUIT), (S.INSTRUIT, S.SOUMIS),
    (S.SOUMIS, S.ACCORDE), (S.SOUMIS, S.REFUSE), (S.ACCORDE, S.DECAISSE),
    (S.DECAISSE, S.EN_REMBOURSEMENT), (S.EN_REMBOURSEMENT, S.SOLDE),
])
def test_transition_autorisee(depart, cible):
    dossier = _dossier(depart)
    changer_statut(dossier, cible)
    assert dossier.statut == cible


@pytest.mark.parametrize("depart, cible", [
    (S.BROUILLON, S.SOUMIS),     # on ne saute pas le scoring ni l'instruction
    (S.SCORE, S.ACCORDE),        # pas de décision sans soumission
    (S.SOUMIS, S.DECAISSE),      # pas de décaissement sans accord
    (S.REFUSE, S.ACCORDE),       # un refus est définitif
    (S.SOLDE, S.EN_REMBOURSEMENT),
])
def test_transition_interdite(depart, cible):
    dossier = _dossier(depart)
    with pytest.raises(HTTPException) as erreur:
        changer_statut(dossier, cible)
    assert erreur.value.status_code == 409
    assert dossier.statut == depart


def test_etats_terminaux():
    assert TRANSITIONS[S.REFUSE] == set() and TRANSITIONS[S.SOLDE] == set()


def test_tous_les_statuts_ont_des_regles():
    assert set(TRANSITIONS) == set(S)


@pytest.mark.parametrize("choix, recommandation, attendu", [
    (D.ACCORDER, "accord", True),
    (D.REFUSER, "refus", True),
    (D.ACCORDER, "refus", False),
    (D.REFUSER, "accord", False),
    (D.ACCORDER, "accord_reduit", False),   # accorder le montant demandé alors que le modèle le réduit
    (D.AJOURNER, "accord", False),
])
def test_concordance_par_type(choix, recommandation, attendu):
    assert est_concordante(choix, recommandation) is attendu


def test_accord_modifie_au_plus_le_montant_suggere_est_concordant():
    assert est_concordante(D.ACCORDER_MODIFIE, "accord_reduit", 300_000, 300_000)
    assert est_concordante(D.ACCORDER_MODIFIE, "accord_reduit", 300_000, 250_000)


def test_accord_modifie_au_dessus_du_montant_suggere_contredit_le_modele():
    """Faille relevée par l'audit : accorder plus que le modèle ne suggère n'est pas concordant."""
    assert not est_concordante(D.ACCORDER_MODIFIE, "accord_reduit", 300_000, 310_000)
