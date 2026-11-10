from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.ops import SCHEMA, Base


class DemandeReinitialisation(Base):
    """Demande « mot de passe oublié » : traitée par l'administrateur après vérification d'identité."""
    __tablename__ = "demande_reinitialisation"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.utilisateur.id"))
    email: Mapped[str] = mapped_column(String(255))
    contact: Mapped[str | None] = mapped_column(String(100))
    statut: Mapped[str] = mapped_column(String(20), default="en_attente", server_default=text("'en_attente'"))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    traitee_par: Mapped[int | None] = mapped_column(ForeignKey(f"{SCHEMA}.utilisateur.id"))
    traitee_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
