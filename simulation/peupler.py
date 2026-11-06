"""Peuplement de la base avec une activité simulée (clients, dossiers, scores, décisions).

Les dossiers passent par le VRAI scoring (evaluer_dossier) et la politique lue en base.
Chaque étape du cycle de vie est datée dans le passé ; les dossiers récents restent donc
à un statut intermédiaire. Les décaissements et paiements viennent à l'étape suivante.

    python -m simulation.peupler --reset     # vide les tables transactionnelles puis peuple
"""
import argparse
import os
import sys
from datetime import date, datetime, timedelta, timezone

import numpy as np
from sqlalchemy import select, text

from app.db import SessionLocal
from app.models import Agence, Client, Decision, DemandeCredit, ProduitCredit, Score, Utilisateur
from app.models.enums import Role, StatutDossier, TypeDecision
from app.parametres import lire_parametres
from app.scoring import VERSION_MODELE, evaluer_dossier
from app.security import hasher_mot_de_passe
from simulation.profils import generer_profils

N_CLIENTS = 1500
GRAINE = 42
AUJOURDHUI = date(2026, 11, 6)
DEBUT = AUJOURDHUI - timedelta(days=730)            # 24 mois d'historique
MAINTENANT = datetime(2026, 11, 6, 19, 0, tzinfo=timezone.utc)

POIDS_AGENCES = {"Dakar": 0.50, "Thiès": 0.25, "Saint-Louis": 0.25}
QUARTIERS = {
    "Dakar": ["Médina", "Pikine", "Guédiawaye", "Parcelles Assainies", "Grand Yoff", "Thiaroye"],
    "Thiès": ["Randoulène", "Mbour 1", "Cité Lamy", "Diakhao"],
    "Saint-Louis": ["Sor", "Guet Ndar", "Pikine", "Balacoss"],
}
DUREES = {"MICRO": [6, 9, 12], "PME": [12, 18, 24], "SALARIE": [12, 18, 24]}
OBJETS = {
    "commercant": ["Achat de marchandises", "Renouvellement du stock", "Extension de l'étal"],
    "artisan": ["Achat de matériel d'atelier", "Achat de matières premières"],
    "agriculteur_eleveur_pecheur": ["Semences et engrais", "Matériel agricole",
                                    "Achat de bétail", "Équipement de pêche"],
    "chauffeur_transporteur": ["Réparation du véhicule", "Pièces et pneus"],
    "restauration_cuisine": ["Équipement de cuisine", "Achat de denrées"],
}
OBJETS_DEFAUT = ["Besoin de trésorerie", "Amélioration de l'habitat",
                 "Frais de scolarité", "Frais familiaux"]
AVIS = ["Activité visitée, revenu moyen estimé confirmé.",
        "Client connu de l'agence, dossier complet.",
        "Visite effectuée, stock et activité constatés.",
        "Pièces d'identité et justificatifs vérifiés."]
NOMS_AGENTS = ["Khady Sène", "Ibrahima Faye", "Aminata Sow", "Modou Gueye",
               "Fatou Ba", "Cheikh Thiam"]

EQUIVALENT = {"accord": TypeDecision.ACCORDER, "accord_reduit": TypeDecision.ACCORDER_MODIFIE,
              "refus": TypeDecision.REFUSER}
