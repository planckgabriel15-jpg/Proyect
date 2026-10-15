"""La base creada por Alembic es la misma que la de los modelos y funciona de punta a punta."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from circularis_rel.datos.db import BaseDatos
from circularis_rel.datos.semillas import sembrar
from circularis_rel.servicios.importador.aplicar import importar

RAIZ = Path(__file__).resolve().parents[2]


def _config(url: str) -> Config:
    cfg = Config(str(RAIZ / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ / "circularis_rel" / "datos" / "migraciones"))
    cfg.attributes["url"] = url
    return cfg


def test_migrar_sembrar_e_importar(tmp_path):
    url = f"sqlite:///{tmp_path / 'm.db'}"
    command.upgrade(_config(url), "head")
    db = BaseDatos(url)
    with db.engine.connect() as c:
        triggers = c.exec_driver_sql("SELECT count(*) FROM sqlite_master WHERE type='trigger'").scalar()
        modo = c.exec_driver_sql("PRAGMA journal_mode").scalar()
    assert triggers == 13 and modo == "wal"
    with db.escritura() as s:
        sembrar(s)
    r = importar(db, RAIZ / "docs" / "plantillas" / "carga_inicial_borrador_TP1.xlsx", simular=False)
    assert r.aplicado, r.texto()


def test_esquema_migrado_igual_al_de_los_modelos(tmp_path):
    url = f"sqlite:///{tmp_path / 'm.db'}"
    command.upgrade(_config(url), "head")
    migrada = BaseDatos(url)
    modelos = BaseDatos("sqlite://")
    modelos.crear_esquema()

    def firma(engine):
        i = inspect(engine)
        return {t: sorted(c["name"] for c in i.get_columns(t)) for t in i.get_table_names() if t != "alembic_version"}

    assert firma(migrada.engine) == firma(modelos.engine)

    def checks(engine):
        with engine.connect() as c:
            return {r[0]: r[1] for r in c.exec_driver_sql("SELECT name, sql FROM sqlite_master WHERE type='table'")}

    sql_migrada, sql_modelos = checks(migrada.engine), checks(modelos.engine)
    for tabla, sql in sql_modelos.items():
        for valor in ("PROPUESTA", "TP1_ILUSTRATIVO"):
            assert (valor in sql) == (valor in sql_migrada.get(tabla, "")), f"CHECK distinto en {tabla}"


def test_downgrade(tmp_path):
    url = f"sqlite:///{tmp_path / 'm.db'}"
    cfg = _config(url)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    assert set(inspect(BaseDatos(url).engine).get_table_names()) <= {"alembic_version"}
