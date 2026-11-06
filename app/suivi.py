"""Situation d'un crédit à une date donnée : imputation des paiements et retards."""
from datetime import date


def situation_credit(echeances, total_paye: int, aujourdhui: date) -> dict:
    """echeances : objets avec numero, date_echeance, montant_du, capital.
    Les paiements sont imputés dans l'ordre des échéances (la plus ancienne d'abord)."""
    reste_a_imputer = total_paye
    lignes = []
    for e in sorted(echeances, key=lambda e: e.numero):
        paye = min(e.montant_du, reste_a_imputer)
        reste_a_imputer -= paye
        reste_du = e.montant_du - paye

        if reste_du == 0:
            statut, jours = "payee", 0
        elif e.date_echeance < aujourdhui:
            statut, jours = "en_retard", (aujourdhui - e.date_echeance).days
        elif paye > 0:
            statut, jours = "partielle", 0
        else:
            statut, jours = "a_venir", 0

        lignes.append({
            "numero": e.numero, "date_echeance": e.date_echeance,
            "montant_du": e.montant_du, "montant_paye": paye,
            "reste_du": reste_du, "statut": statut, "jours_retard": jours,
            "capital": e.capital,
        })

    total_du = sum(l["montant_du"] for l in lignes)
    en_retard = [l for l in lignes if l["statut"] == "en_retard"]
    return {
        "total_du": total_du,
        "total_paye": total_paye,
        "reste_a_payer": total_du - total_paye,
        "capital_restant": sum(l["capital"] for l in lignes if l["reste_du"] > 0),
        "nb_echeances_en_retard": len(en_retard),
        "montant_en_retard": sum(l["reste_du"] for l in en_retard),
        "jours_retard_max": max((l["jours_retard"] for l in en_retard), default=0),
        "solde": total_du - total_paye == 0,
        "echeances": lignes,
    }