"""Las páginas cargan sin errores con datos DEMO, y cada rol ve solo lo suyo."""

from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
import streamlit as st
from sqlalchemy import select
from streamlit.testing.v1 import AppTest

from circularis_rel.cli import migrar
from circularis_rel.datos.db import BaseDatos
from circularis_rel.datos.modelos import Usuario
from circularis_rel.datos.semillas import sembrar
from circularis_rel.servicios import modulos
from circularis_rel.servicios.demo import cargar_demo

APP = Path(__file__).resolve().parents[2] / "circularis_rel" / "app"
INICIO = str(APP / "inicio.py")
PAGINAS_JEFE = ["puesta_en_marcha.py", "carga_inicial.py", "maquinas.py", "historico.py", "usuarios.py",
                "parametros.py", "datos_demo.py", "ayuda.py", "bandeja_validacion.py", "bandeja_encargado.py",
                "cerrar_ot.py", "cambio_preventivo.py", "planta.py", "reportar_falla.py", "parte_turno.py", "tarjeta.py",
                "exportar.py", "panel_planta.py", "ficha_maquina.py", "analisis_weibull.py", "analisis_problemas.py",
                "tablero.py", "catalogos.py", "criticidad.py", "piloto.py", "plan_preventivo.py", "repuestos.py",
                "reportes.py", "predictivo.py", "herramientas.py", "tpm.py", "amfe.py"]
PAGINAS_OPERARIO = ["planta.py", "reportar_falla.py", "parte_turno.py", "tarjeta.py", "ficha_maquina.py", "ayuda.py"]
PAGINAS_GERENCIA = ["panel_planta.py", "tablero.py", "ficha_maquina.py", "reportes.py", "herramientas.py", "tpm.py",
                    "exportar.py", "ayuda.py"]
PAGINAS_ENCARGADO = ["bandeja_encargado.py", "cerrar_ot.py", "cambio_preventivo.py", "analisis_problemas.py",
                     "ficha_maquina.py", "planta.py", "exportar.py", "plan_preventivo.py", "repuestos.py", "predictivo.py"]
TZ = ZoneInfo("America/Argentina/Cordoba")


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    carpeta = tmp_path_factory.mktemp("app")
    url = f"sqlite:///{carpeta / 'app.db'}"
    migrar(url)
    db = BaseDatos(url)
    with db.escritura() as s:
        sembrar(s)
    assert cargar_demo(db, tz=TZ).aplicado  # con historia: el panel y el Weibull tienen datos
    with db.escritura() as s:  # todos los módulos habilitados, para probar todas las pantallas
        for m in modulos.todos(s):
            modulos.fijar(s, m.codigo, True)
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


@pytest.mark.parametrize("archivo", PAGINAS_GERENCIA)
def test_paginas_de_gerencia(base, archivo):
    at = _app(base["GERENCIA"]).run()
    at.switch_page(str(APP / "paginas" / archivo)).run()
    assert not at.exception, [e.value for e in at.exception]


@pytest.mark.parametrize("archivo", PAGINAS_ENCARGADO)
def test_paginas_del_encargado(base, archivo):
    at = _app(base["ENCARGADO"]).run()
    at.switch_page(str(APP / "paginas" / archivo)).run()
    assert not at.exception, [e.value for e in at.exception]


def test_panel_muestra_semaforos_y_ranking(base):
    at = _app(base["JEFE"]).run()
    at.switch_page(str(APP / "paginas" / "panel_planta.py")).run()
    assert not at.exception
    textos = " ".join(m.value for m in at.markdown)
    assert "🔴 **DEMO-AGR-001**" in textos
    assert any("RULEMANES" in w.value for w in at.warning)  # sugerencia de análisis por β ≈ 1


def test_operario_no_ve_costos_en_la_ficha(base):
    at = _app(base["OPERARIO"]).run()
    at.switch_page(str(APP / "paginas" / "ficha_maquina.py")).run()
    assert not at.exception
    contenido = " ".join(str(x.value) for x in [*at.markdown, *at.caption, *at.metric])
    assert "$" not in contenido


def test_cinco_porques_desde_una_sugerencia(base):
    at = _app(base["JEFE"]).run()
    at.switch_page(str(APP / "paginas" / "analisis_problemas.py")).run()
    boton = next(b for b in at.button if b.label == "Iniciar 5 Porqués")
    boton.click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("creado" in s.value for s in at.success)


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
