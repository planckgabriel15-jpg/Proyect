"""Cada regla que no puede romperse se intenta violar y la base debe rechazarla."""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from circularis_rel.datos.enums import EstadoEvento, EstadoParte, TipoFin, TipoOT
from circularis_rel.datos.modelos import (
    EventoFalla,
    OrdenTrabajo,
    ParteTurno,
    VidaComponente,
)
from tests.conftest import dt


def _guardar(db, *objs):
    with db.escritura() as s:
        s.add_all(objs)


def _parte(planta, **kw):
    base = dict(id_activo=planta.activo, fecha=date(2026, 10, 20), id_turno=planta.turno,
                horas_turno=8, estado=EstadoParte.TODO, horas_no_operadas=0, horas_operadas=8)
    base.update(kw)
    return ParteTurno(**base)


def test_una_sola_vida_en_servicio_por_posicion(db, planta):
    _guardar(db, VidaComponente(id_posicion=planta.posicion, fecha_instalacion=dt(2026, 10, 1)))
    with pytest.raises(IntegrityError):
        _guardar(db, VidaComponente(id_posicion=planta.posicion, fecha_instalacion=dt(2026, 10, 2)))


def test_vidas_cerradas_no_chocan_con_la_en_servicio(db, planta):
    _guardar(
        db,
        VidaComponente(id_posicion=planta.posicion, fecha_instalacion=dt(2026, 9, 1), fecha_fin=dt(2026, 9, 20),
                       tipo_fin=TipoFin.SUSPENSION_PREVENTIVA),
        VidaComponente(id_posicion=planta.posicion, fecha_instalacion=dt(2026, 9, 20)),
    )


def test_vida_en_servicio_no_tiene_fecha_fin(db, planta):
    with pytest.raises(IntegrityError):
        _guardar(db, VidaComponente(id_posicion=planta.posicion, fecha_instalacion=dt(2026, 9, 1),
                                    fecha_fin=dt(2026, 9, 2), tipo_fin=TipoFin.EN_SERVICIO))


def test_vida_cerrada_necesita_fecha_fin(db, planta):
    with pytest.raises(IntegrityError):
        _guardar(db, VidaComponente(id_posicion=planta.posicion, fecha_instalacion=dt(2026, 9, 1),
                                    tipo_fin=TipoFin.SUSPENSION_OTRA))


def test_vida_con_falla_necesita_modo(db, planta):
    with pytest.raises(IntegrityError):
        _guardar(db, VidaComponente(id_posicion=planta.posicion, fecha_instalacion=dt(2026, 9, 1),
                                    fecha_fin=dt(2026, 9, 5), tipo_fin=TipoFin.FALLA))


def test_vida_con_modo_de_otro_tipo_de_componente(db, planta):
    with pytest.raises(IntegrityError, match="modo de falla no corresponde"):
        _guardar(db, VidaComponente(id_posicion=planta.posicion, fecha_instalacion=dt(2026, 9, 1),
                                    fecha_fin=dt(2026, 9, 5), tipo_fin=TipoFin.FALLA,
                                    id_modo_falla=planta.modo_otro_tipo))


def test_un_evento_cierra_una_sola_vida(db, planta):
    ev = EventoFalla(id_activo=planta.activo, fecha_hora_falla=dt(2026, 9, 5))
    _guardar(db, ev)
    _guardar(db, VidaComponente(id_posicion=planta.posicion, fecha_instalacion=dt(2026, 9, 1), fecha_fin=dt(2026, 9, 5),
                                tipo_fin=TipoFin.FALLA, id_modo_falla=planta.modo, id_evento_cierre=ev.id))
    with pytest.raises(IntegrityError):
        _guardar(db, VidaComponente(id_posicion=planta.posicion2, fecha_instalacion=dt(2026, 9, 1), fecha_fin=dt(2026, 9, 5),
                                    tipo_fin=TipoFin.SUSPENSION_OTRA, id_evento_cierre=ev.id))


def test_parte_duplicado(db, planta):
    _guardar(db, _parte(planta))
    with pytest.raises(IntegrityError):
        _guardar(db, _parte(planta))


