"""Formats de saisie : téléphone sénégalais, adresse Gmail, client majeur."""
from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas import ClientIn
from app.validation import valider_gmail, valider_telephone


@pytest.mark.parametrize("saisie, attendu", [
    ("771234567", "771234567"),
    ("77 123 45 67", "771234567"),
    (" 701234567 ", "701234567"),
    ("711234567", "711234567"),
    ("751234567", "751234567"),
    ("761234567", "761234567"),
    ("781234567", "781234567"),
])
def test_telephone_valide(saisie, attendu):
    assert valider_telephone(saisie) == attendu


@pytest.mark.parametrize("saisie", [
    "721234567",    # préfixe 72 inexistant
    "741234567",    # préfixe 74
    "791234567",    # préfixe 79
    "331234567",    # fixe
    "77123456",     # 8 chiffres
    "7712345678",   # 10 chiffres
    "+221771234567",
    "77-123-45-67",
    "77abc4567",
])
def test_telephone_invalide(saisie):
    with pytest.raises(ValueError):
        valider_telephone(saisie)


@pytest.mark.parametrize("saisie", [None, "", "   "])
def test_telephone_facultatif(saisie):
    assert valider_telephone(saisie) is None


def test_gmail_normalise_en_minuscules():
    assert valider_gmail("  Awa.Ndiaye@GMAIL.com ") == "awa.ndiaye@gmail.com"


@pytest.mark.parametrize("saisie", ["awa@yahoo.fr", "awa@gmail.fr", "awa@gmail.com.sn",
                                    "@gmail.com", "awa ndiaye@gmail.com", "awa@imf-demo.test"])
def test_gmail_invalide(saisie):
    with pytest.raises(ValueError):
        valider_gmail(saisie)


def _client(**modifs):
    donnees = dict(nom="Ndiaye", prenom="Awa", date_naissance=date(1990, 1, 1), agence_id=1,
                   type_revenu="independant", situation_familiale="marie", type_logement="locataire")
    donnees.update(modifs)
    return ClientIn(**donnees)


def test_fiche_client_nettoie_le_telephone():
    assert _client(telephone="77 123 45 67").telephone == "771234567"


def test_fiche_client_refuse_un_mauvais_telephone():
    with pytest.raises(ValidationError):
        _client(telephone="721234567")


def test_fiche_client_refuse_un_mineur():
    aujourdhui = date.today()
    with pytest.raises(ValidationError):
        _client(date_naissance=date(aujourdhui.year - 17, 1, 1))
