from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.deps import exiger_roles, get_session
from app.models import Journal, Utilisateur
from app.models.enums import Role
from app.rapports.donnees import construire_rapport
from app.rapports.excel import generer_excel
from app.rapports.pdf import generer_pdf

router = APIRouter(prefix="/rapports", tags=["rapports"])

DIRECTION = (Role.DECIDEUR,)
TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}


@router.get("/activite")
def rapport_activite(
        periode: Literal["jour", "mois", "annee"] = "mois",
        jour: date | None = Query(None, description="Un jour de la période voulue (défaut : aujourd'hui)"),
        format_fichier: Literal["xlsx", "pdf"] = Query("xlsx", alias="format"),
        session: Session = Depends(get_session),
        utilisateur: Utilisateur = Depends(exiger_roles(*DIRECTION))):
    rapport = construire_rapport(session, periode, jour or date.today())
    if format_fichier == "xlsx":
        contenu = generer_excel(rapport)
    else:
        contenu = generer_pdf(rapport)

    session.add(Journal(
        utilisateur_id=utilisateur.id, action="rapport_genere", entite="rapport", entite_id=0,
        details={"periode": periode, "debut": str(rapport["debut"]),
                 "fin": str(rapport["fin"]), "format": format_fichier}))
    session.commit()

    nom = f"rapport_activite_{periode}_{rapport['debut']}.{format_fichier}"
    return Response(content=contenu, media_type=TYPES[format_fichier],
                    headers={"Content-Disposition": f'attachment; filename="{nom}"'})