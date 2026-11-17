from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Score(Base):
    """Résultat du modèle pour un dossier. Chaque calcul crée une nouvelle ligne."""
    __tablename__ = "score"
    __table_args__ = ({"schema": "ml"},)

    id: Mapped[int] = mapped_column(primary_key=True)
    demande_id: Mapped[int] = mapped_column(ForeignKey("ops.demande_credit.id"), index=True)
    version_modele: Mapped[str] = mapped_column(String(50))
    p_defaut: Mapped[float] = mapped_column(Numeric(7, 6))
    seuil_applique: Mapped[float] = mapped_column(Numeric(5, 4))
    recommandation: Mapped[str] = mapped_column(String(20))      # accord / accord_reduit / refus
    montant_suggere: Mapped[int | None] = mapped_column(BigInteger)
    p_montant_suggere: Mapped[float | None] = mapped_column(Numeric(7, 6))
    variables_entree: Mapped[dict] = mapped_column(JSONB)         # ce que le modèle a reçu
    facteurs: Mapped[dict | None] = mapped_column(JSONB)          # explications (SHAP)
    calcule_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class RapportSuivi(Base):
    """Rapport de suivi du modèle (src/surveillance.py) : stabilité, décisions, performance."""
    __tablename__ = "rapport_suivi"
    __table_args__ = ({"schema": "ml"},)

    id: Mapped[int] = mapped_column(primary_key=True)
    version_modele: Mapped[str] = mapped_column(String(80))
    debut: Mapped[date] = mapped_column(Date)
    fin: Mapped[date] = mapped_column(Date)
    niveau_global: Mapped[str] = mapped_column(String(10))       # vert / orange / rouge / n/a
    contenu: Mapped[dict] = mapped_column(JSONB)
    produit_par: Mapped[int | None] = mapped_column(ForeignKey("ops.utilisateur.id"))  # vide = planificateur
    produit_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
