"""Décisions, journal et paiements en ajout seul : même la base refuse de les modifier."""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError


@pytest.mark.parametrize("requete", [
    "UPDATE ops.decision SET commentaire = 'modifié'",
    "DELETE FROM ops.decision",
    "UPDATE audit.journal SET action = 'modifié'",
    "DELETE FROM audit.journal",
    "DELETE FROM ops.paiement",
])
def test_ajout_seul(api, entetes, dossier_soumis, session_test, requete):
    dossier, _ = dossier_soumis(200_000, 12)
    api.post(f"/demandes/{dossier['id']}/decider", headers=entetes["directeur"], json={"decision": "accorder"})
    credit = api.post(f"/demandes/{dossier['id']}/decaisser", headers=entetes["agent"],
                      json={"mode_decaissement": "especes"}).json()
    api.post(f"/credits/{credit['id']}/paiements", headers=entetes["agent"], json={"montant": 10_000})
    with pytest.raises(DBAPIError):
        session_test.execute(text(requete))
    session_test.rollback()


def test_chaque_etape_est_journalisee(api, entetes, dossier_soumis, session_test):
    dossier, _ = dossier_soumis(200_000, 12)
    api.post(f"/demandes/{dossier['id']}/decider", headers=entetes["directeur"], json={"decision": "accorder"})
    actions = session_test.scalars(text(
        "SELECT action FROM audit.journal WHERE entite = 'demande_credit' AND entite_id = :id ORDER BY id"),
        {"id": dossier["id"]}).all()
    assert actions == ["dossier_cree", "dossier_complet", "dossier_score", "dossier_instruit",
                       "dossier_soumis", "decision"]
