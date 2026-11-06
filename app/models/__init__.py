from app.models.audit import Journal
from app.models.base import Base
from app.models.ml import Score
from app.models.ops import (Agence, Client, Credit, Decision, DemandeCredit,
                            Echeance, Parametre, ProduitCredit, Utilisateur,Paiement)

__all__ = ["Base", "Agence", "Client", "Credit", "Decision", "DemandeCredit",
           "Echeance", "Journal", "Parametre","Paiement", "ProduitCredit", "Score",
           "Utilisateur"]