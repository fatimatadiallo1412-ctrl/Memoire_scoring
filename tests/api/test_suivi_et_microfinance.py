"""Variables microfinance, historique interne enregistré au scoring, page Santé du modèle."""
from sqlalchemy import select

from app.models import Score


def test_variables_microfinance_facultatives_et_controlees(api, entetes, nouveau_client):
    sans = nouveau_client()
    assert sans["epargne_mensuelle"] is None and sans["usage_mobile_money"] is None

    avec = nouveau_client(epargne_mensuelle=15_000, membre_groupement=True,
                          usage_mobile_money="regulier", activite_saisonniere=False)
    assert avec["epargne_mensuelle"] == 15_000 and avec["membre_groupement"] is True

    r = api.patch(f"/clients/{avec['id']}", headers=entetes["agent"], json={"usage_mobile_money": "souvent"})
    assert r.status_code == 422
    r = api.patch(f"/clients/{avec['id']}", headers=entetes["agent"], json={"epargne_mensuelle": -1})
    assert r.status_code == 422


def test_variables_microfinance_n_invalident_pas_le_score(api, entetes, dossier_soumis, base, session_test):
    dossier, score = dossier_soumis(200_000, 12)
    r = api.patch(f"/clients/{dossier['client_id']}", headers=entetes["agent"],
                  json={"epargne_mensuelle": 20_000, "membre_groupement": True})
    assert r.status_code == 200, r.text
    assert api.get(f"/demandes/{dossier['id']}/score", headers=entetes["agent"]).json()["valide"] is True


def test_score_enregistre_historique_et_complements(api, entetes, base, nouveau_client, session_test):
    client = nouveau_client(epargne_mensuelle=10_000, usage_mobile_money="occasionnel")
    a = entetes["agent"]
    r = api.post("/demandes", headers=a, json={"client_id": client["id"], "produit_id": base["produits"]["MICRO"],
                                               "montant_demande": 200_000, "duree_mois": 12,
                                               "garantie": "caution_solidaire"})
    assert r.status_code == 201 and r.json()["garantie"] == "caution_solidaire"
    dossier = r.json()
    assert api.post(f"/demandes/{dossier['id']}/completer", headers=a).status_code == 200
    score = api.post(f"/demandes/{dossier['id']}/scorer", headers=a).json()

    session_test.expire_all()
    variables = session_test.scalar(select(Score.variables_entree).where(Score.id == score["id"]))
    complements = variables["complements"]
    assert complements["epargne_mensuelle"] == 10_000 and complements["garantie"] == "caution_solidaire"
    assert complements["nb_credits_anterieurs"] == 0 and complements["pire_retard_anterieur_jours"] == 0

    r = api.post("/demandes", headers=a, json={"client_id": client["id"], "produit_id": base["produits"]["MICRO"],
                                               "montant_demande": 200_000, "duree_mois": 12, "garantie": "or"})
    assert r.status_code == 422


def test_sante_du_modele_reservee_a_l_administrateur(api, entetes):
    for qui in ("agent", "directeur"):
        assert api.get("/modele/sante", headers=entetes[qui]).status_code == 403
        assert api.post("/modele/sante", headers=entetes[qui]).status_code == 403

    etat = api.get("/modele/sante", headers=entetes["admin"]).json()
    assert etat["version_en_service"] == "xgb_home_credit_v4"
    assert etat["fiche"]["performances"]["AUC"] == 0.6423

    r = api.post("/modele/sante", headers=entetes["admin"])
    assert r.status_code == 201, r.text
    etat = r.json()
    rapport = etat["dernier"]["contenu"]
    assert rapport["niveau_global"] in ("vert", "orange", "rouge", "n/a")
    assert {"calibration", "auc"} <= set(rapport["alertes"])      # stabilité : seulement si des dossiers sont scorés
    assert etat["dernier"]["automatique"] is False
    assert etat["historique"][0]["id"] == etat["dernier"]["id"]
