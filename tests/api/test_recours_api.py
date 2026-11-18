"""Retour au client après une décision : motif communiqué au client et recommandations."""
import secrets



def _decider(api, entetes, dossier, **corps):
    return api.post(f"/demandes/{dossier['id']}/decider", headers=entetes["directeur"], json=corps)


def _espace_client(api, entetes, client):
    """Ouvre l'espace client et renvoie ses en-têtes (mot de passe temporaire changé)."""
    r = api.post("/comptes/client", headers=entetes["agent"],
                 json={"client_id": client["id"], "email": f"test.client{client['id']}.{secrets.token_hex(4)}@gmail.com"})
    assert r.status_code == 201, r.text
    temporaire = r.json()["mot_de_passe_temporaire"]
    jeton = api.post("/auth/login", data={"username": r.json()["email"], "password": temporaire}).json()
    e = {"Authorization": "Bearer " + jeton["access_token"]}
    nouveau = secrets.token_urlsafe(12) + "Aa1!"
    assert api.post("/auth/mot-de-passe", headers=e, json={"ancien": temporaire, "nouveau": nouveau}).status_code == 204
    return e


def test_score_enregistre_les_recommandations(dossier_soumis):
    _, score = dossier_soumis(1_000_000, 6)                 # mensualité trop lourde : refus
    assert score["recommandation"] == "refus"
    recours = score["facteurs"]["recours"]
    assert recours["motifs"] and recours["institution"]


def test_refus_contre_l_avis_du_modele_exige_un_motif_pour_le_client(api, entetes, dossier_soumis):
    dossier, score = dossier_soumis(300_000, 12)
    assert score["recommandation"] == "accord"
    commentaire = "Endettement auprès d'une autre IMF constaté à l'agence."
    r = _decider(api, entetes, dossier, decision="refuser", commentaire=commentaire)
    assert r.status_code == 422 and "client" in r.json()["detail"]
    r = _decider(api, entetes, dossier, decision="refuser", commentaire=commentaire,
                 motif_client="Votre endettement actuel ne permet pas un nouveau crédit.")
    assert r.status_code == 201, r.text

    retour = api.get(f"/demandes/{dossier['id']}/retour", headers=entetes["agent"]).json()
    assert retour["message"] == "Votre endettement actuel ne permet pas un nouveau crédit."
    # Le modèle recommandait l'accord : ni motif ni plan du modèle, seulement les règles de l'institution
    assert retour["motifs"] == [] and retour["plans"] == [] and retour["institution"]


def test_refus_conforme_au_modele_sans_motif_client(api, entetes, dossier_soumis):
    dossier, score = dossier_soumis(1_000_000, 6)
    assert score["recommandation"] == "refus"
    assert _decider(api, entetes, dossier, decision="refuser").status_code == 201
    retour = api.get(f"/demandes/{dossier['id']}/retour", headers=entetes["directeur"]).json()
    assert retour["motifs"] and retour["message"] is None


def test_le_client_voit_ses_demandes_sans_chiffre_de_risque(api, entetes, base, nouveau_client):
    client = nouveau_client()
    a = entetes["agent"]
    r = api.post("/demandes", headers=a, json={"client_id": client["id"], "produit_id": base["produits"]["MICRO"],
                                               "montant_demande": 1_000_000, "duree_mois": 6})
    dossier = r.json()
    for etape, corps in [("completer", None), ("scorer", None),
                         ("instruire", {"avis": "Activité stable, revenus vérifiés sur place."}), ("soumettre", None)]:
        assert api.post(f"/demandes/{dossier['id']}/{etape}", headers=a, json=corps).status_code == 200
    e = _espace_client(api, entetes, client)

    # Avant la décision : la demande est visible, sans retour
    demandes = api.get("/moi/demandes", headers=e).json()
    assert [d["id"] for d in demandes] == [dossier["id"]] and demandes[0]["retour"] is None

    assert _decider(api, entetes, dossier, decision="refuser").status_code == 201
    retour = api.get("/moi/demandes", headers=e).json()[0]["retour"]
    assert retour["motifs"] and retour["institution"]
    for plan in retour["plans"]:
        assert "p_defaut" not in plan and "endettement" not in plan

    # Un autre client ne voit rien de ce dossier
    autre = _espace_client(api, entetes, nouveau_client())
    assert api.get("/moi/demandes", headers=autre).json() == []


def test_retours_dans_la_fiche_client(api, entetes, dossier_soumis):
    dossier, _ = dossier_soumis(1_000_000, 6)
    _decider(api, entetes, dossier, decision="refuser")
    retours = api.get(f"/clients/{dossier['client_id']}/retours", headers=entetes["directeur"]).json()
    assert [d["id"] for d in retours] == [dossier["id"]]
    # Hors portefeuille : 404
    assert api.get(f"/clients/{dossier['client_id']}/retours", headers=entetes["agent2"]).status_code == 404
