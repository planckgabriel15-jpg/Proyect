from datetime import date

import pytest
from sqlalchemy import func, select

from circularis_rel.datos.modelos import Catalogo, EtapaImplementacion, MotivoParada, Parametro
from circularis_rel.datos.semillas import PARAMETROS, sembrar
from circularis_rel.servicios import parametros as P


def test_sembrar_es_idempotente(db):
    with db.escritura() as s:
        agregados = sembrar(s)
    assert all(v == 0 for v in agregados.values())
    with db.lectura() as s:
        assert s.scalar(select(func.count()).select_from(Parametro)) == len(PARAMETROS)
        assert s.scalar(select(func.count()).select_from(EtapaImplementacion)) == 16


def test_sin_demanda_y_huelga_no_cuentan_como_requeridas(db):
    with db.lectura() as s:
        no_req = set(s.scalars(select(MotivoParada.codigo).where(MotivoParada.cuenta_como_requerida.is_(False))))
    assert no_req == {"SIN_DEMANDA", "HUELGA"}


def test_tipos_de_parametro(db):
    with db.lectura() as s:
        assert P.obtener(s, "semaforo.p_rojo") == pytest.approx(0.30)
        assert P.obtener(s, "motor.min_fallas_mle") == 20
        assert P.obtener(s, "motor.beta_aleatoria_por_ic") is True
        assert P.obtener(s, "criticidad.tp_cortes") == {"Alta": 25, "Media": 20, "Baja": 15}


def test_parametro_de_costo_sin_valor_es_falta_dato(db):
    with db.lectura() as s:
        assert P.obtener(s, "costos.tarifa_mo_ars_h") is None


def test_parametro_con_historia(db):
    with db.escritura() as s:
        P.fijar(s, "costos.tarifa_mo_ars_h", 9000, vigente_desde=date(2026, 10, 15))
        P.fijar(s, "costos.tarifa_mo_ars_h", 9900, vigente_desde=date(2026, 11, 1))
    with db.lectura() as s:
        assert P.obtener(s, "costos.tarifa_mo_ars_h", date(2026, 10, 10)) is None
        assert P.obtener(s, "costos.tarifa_mo_ars_h", date(2026, 10, 20)) == 9000
        assert P.obtener(s, "costos.tarifa_mo_ars_h", date(2026, 12, 1)) == 9900


def test_parametro_de_tipo_incorrecto(db):
    with pytest.raises(ValueError), db.escritura() as s:
        P.fijar(s, "motor.min_fallas_mle", "veinte")


def test_parametro_desconocido(db):
    with pytest.raises(P.ParametroDesconocido), db.lectura() as s:
        P.obtener(s, "no.existe")


def test_causas_propuestas_aplican_a_todos(db):
    with db.lectura() as s:
        causas = s.scalars(select(Catalogo).where(Catalogo.tipo == "CAUSA")).all()
    assert len(causas) >= 15 and all(c.origen == "PROPUESTA" for c in causas)
