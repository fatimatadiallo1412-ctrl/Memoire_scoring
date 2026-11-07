"""Décaissements, échéanciers et remboursements simulés (à lancer après peupler.py).

Le comportement de remboursement dépend du type d'activité, du poids de la mensualité
et d'aléas, JAMAIS du score du modèle : ces données ne valident donc pas le modèle.
"""
import sys
from datetime import timedelta
from types import SimpleNamespace

import numpy as np
from sqlalchemy import func, select

from app.calendrier import generer_calendrier, mensualite_constante
from app.db import SessionLocal
from app.models import Client, Credit, Decision, DemandeCredit, Echeance, Paiement, ProduitCredit
from app.suivi import situation_credit
from simulation.peupler import AUJOURDHUI, GRAINE, S, moment

P_RETARD = {"fonctionnaire": 0.05, "salarie_prive": 0.10, "independant": 0.22, "retraite": 0.08}
RISQUE_TYPE = {"fonctionnaire": 0.5, "salarie_prive": 1.0, "independant": 1.3, "retraite": 0.8}
ALEA_BASE = 0.006              # risque mensuel de défaut de base
SEUIL_CHARGE = 0.20            # au-delà, la mensualité pèse sur le comportement
MODES = {
    "independant": [("mobile_money", .60), ("especes", .40)],
    "salarie_prive": [("virement", .40), ("mobile_money", .40), ("especes", .20)],
    "fonctionnaire": [("virement", .50), ("mobile_money", .35), ("especes", .15)],
    "retraite": [("especes", .50), ("mobile_money", .50)],
}


def choisir(rng, options):
    valeurs, poids = zip(*options)
    p = np.array(poids, dtype=float)
    return valeurs[int(rng.choice(len(valeurs), p=p / p.sum()))]


def simuler_paiements(lignes, type_revenu, endettement, rng):
    """Renvoie la liste des (date, montant) payés jusqu'à AUJOURDHUI."""
    excedent = max(endettement - SEUIL_CHARGE, 0.0)
    p_retard = min(P_RETARD[type_revenu] + 0.5 * excedent, 0.60)
    risque = ALEA_BASE * RISQUE_TYPE[type_revenu] * (1 + 4 * excedent)
    paiements, defaut = [], False
    for ligne in lignes:
        if ligne["date_echeance"] > AUJOURDHUI:
            break
        if not defaut and rng.random() < risque:
            defaut = True
        if defaut:
            continue
        retard = 0
        if rng.random() < p_retard:
            retard = min(1 + int(rng.exponential(10)), 60)
        jour = ligne["date_echeance"] + timedelta(days=retard)
        montant = ligne["montant_du"]
        if rng.random() < 0.08 and montant >= 20_000:       # paiement en deux fois
            premier = int(round(montant * rng.uniform(0.4, 0.7)))
            paiements.append((jour, premier))
            jour2 = jour + timedelta(days=int(rng.integers(3, 16)))
            if jour2 <= AUJOURDHUI:
                paiements.append((jour2, montant - premier))
        elif jour <= AUJOURDHUI:
            paiements.append((jour, montant))
    return sorted(paiements)


def main() -> None:
    rng = np.random.default_rng(GRAINE + 2)
    with SessionLocal() as session:
        if session.scalar(select(func.count()).select_from(Credit)):
            sys.exit("Des crédits existent déjà. Relance d'abord : python -m simulation.peupler --reset")

        produits = {p.id: p for p in session.scalars(select(ProduitCredit)).all()}
        accordes = session.execute(
            select(DemandeCredit, Decision)
            .join(Decision, Decision.demande_id == DemandeCredit.id)
            .where(DemandeCredit.statut.in_([S("accorde"), S("accorde_modifie")]))
            .order_by(DemandeCredit.id)).all()

        bilan = {"statuts": {}, "capital": 0, "retards_30": 0, "actifs": 0}
        for n, (demande, decision) in enumerate(accordes, start=1):
            client = session.get(Client, demande.client_id)
            produit = produits[demande.produit_id]

            # Décaissement 1 à 10 jours après la décision (jamais un dimanche)
            jour = decision.decide_le.date() + timedelta(days=int(rng.integers(1, 11)))
            while jour.weekday() == 6:
                jour += timedelta(days=1)
            if jour > AUJOURDHUI:
                continue                    # décaissement pas encore effectué : reste « accordé »

            montant, duree = decision.montant_accorde, decision.duree_accordee
            taux = float(produit.taux_annuel) / 100
            mensualite = mensualite_constante(montant, duree, taux)
            credit = Credit(demande_id=demande.id, client_id=client.id, montant_accorde=montant,
                            duree_mois=duree, taux_annuel=taux, mensualite=mensualite,
                            date_decaissement=jour, decaisse_par=demande.instructeur_id,
                            cree_le=moment(jour, rng))
            session.add(credit)
            session.flush()

            lignes = generer_calendrier(montant, duree, taux, jour)
            session.add_all(Echeance(credit_id=credit.id, **l) for l in lignes)

            endettement = mensualite / max(client.revenu_mensuel, 1)
            paiements = simuler_paiements(lignes, client.type_revenu, endettement, rng)
            for date_p, montant_p in paiements:
                session.add(Paiement(
                    credit_id=credit.id, montant=montant_p, date_paiement=date_p,
                    mode=choisir(rng, MODES[client.type_revenu]),
                    enregistre_par=demande.instructeur_id, cree_le=moment(date_p, rng)))

            situation = situation_credit([SimpleNamespace(**l) for l in lignes],
                                         sum(m for _, m in paiements), AUJOURDHUI)
            if situation["solde"]:
                statut = "solde"
            elif situation["jours_retard_max"] > 90:
                statut = "contentieux"
            else:
                statut = "en_remboursement"
            demande.statut = S(statut)
            derniere = max([credit.cree_le] + [moment(d, rng) for d, _ in paiements[-1:]])
            demande.maj_le = derniere

            bilan["statuts"][statut] = bilan["statuts"].get(statut, 0) + 1
            bilan["capital"] += montant
            if statut != "solde":
                bilan["actifs"] += 1
                if situation["jours_retard_max"] > 30:
                    bilan["retards_30"] += 1
            if n % 250 == 0:
                session.flush()
                print(f"  {n} dossiers accordés traités…")

        session.commit()

    print("\nStatuts des crédits :", dict(sorted(bilan["statuts"].items())))
    print(f"Capital décaissé : {bilan['capital']:,} FCFA".replace(",", " "))
    if bilan["actifs"]:
        print(f"Portefeuille à risque > 30 jours : {bilan['retards_30']} / {bilan['actifs']} "
              f"crédits non soldés ({100 * bilan['retards_30'] / bilan['actifs']:.1f} %)")


if __name__ == "__main__":
    main()