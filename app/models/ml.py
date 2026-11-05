from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, func
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