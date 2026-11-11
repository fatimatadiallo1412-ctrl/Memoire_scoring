"""Connexion, jetons et verrouillage des comptes."""
from tests.api.conftest import COMPTES, MOT_DE_PASSE


def test_base_de_test_utilisee(base):
    from app.db import engine
    from tests.conftest import BASE_REELLE
    assert engine.url.database != BASE_REELLE and "test" in engine.url.database


def test_connexion_et_profil(api, entetes):
    r = api.get("/auth/me", headers=entetes["directeur"])
    assert r.status_code == 200 and r.json()["role"] == "decideur"


def test_mauvais_mot_de_passe(api):
    r = api.post("/auth/login", data={"username": COMPTES["agent2"][0], "password": "mauvais"})
    assert r.status_code == 401
    # le compteur d'échecs est remis à zéro par une connexion réussie
    assert api.post("/auth/login", data={"username": COMPTES["agent2"][0], "password": MOT_DE_PASSE}).status_code == 200


def test_compte_inconnu_meme_reponse(api):
    r = api.post("/auth/login", data={"username": "personne@imf-test.local", "password": "x"})
    assert r.status_code == 401 and r.json()["detail"] == "Identifiants incorrects"


def test_sans_jeton(api):
    assert api.get("/clients").status_code == 401


def test_jeton_invalide(api):
    assert api.get("/clients", headers={"Authorization": "Bearer abc.def.ghi"}).status_code == 401


def test_verrouillage_apres_cinq_echecs(api):
    email = COMPTES["verrou"][0]
    for _ in range(5):
        assert api.post("/auth/login", data={"username": email, "password": "faux"}).status_code == 401
    # Même le bon mot de passe est refusé pendant le verrouillage
    assert api.post("/auth/login", data={"username": email, "password": MOT_DE_PASSE}).status_code == 429
