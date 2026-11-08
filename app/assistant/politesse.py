"""Prétraitement des messages : politesse, puis découpage en questions.

Un client écrit souvent « Bonjour, quel est mon solde et ma date de remboursement ? merci ».
Le classifieur ne choisit qu'une intention par texte. On retire donc la politesse, on découpe
le reste en questions et on classe chacune (mêmes seuils de confiance).

Garde-fou : ce traitement n'est retenu que s'il trouve au moins une question de service.
Sinon on classe le message entier, tel que le modèle a été validé (sans accents retirés ni
apostrophes modifiées).
"""
import re

from app.assistant.classifieur import SERVICES, comprendre

SALUTATIONS = (r"\b(?:bonjour|bonsoir|salut|slt|bjr|bsr|coucou|hello|a?ssalam\w*|salam\w*"
               r"|\w*al[ae]y?k(?:ou|u|o)?m)\b")
REMERCIEMENTS = (r"\b(?:merci(?:\s+(?:beaucoup|bien|encore))?|je\s+vous\s+remercie"
                 r"|au\s+revoir|[àa]\s+bient[ôo]t|bonne\s+(?:journ[ée]e|soir[ée]e))\b")
FORMULES = r"\b(?:s['’ ]?il\s+(?:vous|te)\s+pla[iî]t|svp|stp)\b"
PONCTUATION_BORDS = " ,;.!:-"
LIENS = r"\b(?:et|puis|alors|ok)\b"
SEPARATEURS = r"\s*(?:[,;?]|\bet\b|\bpuis\b|\baussi\b|\bainsi\s+que\b)\s*"

# Nombre maximal de questions traitées dans un même message.
INTENTIONS_MAX = 3


def separer_politesse(texte: str) -> tuple[str, bool, bool]:
    """Renvoie (reste du message, a salué, a remercié). Le texte reste en minuscules, accentué."""
    bas = texte.lower()
    salue = re.search(SALUTATIONS, bas) is not None
    remercie = re.search(REMERCIEMENTS, bas) is not None

    reste = re.sub(SALUTATIONS, " ", bas)
    reste = re.sub(REMERCIEMENTS, " ", reste)
    reste = re.sub(FORMULES, " ", reste)
    reste = re.sub(r"\s+", " ", reste).strip(PONCTUATION_BORDS)
    reste = re.sub(rf"^(?:{LIENS}[\s,;.!:-]*)+", "", reste)
    reste = re.sub(rf"(?:[\s,;.!:-]*{LIENS})+$", "", reste)
    return reste.strip(PONCTUATION_BORDS), salue, remercie


def decouper(reste: str) -> list[str]:
    """Découpe le message en questions séparées par « et », « puis », une virgule, etc."""
    morceaux = re.split(SEPARATEURS, reste)
    return [m.strip(PONCTUATION_BORDS) for m in morceaux if m.strip(PONCTUATION_BORDS)]


def analyser(texte: str) -> tuple[list[tuple[str, float]], bool, bool]:
    """Renvoie (liste de (intention, confiance), a salué, a remercié)."""
    reste, salue, remercie = separer_politesse(texte)

    services: list[tuple[str, float]] = []
    for morceau in decouper(reste):
        intention, confiance = comprendre(morceau)
        if intention in SERVICES and all(intention != i for i, _ in services):
            services.append((intention, confiance))

    if services:
        return services[:INTENTIONS_MAX], salue, remercie

    # Pas de question de service : comportement validé, message entier, réponse seule.
    return [comprendre(texte)], False, False