import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Journal, Metier, Utilisateur


def normaliser(texte: str) -> str:
    """Minuscules, sans accents ni ponctuation : sert à reconnaître un métier saisi à la main."""
    texte = texte.lower().strip().replace("œ", "oe").replace("æ", "ae")
    decompose = unicodedata.normalize("NFD", texte)
    sans_accents = "".join(c for c in decompose if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", sans_accents).strip()


def resoudre_metier(session: Session, texte: str, utilisateur: Utilisateur) -> Metier:
    """Renvoie le métier correspondant au texte saisi ; le crée « à classer » s'il n'existe pas.

    Un métier est reconnu par son code ou par son libellé, sans tenir compte des accents,
    des majuscules ni de la ponctuation. Un nouveau métier n'a pas de catégorie du modèle :
    un responsable doit la choisir (voir routers/professions.py).
    """
    cle = normaliser(texte)
    if not cle:
        raise ValueError("Métier vide")
    code = cle.replace(" ", "_")[:60]
    for metier in session.scalars(select(Metier)):
        if metier.code == code or normaliser(metier.libelle) == cle:
            return metier
    libelle = texte.strip()
    nouveau = Metier(code=code, libelle=(libelle[:1].upper() + libelle[1:])[:100],
                     categorie_modele=None, valide=False, cree_par=utilisateur.id)
    session.add(nouveau)
    session.flush()
    session.add(Journal(utilisateur_id=utilisateur.id, action="metier_cree",
                        entite="metier", entite_id=nouveau.id,
                        details={"code": code}))
    return nouveau
