"""Données du rapport d'activité, lues dans l'entrepôt (schéma dwh)."""
from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

DEBUT_FIN = "t.date BETWEEN :debut AND :fin"

# feuille Excel, titre, colonnes (titre, clé, format)
TABLES = {
    "remboursements": ("Remboursements", "Remboursements par mode de paiement", [
        ("Mode de paiement", "mode", None),
        ("Paiements", "nb_paiements", "entier"),
        ("Montant", "montant", "fcfa"),
    ]),
    "inclusion_activite": ("Inclusion activité", "Acceptation par type d'activité", [
        ("Type d'activité", "groupe", None),
        ("Décidées", "nb_decidees", "entier"),
        ("Accordées", "nb_accordees", "entier"),
        ("Refusées", "nb_refusees", "entier"),
        ("Taux d'accord", "taux_accord", "pourcent"),
    ]),
    "inclusion_anciennete": ("Inclusion ancienneté", "Acceptation par ancienneté d'activité", [
        ("Ancienneté", "groupe", None),
        ("Décidées", "nb_decidees", "entier"),
        ("Accordées", "nb_accordees", "entier"),
        ("Refusées", "nb_refusees", "entier"),
        ("Taux d'accord", "taux_accord", "pourcent"),
    ]),
    "retards": ("Crédits en retard", "Crédits en retard de plus de 30 jours", [
        ("Client", "code_client", None),
        ("Produit", "produit", None),
        ("Agence", "agence", None),
        ("Jours retard", "jours_retard_max", "entier"),
        ("Éch. en retard", "nb_echeances_en_retard", "entier"),
        ("Montant en retard", "montant_en_retard", "fcfa"),
        ("Reste à payer", "reste_a_payer", "fcfa"),
    ]),
}


def bornes_periode(periode: str, jour: date) -> tuple[date, date]:
    """Premier et dernier jour de la période qui contient `jour`."""
    if periode == "jour":
        return jour, jour
    if periode == "mois":
        return jour.replace(day=1), jour.replace(day=monthrange(jour.year, jour.month)[1])
    if periode == "annee":
        return date(jour.year, 1, 1), date(jour.year, 12, 31)
    raise ValueError(f"Période inconnue : {periode}")


def _nettoyer(valeur):
    """PostgreSQL renvoie les sommes en Decimal : on les ramène à int ou float."""
    if isinstance(valeur, Decimal):
        return int(valeur) if valeur == valeur.to_integral_value() else float(valeur)
    return valeur


def _lignes(session: Session, sql: str, **params) -> list[dict]:
    resultat = session.execute(text(sql), params).mappings().all()
    return [{cle: _nettoyer(v) for cle, v in ligne.items()} for ligne in resultat]


def _taux(numerateur, denominateur):
    return numerateur / denominateur if denominateur else None


def _inclusion(session: Session, colonne: str, debut: date, fin: date) -> list[dict]:
    """Acceptation des demandes décidées, par groupe (colonne de dim_client)."""
    lignes = _lignes(session, f"""
        SELECT cl.{colonne} AS groupe, COUNT(*) AS nb_decidees,
               SUM(d.est_accordee) AS nb_accordees, SUM(d.est_refusee) AS nb_refusees
        FROM dwh.fait_demande d
        JOIN dwh.dim_temps t ON t.date_key = d.date_demande_key
        JOIN dwh.dim_client cl ON cl.client_key = d.client_key
        WHERE {DEBUT_FIN} AND d.est_decidee = 1
        GROUP BY cl.{colonne} ORDER BY nb_decidees DESC""", debut=debut, fin=fin)
    for ligne in lignes:
        ligne["taux_accord"] = _taux(ligne["nb_accordees"], ligne["nb_decidees"])
    return lignes