@pytest.mark.parametrize("kw", [
    dict(estado=EstadoParte.PARCIAL, horas_no_operadas=9, horas_operadas=-1),       # más que el turno
    dict(estado=EstadoParte.PARCIAL, horas_no_operadas=1.25, horas_operadas=6.75),  # no es paso de 0,5
    dict(estado=EstadoParte.TODO, horas_no_operadas=1, horas_operadas=7),           # "todo" con horas paradas
    dict(estado=EstadoParte.PARCIAL, horas_no_operadas=1, horas_operadas=7),        # sin motivo
    dict(estado=EstadoParte.TODO, horas_no_operadas=0, horas_operadas=7),           # operadas incoherentes
    dict(estado=EstadoParte.NO_OPERO, horas_no_operadas=4, horas_operadas=4),       # "no operó" con horas
])
def test_parte_incoherente(db, planta, kw):
    with pytest.raises(IntegrityError):
        _guardar(db, _parte(planta, **kw))


def test_parte_parcial_valido(db, planta):
    from sqlalchemy import select

    from circularis_rel.datos.modelos import MotivoParada
    with db.lectura() as s:
        motivo = s.scalar(select(MotivoParada.id).where(MotivoParada.codigo == "LIMPIEZA"))
    _guardar(db, _parte(planta, estado=EstadoParte.PARCIAL, horas_no_operadas=1.5, horas_operadas=6.5, id_motivo=motivo))


def test_evento_con_modo_incoherente(db, planta):
    with pytest.raises(IntegrityError, match="modo de falla no corresponde"):
        _guardar(db, EventoFalla(id_activo=planta.activo, id_posicion=planta.posicion,
                                 fecha_hora_falla=dt(2026, 9, 5), id_modo=planta.modo_otro_tipo))


def test_evento_con_sintoma_usado_como_modo(db, planta):
    with pytest.raises(IntegrityError):
        _guardar(db, EventoFalla(id_activo=planta.activo, fecha_hora_falla=dt(2026, 9, 5), id_modo=planta.sintoma))


def test_evento_con_posicion_de_otra_maquina(db, planta):
    with pytest.raises(IntegrityError, match="no pertenece"):
        _guardar(db, EventoFalla(id_activo=planta.activo2, id_posicion=planta.posicion, fecha_hora_falla=dt(2026, 9, 5)))


def test_cierre_de_evento_exige_campos(db, planta):
    with pytest.raises(IntegrityError):
        _guardar(db, EventoFalla(id_activo=planta.activo, fecha_hora_falla=dt(2026, 9, 5), estado=EstadoEvento.CERRADO))


def test_reparacion_antes_de_la_falla(db, planta):
    with pytest.raises(IntegrityError):
        _guardar(db, EventoFalla(id_activo=planta.activo, fecha_hora_falla=dt(2026, 9, 5, 10),
                                 inicio_reparacion=dt(2026, 9, 5, 9)))


def test_ot_correctiva_necesita_evento(db, planta):
    with pytest.raises(IntegrityError):
        _guardar(db, OrdenTrabajo(numero="OT-1", tipo=TipoOT.CORRECTIVA, id_activo=planta.activo))


def test_evento_validado_no_se_borra(db, planta):
    ev = EventoFalla(id_activo=planta.activo, id_posicion=planta.posicion, fecha_hora_falla=dt(2026, 9, 5),
                     id_modo=planta.modo, id_causa=planta.causa, inicio_reparacion=dt(2026, 9, 5, 1),
                     fin_reparacion=dt(2026, 9, 5, 3), estado=EstadoEvento.VALIDADO)
    _guardar(db, ev)
    with pytest.raises(IntegrityError, match="no se puede borrar"), db.escritura(motivo="prueba") as s:
        s.delete(s.get(EventoFalla, ev.id))


def test_fecha_sin_zona_horaria_se_rechaza(db, planta):
    from datetime import datetime

    from sqlalchemy.exc import StatementError
    with pytest.raises(StatementError, match="sin zona"):
        _guardar(db, EventoFalla(id_activo=planta.activo, fecha_hora_falla=datetime(2026, 9, 5)))


def test_enum_invalido_se_rechaza(db, planta):
    from sqlalchemy import text
    with pytest.raises(IntegrityError), db.escritura() as s:
        s.execute(text("UPDATE activo SET etapa_proceso = 'INVENTADA' WHERE id = :i"), {"i": planta.activo})
