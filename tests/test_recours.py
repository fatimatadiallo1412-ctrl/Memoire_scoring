"""Recours : les conseils donnés aux clients refusés ou partiellement accordés (src/recours.py).

Les plans « modèle » sont vérifiés avec le vrai modèle v4 : chaque plan proposé doit réellement
entrer dans la politique, et seules les variables sur lesquelles le client peut agir varient.
"""
from datetime import date
from types import SimpleNamespace

import pytest

from app.scoring import charger_modele, evaluer_dossier, profil_client
from src import recours as RC
from src.modeling import COLONNES
from src.suggestion import mensualite, probabilite_defaut

JOUR = date(2026, 11, 1)
PRODUIT = SimpleNamespace(taux_annuel=24.0, montant_min=50_000, montant_max=2_000_000,
                          duree_min_mois=3, duree_max_mois=36)
PARAMETRES = {"seuil_defaut": 0.12, "facteur_prudence_antecedent": 0.8, "endettement_max": 0.40,
              "pas_montant": 10_000, "ratio_min": 0.5}


def client(**changements):
    valeurs = dict(nb_enfants=3, taille_menage=6, date_naissance=date(1990, 1, 1),
                   anciennete_activite_mois=20, type_revenu="independant", situation_familiale="marie",
                   type_logement="locataire", profession="commercant", categorie_profession=None,
                   possede_bien_immobilier=False, possede_vehicule=False, revenu_mensuel=120_000,
                   epargne_mensuelle=None, membre_groupement=None, usage_mobile_money=None,
                   activite_saisonniere=None)
    valeurs.update(changements)
    return SimpleNamespace(**valeurs)


def demande(montant=900_000, duree=12, garantie="aucune"):
    return SimpleNamespace(date_demande=JOUR, montant_demande=montant, duree_mois=duree, garantie=garantie)


@pytest.fixture(scope="module")
def modele():
    return charger_modele()


def _plans(modele, c, d, **options):
    reglages = dict(taux_annuel=0.24, seuil=0.12, endettement_max=0.40, montant_min=PRODUIT.montant_min,
                    duree_min=PRODUIT.duree_min_mois, duree_max=PRODUIT.duree_max_mois, pas=10_000)
    reglages.update(options)
    return RC.chercher_plans(modele, profil_client(c, JOUR), d.montant_demande, d.duree_mois,
                             c.revenu_mensuel, COLONNES, **reglages)


# ---- Plans calculés par le modèle --------------------------------------------------------------

def test_chaque_plan_entre_vraiment_dans_la_politique(modele):
    c = client()
    plans = _plans(modele, c, demande())
    assert plans, "un profil refusé pour montant trop élevé doit recevoir au moins un plan"
    for p in plans:
        # Recalcul indépendant, avec la fonction de scoring de l'application : le client a vieilli
        # de l'attente conseillée, son activité aussi.
        profil = profil_client(c, JOUR)
        profil["age_ans"] += p["attente_mois"] / 12
        profil["anciennete_emploi_ans"] += p["attente_mois"] / 12
        revenu = c.revenu_mensuel * (1 + p["hausse_revenu"])
        prob = probabilite_defaut(modele, profil, p["montant"], p["duree_mois"], revenu, COLONNES, 0.24)
        assert prob <= 0.12 + 1e-6
        assert mensualite(p["montant"], p["duree_mois"], 0.24) / revenu <= 0.40 + 1e-9


def test_lignes_identiques_au_scoring_sans_changement(modele):
    """Sans attente ni hausse, la ligne du recours est exactement celle du scoring."""
    c = client()
    profil = profil_client(c, JOUR)
    scenario = {"montant": 300_000, "duree": 12, "revenu": c.revenu_mensuel, "attente": 0}
    ligne = RC._lignes(profil, [scenario], COLONNES, 0.24)
    p_recours = float(modele.predict_proba(ligne)[0, 1])
    assert p_recours == pytest.approx(
        probabilite_defaut(modele, profil, 300_000, 12, c.revenu_mensuel, COLONNES, 0.24))


def test_seules_les_variables_modifiables_changent():
    profil = profil_client(client(), JOUR)
    base = RC._lignes(profil, [{"montant": 300_000, "duree": 12, "revenu": 120_000, "attente": 0}], COLONNES, 0.24)
    autre = RC._lignes(profil, [{"montant": 200_000, "duree": 18, "revenu": 156_000, "attente": 12}], COLONNES, 0.24)
    changees = {col for col in COLONNES if base[col].iloc[0] != autre[col].iloc[0]}
    assert changees <= RC.VARIABLES_MODIFIABLES
    # Jamais conseillé : famille, profession, logement, biens
    for fixe in ("CNT_CHILDREN", "NAME_FAMILY_STATUS", "OCCUPATION_TYPE", "NAME_HOUSING_TYPE",
                 "FLAG_OWN_CAR", "FLAG_OWN_REALTY"):
        assert fixe not in changees


