"""Conexión a la base de datos.

Reglas de concurrencia para SQLite (PLAN_TECNICO §3.4):
- WAL, busy_timeout de 10 s, foreign_keys y synchronous=NORMAL en cada conexión.
- Las lecturas usan BEGIN diferido; las escrituras usan BEGIN IMMEDIATE para que dos
  escritores no entren en deadlock al pasar de lectura a escritura.
- Un engine por proceso; una sesión por operación (nunca guardada en el estado de Streamlit).

Todo el acceso pasa por SQLAlchemy: para migrar a PostgreSQL alcanza con cambiar la URL
(los triggers de `ddl_extra.py` son solo para SQLite; ver DECISIONES D-018).
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from sqlalchemy import DateTime, Engine, create_engine, event
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator

REINTENTOS_BLOQUEO = 3


class FechaHoraUTC(TypeDecorator):
    """Fecha y hora con zona. Se guarda en UTC sin zona y se devuelve en UTC con zona.

    Rechaza fechas sin zona: así nadie guarda por error la hora local como si fuera UTC.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Fecha y hora sin zona horaria: usar datetime con tzinfo")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=UTC)


def ahora() -> datetime:
    return datetime.now(UTC)


def crear_engine(url: str, *, eco: bool = False) -> Engine:
    es_sqlite = url.startswith("sqlite")
    en_memoria = es_sqlite and (url.endswith(":memory:") or url == "sqlite://")
    kwargs: dict = {"echo": eco, "future": True}
    if es_sqlite:
        kwargs["connect_args"] = {"check_same_thread": False, "timeout": 10}
        if en_memoria:
            kwargs["poolclass"] = StaticPool
    engine = create_engine(url, **kwargs)

    if es_sqlite:

        @event.listens_for(engine, "connect")
        def _al_conectar(dbapi_conn, _registro):
            # Que pysqlite no emita su propio BEGIN: lo controlamos en "begin".
            dbapi_conn.isolation_level = None
            cur = dbapi_conn.cursor()
            if not en_memoria:
                cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA busy_timeout=10000")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.execute("PRAGMA synchronous=NORMAL")
            cur.close()

        @event.listens_for(engine, "begin")
        def _al_comenzar(conn):
            if conn.get_execution_options().get("escritura"):
                conn.exec_driver_sql("BEGIN IMMEDIATE")
            else:
                conn.exec_driver_sql("BEGIN")

    return engine


class BaseDatos:
    """Agrupa el engine y las fábricas de sesión de un proceso."""

    def __init__(self, url: str, *, eco: bool = False) -> None:
        from circularis_rel.datos.auditoria_listener import registrar_auditoria

        registrar_auditoria()
        self.url = url
        self.engine = crear_engine(url, eco=eco)
        self._lectura = sessionmaker(bind=self.engine, expire_on_commit=False)
        self._escritura = sessionmaker(
            bind=self.engine.execution_options(escritura=True), expire_on_commit=False
        )

    @contextmanager
    def lectura(self) -> Iterator[Session]:
        with self._lectura() as s:
            yield s

    @contextmanager
    def escritura(
        self, *, usuario_id: int | None = None, motivo: str | None = None, accion=None
    ) -> Iterator[Session]:
        """Sesión de escritura con commit al salir y rollback ante error.

        `usuario_id` y `motivo` viajan a la auditoría (ver `auditoria_listener`).
        Reintenta hasta REINTENTOS_BLOQUEO veces si SQLite responde "database is locked"
        al comenzar la transacción.
        """
        for intento in range(REINTENTOS_BLOQUEO):
            s = self._escritura()
            s.info["usuario_id"] = usuario_id
            s.info["motivo"] = motivo
            s.info["accion"] = accion
            try:
                s.connection()  # dispara BEGIN IMMEDIATE acá, antes de tocar datos
            except OperationalError as e:
                s.close()
                if "locked" in str(e).lower() and intento < REINTENTOS_BLOQUEO - 1:
                    time.sleep(0.5 * (intento + 1))
                    continue
                raise
            try:
                yield s
                s.commit()
            except Exception:
                s.rollback()
                raise
            finally:
                s.close()
            return

    def crear_esquema(self) -> None:
        """Crea todas las tablas (tests y base nueva). En producción se usa Alembic."""
        from circularis_rel.datos import ddl_extra  # noqa: F401  (registra triggers)
        from circularis_rel.datos.modelos import Base

        Base.metadata.create_all(self.engine)
