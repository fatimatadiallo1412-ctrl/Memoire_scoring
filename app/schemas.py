from pydantic import BaseModel, ConfigDict
from app.models.enums import Role
from datetime import date, datetime
from typing import Literal
from pydantic import Field, field_validator
from app.models.enums import StatutDossier
from app.referentiels import PROFESSION
from app.models.enums import TypeDecision

class UtilisateurOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nom_complet: str
    role: Role
    doit_changer_mdp: bool = False


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
    gestionnaire_id: int | None = None
    categorie_profession: str | None = None
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

class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    demande_id: int
    version_modele: str
    p_defaut: float
    seuil_applique: float
    recommandation: str
    montant_suggere: int | None
    p_montant_suggere: float | None
    calcule_le: datetime
    facteurs: dict | None = None
    valide: bool = True

class InstructionIn(BaseModel):
    avis: str = Field(min_length=10, max_length=2000)


class DecisionIn(BaseModel):
    decision: TypeDecision
    montant_accorde: int | None = Field(default=None, gt=0)
    duree_accordee: int | None = Field(default=None, gt=0, le=120)
    commentaire: str | None = Field(default=None, max_length=2000)


class DecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    demande_id: int
    score_id: int | None
    decideur_id: int
    decision: TypeDecision
    montant_accorde: int | None
    duree_accordee: int | None
    commentaire: str | None
    recommandation_modele: str | None
    concordance: bool | None
    decide_le: datetime  
class ParametreIn(BaseModel):
    valeur: float


class ParametreOut(BaseModel):
    cle: str
    valeur: float
    description: str
    modifie_le: datetime | None = None  

from typing import Literal


class DecaissementIn(BaseModel):
    # Date facultative : par défaut, la date du jour
    date_decaissement: date | None = None
    mode_decaissement: Literal["especes", "mobile_money", "virement"] | None = None
    reference: str | None = None   # n° de transaction (obligatoire hors espèces)


class CreditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    demande_id: int
    client_id: int
    montant_accorde: int
    duree_mois: int
    taux_annuel: float
    mensualite: int
    date_decaissement: date
    decaisse_par: int
    mode_decaissement: str | None = None
    reference_decaissement: str | None = None


class EcheanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    numero: int
    date_echeance: date
    montant_du: int
    capital: int
    interet: int    
class PaiementIn(BaseModel):
    montant: int = Field(gt=0)
    date_paiement: date | None = None      # par défaut : aujourd'hui
    mode: Literal["especes", "mobile_money", "virement"] = "especes"


class PaiementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    credit_id: int
    montant: int
    date_paiement: date
    mode: str
    enregistre_par: int


class LigneEcheanceOut(BaseModel):
    numero: int
    date_echeance: date
    montant_du: int
    montant_paye: int
    reste_du: int
    statut: str
    jours_retard: int


class SituationOut(BaseModel):
    total_du: int
    total_paye: int
    reste_a_payer: int
    capital_restant: int
    nb_echeances_en_retard: int
    montant_en_retard: int
    jours_retard_max: int
    solde: bool
    echeances: list[LigneEcheanceOut]
class ProchaineEcheanceOut(BaseModel):
    credit_id: int
    numero: int
    date_echeance: date
    reste_du: int
    en_retard: bool
    jours: int          # jours de retard si en_retard, sinon jours restants


class ClientMaj(BaseModel):
    """Modification partielle d'un client : seuls les champs envoyés sont modifiés."""
    nom: str | None = Field(default=None, min_length=1, max_length=100)
    prenom: str | None = Field(default=None, min_length=1, max_length=100)
    date_naissance: date | None = None
    sexe: Literal["F", "M"] | None = None
    telephone: str | None = Field(default=None, max_length=20)
    adresse: str | None = Field(default=None, max_length=200)
    agence_id: int | None = None
    type_revenu: Literal["salarie_prive", "fonctionnaire", "independant", "retraite"] | None = None
    profession: str | None = Field(default=None, max_length=60)
    situation_familiale: Literal["celibataire", "marie", "divorce", "veuf"] | None = None
    type_logement: Literal["proprietaire", "locataire", "famille", "logement_fonction"] | None = None
    anciennete_activite_mois: int | None = Field(default=None, ge=0)
    nb_enfants: int | None = Field(default=None, ge=0, le=30)
    taille_menage: int | None = Field(default=None, ge=1, le=40)
    possede_bien_immobilier: bool | None = None
    possede_vehicule: bool | None = None
    revenu_mensuel: int | None = Field(default=None, ge=0)
