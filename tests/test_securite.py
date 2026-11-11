"""Mots de passe et jetons d'accès."""
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.security import (ALGORITHME, CLE_SECRETE, creer_jeton, decoder_jeton, hasher_mot_de_passe,
                          verifier_mot_de_passe)


def test_mot_de_passe_hache_et_verifie():
    empreinte = hasher_mot_de_passe("Bonjour-Dakar-2026")
    assert empreinte.startswith("$argon2")
    assert "Bonjour-Dakar-2026" not in empreinte
    assert verifier_mot_de_passe("Bonjour-Dakar-2026", empreinte)
    assert not verifier_mot_de_passe("bonjour-dakar-2026", empreinte)


def test_deux_empreintes_differentes_pour_le_meme_mot_de_passe():
    assert hasher_mot_de_passe("abc") != hasher_mot_de_passe("abc")   # sel aléatoire


def test_jeton_aller_retour():
    charge = decoder_jeton(creer_jeton(42, "decideur"))
    assert charge["sub"] == "42" and charge["role"] == "decideur"


def test_jeton_falsifie_refuse():
    faux = jwt.encode({"sub": "1", "role": "administrateur",
                       "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
                      "une-autre-cle-" + "y" * 40, algorithm=ALGORITHME)
    with pytest.raises(jwt.InvalidSignatureError):
        decoder_jeton(faux)


def test_jeton_expire_refuse():
    expire = jwt.encode({"sub": "1", "role": "agent_credit",
                         "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
                        CLE_SECRETE, algorithm=ALGORITHME)
    with pytest.raises(jwt.ExpiredSignatureError):
        decoder_jeton(expire)


def test_algorithme_none_refuse():
    sans_signature = jwt.encode({"sub": "1", "role": "administrateur"}, None, algorithm="none")
    with pytest.raises(jwt.InvalidTokenError):
        decoder_jeton(sans_signature)
