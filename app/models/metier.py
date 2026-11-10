from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.ops import SCHEMA, Base


class Metier(Base):
    """Référentiel des métiers : chaque métier est rattaché à une catégorie connue du modèle.

    categorie_modele vide = métier saisi librement, « à classer » : le client est alors scoré
    avec « Non renseigné » jusqu'à ce qu'un responsable choisisse une catégorie.
    """
    __tablename__ = "metier"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True)
    libelle: Mapped[str] = mapped_column(String(100))
    categorie_modele: Mapped[str | None] = mapped_column(String(40))
    valide: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    actif: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    cree_par: Mapped[int | None] = mapped_column(ForeignKey(f"{SCHEMA}.utilisateur.id"))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
