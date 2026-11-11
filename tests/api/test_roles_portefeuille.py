"""Droits par rôle et cloisonnement des portefeuilles."""
import pytest


@pytest.mark.parametrize("qui, methode, route", [
    ("admin", "get", "/clients"),                        # l'administrateur ne voit pas les clients
    ("admin", "get", "/demandes"),
    ("directeur", "post", "/clients"),                   # le directeur ne saisit pas
    ("directeur", "post", "/demandes"),
    ("agent", "get", "/demandes/1/simuler?montant=100000&duree=6"),   # simulation réservée au directeur
    ("agent", "post", "/demandes/1/decider"),            # l'agent ne décide pas
])
def test_acces_refuse_selon_le_role(api, entetes, qui, methode, route):
    r = getattr(api, methode)(route, headers=entetes[qui], **({"json": {}} if methode == "post" else {}))
    assert r.status_code == 403


def test_un_agent_ne_voit_pas_le_client_d_un_collegue(api, entetes, nouveau_client):
    client = nouveau_client(qui="agent")
    # 404 et non 403 : on ne révèle pas l'existence du client
    assert api.get(f"/clients/{client['id']}", headers=entetes["agent2"]).status_code == 404
    ids = [c["id"] for c in api.get("/clients?limite=100", headers=entetes["agent2"]).json()]
    assert client["id"] not in ids
    # ni modifier sa fiche, ni lui ouvrir un dossier
    assert api.patch(f"/clients/{client['id']}", json={"adresse": "Thiès"},
                     headers=entetes["agent2"]).status_code == 404


def test_un_agent_ne_peut_pas_ouvrir_un_dossier_pour_le_client_d_un_collegue(api, entetes, base, nouveau_client):
    client = nouveau_client(qui="agent")
    r = api.post("/demandes", headers=entetes["agent2"], json={
        "client_id": client["id"], "produit_id": base["produits"]["MICRO"],
        "montant_demande": 100_000, "duree_mois": 6})
    assert r.status_code == 422


def test_le_directeur_voit_tous_les_portefeuilles(api, entetes, nouveau_client):
    client = nouveau_client(qui="agent2")
    assert api.get(f"/clients/{client['id']}", headers=entetes["directeur"]).status_code == 200


def test_pagination_et_total(api, entetes, nouveau_client):
    for _ in range(3):
        nouveau_client(qui="agent2")
    r = api.get("/clients?limite=2&decalage=0", headers=entetes["agent2"])
    assert r.status_code == 200 and len(r.json()) == 2
    total = int(r.headers["X-Total-Count"])
    assert total >= 3
    derniere = api.get(f"/clients?limite=2&decalage={total - 1}", headers=entetes["agent2"]).json()
    assert len(derniere) == 1


def test_telephone_invalide_refuse_par_l_api(api, entetes, nouveau_client):
    with pytest.raises(AssertionError):
        nouveau_client(telephone="721234567")


def test_montant_hors_produit_refuse(api, entetes, base, nouveau_client):
    client = nouveau_client()
    r = api.post("/demandes", headers=entetes["agent"], json={
        "client_id": client["id"], "produit_id": base["produits"]["MICRO"],
        "montant_demande": 5_000_000, "duree_mois": 6})     # MICRO : 1 000 000 FCFA au plus
    assert r.status_code == 422
