from pydantic import BaseModel, ConfigDict

from app.models.enums import Role


class UtilisateurOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nom_complet: str
    role: Role


class Jeton(BaseModel):
    access_token: str
    token_type: str = "bearer"