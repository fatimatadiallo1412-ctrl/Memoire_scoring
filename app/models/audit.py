from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Journal(Base):
    """Trace des actions. Table en AJOUT SEUL (un déclencheur interdit UPDATE et DELETE)."""
    __tablename__ = "journal"
    __table_args__ = ({"schema": "audit"},)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    utilisateur_id: Mapped[int | None] = mapped_column(ForeignKey("ops.utilisateur.id"))
    action: Mapped[str] = mapped_column(String(50))
    entite: Mapped[str] = mapped_column(String(50))
    entite_id: Mapped[int | None] = mapped_column()
    details: Mapped[dict | None] = mapped_column(JSONB)
    horodatage: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())