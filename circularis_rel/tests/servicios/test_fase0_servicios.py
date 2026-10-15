"""Permisos, usuarios, QR, ficha de catastro, demo y puesta en marcha."""

import pytest
from pypdf import PdfReader
from sqlalchemy import func, select

from circularis_rel.asistente import etapas
from circularis_rel.datos.enums import EstadoEtapa, Rol
from circularis_rel.datos.modelos import Activo, Auditoria, Usuario
from circularis_rel.servicios import auth, catastro
from circularis_rel.servicios.demo import borrar_demo, cargar_demo, hay_demo
from circularis_rel.servicios.permisos import MATRIZ, Accion, PermisoDenegado, puede, requerir
from circularis_rel.servicios.qr import etiquetas_pdf, url_maquina


# --- Permisos (Plan §2) -------------------------------------------------------
@pytest.mark.parametrize("accion,roles", [
    (Accion.CARGAR_PARTE, {"OPERARIO", "ENCARGADO", "JEFE"}),
    (Accion.CREAR_AVISO, {"OPERARIO", "ENCARGADO", "JEFE"}),
    (Accion.CERRAR_OT, {"ENCARGADO", "JEFE"}),
    (Accion.VALIDAR_EVENTO, {"JEFE"}),
    (Accion.CORREGIR_VALIDADO, {"JEFE"}),
    (Accion.CONFIGURAR, {"JEFE"}),
    (Accion.VER_FICHA, {"OPERARIO", "ENCARGADO", "JEFE", "GERENCIA"}),
    (Accion.VER_COSTOS, {"JEFE", "GERENCIA"}),
    (Accion.EXPORTAR, {"ENCARGADO", "JEFE", "GERENCIA"}),
])
def test_matriz_del_plan(accion, roles):
    assert {r.value for r in Rol if puede(r, accion)} == roles


def test_toda_accion_tiene_fila_en_la_matriz():
    assert set(MATRIZ) == set(Accion)


def test_operario_solo_en_sus_maquinas():
    assert puede(Rol.OPERARIO, Accion.CREAR_AVISO, maquina_asignada=True)
    assert not puede(Rol.OPERARIO, Accion.CREAR_AVISO, maquina_asignada=False)
    assert puede(Rol.ENCARGADO, Accion.CREAR_AVISO, maquina_asignada=False)
    with pytest.raises(PermisoDenegado):
        requerir(Rol.GERENCIA, Accion.CARGAR_PARTE)


# --- Usuarios ---------------------------------------------------------------
def test_pin_y_contrasena(db, planta):
    with db.escritura() as s:
        with pytest.raises(auth.ClaveInvalida):
            auth.crear_usuario(s, "op1", "Op", "OPERARIO", "12")
        with pytest.raises(auth.ClaveInvalida):
            auth.crear_usuario(s, "enc", "Enc", "ENCARGADO", "corta")
        u = auth.crear_usuario(s, "op1", "Operario Uno", "OPERARIO", "4321", maquinas=["DEMO-AGR-001"])
        uid = u.id
    with db.lectura() as s:
        assert auth.autenticar(s, "OP1", "4321").id == uid
        assert auth.autenticar(s, "op1", "0000") is None
        assert auth.maquinas_de(s, uid) == ["DEMO-AGR-001"]
        cred = auth.credenciales(s)
        assert cred["usernames"]["op1"]["roles"] == ["OPERARIO"]
        assert s.get(Usuario, uid).hash_password.startswith("$2")


def test_usuario_duplicado_y_baja(db, planta):
    with db.escritura() as s:
        auth.crear_usuario(s, "enc", "Enc", "ENCARGADO", "clave-larga")
        with pytest.raises(ValueError, match="Ya existe"):
            auth.crear_usuario(s, "ENC", "Otro", "ENCARGADO", "clave-larga")
        with pytest.raises(ValueError, match="a vos mismo"):
            auth.fijar_activo(s, planta.jefe, False, planta.jefe)


# --- QR y ficha ---------------------------------------------------------------
def test_qr_pdf():
    pdf = etiquetas_pdf([(f"AGR-00{i}", f"Máquina {i}") for i in range(1, 10)], "http://192.168.0.10:8501")
    assert pdf.startswith(b"%PDF") and len(PdfReader(__import__("io").BytesIO(pdf)).pages) == 2
    assert url_maquina("http://x:8501/", "EXT-001") == "http://x:8501/?maq=EXT-001"


def test_ficha_y_revision(db):
    assert cargar_demo(db).aplicado
    with db.lectura() as s:
        pdf = catastro.ficha_pdf(s, "DEMO-AGR-001")
        texto = "".join(p.extract_text() for p in PdfReader(__import__("io").BytesIO(pdf)).pages)
        jefe = s.scalar(select(Usuario).where(Usuario.usuario == "demo.jefe"))
    assert "MANT/RHM001" in texto and "MANT/RM001" in texto and "DEMO-REP-CUCH" in texto
    assert "598.000,00" in texto
    with db.escritura(usuario_id=jefe.id) as s:
        catastro.marcar_revisado(s, "DEMO-AGR-001", jefe.id)
        assert catastro.actualizar_catastro(s, "DEMO-AGR-001", {"peso_kg": 850.0, "modelo": "AG-DEMO"}) == ["peso_kg"]
        with pytest.raises(ValueError):
            catastro.actualizar_catastro(s, "DEMO-AGR-001", {"codigo": "X"})
        assert catastro.marcar_criticas(s, "DEMO-AGR-001", {"RULEMANES": False}) == 1
    with db.lectura() as s:
        estados = {e.codigo: e for e in catastro.estado_revision(s)}
        assert estados["DEMO-AGR-001"].revisado and estados["DEMO-AGR-001"].revisado_por == "Jefe DEMO"
        assert estados["DEMO-AGR-001"].posiciones_criticas == 1
        assert [e.codigo for e in catastro.estado_revision(s)] == ["DEMO-AGR-001", "DEMO-LAV-001", "DEMO-EXT-001"]


# --- Demo -------------------------------------------------------------------------
def test_demo_cargar_y_borrar(db):
    assert cargar_demo(db).aplicado
    with db.lectura() as s:
        assert hay_demo(s)
    borrar_demo(db)
    with db.lectura() as s:
        assert not hay_demo(s)
        assert s.scalar(select(func.count()).select_from(Activo)) == 0
        assert s.scalar(select(func.count()).select_from(Auditoria).where(Auditoria.accion == "BAJA")) > 0


# --- Puesta en marcha (12.A) --------------------------------------------------------
def test_etapas(db):
    with db.lectura() as s:
        lista = etapas.listar(s)
    assert len(lista) == 16 and {e.fase for e in lista} == {1, 2, 3}
    assert next(e for e in lista if e.numero == 1).verificacion.cumple is False
    assert next(e for e in lista if e.numero == 16).verificacion.detalle.startswith("Todavía no hay datos suficientes")
    assert etapas.progreso(lista) == 0
    assert cargar_demo(db).aplicado
    with db.escritura() as s:
        etapas.marcar(s, 1, EstadoEtapa.HECHA, None)
        etapas.marcar(s, 2, EstadoEtapa.EN_CURSO, None)
    with db.lectura() as s:
        lista = etapas.listar(s)
    assert next(e for e in lista if e.numero == 1).verificacion.cumple is True
    assert next(e for e in lista if e.numero == 7).verificacion.cumple is False  # códigos DEMO-… no son AAA-000
    assert etapas.progreso(lista) == pytest.approx(1.5 / 16)
