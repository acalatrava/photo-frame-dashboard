from alembic import context
from sqlalchemy import create_engine

from app import models  # noqa: F401 - registers tables
from app.core.db import Base

target_metadata = Base.metadata


def run_migrations_online() -> None:
    connection = context.config.attributes.get("connection")
    if connection is None:
        engine = create_engine(context.config.get_main_option("sqlalchemy.url"))
        with engine.connect() as connection:
            _run(connection)
    else:
        _run(connection)


def _run(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


run_migrations_online()