# Comportement simulé du directeur selon la recommandation du modèle
CHOIX_DIRECTEUR = {
    "accord": [(TypeDecision.ACCORDER, .92), (TypeDecision.ACCORDER_MODIFIE, .04),
               (TypeDecision.AJOURNER, .02), (TypeDecision.REFUSER, .02)],
    "accord_reduit": [(TypeDecision.ACCORDER_MODIFIE, .85), (TypeDecision.ACCORDER, .08),
                      (TypeDecision.REFUSER, .07)],
    "refus": [(TypeDecision.REFUSER, .88), (TypeDecision.ACCORDER_MODIFIE, .12)],
}
MOTIFS = {
    ("accord", TypeDecision.ACCORDER_MODIFIE): "Montant réduit par prudence : activité récente.",
    ("accord", TypeDecision.AJOURNER): "Pièces complémentaires demandées avant décision.",
    ("accord", TypeDecision.REFUSER): "Client déjà endetté auprès d'une autre institution.",
    ("accord_reduit", TypeDecision.ACCORDER): "Montant intégral accordé : bonne connaissance du client, garantie apportée.",
    ("accord_reduit", TypeDecision.REFUSER): "Capacité de remboursement jugée insuffisante.",
    ("refus", TypeDecision.ACCORDER_MODIFIE): "Client connu de l'agence, montant réduit accepté avec garantie.",
}
STATUT_DECISION = {TypeDecision.ACCORDER: "accorde", TypeDecision.ACCORDER_MODIFIE: "accorde_modifie",
                   TypeDecision.REFUSER: "refuse", TypeDecision.AJOURNER: "ajourne"}


def S(valeur: str) -> StatutDossier:
    return StatutDossier(valeur)


def choisir(rng, options):
    valeurs, poids = zip(*options)
    p = np.array(poids, dtype=float)
    return valeurs[int(rng.choice(len(valeurs), p=p / p.sum()))]


def moment(jour: date, rng) -> datetime:
    """Heure ouvrable aléatoire (8 h – 17 h) pour un jour donné, en UTC (= Dakar)."""
    return datetime(jour.year, jour.month, jour.day, int(rng.integers(8, 17)),
                    int(rng.integers(0, 60)), tzinfo=timezone.utc)


def tirer_date_demande(rng) -> date:
    """Plus de dossiers récents que d'anciens (portefeuille en croissance), jamais le dimanche."""
    decalage = int(730 * np.sqrt(rng.random()))
    jour = DEBUT + timedelta(days=decalage)
    if jour.weekday() == 6:
        jour += timedelta(days=1)
    return min(jour, AUJOURDHUI)


def reinitialiser(session) -> None:
    """Vide les tables transactionnelles. Les tables en ajout seul ne se vident que par TRUNCATE
    (les triggers ne bloquent que UPDATE et DELETE)."""
    session.execute(text(
        "TRUNCATE ops.paiement, ops.echeance, ops.credit, ops.decision, audit.journal "
        "RESTART IDENTITY"))
    session.execute(text("DELETE FROM ml.score"))
    session.execute(text("DELETE FROM ops.demande_credit"))
    session.execute(text("DELETE FROM ops.utilisateur WHERE role = 'client'"))
    session.execute(text("DELETE FROM ops.client"))
    session.commit()


def preparer_agents(session, agences) -> dict:
    """Deux agents de crédit par agence (créés au besoin). Renvoie {agence_id: [agents]}."""
    mot_de_passe = os.environ.get("SEED_PASSWORD")
    if not mot_de_passe:
        sys.exit("Définis SEED_PASSWORD dans le fichier .env")
    empreinte = hasher_mot_de_passe(mot_de_passe)
    agents = {}
    i = 0
    for agence in agences:
        agents[agence.id] = []
        for k in (1, 2):
            email = f"agent.{agence.code.lower()}.{k}@imf-demo.test"
            agent = session.scalar(select(Utilisateur).where(Utilisateur.email == email))
            if agent is None:
                agent = Utilisateur(email=email, nom_complet=NOMS_AGENTS[i % len(NOMS_AGENTS)],
                                    mot_de_passe_hash=empreinte, role=Role.AGENT_CREDIT,
                                    agence_id=agence.id)
                session.add(agent)
                session.flush()
            agents[agence.id].append(agent)
            i += 1
    return agents


def facteur_annuite(duree: int, taux_annuel: float) -> float:
    """Mensualité par FCFA emprunté (formule des annuités constantes)."""
    r = taux_annuel / 12
    return r / (1 - (1 + r) ** -duree)


