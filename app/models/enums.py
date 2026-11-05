import enum


class Role(str, enum.Enum):
    AGENT_CREDIT = "agent_credit"
    DECIDEUR = "decideur"
    ADMINISTRATEUR = "administrateur"
    CLIENT = "client"


class StatutDossier(str, enum.Enum):
    BROUILLON = "brouillon"
    COMPLET = "complet"
    SCORE = "score"
    INSTRUIT = "instruit"
    SOUMIS = "soumis_decision"
    ACCORDE = "accorde"
    ACCORDE_MODIFIE = "accorde_modifie"
    REFUSE = "refuse"
    AJOURNE = "ajourne"
    DECAISSE = "decaisse"
    EN_REMBOURSEMENT = "en_remboursement"
    SOLDE = "solde"
    CONTENTIEUX = "contentieux"

class TypeDecision(str, enum.Enum):
    ACCORDER = "accorder"
    ACCORDER_MODIFIE = "accorder_modifie"
    REFUSER = "refuser"
    AJOURNER = "ajourner"