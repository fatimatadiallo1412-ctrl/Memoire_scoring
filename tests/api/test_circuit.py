"""Circuit complet d'un dossier : saisie, scoring, décision, décaissement, remboursement."""
from app.calendrier import mensualite_constante


def test_circuit_complet_jusqu_au_solde(api, entetes, dossier_soumis):
    dossier, score = dossier_soumis(200_000, 12)
    assert score["recommandation"] == "accord" and score["version_modele"] == "xgb_home_credit_v4"
    assert len(score["facteurs"]["contributions"]) == 6             # explication du score

    # Décision conforme au modèle : pas de motif exigé
    r = api.post(f"/demandes/{dossier['id']}/decider", headers=entetes["directeur"], json={"decision": "accorder"})
    assert r.status_code == 201, r.text
    assert r.json()["concordance"] is True and r.json()["montant_accorde"] == 200_000

    # Une seconde décision sur le même dossier est impossible
    r = api.post(f"/demandes/{dossier['id']}/decider", headers=entetes["directeur"], json={"decision": "refuser",
                                                                                           "commentaire": "Erreur"})
    assert r.status_code == 409

    # Décaissement : mode obligatoire, puis référence obligatoire hors espèces
    url = f"/demandes/{dossier['id']}/decaisser"
    assert api.post(url, headers=entetes["agent"], json={}).status_code == 422
    assert api.post(url, headers=entetes["agent"], json={"mode_decaissement": "mobile_money"}).status_code == 422
    r = api.post(url, headers=entetes["agent"], json={"mode_decaissement": "mobile_money", "reference": "OM-123456"})
    assert r.status_code == 201, r.text
    credit = r.json()
    assert credit["mensualite"] == mensualite_constante(200_000, 12, 0.24)

    echeances = api.get(f"/credits/{credit['id']}/echeances", headers=entetes["agent"]).json()
    assert len(echeances) == 12 and sum(e["capital"] for e in echeances) == 200_000

    # Remboursement : un trop-perçu est refusé, puis le solde clôt le dossier
    situation = api.get(f"/credits/{credit['id']}/situation", headers=entetes["agent"]).json()
    reste = situation["reste_a_payer"]
    url = f"/credits/{credit['id']}/paiements"
    assert api.post(url, headers=entetes["agent"], json={"montant": reste + 1}).status_code == 422
    assert api.post(url, headers=entetes["agent"], json={"montant": 50_000}).status_code == 201
    assert api.post(url, headers=entetes["agent"], json={"montant": reste - 50_000}).status_code == 201
    assert api.get(f"/demandes/{dossier['id']}", headers=entetes["agent"]).json()["statut"] == "solde"
    assert api.post(url, headers=entetes["agent"], json={"montant": 1}).status_code == 409


def test_contredire_le_modele_exige_un_motif(api, entetes, dossier_soumis):
    dossier, score = dossier_soumis(1_000_000, 6)          # mensualité trop lourde : refus recommandé
    assert score["recommandation"] == "refus"
    url = f"/demandes/{dossier['id']}/decider"
    assert api.post(url, headers=entetes["directeur"], json={"decision": "accorder"}).status_code == 422
    r = api.post(url, headers=entetes["directeur"], json={
        "decision": "accorder", "commentaire": "Client connu depuis dix ans, garantie du groupement."})
    assert r.status_code == 201 and r.json()["concordance"] is False


def test_accord_modifie_au_dessus_de_la_suggestion(api, entetes, dossier_soumis):
    """Correction de l'audit : accorder plus que le montant suggéré contredit le modèle."""
    dossier, score = dossier_soumis(1_000_000, 12)
    assert score["recommandation"] == "accord_reduit"
    suggere = score["montant_suggere"]
    url = f"/demandes/{dossier['id']}/decider"
    corps = {"decision": "accorder_modifie", "montant_accorde": suggere + 50_000, "duree_accordee": 12}
    assert api.post(url, headers=entetes["directeur"], json=corps).status_code == 422
    r = api.post(url, headers=entetes["directeur"], json={**corps, "commentaire": "Stock saisonnier, Tabaski."})
    assert r.status_code == 201 and r.json()["concordance"] is False


def test_accord_modifie_au_montant_suggere_est_concordant(api, entetes, dossier_soumis):
    dossier, score = dossier_soumis(1_000_000, 12)
    r = api.post(f"/demandes/{dossier['id']}/decider", headers=entetes["directeur"], json={
        "decision": "accorder_modifie", "montant_accorde": score["montant_suggere"], "duree_accordee": 12})
    assert r.status_code == 201, r.text
    assert r.json()["concordance"] is True


def test_simulation_en_lecture_seule(api, entetes, dossier_soumis):
    dossier, _ = dossier_soumis(1_000_000, 12)
    r = api.get(f"/demandes/{dossier['id']}/simuler?montant=900000&duree=12", headers=entetes["directeur"])
    assert r.status_code == 200 and r.json()["dans_politique"] is False
    assert api.get(f"/demandes/{dossier['id']}", headers=entetes["directeur"]).json()["statut"] == "soumis_decision"


def test_score_perime_apres_modification(api, entetes, base, nouveau_client):
    client = nouveau_client()
    a = entetes["agent"]
    corps = {"client_id": client["id"], "produit_id": base["produits"]["MICRO"], "montant_demande": 200_000,
             "duree_mois": 12}
    dossier = api.post("/demandes", headers=a, json=corps).json()
    api.post(f"/demandes/{dossier['id']}/completer", headers=a)
    api.post(f"/demandes/{dossier['id']}/scorer", headers=a)
    # Le revenu change : le score n'est plus valable, il faut le recalculer avant de soumettre
    assert api.patch(f"/clients/{client['id']}", headers=a, json={"revenu_mensuel": 90_000}).status_code == 200
    assert api.post(f"/demandes/{dossier['id']}/soumettre", headers=a).status_code == 409


def test_etapes_dans_le_desordre(api, entetes, base, nouveau_client):
    client = nouveau_client()
    a = entetes["agent"]
    dossier = api.post("/demandes", headers=a, json={"client_id": client["id"], "produit_id": base["produits"]["MICRO"],
                                                     "montant_demande": 200_000, "duree_mois": 12}).json()
    assert api.post(f"/demandes/{dossier['id']}/scorer", headers=a).status_code == 409        # pas encore complet
    assert api.post(f"/demandes/{dossier['id']}/decaisser", headers=a,
                    json={"mode_decaissement": "especes"}).status_code == 409                 # pas accordé
