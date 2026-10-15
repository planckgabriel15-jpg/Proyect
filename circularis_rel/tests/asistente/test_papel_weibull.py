"""Calculadora del papel de Weibull: reproduce el ejemplo de la UNIDAD 2 (diap. 33–38) y dibuja el papel."""

import math

import pytest

from circularis_rel.app.componentes import graficos as G
from circularis_rel.asistente import papel_weibull as PW
from circularis_rel.motor.tipos import Configuracion


def test_ejemplo_de_la_unidad_2():
    datos = [(t, True) for t in PW.EJEMPLO_UNIDAD2["tiempos"]]
    r = PW.calcular(datos, PW.EJEMPLO_UNIDAD2["mision"])
    # Tabla ordenada con F(i) de Benard (la propia diapositiva calcula 10,9; 26,5; 42,1; 57,8; 73,4; 89 %).
    assert [f.tiempo for f in r.filas] == [16, 34, 53, 75, 93, 120]
    assert [round(100 * f.f_benard, 1) for f in r.filas] == [10.9, 26.6, 42.2, 57.8, 73.4, 89.1]
    # β ≈ 1,4 y η ≈ 76 h leídos del papel; R(15) = 90,2 % (±10 % y ±2 puntos, B-012).
    assert r.beta == pytest.approx(1.4, rel=0.10) and r.eta == pytest.approx(76, rel=0.10)
    assert r.r_mision == pytest.approx(0.902, abs=0.02)
    assert r.estado.startswith("Desgaste") and r.ajuste is not None and r.ajuste.vigente.metodo == "RRX"
    assert PW.r_en_eta() == pytest.approx(0.368, abs=0.001)


def test_suspensiones_y_dias():
    horas = PW.a_horas([30, 45, 60], "días", 8)
    assert horas == [240, 360, 480]
    with pytest.raises(ValueError):
        PW.a_horas([30], "días", None)
    r = PW.calcular([(240, True), (300, False), (360, True), (480, True)], cfg=Configuracion(), con_ajuste=False)
    assert r.n_fallas == 3 and r.n_suspensiones == 1
    suspendida = next(f for f in r.filas if not f.falla)
    assert suspendida.f_benard is None and suspendida.orden == 2
    # Con una suspensión antes, el rango ajustado de la segunda falla pasa de 2 a 1 + (5 − 1)/(1 + 2) = 7/3 (Johnson).
    assert r.filas[2].rango == pytest.approx(7 / 3)


def test_pocos_datos_y_errores():
    r = PW.calcular([(100, True), (200, False)])
    assert r.beta is None and r.avisos
    with pytest.raises(ValueError):
        PW.calcular([(0, True), (10, True)])


def test_papel_de_la_catedra():
    r = PW.calcular([(t, True) for t in PW.EJEMPLO_UNIDAD2["tiempos"]], 15, con_ajuste=False)
    fig = G.probabilidad(r.rangos, r.beta, r.eta, t_mision=15)
    # Décadas completas (10 a 1.000, como en la diapositiva 35) y eje de F en escala de Weibull.
    assert tuple(fig.layout.xaxis.range) == (1, 3) and fig.layout.xaxis.type == "log"
    textos = [a.text for a in fig.layout.annotations]
    assert any(t.startswith("<b>β = 1,4") for t in textos) and any("η = 76 h" in t for t in textos)
    # Abanico de β: las 12 guías entran en dos décadas, con su rótulo arriba.
    assert all(G._num(b, 1) in textos for b in G.BETAS_ABANICO)
    assert any("F = 9," in t and "R = 90," in t for t in textos)  # lectura a la misión (diap. 38)
    assert "63,2" in fig.layout.yaxis.ticktext
    # Cada guía del abanico pasa por el polo (borde izquierdo, F = 63,2 %) con pendiente β en el papel.
    guias = [t for t in fig.data if t.hovertext and str(t.hovertext).startswith("Guía de β")]
    for g in guias:
        b = float(str(g.hovertext).split("= ")[1].split(":")[0].replace(",", "."))
        pendiente = (g.y[1] - g.y[0]) / math.log(g.x[1] / g.x[0])
        assert g.x[0] == 10 and g.y[0] == 0 and pendiente == pytest.approx(b)


def test_papel_sin_ajuste_ni_datos():
    assert G.probabilidad(None, None, None).data == ()
    fig = G.probabilidad([(500, 1, 0.5)], None, None)
    assert fig.layout.xaxis.range[1] - fig.layout.xaxis.range[0] >= 2
