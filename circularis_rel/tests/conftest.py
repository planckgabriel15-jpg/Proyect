"""Fixtures comunes: base en memoria con esquema, semillas y una planta mínima ficticia."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time

import pytest

from circularis_rel.datos.db import BaseDatos
from circularis_rel.datos.enums import EtapaProceso, Rol, TipoCatalogo
from circularis_rel.datos.modelos import (
    Activo,
    Catalogo,
    CatalogoAplica,
    Linea,
    PosicionComponente,
    TipoComponente,
    Turno,
    Usuario,
)
from circularis_rel.datos.semillas import sembrar


@pytest.fixture
def db() -> BaseDatos:
    base = BaseDatos("sqlite://")
    base.crear_esquema()
    with base.escritura() as s:
        sembrar(s)
    return base


@dataclass
class Planta:
    linea: int
    activo: int
    activo2: int
    tipo: int
    tipo2: int
    posicion: int
    posicion2: int  # posición de otro tipo en la misma máquina
    modo: int
    modo_otro_tipo: int
    causa: int
    sintoma: int
    turno: int
    jefe: int


def dt(*args) -> datetime:
    return datetime(*args, tzinfo=UTC)


@pytest.fixture
def planta(db: BaseDatos) -> Planta:
    with db.escritura() as s:
        linea = Linea(codigo="DEMO-TWOOD", nombre="Línea DEMO")
        s.add(linea)
        s.flush()
        a1 = Activo(codigo="DEMO-AGR-001", nombre="Agrumadora DEMO 1", id_linea=linea.id,
                    etapa_proceso=EtapaProceso.PREPROCESADO, horas_promedio_dia=8)
        a2 = Activo(codigo="DEMO-AGR-002", nombre="Agrumadora DEMO 2", id_linea=linea.id,
                    etapa_proceso=EtapaProceso.PREPROCESADO, horas_promedio_dia=8)
        t1 = TipoComponente(codigo="DEMO-CUCHILLAS", nombre="Cuchillas")
        t2 = TipoComponente(codigo="DEMO-CORREA", nombre="Correa")
        s.add_all([a1, a2, t1, t2])
        s.flush()
        p1 = PosicionComponente(id_activo=a1.id, id_tipo_componente=t1.id, codigo="CUCH", critica=True)
        p2 = PosicionComponente(id_activo=a1.id, id_tipo_componente=t2.id, codigo="CORREA")
        modo = Catalogo(tipo=TipoCatalogo.MODO, codigo="DEMO-PERDIDA-FILO", descripcion="Pérdida de filo")
        modo2 = Catalogo(tipo=TipoCatalogo.MODO, codigo="DEMO-CORTE-CORREA", descripcion="Corte de correa")
        turno = Turno(codigo="DEMO-T1", nombre="Mañana DEMO", hora_inicio=time(6), hora_fin=time(14), duracion_h=8)
        jefe = Usuario(usuario="jefe", nombre="Jefe DEMO", rol=Rol.JEFE, hash_password="x")
        s.add_all([p1, p2, modo, modo2, turno, jefe])
        s.flush()
        s.add_all([CatalogoAplica(id_catalogo=modo.id, id_tipo_componente=t1.id),
                   CatalogoAplica(id_catalogo=modo2.id, id_tipo_componente=t2.id)])
        from sqlalchemy import select
        causa = s.scalar(select(Catalogo).where(Catalogo.codigo == "DESGASTE"))
        sintoma = s.scalar(select(Catalogo).where(Catalogo.codigo == "RUIDO"))
        return Planta(linea.id, a1.id, a2.id, t1.id, t2.id, p1.id, p2.id, modo.id, modo2.id,
                      causa.id, sintoma.id, turno.id, jefe.id)
