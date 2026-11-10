from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.ops import SCHEMA, Base


class MessageContact(Base):
    """Message envoyé depuis le formulaire public « Contactez-nous ».

    On ne stocke volontairement pas l'adresse IP du visiteur (donnée personnelle inutile).
    """
    __tablename__ = "message_contact"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200))
    objet: Mapped[str | None] = mapped_column(String(150))
    message: Mapped[str] = mapped_column(Text)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    traite: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    traite_par: Mapped[int | None] = mapped_column(ForeignKey(f"{SCHEMA}.utilisateur.id"))
    traite_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
