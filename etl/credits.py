"""Chargement des faits liés aux crédits : crédits, échéances, paiements, portefeuille mensuel.

Les retards sont calculés par app.suivi : même logique que l'API.
"""
import calendar
from collections import defaultdict
from datetime import date
from types import SimpleNamespace

from sqlalchemy import text

from app.suivi import situation_credit


def cle(d: date) -> int:
    """Clé de la dimension temps : AAAAMMJJ."""
    return d.year * 10000 + d.month * 100 + d.day


def fins_de_mois(depart: date, fin: date):
    """Derniers jours de chaque mois, du mois de `depart` jusqu'à `fin` incluse."""
    annee, mois = depart.year, depart.month
    while True:
        dernier = date(annee, mois, calendar.monthrange(annee, mois)[1])
        if dernier > fin:
            return
        yield dernier
        mois += 1
        if mois == 13:
            annee, mois = annee + 1, 1


def inserer(connexion, table: str, lignes: list[dict]) -> None:
    if not lignes:
        return
    colonnes = list(lignes[0])
    sql = (f"INSERT INTO dwh.{table} ({', '.join(colonnes)}) "
           f"VALUES ({', '.join(':' + c for c in colonnes)})")
    connexion.execute(text(sql), lignes)


def charger_credits(connexion, aujourdhui: date) -> None:
    credits = connexion.execute(text("""
        SELECT k.id, k.demande_id, k.client_id, c.agence_id, d.produit_id, k.decaisse_par,
               d.statut::text AS statut, k.montant_accorde, k.mensualite, k.taux_annuel,
               k.duree_mois, k.date_decaissement
        FROM ops.credit k
        JOIN ops.demande_credit d ON d.id = k.demande_id
        JOIN ops.client c ON c.id = k.client_id
        ORDER BY k.id""")).mappings().all()

    echeances = defaultdict(list)
    for e in connexion.execute(text(
            "SELECT id, credit_id, numero, date_echeance, montant_du, capital, interet "
            "FROM ops.echeance ORDER BY credit_id, numero")).mappings():
        echeances[e["credit_id"]].append(SimpleNamespace(**dict(e)))

    paiements = defaultdict(list)
    for p in connexion.execute(text(
            "SELECT id, credit_id, montant, date_paiement, mode, enregistre_par "
            "FROM ops.paiement ORDER BY date_paiement, id")).mappings():
        paiements[p["credit_id"]].append(dict(p))

    f_credit, f_echeance, f_paiement, f_mensuel = [], [], [], []
    for k in credits:
        ech, pays = echeances[k["id"]], paiements[k["id"]]
        par_numero = {e.numero: e for e in ech}
        situation = situation_credit(ech, sum(p["montant"] for p in pays), aujourdhui)
        jours = situation["jours_retard_max"]
        axes = {"client_key": k["client_id"], "agence_key": k["agence_id"],
                "produit_key": k["produit_id"]}

        f_credit.append({
            **axes, "credit_key": k["id"], "demande_key": k["demande_id"],
            "date_decaissement_key": cle(k["date_decaissement"]),
            "agent_key": k["decaisse_par"], "statut": k["statut"],
            "montant_decaisse": k["montant_accorde"], "mensualite": k["mensualite"],
            "taux_annuel": k["taux_annuel"], "duree_mois": k["duree_mois"],
            "total_du": situation["total_du"], "total_paye": situation["total_paye"],
            "reste_a_payer": situation["reste_a_payer"],
            "capital_restant": situation["capital_restant"],
            "nb_echeances_en_retard": situation["nb_echeances_en_retard"],
            "montant_en_retard": situation["montant_en_retard"],
            "jours_retard_max": jours, "est_solde": int(situation["solde"]),
            "est_retard_30": int(jours > 30), "est_contentieux": int(jours > 90)})

        for ligne in situation["echeances"]:
            origine = par_numero[ligne["numero"]]
            f_echeance.append({
                **axes, "echeance_key": origine.id, "credit_key": k["id"],
                "numero": ligne["numero"], "date_echeance_key": cle(ligne["date_echeance"]),
                "montant_du": ligne["montant_du"], "capital": ligne["capital"],
                "interet": origine.interet, "montant_paye": ligne["montant_paye"],
                "reste_du": ligne["reste_du"], "statut": ligne["statut"],
                "jours_retard": ligne["jours_retard"]})

        for p in pays:
            f_paiement.append({
                **axes, "paiement_key": p["id"], "credit_key": k["id"],
                "date_paiement_key": cle(p["date_paiement"]), "agent_key": p["enregistre_par"],
                "montant": p["montant"], "mode": p["mode"]})

        # Instantanés : situation du crédit à chaque fin de mois, puis aujourd'hui
        dates = list(fins_de_mois(k["date_decaissement"], aujourdhui))
        if not dates or dates[-1] != aujourdhui:
            dates.append(aujourdhui)
        for m in dates:
            paye_a_m = sum(p["montant"] for p in pays if p["date_paiement"] <= m)
            s = situation_credit(ech, paye_a_m, m)
            f_mensuel.append({
                **axes, "credit_key": k["id"], "date_key": cle(m),
                "capital_restant": s["capital_restant"], "reste_a_payer": s["reste_a_payer"],
                "jours_retard_max": s["jours_retard_max"],
                "est_retard_30": int(s["jours_retard_max"] > 30),
                "est_retard_90": int(s["jours_retard_max"] > 90)})
            if s["solde"]:
                break

    inserer(connexion, "fait_credit", f_credit)
    inserer(connexion, "fait_echeance", f_echeance)
    inserer(connexion, "fait_paiement", f_paiement)
    inserer(connexion, "fait_portefeuille_mensuel", f_mensuel)