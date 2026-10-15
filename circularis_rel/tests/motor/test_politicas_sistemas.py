"""Políticas, inventarios (UNIDAD 5), Crow-AMSAA, Laplace, costos y semáforo."""

import pytest

from circularis_rel.motor import costos, politicas, semaforo, sistemas
from circularis_rel.motor import weibull as W
from circularis_rel.motor.tipos import Configuracion
from circularis_rel.motor.tipos import Observacion as O


def test_sin_optimo_con_beta_menor_o_igual_a_1():
    assert politicas.intervalo_optimo(400, 2500, 0.8, 700) is None
    rec = politicas.recomendar(0.8, 700, cp=400, cf=2500, critico=False, seguridad=False, intervalo_pf=None,
                               r_objetivo=0.9, cf_cp_minimo=2, paso_redondeo=25)
    assert rec.regla == "NINGUNO" and "causa raíz" in rec.texto


def test_critico_usa_confiabilidad_objetivo_y_pf():
    rec = politicas.recomendar(3.42, 774, cp=400, cf=2500, critico=True, seguridad=False, intervalo_pf=None,
                               r_objetivo=0.9, cf_cp_minimo=2, paso_redondeo=25)
    assert rec.regla == "CONFIABILIDAD_OBJETIVO" and rec.t_optimo == pytest.approx(401, rel=0.005)
    assert politicas.recomendar(3, 700, cp=1, cf=1, critico=False, seguridad=False, intervalo_pf=200, r_objetivo=0.9,
                                cf_cp_minimo=2, paso_redondeo=25).intervalo == 100


def test_cf_cp_bajo_y_falta_de_costos():
    r = politicas.recomendar(3, 700, cp=400, cf=600, critico=False, seguridad=False, intervalo_pf=None, r_objetivo=0.9,
                             cf_cp_minimo=2, paso_redondeo=25)
    assert r.regla == "NINGUNO" and "Cf/Cp" in r.texto
    r = politicas.recomendar(3, 700, cp=None, cf=None, critico=False, seguridad=False, intervalo_pf=None,
                             r_objetivo=0.9, cf_cp_minimo=2, paso_redondeo=25)
    assert "costos" in r.texto


def test_inventarios_catedra():
    assert politicas.lote_economico(200, 1200, 50, 0.25) == pytest.approx((2 * 200 * 1200 / (50 * 0.25)) ** 0.5)
    q = politicas.lote_economico(200, 1200, 50, 0.25)
    assert politicas.costo_total_inventario(q, 200, 1200, 50, 0.25) <= politicas.costo_total_inventario(q * 1.2, 200, 1200, 50, 0.25)
    assert politicas.factor_h(0.10) == pytest.approx(1.29, abs=0.01)  # tabla de la UNIDAD 5 (B-007)
    assert politicas.stock_proteccion(0.10, 2, 9) == pytest.approx(1.2816 * 18**0.5, rel=1e-3)
    assert politicas.stock_minimo_poisson(1.3, 0.95) == 3
    assert politicas.stock_minimo_poisson(0, 0.95) == 0


def test_crow_amsaa_y_laplace():
    degradacion = [500, 800, 1000, 1150, 1250, 1320, 1380, 1420]
    c = sistemas.crow_amsaa(degradacion, 1450)
    assert c.beta > 1 and c.beta_ic[0] < c.beta < c.beta_ic[1]
    assert c.fallas_esperadas(1450) == pytest.approx(len(degradacion))
    u, p = sistemas.laplace(degradacion, 1450)
    assert u > 0
    mejora = [50, 120, 220, 400, 700, 1100]
    assert sistemas.crow_amsaa(mejora, 1450).beta < 1
    assert sistemas.laplace(mejora, 1450)[0] < 0


