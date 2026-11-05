from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe mère de tous les modèles. Elle garde la liste des tables ('metadata'),
    qu'Alembic lit pour générer les migrations."""