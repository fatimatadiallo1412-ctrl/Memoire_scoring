"""Recours : ce qu'un client refusé (ou partiellement accordé) peut changer pour être accepté
à sa prochaine demande.

Deux sources, toujours distinguées :

1. Le modèle : on recalcule réellement le risque et l'endettement d'autres scénarios
   (montant, durée, revenu justifié, attente). Un plan n'est proposé que s'il respecte
   la politique (risque <= seuil, endettement <= maximum). Seuls des leviers sur lesquels
   le client peut agir sont explorés : jamais l'âge, la famille, la profession, le logement
   ou les biens possédés (variables fixes, ou corrélations qu'il serait faux de présenter
   comme des causes).
2. L'institution : règles de bonne pratique en microfinance (épargne préalable, garantie,
   groupement, mobile money, saisonnalité, crédit progressif). Elles ne sont PAS issues du
   modèle v4, qui n'utilise pas ces variables : elles renforcent le dossier lors du
   réexamen, sans garantie d'accord.

Le module ne dépend ni de la base ni de l'API.
"""
from itertools import product

import pandas as pd

from src.features import PLAFOND_RATIO_CREDIT
from src.suggestion import mensualite

# Valeurs par défaut des paramètres du recours (réglables par le directeur, voir app/parametres.py)
MOIS_EPARGNE = 3            # durée de l'épargne préalable conseillée
PART_NANTIE = 0.10          # épargne nantie conseillée, en part du montant
HAUSSE_REVENU_MAX = 0.30    # hausse de revenu justifié jugée réaliste
ATTENTE_MAX_MOIS = 12       # attente maximale conseillée

# Difficulté de chaque levier pour le client, utilisée pour classer les plans :
# +10 % de revenu justifié ≈ 6 mois d'attente ≈ -10 % de montant ≈ 2 × 6 mois de durée en plus ou en moins.
COUT_HAUSSE_REVENU_10PCT = 1.0
COUT_ATTENTE_6_MOIS = 1.0
COUT_REDUCTION_10PCT = 1.0
COUT_DUREE_6_MOIS = 0.5

NB_PLANS_MAX = 3

# Variables du modèle que le recours a le droit de faire varier. Toute autre variable reste
# celle de la fiche client (vérifié par les tests).
VARIABLES_MODIFIABLES = {"age_ans", "anciennete_emploi_ans", "credit_sur_revenu",
                         "annuite_sur_revenu", "duree_implicite"}


def fcfa(montant) -> str:
    return f"{int(round(montant)):,}".replace(",", " ") + " FCFA"


