"""Règles de format communes : téléphone sénégalais et adresse Gmail.

Les mêmes règles sont appliquées dans le front (frontend/src/validation.js).
"""
import re

# Mobile sénégalais : 9 chiffres, préfixe opérateur 70, 71, 75, 76, 77 ou 78.
MOTIF_TELEPHONE = re.compile(r"^7[015678]\d{7}$")
# Adresse Gmail : partie locale simple, domaine gmail.com uniquement.
MOTIF_GMAIL = re.compile(r"^[a-z0-9._%+-]+@gmail\.com$")

MESSAGE_TELEPHONE = "numéro invalide : 9 chiffres commençant par 70, 71, 75, 76, 77 ou 78"
MESSAGE_GMAIL = "adresse e-mail invalide : seules les adresses @gmail.com sont acceptées"


def valider_telephone(valeur: str | None) -> str | None:
    """Accepte les espaces à la saisie (« 77 123 45 67 ») et renvoie les 9 chiffres collés."""
    if valeur is None:
        return None
    nettoye = re.sub(r"\s+", "", valeur)
    if nettoye == "":
        return None
    if not MOTIF_TELEPHONE.match(nettoye):
        raise ValueError(MESSAGE_TELEPHONE)
    return nettoye


def valider_gmail(valeur: str) -> str:
    valeur = valeur.strip().lower()
    if not MOTIF_GMAIL.match(valeur):
        raise ValueError(MESSAGE_GMAIL)
    return valeur
