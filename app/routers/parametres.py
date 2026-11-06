from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import exiger_roles
from app.models import Journal, Parametre, Utilisateur
from app.models.enums import Role
from app.parametres import PARAMETRES_DEFAUT
from app.schemas import ParametreIn, ParametreOut

router = APIRouter(prefix="/parametres", tags=["paramètres"])


@router.get("", response_model=list[ParametreOut])
def lister_parametres(session: Session = Depends(get_session),
                      utilisateur: Utilisateur = Depends(
                          exiger_roles(Role.AGENT_CREDIT, Role.DECIDEUR, Role.ADMINISTRATEUR))):
    en_base = {p.cle: p for p in session.scalars(select(Parametre))}
    resultat = []
    for cle, (defaut, description, _, _) in PARAMETRES_DEFAUT.items():
        p = en_base.get(cle)
        resultat.append(ParametreOut(
            cle=cle, valeur=float(p.valeur) if p else defaut, description=description,
            modifie_le=p.modifie_le if p else None))
    return resultat


@router.put("/{cle}", response_model=ParametreOut)
def modifier_parametre(cle: str, donnees: ParametreIn, session: Session = Depends(get_session),
                       utilisateur: Utilisateur = Depends(exiger_roles(Role.DECIDEUR))):
    if cle not in PARAMETRES_DEFAUT:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paramètre inconnu")
    defaut, description, mini, maxi = PARAMETRES_DEFAUT[cle]
    if not mini <= donnees.valeur <= maxi:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            f"Valeur hors limites ({mini} à {maxi})")

    parametre = session.get(Parametre, cle)
    ancienne = float(parametre.valeur) if parametre else defaut
    if parametre is None:
        parametre = Parametre(cle=cle, description=description, valeur=donnees.valeur)
        session.add(parametre)
    else:
        parametre.valeur = donnees.valeur
    parametre.modifie_par = utilisateur.id

    session.add(Journal(utilisateur_id=utilisateur.id, action="parametre_modifie",
                        entite="parametre",
                        details={"cle": cle, "ancienne": ancienne, "nouvelle": donnees.valeur}))
    session.commit()
    session.refresh(parametre)
    return ParametreOut(cle=cle, valeur=float(parametre.valeur), description=description,
                        modifie_le=parametre.modifie_le)