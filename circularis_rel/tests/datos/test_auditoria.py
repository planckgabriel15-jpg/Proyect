import pytest
from sqlalchemy import select

from circularis_rel.datos.auditoria_listener import MotivoRequerido
from circularis_rel.datos.enums import AccionAuditoria, EstadoEvento
from circularis_rel.datos.modelos import Activo, Auditoria, EventoFalla
from tests.conftest import dt


def _auditoria(db, tabla, id_registro):
    with db.lectura() as s:
        return list(s.scalars(select(Auditoria).where(Auditoria.tabla == tabla, Auditoria.id_registro == id_registro)
                              .order_by(Auditoria.id)))


def test_alta_y_modificacion_quedan_auditadas(db, planta):
    with db.escritura(usuario_id=planta.jefe) as s:
        a = s.get(Activo, planta.activo)
        a.autonomia_pulmon_h = 4
    filas = _auditoria(db, "activo", planta.activo)
    assert filas[0].accion == AccionAuditoria.ALTA
    mod = [f for f in filas if f.accion == AccionAuditoria.MODIFICACION]
    assert len(mod) == 1
    assert mod[0].campo == "autonomia_pulmon_h"
    assert mod[0].valor_anterior is None and mod[0].valor_nuevo == "4"
    assert mod[0].id_usuario == planta.jefe


def _evento_validado(db, planta):
    ev = EventoFalla(id_activo=planta.activo, id_posicion=planta.posicion, fecha_hora_falla=dt(2026, 9, 5),
                     id_modo=planta.modo, id_causa=planta.causa, inicio_reparacion=dt(2026, 9, 5, 1),
                     fin_reparacion=dt(2026, 9, 5, 3), estado=EstadoEvento.CERRADO)
    with db.escritura() as s:
        s.add(ev)
    with db.escritura(usuario_id=planta.jefe) as s:
        s.get(EventoFalla, ev.id).estado = EstadoEvento.VALIDADO
    return ev.id


def test_validar_no_pide_motivo_y_queda_como_validacion(db, planta):
    eid = _evento_validado(db, planta)
    acciones = {f.accion for f in _auditoria(db, "evento_falla", eid)}
    assert AccionAuditoria.VALIDACION in acciones


def test_corregir_validado_sin_motivo_falla(db, planta):
    eid = _evento_validado(db, planta)
    with pytest.raises(MotivoRequerido), db.escritura(usuario_id=planta.jefe) as s:
        s.get(EventoFalla, eid).tiempo_reparacion_h = 5
    with db.lectura() as s:
        assert s.get(EventoFalla, eid).tiempo_reparacion_h is None  # no se guardó nada


def test_corregir_validado_con_motivo_queda_auditado(db, planta):
    eid = _evento_validado(db, planta)
    with db.escritura(usuario_id=planta.jefe, motivo="El encargado cargó mal el tiempo") as s:
        s.get(EventoFalla, eid).tiempo_reparacion_h = 5
    fila = [f for f in _auditoria(db, "evento_falla", eid) if f.campo == "tiempo_reparacion_h"][0]
    assert fila.motivo == "El encargado cargó mal el tiempo"
    assert fila.valor_nuevo == "5"


def test_auditoria_se_revierte_con_la_operacion(db, planta):
    antes = len(_auditoria(db, "activo", planta.activo))
    with pytest.raises(RuntimeError), db.escritura() as s:
        s.get(Activo, planta.activo).peso_kg = 1000
        s.flush()
        raise RuntimeError("falla a mitad de la operación")
    assert len(_auditoria(db, "activo", planta.activo)) == antes
