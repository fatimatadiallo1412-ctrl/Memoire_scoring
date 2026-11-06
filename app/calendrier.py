"""Génération du calendrier de remboursement à mensualités constantes."""
import calendar
from datetime import date


def ajouter_mois(depart: date, n: int) -> date:
    """Date située n mois après 'depart'. Si le jour n'existe pas dans le
    mois cible (ex. 31 janvier + 1 mois), on prend le dernier jour du mois."""
    index = depart.month - 1 + n
    annee = depart.year + index // 12
    mois = index % 12 + 1
    jour = min(depart.day, calendar.monthrange(annee, mois)[1])
    return date(annee, mois, jour)


def mensualite_constante(montant: int, duree_mois: int, taux_annuel: float) -> int:
    """Mensualité d'un prêt amorti (formule des annuités constantes)."""
    r = taux_annuel / 12
    if r == 0:
        return round(montant / duree_mois)
    return round(montant * r / (1 - (1 + r) ** -duree_mois))


def generer_calendrier(montant: int, duree_mois: int, taux_annuel: float,
                       date_decaissement: date) -> list[dict]:
    """Liste des échéances : numero, date, montant_du, capital, interet."""
    r = taux_annuel / 12
    mensualite = mensualite_constante(montant, duree_mois, taux_annuel)
    solde = montant
    lignes = []
    for k in range(1, duree_mois + 1):
        interet = round(solde * r)
        if k == duree_mois:
            capital = solde                 # la dernière échéance solde le crédit
        else:
            capital = mensualite - interet
        lignes.append({
            "numero": k,
            "date_echeance": ajouter_mois(date_decaissement, k),
            "montant_du": capital + interet,
            "capital": capital,
            "interet": interet,
        })
        solde -= capital
    return lignes