def _arrondi_haut(valeur, pas=5_000):
    return int(-(-valeur // pas) * pas)


def _lignes(profil, scenarios, colonnes, taux_annuel):
    """Lignes au format du modèle (mêmes formules que src.suggestion.construire_ligne)."""
    lignes = []
    for s in scenarios:
        ligne = dict(profil)
        if s["attente"]:
            ligne["age_ans"] = profil["age_ans"] + s["attente"] / 12
            if not profil.get("sans_emploi"):
                ligne["anciennete_emploi_ans"] = profil["anciennete_emploi_ans"] + s["attente"] / 12
        annuite = mensualite(s["montant"], s["duree"], taux_annuel)
        ligne["credit_sur_revenu"] = min(s["montant"] / s["revenu"], PLAFOND_RATIO_CREDIT)
        ligne["annuite_sur_revenu"] = min(annuite / s["revenu"], 1)
        ligne["duree_implicite"] = s["montant"] / annuite
        lignes.append(ligne)
    return pd.DataFrame(lignes)[colonnes]


def _montants(montant_demande, montant_min, pas, fixe):
    if fixe:
        return [montant_demande]
    montants = list(range(montant_demande, montant_min - 1, -pas)) or [montant_demande]
    if montants[-1] != montant_min and montant_min < montant_demande:
        montants.append(montant_min)
    # Au plus 30 montants : au-delà, on espace les essais.
    if len(montants) > 30:
        saut = -(-len(montants) // 30)
        montants = montants[::saut] + ([montant_min] if montants[::saut][-1] != montant_min else [])
    return montants


def _durees(duree, duree_min, duree_max):
    candidates = {duree + d for d in (-12, -6, -3, 0, 3, 6, 12)}
    return sorted(d for d in candidates if duree_min <= d <= duree_max) or [duree]


def _cout(s, montant_demande, duree):
    return (COUT_HAUSSE_REVENU_10PCT * s["hausse"] * 10
            + COUT_ATTENTE_6_MOIS * s["attente"] / 6
            + COUT_REDUCTION_10PCT * (1 - s["montant"] / montant_demande) * 10
            + COUT_DUREE_6_MOIS * abs(s["duree"] - duree) / 6)


def _leviers(s, montant_demande, duree):
    leviers = []
    if s["attente"]:
        leviers.append("attente")
    if s["hausse"]:
        leviers.append("revenu")
    if s["montant"] != montant_demande:
        leviers.append("montant")
    if s["duree"] != duree:
        leviers.append("duree")
    return leviers


def chercher_plans(modele, profil, montant_demande, duree, revenu, colonnes, *, taux_annuel,
                   seuil, endettement_max, montant_min, duree_min, duree_max, pas,
                   montant_fixe=False, hausse_revenu_max=HAUSSE_REVENU_MAX,
                   attente_max=ATTENTE_MAX_MOIS):
    """Les plans les plus simples qui font entrer la demande dans la politique.

    montant_fixe : pour un accord réduit, on cherche comment obtenir le montant demandé en entier.
    Renvoie au plus NB_PLANS_MAX plans, du plus simple au plus exigeant ; une liste vide si aucun
    scénario réaliste (dans les limites fixées par la politique) ne suffit.
    """
    hausses = [round(h / 100, 2) for h in range(0, int(round(hausse_revenu_max * 100)) + 1, 10)]
    # Attendre ne fait pas avancer l'ancienneté d'un client sans activité déclarée : levier exclu.
    attentes = [0] if profil.get("sans_emploi") else [a for a in (0, 3, 6, 12) if a <= attente_max]

    scenarios = []
    for m, d, h, a in product(_montants(montant_demande, montant_min, pas, montant_fixe),
                              _durees(duree, duree_min, duree_max), hausses, attentes):
        r = revenu * (1 + h)
        endettement = mensualite(m, d, taux_annuel) / r
        if endettement <= endettement_max:
            scenarios.append({"montant": m, "duree": d, "hausse": h, "attente": a,
                              "revenu": r, "endettement": endettement})
    if not scenarios:
        return []

    probas = modele.predict_proba(_lignes(profil, scenarios, colonnes, taux_annuel))[:, 1]
    faisables = []
    for s, p in zip(scenarios, probas):
        if p <= seuil:
            s["p_defaut"] = float(p)
            s["leviers"] = _leviers(s, montant_demande, duree)
            s["cout"] = _cout(s, montant_demande, duree)
            faisables.append(s)
    retenus = (_plans_montant_fixe(faisables) if montant_fixe
               else _frontiere_effort_montant(faisables, duree))
    return [{
        "montant": s["montant"],
        "duree_mois": s["duree"],
        "attente_mois": s["attente"],
        "hausse_revenu": s["hausse"],
        "revenu_vise": _arrondi_haut(s["revenu"]) if s["hausse"] else int(revenu),
        "mensualite": round(mensualite(s["montant"], s["duree"], taux_annuel)),
        "endettement": round(s["endettement"], 4),
        "p_defaut": round(s["p_defaut"], 4),
        "leviers": s["leviers"],
        "texte": texte_plan(s, revenu, taux_annuel),
    } for s in retenus]


def _plans_montant_fixe(faisables):
    """Montant demandé imposé : les façons les plus simples de l'obtenir, avec des leviers différents."""
    # Ex aequo : on préfère le risque le plus faible.
    faisables = sorted(faisables, key=lambda s: (round(s["cout"], 6), s["p_defaut"]))
    retenus = []
    for s in faisables:
        # Un plan qui utilise les mêmes leviers qu'un plan déjà retenu (ou davantage) est plus exigeant : écarté.
        if any(set(r["leviers"]) <= set(s["leviers"]) for r in retenus):
            continue
        retenus.append(s)
        if len(retenus) == NB_PLANS_MAX:
            break
    return retenus


def _effort(s):
    return COUT_HAUSSE_REVENU_10PCT * s["hausse"] * 10 + COUT_ATTENTE_6_MOIS * s["attente"] / 6


def _frontiere_effort_montant(faisables, duree):
    """Montant libre : compromis entre l'effort demandé au client (attente, revenu) et le montant obtenu.

    Pour chaque niveau d'effort, on garde le plus gros montant accordable (à durée la plus proche de
    la durée demandée). On ne retient ensuite que les efforts qui rapportent davantage que tous les
    efforts plus faibles (frontière de Pareto), et on en présente au plus trois : le plus simple,
    celui qui s'approche le plus de la demande, et un compromis entre les deux."""
    meilleurs = {}
    for s in faisables:
        cle = (s["hausse"], s["attente"])
        rang = (s["montant"], -abs(s["duree"] - duree), -s["p_defaut"])
        if cle not in meilleurs or rang > meilleurs[cle][0]:
            meilleurs[cle] = (rang, s)
    par_effort = sorted((s for _, s in meilleurs.values()),
                        key=lambda s: (round(_effort(s), 6), s["hausse"], s["attente"]))
    frontiere = []
    for s in par_effort:
        if not frontiere or s["montant"] > frontiere[-1]["montant"]:
            frontiere.append(s)
    if len(frontiere) <= NB_PLANS_MAX:
        return frontiere
    return [frontiere[0], frontiere[len(frontiere) // 2], frontiere[-1]]


def texte_plan(s, revenu_actuel, taux_annuel) -> str:
    """Phrase destinée au client, sans aucun chiffre de risque."""
    morceaux = []
    if s["attente"]:
        morceaux.append(f"Dans {s['attente']} mois")
    if s["hausse"]:
        morceaux.append(f"si vous justifiez un revenu mensuel d'au moins {fcfa(_arrondi_haut(s['revenu']))}"
                        f" (aujourd'hui {fcfa(revenu_actuel)})")
    debut = ", ".join(morceaux) or "Dès maintenant"
    debut = debut[0].upper() + debut[1:]
    m = round(mensualite(s["montant"], s["duree"], taux_annuel))
    return (f"{debut}, une demande de {fcfa(s['montant'])} sur {s['duree']} mois "
            f"(mensualité d'environ {fcfa(m)}) entrerait dans les critères de notre politique de crédit.")


# ---- Motifs, en langage simple ---------------------------------------------------------------

def motifs_client(motifs, *, mensualite_demandee, endettement, endettement_max, antecedent):
    """Pourquoi le montant demandé n'a pas été accordé tel quel (aucun chiffre de risque)."""
    textes = []
    if antecedent == "en_cours":
        textes.append({"code": "antecedent_en_cours",
                       "texte": "Vous avez un crédit en retard de plus de 90 jours."})
        return textes
    if "risque_modele" in motifs:
        textes.append({"code": "risque_modele",
                       "texte": "Selon notre analyse, le risque de difficultés de remboursement est trop "
                                "élevé pour le montant et la durée demandés."})
    if "endettement" in motifs:
        textes.append({"code": "endettement",
                       "texte": f"La mensualité ({fcfa(mensualite_demandee)}) représenterait "
                                f"{endettement * 100:.0f} % de votre revenu mensuel, alors que notre "
                                f"politique en autorise au plus {endettement_max * 100:.0f} %."})
    if antecedent == "regularise":
        textes.append({"code": "antecedent_regularise",
                       "texte": "Un retard de paiement passé, aujourd'hui régularisé, est pris en compte : "
                                "notre analyse est plus prudente."})
    return textes


# ---- Règles de l'institution -----------------------------------------------------------------

def recommandations_institution(client, demande, *, mensualite_visee, historique, plan_reduit=None,
                                montant_vise=None, mois_epargne=MOIS_EPARGNE, part_nantie=PART_NANTIE):
    """Conseils fondés sur les règles de l'institution, selon la fiche du client.

    plan_reduit : plan du modèle accordable dès maintenant à un montant plus faible (crédit progressif).
    montant_vise : montant du crédit envisagé (par défaut, le montant demandé), base de l'épargne nantie.
    """
    montant_vise = montant_vise or demande.montant_demande
    reco = []

    def ajouter(code, titre, texte):
        reco.append({"code": code, "source": "institution", "titre": titre, "texte": texte})

    epargne = getattr(client, "epargne_mensuelle", None)
    if epargne is not None and epargne >= mensualite_visee:
        ajouter("epargne_prealable", "Épargne régulière",
                f"Vous épargnez déjà {fcfa(epargne)} par mois : continuez pendant au moins {mois_epargne} mois "
                f"et apportez vos relevés à votre agent. Ils montrent que vous pouvez payer une mensualité "
                f"d'environ {fcfa(mensualite_visee)}.")
    else:
        ajouter("epargne_prealable", "Épargne régulière",
                f"Épargnez au moins {fcfa(mensualite_visee)} par mois pendant {mois_epargne} mois : c'est le "
                f"montant de la mensualité visée. Vous montrerez ainsi que vous pouvez la rembourser.")

    garantie = getattr(demande, "garantie", None)
    if garantie != "epargne_nantie":
        ajouter("epargne_nantie", "Épargne en garantie",
                f"Constituez une épargne bloquée (épargne nantie) d'environ "
                f"{fcfa(_arrondi_haut(part_nantie * montant_vise))}, soit {part_nantie * 100:.0f} % "
                f"du montant visé ({fcfa(montant_vise)}), en garantie du crédit.")
    if garantie in (None, "aucune"):
        ajouter("garant", "Garant ou caution solidaire",
                "Présentez un garant, ou une caution solidaire de membres de votre groupement.")
    if getattr(client, "membre_groupement", None) is not True:
        ajouter("groupement", "Groupement",
                "Rejoignez un groupement (tontine, GIE, coopérative) : l'entraide et le suivi du groupe "
                "renforcent votre dossier.")
    if getattr(client, "usage_mobile_money", None) != "regulier":
        ajouter("mobile_money", "Revenus vérifiables",
                "Faites passer régulièrement vos encaissements et vos paiements par le mobile money ou un "
                "compte : vos revenus deviennent vérifiables.")
    if getattr(client, "activite_saisonniere", None) is True:
        ajouter("saisonnalite", "Activité saisonnière",
                "Votre activité est saisonnière : présentez votre demande avant votre période de forte "
                "activité et demandez à votre agent un calendrier de remboursement adapté.")
    if plan_reduit is not None and (historique or {}).get("nb_credits_anterieurs", 0) == 0:
        ajouter("credit_progressif", "Crédit progressif",
                f"Commencez par un premier crédit de {fcfa(plan_reduit['montant'])} sur "
                f"{plan_reduit['duree_mois']} mois. Bien le rembourser vous permettra de demander "
                f"davantage ensuite.")
    return reco


def regulariser() -> list[dict]:
    return [{"code": "regulariser", "source": "institution", "titre": "Régulariser d'abord",
             "texte": "Régularisez votre crédit en retard avant toute nouvelle demande. Votre agent peut "
                      "vous proposer un échéancier de régularisation."}]
