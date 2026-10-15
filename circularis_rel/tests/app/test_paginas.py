"""Las páginas cargan sin errores con datos DEMO, y cada rol ve solo lo suyo."""

from pathlib import Path

import pytest
import streamlit as st
from sqlalchemy import select
from streamlit.testing.v1 import AppTest

from circularis_rel.cli import migrar
from circularis_rel.datos.db import BaseDatos
from circularis_rel.datos.modelos import Usuario
from circularis_rel.datos.semillas import sembrar
from circularis_rel.servicios.demo import cargar_demo

APP = Path(__file__).resolve().parents[2] / "circularis_rel" / "app"
INICIO = str(APP / "inicio.py")
PAGINAS_JEFE = ["puesta_en_marcha.py", "carga_inicial.py", "maquinas.py", "historico.py", "usuarios.py",
                "parametros.py", "datos_demo.py", "ayuda.py", "bandeja_validacion.py", "bandeja_encargado.py",
                "cerrar_ot.py", "cambio_preventivo.py", "planta.py", "reportar_falla.py", "parte_turno.py", "tarjeta.py",
                "exportar.py"]
PAGINAS_OPERARIO = ["planta.py", "reportar_falla.py", "parte_turno.py", "tarjeta.py", "ayuda.py"]


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    carpeta = tmp_path_factory.mktemp("app")
    url = f"sqlite:///{carpeta / 'app.db'}"
    migrar(url)
    db = BaseDatos(url)
    with db.escritura() as s:
        sembrar(s)
    assert cargar_demo(db).aplicado
    with db.lectura() as s:
        usuarios = {u.rol.value: {"id": u.id, "usuario": u.usuario, "nombre": u.nombre, "rol": u.rol.value}
                    for u in s.scalars(select(Usuario))}
    mp = pytest.MonkeyPatch()
    mp.setenv("CIRCULARIS_DB_URL", url)
    mp.setenv("CIRCULARIS_DATA_DIR", str(carpeta))
    yield usuarios
    mp.undo()


def _app(usuario: dict | None) -> AppTest:
    st.cache_resource.clear()
    at = AppTest.from_file(INICIO, default_timeout=60)
    if usuario:
        at.session_state["usuario"] = usuario
    return at


def test_sin_sesion_muestra_login(base):
    at = _app(None).run()
    assert not at.exception
    assert any("Circularis" in t.value for t in at.title)


@pytest.mark.parametrize("archivo", PAGINAS_JEFE)
def test_paginas_del_jefe(base, archivo):
    at = _app(base["JEFE"]).run()
    assert not at.exception, at.exception
    at.switch_page(str(APP / "paginas" / archivo)).run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("DATOS FICTICIOS" in m.value for m in at.markdown)


@pytest.mark.parametrize("archivo", PAGINAS_OPERARIO)
def test_paginas_del_operario(base, archivo):
    at = _app(base["OPERARIO"]).run()
    at.switch_page(str(APP / "paginas" / archivo)).run()
    assert not at.exception, [e.value for e in at.exception]


@pytest.mark.parametrize("rol", ["OPERARIO", "ENCARGADO", "GERENCIA"])
def test_otros_roles_solo_ven_su_inicio(base, rol):
    at = _app(base[rol]).run()
    assert not at.exception
    assert not at.exception
    # Una página del jefe no está en su navegación.
    with pytest.raises(Exception):  # noqa: B017
        at.switch_page(str(APP / "paginas" / "usuarios.py")).run()


def test_qr_preselecciona_maquina(base):
    at = _app(base["JEFE"])
    at.query_params["maq"] = "DEMO-EXT-001"
    at.run()
    at.switch_page(str(APP / "paginas" / "maquinas.py")).run()
    assert not at.exception
    assert at.selectbox[0].value == "DEMO-EXT-001"
