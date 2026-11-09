"""Garde-fou : refuse les messages qui portent sur une autre personne que le client connecté.

Le cloisonnement des données est déjà garanti par le code (toutes les requêtes passent par
le client connecté). Ce module rend le refus EXPLICITE : sans lui, « solde de Moussa Ndiaye »
afficherait le solde du client connecté, ce qui serait trompeur.
Détection par règles : identifiant d'un autre client, relation à un tiers, nom d'un autre client.
"""
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Client, Utilisateur

REFUS_TIERS = ("Je ne peux répondre qu'aux questions concernant votre propre compte. "
               "Pour toute information sur une autre personne, elle doit se connecter "
               "elle-même ou s'adresser à son agence.")

FICHIER_PHRASES = Path(__file__).resolve().parents[2] / "data" / "assistant" / "phrases.csv"

# Noms propres qui sont aussi des mots courants : jamais pris pour le nom d'un tiers
MOTS_COURANTS_SUPPLEMENTAIRES = frozenset({"marie", "grace", "ange", "rose"})
LONGUEUR_MIN_NOM = 3

IDENTIFIANT = re.compile(
    r"\b(?:client|clients|cl|id|identifiant|code)\s*(?:numero|no|n°|n)?\s*[:#]?\s*(?:cl)?0*(\d{2,})\b")
RELATION = re.compile(
    r"\b(?:mon|ma|mes|son|sa|ses|leur|leurs)\s+(?:beau\s+|belle\s+|grand\s+|petit\s+|petite\s+)?"
    r"(?:mari|epoux|epouse|femme|frere|soeur|pere|mere|fils|fille|oncle|tante|cousin|cousine|"
    r"voisin|voisine|ami|amie|associe|associee|collegue|patron|patronne|employe|employee|"
    r"neveu|niece|parent|parents|enfant|enfants|pere|mere|voisins)\b")
AUTRE_PERSONNE = re.compile(
    r"\b(?:au\s+nom\s+de|quelqu\s+un\s+d\s+autre|une\s+autre\s+personne|une\s+tierce\s+personne|"
    r"un\s+autre\s+client|d\s+autres?\s+clients?|autres?\s+clients?)\b")


def sans_accents(texte: str) -> str:
    decompose = unicodedata.normalize("NFD", texte.lower())
    texte = "".join(c for c in decompose if unicodedata.category(c) != "Mn")
    return re.sub(r"['’`]", " ", texte)


def mots(texte: str) -> set[str]:
    return set(re.findall(r"[a-z]+", sans_accents(texte)))


@lru_cache(maxsize=1)
def vocabulaire_courant() -> frozenset:
    """Mots utilisés dans les exemples de l'assistant : ce ne sont pas des noms de personnes."""
    phrases = pd.read_csv(FICHIER_PHRASES, sep=";", encoding="utf-8")["phrase"]
    vocabulaire = set()
    for phrase in phrases:
        vocabulaire |= mots(phrase)
    return frozenset(vocabulaire | MOTS_COURANTS_SUPPLEMENTAIRES)


def noms_du_client(nom: str, prenom: str) -> set[str]:
    return {m for m in mots(f"{prenom} {nom}") if len(m) >= LONGUEUR_MIN_NOM}


def mentionne_un_tiers(session: Session, utilisateur: Utilisateur, message: str) -> bool:
    norm = sans_accents(message)

    for trouve in IDENTIFIANT.finditer(norm):          # 1. identifiant d'un autre client
        if int(trouve.group(1)) != utilisateur.client_id:
            return True
    if RELATION.search(norm) or AUTRE_PERSONNE.search(norm):   # 2. relation à un tiers
        return True

    candidats = mots(message) - vocabulaire_courant()  # 3. nom ou prénom d'un autre client
    if not candidats:
        return False
    propre = session.get(Client, utilisateur.client_id)
    propres = noms_du_client(propre.nom, propre.prenom) if propre else set()
    for client_id, nom, prenom in session.execute(
            select(Client.id, Client.nom, Client.prenom)).all():
        if client_id == utilisateur.client_id:
            continue
        if (noms_du_client(nom, prenom) - propres) & candidats:
            return True
    return False
