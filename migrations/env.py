from logging.config import fileConfig

from alembic import context

from app.db import engine
from app.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_name(name, type_, parent_names):
    """Alembic ne gère que nos schémas ; staging (données Kaggle) reste hors de son champ."""
    if type_ == "schema":
        return name in ("ops", "ml", "audit")
    return True


def run_migrations_online():
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name,
        )
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()