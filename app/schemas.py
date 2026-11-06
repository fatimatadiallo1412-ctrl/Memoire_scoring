from pydantic import BaseModel, ConfigDict
from app.models.enums import Role
from datetime import date, datetime
from typing import Literal
from pydantic import Field, field_validator
from app.models.enums import StatutDossier

class UtilisateurOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nom_complet: str
    role: Role


class Jeton(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ClientIn(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    date_naissance: date
    sexe: Literal["F", "M"] | None = None
    telephone: str | None = Field(default=None, max_length=20)
    adresse: str | None = Field(default=None, max_length=200)
    agence_id: int
    type_revenu: Literal["salarie_prive", "fonctionnaire", "independant", "retraite"]
    profession: str | None = Field(default=None, max_length=60)
    situation_familiale: Literal["celibataire", "marie", "divorce", "veuf"]
    type_logement: Literal["proprietaire", "locataire", "famille", "logement_fonction"]
    anciennete_activite_mois: int = Field(default=0, ge=0)
    nb_enfants: int = Field(default=0, ge=0, le=30)
    taille_menage: int = Field(default=1, ge=1, le=40)
    possede_bien_immobilier: bool = False
    possede_vehicule: bool = False
    revenu_mensuel: int = Field(default=0, ge=0)

    @field_validator("date_naissance")
    @classmethod
    def majeur(cls, valeur: date) -> date:
        aujourdhui = date.today()
        age = aujourdhui.year - valeur.year - ((aujourdhui.month, aujourdhui.day) < (valeur.month, valeur.day))
        if age < 18:
            raise ValueError("Le client doit être majeur")
        return valeur


class ClientOut(ClientIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code_client: str
    cree_le: datetime
    maj_le: datetime

class DemandeIn(BaseModel):
    client_id: int
    produit_id: int
    montant_demande: int = Field(gt=0)
    duree_mois: int = Field(gt=0, le=120)
    objet: str | None = Field(default=None, max_length=200)
    date_demande: date | None = None


class DemandeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    client_id: int
    produit_id: int
    instructeur_id: int
    montant_demande: int
    duree_mois: int
    objet: str | None
    statut: StatutDossier
    date_demande: date
    avis_instruction: str | None
    cree_le: datetime
    maj_le: datetime