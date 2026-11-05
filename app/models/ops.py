from datetime import date, datetime

from sqlalchemy import (BigInteger, Boolean, CheckConstraint, Date, DateTime,
                        Enum as SAEnum, ForeignKey, Index, Integer, Numeric,
                        String, Text, func)
from sqlalchemy.orm import Mapped, mapped_column

from app.models import enums as E
from app.models.base import Base

SCHEMA = "ops"


def enum_col(enum_cls, name, **kw):
    """Colonne à valeurs fermées : stockée en texte, avec une contrainte CHECK en base."""
    return mapped_column(
        SAEnum(enum_cls, name=name, native_enum=False, length=32,
               create_constraint=True, validate_strings=True,
               values_callable=lambda e: [m.value for m in e]),
        **kw)


class Agence(Base):
    __tablename__ = "agence"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    nom: Mapped[str] = mapped_column(String(100))
    zone: Mapped[str] = mapped_column(String(100))
    actif: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class ProduitCredit(Base):
    __tablename__ = "produit_credit"
    __table_args__ = (
        CheckConstraint("montant_min <= montant_max", name="plage_montant"),
        CheckConstraint("duree_min_mois <= duree_max_mois", name="plage_duree"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    libelle: Mapped[str] = mapped_column(String(100))
    montant_min: Mapped[int] = mapped_column(BigInteger)
    montant_max: Mapped[int] = mapped_column(BigInteger)
    duree_min_mois: Mapped[int] = mapped_column(Integer)
    duree_max_mois: Mapped[int] = mapped_column(Integer)
    taux_annuel: Mapped[float] = mapped_column(Numeric(5, 2))
    actif: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class Client(Base):
    __tablename__ = "client"
    __table_args__ = (
        Index("ix_client_nom_prenom", "nom", "prenom"),
        CheckConstraint("revenu_mensuel >= 0", name="revenu_positif"),
        CheckConstraint("nb_enfants >= 0", name="enfants_positif"),
        CheckConstraint("taille_menage >= 1", name="menage_minimum"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code_client: Mapped[str] = mapped_column(String(20), unique=True)

    # Identité
    nom: Mapped[str] = mapped_column(String(100))
    prenom: Mapped[str] = mapped_column(String(100))
    date_naissance: Mapped[date] = mapped_column(Date)
    sexe: Mapped[str | None] = mapped_column(String(1))   # identification et audit seulement, jamais donné au modèle
    telephone: Mapped[str | None] = mapped_column(String(20), index=True)
    adresse: Mapped[str | None] = mapped_column(String(200))
    agence_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.agence.id"))

    # Variables utilisées par le modèle
    type_revenu: Mapped[str] = mapped_column(String(30))
    profession: Mapped[str | None] = mapped_column(String(60))
    situation_familiale: Mapped[str] = mapped_column(String(30))
    type_logement: Mapped[str] = mapped_column(String(30))
    anciennete_activite_mois: Mapped[int] = mapped_column(Integer, default=0)
    nb_enfants: Mapped[int] = mapped_column(Integer, default=0)
    taille_menage: Mapped[int] = mapped_column(Integer, default=1)
    possede_bien_immobilier: Mapped[bool] = mapped_column(Boolean, default=False)
    possede_vehicule: Mapped[bool] = mapped_column(Boolean, default=False)
    revenu_mensuel: Mapped[int] = mapped_column(BigInteger, default=0)   # en FCFA

    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    maj_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                             onupdate=func.now())


class Utilisateur(Base):
    __tablename__ = "utilisateur"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    nom_complet: Mapped[str] = mapped_column(String(150))
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[E.Role] = enum_col(E.Role, "role")
    agence_id: Mapped[int | None] = mapped_column(ForeignKey(f"{SCHEMA}.agence.id"))
    client_id: Mapped[int | None] = mapped_column(ForeignKey(f"{SCHEMA}.client.id"), unique=True)
    actif: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    derniere_connexion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DemandeCredit(Base):
    """Le dossier : il suit tout le cycle de vie, de la saisie au solde, par son statut."""
    __tablename__ = "demande_credit"
    __table_args__ = (
        CheckConstraint("montant_demande > 0", name="montant_positif"),
        CheckConstraint("duree_mois > 0", name="duree_positive"),
        Index("ix_demande_credit_statut", "statut"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(30), unique=True)
    client_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.client.id"), index=True)
    produit_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.produit_credit.id"))
    instructeur_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.utilisateur.id"))
    montant_demande: Mapped[int] = mapped_column(BigInteger)
    duree_mois: Mapped[int] = mapped_column(Integer)
    objet: Mapped[str | None] = mapped_column(String(200))
    statut: Mapped[E.StatutDossier] = enum_col(
        E.StatutDossier, "statut_dossier", default=E.StatutDossier.BROUILLON)
    date_demande: Mapped[date] = mapped_column(Date)
    avis_instruction: Mapped[str | None] = mapped_column(Text)
    avis_instruction_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Dernière modification des données utiles au scoring : si elle est postérieure
    # au score, le score est invalidé (règle de gestion du cahier des charges).
    donnees_modifiees_le: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    maj_le: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
class Decision(Base):
    """Décision humaine. Table en AJOUT SEUL : une décision n'est jamais modifiée."""
    __tablename__ = "decision"
    __table_args__ = (
        CheckConstraint(
            "decision NOT IN ('accorder', 'accorder_modifie') OR "
            "(montant_accorde IS NOT NULL AND duree_accordee IS NOT NULL)",
            name="montant_si_accord"),
        CheckConstraint(
            "concordance IS DISTINCT FROM FALSE OR "
            "(commentaire IS NOT NULL AND length(trim(commentaire)) > 0)",
            name="motif_si_divergence"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    demande_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.demande_credit.id"), index=True)
    score_id: Mapped[int | None] = mapped_column(ForeignKey("ml.score.id"))
    decideur_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.utilisateur.id"))
    decision: Mapped[E.TypeDecision] = enum_col(E.TypeDecision, "type_decision")
    montant_accorde: Mapped[int | None] = mapped_column(BigInteger)
    duree_accordee: Mapped[int | None] = mapped_column(Integer)
    commentaire: Mapped[str | None] = mapped_column(Text)
    # Recommandation du modèle au moment de la décision, conservée À PART de la décision
    recommandation_modele: Mapped[str | None] = mapped_column(String(30))
    concordance: Mapped[bool | None] = mapped_column(Boolean)
    decide_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())