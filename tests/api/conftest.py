"""Tests de l'API sur la base de test dédiée (TEST_POSTGRES_DB).

À chaque lancement, la base de test est vidée puis recréée par les migrations Alembic :
tables, contraintes et déclencheurs « ajout seul » identiques à la vraie base.
"""
import secrets
from pathlib import Path

import pytest
from sqlalchemy import select, text

from tests.conftest import BASE_TEST, BASE_TEST_VALIDE

RACINE = Path(__file__).resolve().parents[2]

# Mot de passe des comptes de test : tiré au hasard à chaque lancement, jamais enregistré.
MOT_DE_PASSE = secrets.token_urlsafe(16)

COMPTES = {
    "agent": ("agent.test@imf-test.local", "Agent de test", "agent_credit"),
    "agent2": ("agent2.test@imf-test.local", "Second agent de test", "agent_credit"),
    "directeur": ("directeur.test@imf-test.local", "Directeur de test", "decideur"),
    "admin": ("admin.test@imf-test.local", "Administrateur de test", "administrateur"),
    "verrou": ("verrou.test@imf-test.local", "Compte pour le verrouillage", "agent_credit"),
}


def _verifier_cible(engine):
    nom = engine.url.database
    if not BASE_TEST_VALIDE or nom != BASE_TEST:
        pytest.exit(f"Arrêt de sécurité : la base visée ({nom}) n'est pas la base de test.", returncode=2)


@pytest.fixture(scope="session")
def base():
    """Recrée le schéma de la base de test, puis y place agences, produits et comptes."""
    if not BASE_TEST_VALIDE:
        pytest.skip("Base de test non configurée : ajoutez TEST_POSTGRES_DB=scoring_test dans .env")

    from alembic import command
    from alembic.config import Config

    from app.db import SessionLocal, engine
    from app.models import Agence, ProduitCredit, Utilisateur
    from app.models.enums import Role
    from app.security import hasher_mot_de_passe
    from app.seed import AGENCES, PRODUITS

    _verifier_cible(engine)
    with engine.begin() as cx:
        schemas = cx.scalars(text(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name NOT LIKE 'pg\\_%' AND schema_name NOT IN ('information_schema', 'public')")).all()
        for nom in schemas:
            cx.execute(text(f'DROP SCHEMA "{nom}" CASCADE'))
        cx.execute(text("DROP TABLE IF EXISTS public.alembic_version"))

    config = Config(str(RACINE / "alembic.ini"))
    config.set_main_option("script_location", str(RACINE / "migrations"))
    command.upgrade(config, "head")

    with SessionLocal() as session:
        for code, nom, zone in AGENCES:
            if session.scalar(select(Agence).filter_by(code=code)) is None:
                session.add(Agence(code=code, nom=nom, zone=zone))
        session.flush()
        for code, libelle, mn, mx, dmin, dmax, taux in PRODUITS:
            if session.scalar(select(ProduitCredit).filter_by(code=code)) is None:
                session.add(ProduitCredit(code=code, libelle=libelle, montant_min=mn, montant_max=mx,
                                          duree_min_mois=dmin, duree_max_mois=dmax, taux_annuel=taux))
        agence = session.scalar(select(Agence).filter_by(code="DKR01"))
        empreinte = hasher_mot_de_passe(MOT_DE_PASSE)
        for email, nom, role in COMPTES.values():
            session.add(Utilisateur(email=email, nom_complet=nom, role=Role(role), mot_de_passe_hash=empreinte,
                                    agence_id=None if role == "administrateur" else agence.id))
        session.commit()
        ids = {cle: session.scalar(select(Utilisateur.id).filter_by(email=email))
               for cle, (email, _, _) in COMPTES.items()}
        produits = {p.code: p.id for p in session.scalars(select(ProduitCredit))}
        agences = {a.code: a.id for a in session.scalars(select(Agence))}
    return {"utilisateurs": ids, "produits": produits, "agences": agences}


@pytest.fixture(scope="session")
def api(base):
    from fastapi.testclient import TestClient

    from app.main import app
    return TestClient(app)


@pytest.fixture(scope="session")
def entetes(api):
    """En-têtes d'autorisation de chaque compte (une connexion par compte et par lancement)."""
    resultat = {}
    for cle in ("agent", "agent2", "directeur", "admin"):
        r = api.post("/auth/login", data={"username": COMPTES[cle][0], "password": MOT_DE_PASSE})
        assert r.status_code == 200, r.text
        resultat[cle] = {"Authorization": "Bearer " + r.json()["access_token"]}
    return resultat


@pytest.fixture(scope="session")
def session_test(base):
    from app.db import SessionLocal
    with SessionLocal() as session:
        yield session


@pytest.fixture
def nouveau_client(api, entetes, base):
    """Fabrique un client dans le portefeuille de l'agent indiqué."""
    compteur = iter(range(10_000))

    def fabriquer(qui="agent", revenu=150_000, **modifs):
        n = next(compteur)
        corps = dict(nom="Ndiaye", prenom=f"Awa{n}", date_naissance="1985-05-01", sexe="F",
                     telephone="77 123 45 67", agence_id=base["agences"]["DKR01"], type_revenu="independant",
                     situation_familiale="marie", type_logement="locataire", anciennete_activite_mois=60,
                     nb_enfants=3, taille_menage=6, revenu_mensuel=revenu)
        corps.update(modifs)
        r = api.post("/clients", json=corps, headers=entetes[qui])
        assert r.status_code == 201, r.text
        return r.json()
    return fabriquer


@pytest.fixture
def dossier_soumis(api, entetes, base, nouveau_client):
    """Crée un dossier et le mène jusqu'à la soumission au directeur. Renvoie (dossier, score)."""
    def mener(montant, duree=12, produit="MICRO", revenu=150_000):
        client = nouveau_client(revenu=revenu)
        a = entetes["agent"]
        r = api.post("/demandes", headers=a, json={"client_id": client["id"], "produit_id": base["produits"][produit],
                                                   "montant_demande": montant, "duree_mois": duree,
                                                   "objet": "Achat de marchandises"})
        assert r.status_code == 201, r.text
        dossier = r.json()
        for etape, corps in [("completer", None), ("scorer", None),
                             ("instruire", {"avis": "Activité stable, revenus vérifiés sur place."}),
                             ("soumettre", None)]:
            r = api.post(f"/demandes/{dossier['id']}/{etape}", headers=a, json=corps)
            assert r.status_code == 200, (etape, r.text)
            if etape == "scorer":
                score = r.json()
        return dossier, score
    return mener
