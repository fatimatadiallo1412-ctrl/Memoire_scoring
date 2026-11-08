from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.assistant.politesse import analyser
from app.assistant.reponses import REMERCIEMENT, repondre
from app.db import get_session
from app.models import Journal, Utilisateur
from app.routers.moi import client_connecte

router = APIRouter(prefix="/moi/assistant", tags=["assistant client"])


class QuestionIn(BaseModel):
    message: str = Field(min_length=1, max_length=300)


class ReponseOut(BaseModel):
    intention: str          # plusieurs intentions possibles, séparées par « + »
    confiance: float        # la plus faible des confiances retenues
    reponse: str
    langue: str = "fr"


@router.post("", response_model=ReponseOut)
def poser_question(donnees: QuestionIn, session: Session = Depends(get_session),
                   utilisateur: Utilisateur = Depends(client_connecte)):
    intentions, salue, remercie = analyser(donnees.message)
    reponse = "\n\n".join(repondre(i, session, utilisateur) for i, _ in intentions)
    if salue:
        reponse = "Bonjour ! " + reponse
    if remercie and intentions[0][0] != "non_compris":
        reponse = reponse + "\n\n" + REMERCIEMENT

    noms = [i for i, _ in intentions]
    confiance = min(c for _, c in intentions)

    # Minimisation des données : on journalise les intentions, pas le texte saisi
    session.add(Journal(
        utilisateur_id=utilisateur.id, action="assistant_question", entite="assistant",
        entite_id=0, details={"intentions": noms, "confiance": round(confiance, 3)}))
    session.commit()
    return ReponseOut(intention="+".join(noms), confiance=round(confiance, 3), reponse=reponse)