def test_costos_y_ctmc():
    assert costos.cp(300, 2, 50) == 400
    assert costos.lucro_cesante(2, 4, 1000) == 0  # la parada no supera el pulmón
    assert costos.cf(300, 4, 50, 6, 4, 900) == 300 + 200 + 2 * 900
    d = costos.DesgloseCTMC(modm=200, cr=300, cm=10, ch=5, co=1800, ci=0, cdrp=50)
    assert d.cdmc == 515 and d.clc == 1850 and d.ctmc == 2365
    assert costos.cit(1000, 500, 200, 2365) == 4065
    assert costos.a_dolares(1495, 1495) == 1


def test_semaforo_reglas():
    s = semaforo.color_componente
    assert s(0.05, 100, 400, False, "MEDIA", "B").color == "VERDE"
    assert s(0.12, 100, 400, False, "MEDIA", "B").color == "AMARILLO"
    assert s(0.05, 330, 400, False, "MEDIA", "B").color == "AMARILLO"  # > 80 % del intervalo
    assert s(0.05, 100, 400, True, "MEDIA", "B").color == "ROJO"  # OT abierta
    assert s(0.22, 100, 400, False, "MEDIA", "A").color == "ROJO"  # más exigente para clase A
    assert s(None, 100, None, False, "GRIS", "B").color == "GRIS"
    assert s(None, 450, 400, False, "GRIS", "B").color == "ROJO"  # gris con intervalo del fabricante superado
    m = semaforo.color_maquina([s(0.05, 1, 400, False, "MEDIA", "B"), s(0.4, 1, 400, False, "BAJA", "B")])
    assert m.color == "ROJO" and not m.duro


def test_weibayes_y_seleccion():
    cfg = Configuracion()
    assert W.seleccionar_metodo(1, 3, 0, 3.0, cfg) == "WEIBAYES"
    assert W.seleccionar_metodo(1, 3, 0, None, cfg) == "NINGUNO"
    assert W.seleccionar_metodo(5, 2, 0, None, cfg) == "RRX"
    assert W.seleccionar_metodo(5, 6, 0, None, cfg) == "MLE"  # > 50 % suspensiones
    assert W.seleccionar_metodo(20, 0, 0, None, cfg) == "MLE"
    assert W.seleccionar_metodo(3, 0, 1, None, cfg) == "MLE"  # intervalos
    eta, ic = W.weibayes([O(400, "S"), O(500, "S")], 3.0, 0.9)
    assert eta == pytest.approx((400**3 + 500**3) ** (1 / 3))  # r = 0 → r = 1 (D-011)
    r = W.ajustar([O(400, "S"), O(500, "S")], beta_ref=3.0)
    assert r.vigente.metodo == "WEIBAYES" and r.vigente.confianza == "GRIS" and any("supuesto" in a for a in r.vigente.advertencias)
    assert W.ajustar([O(400, "F")]).vigente.metodo == "NINGUNO"


def test_interpretacion_de_beta():
    cfg = Configuracion()
    assert W.interpretar(0.6, (0.4, 0.8), cfg) == "MORTALIDAD_INFANTIL"
    assert W.interpretar(1.05, None, cfg) == "ALEATORIA"
    assert W.interpretar(1.6, (0.8, 2.5), cfg) == "ALEATORIA"  # el IC contiene a 1 (D-006)
    assert W.interpretar(2.5, (1.6, 3.4), cfg) == "DESGASTE"
    assert W.interpretar(5, (4.2, 6), cfg) == "DESGASTE_RAPIDO"


def test_flota():
    import numpy as np

    rng = np.random.default_rng(3)
    a = [O(float(x), "F") for x in 500 * rng.weibull(3, 15)]
    b = [O(float(x), "F") for x in 520 * rng.weibull(3, 15)]
    c = [O(float(x), "F") for x in 150 * rng.weibull(1.2, 15)]
    assert W.prueba_flota({"a": a, "b": b})[1] > 0.05  # misma población: se pueden agrupar
    assert W.prueba_flota({"a": a, "c": c})[1] < 0.05  # distintas
