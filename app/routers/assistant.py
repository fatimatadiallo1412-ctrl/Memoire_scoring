from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.assistant.politesse import analyser
from app.assistant.reponses import REMERCIEMENT, repondre
from app.assistant.reponses_personnel import repondre_personnel
from app.assistant.tiers import REFUS_TIERS, mentionne_un_tiers
from app.db import get_session
from app.deps import exiger_roles
from app.models import Journal, Utilisateur
from app.models.enums import Role
from app.portefeuille import exiger_client
from app.routers.moi import client_connecte

router = APIRouter()

PERSONNEL = (Role.AGENT_CREDIT, Role.DECIDEUR, Role.ADMINISTRATEUR)


class QuestionIn(BaseModel):
    message: str = Field(min_length=1, max_length=300)


class ReponseOut(BaseModel):
    intention: str          # plusieurs intentions possibles, séparées par « + »
    confiance: float        # la plus faible des confiances retenues
    reponse: str
    langue: str = "fr"


class QuestionPersonnelIn(BaseModel):
    client_id: int
    message: str = Field(min_length=1, max_length=300)


class ReponsePersonnelOut(BaseModel):
    client_id: int
    client: str
    intention: str
    confiance: float
    reponse: str


@router.post("/moi/assistant", response_model=ReponseOut, tags=["assistant client"])
def poser_question(donnees: QuestionIn, session: Session = Depends(get_session),
                   utilisateur: Utilisateur = Depends(client_connecte)):
    if mentionne_un_tiers(session, utilisateur, donnees.message):
        # Garde-fou : le client parle d'une autre personne, on ne répond pas
        intentions, reponse = [("tiers_refuse", 1.0)], REFUS_TIERS
    else:
        intentions, salue, remercie = analyser(donnees.message)
        reponse = "\n\n".join(repondre(i, session, utilisateur) for i, _ in intentions)
        if salue:
            reponse = "Bonjour ! " + reponse
        if remercie and intentions[0][0] != "non_compris":
            reponse = reponse + "\n\n" + REMERCIEMENT

    noms = [i for i, _ in intentions]
    confiance = min(c for _, c in intentions)

    # Minimisation des données : on journalise les intentions, jamais le texte saisi
    session.add(Journal(
        utilisateur_id=utilisateur.id, action="assistant_question", entite="assistant",
        entite_id=0, details={"intentions": noms, "confiance": round(confiance, 3)}))
    session.commit()
    return ReponseOut(intention="+".join(noms), confiance=round(confiance, 3), reponse=reponse)


@router.post("/assistant/personnel", response_model=ReponsePersonnelOut,
             tags=["assistant personnel"])
def poser_question_personnel(donnees: QuestionPersonnelIn,
                             session: Session = Depends(get_session),
                             utilisateur: Utilisateur = Depends(exiger_roles(*PERSONNEL))):
    """Le client doit être dans le portefeuille de l'utilisateur (sinon 404)."""
    client = exiger_client(session, donnees.client_id, utilisateur)
    intentions, _, _ = analyser(donnees.message)
    texte = "\n\n".join(repondre_personnel(i, session, client) for i, _ in intentions)
    identite = f"{client.prenom} {client.nom} ({client.code_client})"

    noms = [i for i, _ in intentions]
    confiance = min(c for _, c in intentions)

    # On journalise le client consulté et l'intention, jamais le texte saisi
    session.add(Journal(
        utilisateur_id=utilisateur.id, action="assistant_personnel_question",
        entite="client", entite_id=client.id,
        details={"intentions": noms, "confiance": round(confiance, 3)}))
    session.commit()
    return ReponsePersonnelOut(
        client_id=client.id, client=identite, intention="+".join(noms),
        confiance=round(confiance, 3), reponse=f"Client : {identite}\n\n{texte}")