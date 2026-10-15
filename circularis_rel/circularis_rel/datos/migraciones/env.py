"""Entorno de Alembic. La URL sale de la configuración del sistema, salvo que se pase
`config.attributes["url"]` (tests) o `-x url=...` en la línea de comandos."""

from alembic import context

from circularis_rel.config import cargar_config
from circularis_rel.datos.db import crear_engine
from circularis_rel.datos.modelos import Base

config = context.config
target_metadata = Base.metadata


def _url() -> str:
    return (
        config.attributes.get("url")
        or context.get_x_argument(as_dictionary=True).get("url")
        or cargar_config().url_db
    )


def run_migrations_offline() -> None:
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True,
                      render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    conexion = config.attributes.get("connection")
    if conexion is not None:
        context.configure(connection=conexion, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = crear_engine(_url())
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