def tirer_demande(p: dict, produits: dict, rng) -> tuple:
    revenu = p["revenu_mensuel"]
    if p["type_revenu"] == "independant":
        code = "PME" if revenu >= 250_000 and rng.random() < 0.30 else "MICRO"
    else:
        code = "SALARIE"
    produit = produits[code]
    duree = DUREES[code][int(rng.integers(0, len(DUREES[code])))]

    # Part du revenu que le client compte consacrer à la mensualité : lognormale de
    # médiane 25 % ; environ 12 % des clients visent plus de 40 % (surestimation)
    charge = float(np.clip(rng.lognormal(np.log(0.20), 0.45), 0.08, 0.80))
    taux = float(produit.taux_annuel) / 100
    montant = charge * revenu / facteur_annuite(duree, taux)
    montant = round(montant / 10_000) * 10_000
    montant = int(min(max(montant, produit.montant_min), produit.montant_max))

    objets = OBJETS.get(p["profession"], OBJETS_DEFAUT)
    return produit, montant, duree, str(rng.choice(objets))
def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--reset", action="store_true",
                         help="vide d'abord les tables transactionnelles")
    args = parseur.parse_args()
    rng = np.random.default_rng(GRAINE + 1)

    with SessionLocal() as session:
        if args.reset:
            if input("Cela efface clients, dossiers, scores, décisions, crédits et paiements. "
                     "Tape OUI pour continuer : ") != "OUI":
                sys.exit("Annulé.")
            reinitialiser(session)
        elif session.scalar(select(Client.id).where(Client.code_client.like("SIM%")).limit(1)):
            sys.exit("Des clients simulés existent déjà. Relance avec --reset.")

        agences = session.scalars(select(Agence).order_by(Agence.id)).all()
        produits = {p.code: p for p in session.scalars(select(ProduitCredit)).all()}
        agents = preparer_agents(session, agences)
        directeur = session.scalar(select(Utilisateur).where(
            Utilisateur.email == "directeur@imf-demo.test"))
        parametres = lire_parametres(session)
        print("Politique appliquée :", parametres)

        poids_ag = np.array([POIDS_AGENCES.get(a.zone, 0.25) for a in agences], dtype=float)
        poids_ag /= poids_ag.sum()
        compteur_annee = {}
        bilan = {"statuts": {}, "reco": {}, "concordance": []}

        for i, p in enumerate(generer_profils(N_CLIENTS), start=1):
            agence = agences[int(rng.choice(len(agences), p=poids_ag))]
            date_dem = tirer_date_demande(rng)
            m0 = moment(date_dem, rng)

            client = Client(
                code_client=f"SIM{i:06d}", nom=p["nom"], prenom=p["prenom"],
                date_naissance=p["date_naissance"], sexe=p["sexe"], telephone=p["telephone"],
                adresse=f"{rng.choice(QUARTIERS.get(agence.zone, ['Centre']))}, {agence.zone}",
                agence_id=agence.id, type_revenu=p["type_revenu"], profession=p["profession"],
                situation_familiale=p["situation_familiale"], type_logement=p["type_logement"],
                anciennete_activite_mois=p["anciennete_activite_mois"],
                nb_enfants=p["nb_enfants"], taille_menage=p["taille_menage"],
                possede_bien_immobilier=p["possede_bien_immobilier"],
                possede_vehicule=p["possede_vehicule"], revenu_mensuel=p["revenu_mensuel"],
                cree_le=m0 - timedelta(hours=1), maj_le=m0 - timedelta(hours=1))
            session.add(client)

            produit, montant, duree, objet = tirer_demande(p, produits, rng)
            instructeur = agents[agence.id][int(rng.integers(0, 2))]
            compteur_annee[date_dem.year] = compteur_annee.get(date_dem.year, 0) + 1
            demande = DemandeCredit(
                numero=f"DC{date_dem.year}-S{compteur_annee[date_dem.year]:05d}",
                produit_id=produit.id, instructeur_id=instructeur.id,
                montant_demande=montant, duree_mois=duree, objet=objet,
                statut=S("brouillon"), date_demande=date_dem,
                donnees_modifiees_le=m0, cree_le=m0, maj_le=m0)
            client_id_pending = client
            session.flush()
            demande.client_id = client.id
            session.add(demande)
            session.flush()

            # Calendrier du dossier : chaque étape a un horodatage
            t_complet = m0 + timedelta(minutes=int(rng.integers(30, 90)))
            t_score = t_complet + timedelta(minutes=int(rng.integers(5, 30)))
            t_instruit = t_score + timedelta(days=int(rng.integers(1, 4)),
                                             hours=int(rng.integers(0, 6)))
            t_soumis = t_instruit + timedelta(hours=int(rng.integers(2, 30)))
            t_decision = t_soumis + timedelta(days=int(rng.integers(1, 5)),
                                              hours=int(rng.integers(0, 6)))

            statut, derniere = "brouillon", m0
            reco = None
            if t_complet <= MAINTENANT:
                statut, derniere = "complet", t_complet
            if t_score <= MAINTENANT:
                reco, variables = evaluer_dossier(client, demande, produit, parametres)
                montant_sug = (demande.montant_demande if reco["decision"] == "accord"
                               else reco["montant"])
                score = Score(
                    demande_id=demande.id, version_modele=VERSION_MODELE,
                    p_defaut=reco["p_demande"], seuil_applique=parametres["seuil_defaut"],
                    recommandation=reco["decision"], montant_suggere=montant_sug,
                    p_montant_suggere=reco["p_defaut"], variables_entree=variables,
                    facteurs={"motifs": reco["motifs"],
                              "endettement_demande": round(reco["endettement_demande"], 3),
                              "parametres": parametres},
                    calcule_le=t_score)
                session.add(score)
                session.flush()
                statut, derniere = "score", t_score
                bilan["reco"][reco["decision"]] = bilan["reco"].get(reco["decision"], 0) + 1
            if t_instruit <= MAINTENANT and reco is not None:
                demande.avis_instruction = str(rng.choice(AVIS))
                demande.avis_instruction_le = t_instruit
                statut, derniere = "instruit", t_instruit
            if t_soumis <= MAINTENANT and reco is not None:
                statut, derniere = "soumis_decision", t_soumis

            if t_decision <= MAINTENANT and reco is not None:
                choix = choisir(rng, CHOIX_DIRECTEUR[reco["decision"]])
                montant_acc = duree_acc = None
                if choix == TypeDecision.ACCORDER:
                    montant_acc, duree_acc = demande.montant_demande, demande.duree_mois
                elif choix == TypeDecision.ACCORDER_MODIFIE:
                    if reco["decision"] == "accord_reduit":
                        montant_acc = int(reco["montant"])
                    else:
                        reduit = round(demande.montant_demande * rng.uniform(0.5, 0.8) / 10_000) * 10_000
                        montant_acc = int(max(reduit, produit.montant_min))
                    duree_acc = demande.duree_mois
                concordance = choix == EQUIVALENT[reco["decision"]]
                commentaire = MOTIFS.get((reco["decision"], choix))
                if concordance and rng.random() < 0.4:
                    commentaire = "Conforme à l'analyse du dossier."
                session.add(Decision(
                    demande_id=demande.id, score_id=score.id, decideur_id=directeur.id,
                    decision=choix, montant_accorde=montant_acc, duree_accordee=duree_acc,
                    commentaire=commentaire, recommandation_modele=reco["decision"],
                    concordance=concordance, decide_le=t_decision))
                statut, derniere = STATUT_DECISION[choix], t_decision
                bilan["concordance"].append(concordance)

            demande.statut = S(statut)
            demande.maj_le = derniere
            bilan["statuts"][statut] = bilan["statuts"].get(statut, 0) + 1
            if i % 250 == 0:
                session.flush()
                print(f"  {i} clients traités…")

        session.commit()

    print("\nStatuts des dossiers :", dict(sorted(bilan["statuts"].items())))
    print("Recommandations du modèle :", bilan["reco"])
    if bilan["concordance"]:
        taux = 100 * sum(bilan["concordance"]) / len(bilan["concordance"])
        print(f"Décisions : {len(bilan['concordance'])}, concordantes avec le modèle : {taux:.1f} %")


if __name__ == "__main__":
    main()