def test_accord_reduit_vise_le_montant_entier(modele):
    # Risque du montant demandé ≈ 14,7 % : un seuil de 14,5 % laisse des leviers possibles.
    plans = _plans(modele, client(revenu_mensuel=150_000), demande(500_000), seuil=0.145, montant_fixe=True)
    assert plans and all(p["montant"] == 500_000 for p in plans)
    # Leviers différents d'un plan à l'autre
    assert len({tuple(p["leviers"]) for p in plans}) == len(plans)


def test_sans_activite_pas_de_conseil_d_attente(modele):
    plans = _plans(modele, client(anciennete_activite_mois=0), demande())
    assert all(p["attente_mois"] == 0 for p in plans)


def test_limites_de_la_politique_respectees(modele):
    plans = _plans(modele, client(), demande(), hausse_revenu_max=0.2, attente_max=6)
    assert all(p["hausse_revenu"] <= 0.2 and p["attente_mois"] <= 6 for p in plans)


def test_aucun_plan_si_rien_de_realiste_ne_suffit(modele):
    assert _plans(modele, client(), demande(), seuil=0.001) == []


def test_plans_du_plus_simple_au_plus_ambitieux(modele):
    plans = _plans(modele, client(), demande())
    montants = [p["montant"] for p in plans]
    assert montants == sorted(montants) and len(set(montants)) == len(montants)


# ---- Textes destinés au client ---------------------------------------------------------------

def test_textes_client_sans_chiffre_de_risque(modele):
    reco, _ = evaluer_dossier(client(), demande(), PRODUIT, PARAMETRES)
    r = reco["recours"]
    textes = [m["texte"] for m in r["motifs"]] + [p["texte"] for p in r["plans"]] + \
             [i["texte"] for i in r["institution"]]
    assert textes
    for t in textes:
        assert "probabilit" not in t.lower() and "seuil" not in t.lower()


def test_motif_endettement_chiffre():
    m = RC.motifs_client(["endettement"], mensualite_demandee=56_736, endettement=0.95,
                         endettement_max=0.40, antecedent="aucun")
    assert "95 %" in m[0]["texte"] and "40 %" in m[0]["texte"]


# ---- Règles de l'institution ----------------------------------------------------------------

def test_credit_en_retard_un_seul_conseil(modele):
    reco, _ = evaluer_dossier(client(), demande(), PRODUIT, PARAMETRES, antecedent="en_cours")
    r = reco["recours"]
    assert r["bloque"] and r["plans"] == []
    assert [i["code"] for i in r["institution"]] == ["regulariser"]


def test_conseils_selon_la_fiche():
    codes = lambda c, d, h=None, plan=None: {i["code"] for i in RC.recommandations_institution(  # noqa: E731
        c, d, mensualite_visee=20_000, historique=h, plan_reduit=plan)}
    complet = client(membre_groupement=True, usage_mobile_money="regulier", activite_saisonniere=False)
    assert codes(complet, demande(garantie="epargne_nantie")) == {"epargne_prealable"}
    assert "garant" in codes(client(), demande(garantie="aucune"))
    assert "garant" not in codes(client(), demande(garantie="garant"))
    assert "saisonnalite" in codes(client(activite_saisonniere=True), demande())
    plan = {"montant": 200_000, "duree_mois": 12}
    assert "credit_progressif" in codes(client(), demande(), {"nb_credits_anterieurs": 0}, plan)
    assert "credit_progressif" not in codes(client(), demande(), {"nb_credits_anterieurs": 2}, plan)


def test_epargne_prealable_egale_a_la_mensualite_visee():
    reco = RC.recommandations_institution(client(), demande(), mensualite_visee=25_000, historique=None,
                                          mois_epargne=4)
    texte = next(i["texte"] for i in reco if i["code"] == "epargne_prealable")
    assert "25 000 FCFA" in texte and "4 mois" in texte


def test_accord_sans_motif_mais_avec_conseils_de_l_institution():
    """Si le directeur refuse contre l'avis du modèle, les conseils de l'institution restent disponibles."""
    reco, _ = evaluer_dossier(client(revenu_mensuel=300_000), demande(300_000), PRODUIT, PARAMETRES)
    assert reco["decision"] == "accord"
    assert reco["recours"]["motifs"] == [] and reco["recours"]["plans"] == []
    assert reco["recours"]["institution"]


def test_epargne_conseillee_jamais_superieure_a_ce_que_la_politique_permet():
    """Mensualité demandée (1 000 000 FCFA sur 6 mois) bien au-delà du revenu : l'épargne conseillée
    reste à la mesure d'un crédit envisageable."""
    c = client(revenu_mensuel=150_000)
    reco, _ = evaluer_dossier(c, demande(1_000_000, 6), PRODUIT, PARAMETRES)
    assert reco["recours"]["mensualite_visee"] <= 0.40 * c.revenu_mensuel
