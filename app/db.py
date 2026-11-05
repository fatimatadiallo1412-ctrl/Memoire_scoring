from sqlalchemy.orm import sessionmaker

from src.db import get_engine

engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session():
    """Fournit une session à chaque requête de l'API, puis la ferme."""
    with SessionLocal() as session:
        yield session