def construire_rapport(session: Session, periode: str, jour: date) -> dict:
    debut, fin = bornes_periode(periode, jour)
    p = {"debut": debut, "fin": fin}

    demandes = _lignes(session, f"""
        SELECT COUNT(*) AS nb_demandes,
               COUNT(*) FILTER (WHERE d.recommandation = 'accord') AS reco_accord,
               COUNT(*) FILTER (WHERE d.recommandation = 'accord_reduit') AS reco_reduit,
               COUNT(*) FILTER (WHERE d.recommandation = 'refus') AS reco_refus,
               COALESCE(SUM(d.est_decidee), 0) AS nb_decidees,
               COALESCE(SUM(d.est_accordee), 0) AS nb_accordees,
               COALESCE(SUM(d.est_refusee), 0) AS nb_refusees,
               AVG(CAST(d.concordance AS integer)) AS taux_concordance,
               AVG(d.delai_decision_jours) AS delai_moyen_jours,
               COALESCE(SUM(d.montant_demande), 0) AS montant_demande,
               COALESCE(SUM(d.montant_accorde), 0) AS montant_accorde
        FROM dwh.fait_demande d
        JOIN dwh.dim_temps t ON t.date_key = d.date_demande_key
        WHERE {DEBUT_FIN}""", **p)[0]
    demandes["taux_accord"] = _taux(demandes["nb_accordees"], demandes["nb_decidees"])

    decaissements = _lignes(session, f"""
        SELECT COUNT(*) AS nb_credits,
               COALESCE(SUM(c.montant_decaisse), 0) AS montant_decaisse,
               AVG(c.montant_decaisse) AS montant_moyen
        FROM dwh.fait_credit c
        JOIN dwh.dim_temps t ON t.date_key = c.date_decaissement_key
        WHERE {DEBUT_FIN}""", **p)[0]

    # État du portefeuille au dernier chargement de l'entrepôt (pas limité à la période)
    portefeuille = _lignes(session, """
        SELECT COUNT(*) AS nb_credits,
               COUNT(*) FILTER (WHERE est_solde = 0) AS nb_en_cours,
               COUNT(*) FILTER (WHERE est_solde = 1) AS nb_soldes,
               COALESCE(SUM(capital_restant), 0) AS encours,
               COALESCE(SUM(montant_decaisse), 0) - COALESCE(SUM(capital_restant), 0)
                   AS capital_rembourse,
               COUNT(*) FILTER (WHERE est_retard_30 = 1 AND est_solde = 0) AS nb_retard_30,
               COUNT(*) FILTER (WHERE est_contentieux = 1 AND est_solde = 0) AS nb_contentieux
        FROM dwh.fait_credit""")[0]
    portefeuille["par_30"] = _taux(portefeuille["nb_retard_30"], portefeuille["nb_en_cours"])
    portefeuille["par_90"] = _taux(portefeuille["nb_contentieux"], portefeuille["nb_en_cours"])

    remboursements = _lignes(session, f"""
        SELECT p.mode, COUNT(*) AS nb_paiements, SUM(p.montant) AS montant
        FROM dwh.fait_paiement p
        JOIN dwh.dim_temps t ON t.date_key = p.date_paiement_key
        WHERE {DEBUT_FIN}
        GROUP BY p.mode ORDER BY montant DESC""", **p)

    retards = _lignes(session, """
        SELECT cl.code_client, pr.libelle AS produit, a.nom AS agence,
               c.jours_retard_max, c.nb_echeances_en_retard,
               c.montant_en_retard, c.reste_a_payer
        FROM dwh.fait_credit c
        JOIN dwh.dim_client cl ON cl.client_key = c.client_key
        JOIN dwh.dim_produit pr ON pr.produit_key = c.produit_key
        JOIN dwh.dim_agence a ON a.agence_key = c.agence_key
        WHERE c.est_solde = 0 AND c.est_retard_30 = 1
        ORDER BY c.jours_retard_max DESC, c.montant_en_retard DESC""")

    derniere = _lignes(session, """
        SELECT MAX(t.date) AS date FROM dwh.fait_paiement p
        JOIN dwh.dim_temps t ON t.date_key = p.date_paiement_key""")[0]["date"]

    return {
        "periode": periode, "debut": debut, "fin": fin,
        "genere_le": datetime.now(), "donnees_jusqu_au": derniere,
        "demandes": demandes, "decaissements": decaissements,
        "portefeuille": portefeuille,
        "nb_paiements": sum(r["nb_paiements"] for r in remboursements),
        "total_encaisse": sum(r["montant"] for r in remboursements),
        "remboursements": remboursements,
        "inclusion_activite": _inclusion(session, "type_revenu", debut, fin),
        "inclusion_anciennete": _inclusion(session, "tranche_anciennete", debut, fin),
        "retards": retards,
    }


def lignes_synthese(r: dict) -> list[tuple]:
    """(libellé, valeur, format) ; format None = titre de section."""
    d, c, p = r["demandes"], r["decaissements"], r["portefeuille"]
    return [
        ("Demandes de la période", None, None),
        ("Demandes reçues", d["nb_demandes"], "entier"),
        ("Recommandation du modèle : accord", d["reco_accord"], "entier"),
        ("Recommandation du modèle : accord réduit", d["reco_reduit"], "entier"),
        ("Recommandation du modèle : refus", d["reco_refus"], "entier"),
        ("Demandes décidées par le directeur", d["nb_decidees"], "entier"),
        ("Taux d'accord (sur les demandes décidées)", d["taux_accord"], "pourcent"),
        ("Concordance modèle / directeur", d["taux_concordance"], "pourcent"),
        ("Délai moyen de décision (jours)", d["delai_moyen_jours"], "decimal"),
        ("Montant demandé", d["montant_demande"], "fcfa"),
        ("Montant accordé", d["montant_accorde"], "fcfa"),
        ("Décaissements de la période", None, None),
        ("Crédits décaissés", c["nb_credits"], "entier"),
        ("Montant décaissé", c["montant_decaisse"], "fcfa"),
        ("Montant moyen par crédit", c["montant_moyen"], "fcfa"),
        ("Remboursements de la période", None, None),
        ("Paiements enregistrés", r["nb_paiements"], "entier"),
        ("Montant encaissé", r["total_encaisse"], "fcfa"),
        ("Portefeuille (situation au dernier chargement)", None, None),
        ("Crédits décaissés depuis l'origine", p["nb_credits"], "entier"),
        ("Crédits en cours", p["nb_en_cours"], "entier"),
        ("Crédits soldés", p["nb_soldes"], "entier"),
        ("Encours (capital restant dû)", p["encours"], "fcfa"),
        ("Capital remboursé", p["capital_rembourse"], "fcfa"),
        ("PAR 30 (crédits en cours en retard de plus de 30 jours)", p["par_30"], "pourcent"),
        ("PAR 90 (crédits en contentieux, plus de 90 jours)", p["par_90"], "pourcent"),
        ("Crédits en contentieux", p["nb_contentieux"], "entier"),
    ]


def formater(valeur, fmt) -> str:
    """Texte lisible d'une valeur (utilisé par le PDF)."""
    if valeur is None:
        return "n/d"
    if fmt is None:
        return str(valeur).replace("_", " ")
    if fmt == "pourcent":
        return f"{valeur * 100:.1f} %"
    if fmt == "decimal":
        return f"{valeur:.1f}"
    nombre = f"{round(valeur):,}".replace(",", " ")
    return f"{nombre} FCFA" if fmt == "fcfa" else nombre