"""Sección 13, caso 9: preparación de datos, casos borde."""

from circularis_rel.motor.preparacion import VidaDatos as V
from circularis_rel.motor.preparacion import armar_poblacion

MODO, OTRO = 1, 2


def test_casos_borde():
    vidas = [
        V(410, "FALLA", MODO),                                   # falla del modo → F
        V(300, "SUSPENSION_PREVENTIVA"),                         # preventivo → S
        V(250, "FALLA", OTRO),                                   # otro modo → S (riesgos competitivos)
        V(520, "EN_SERVICIO"),                                   # vida abierta → S
        V(600, "FALLA", MODO, validado=False),                   # sin validar → fuera
        V(700, "FALLA", MODO, edad_conocida=False),              # instalado antes del sistema → fuera
        V(None, "FALLA", MODO),                                  # sin edad → fuera
        V(800, "FALLA", MODO, edad_inf=650, origen="HIST_B"),    # histórico B → intervalo
        V(450, "FALLA", MODO, origen="HIST_A"),                  # histórico A → F con horas E
        V(0, "FALLA", MODO),                                     # edad 0 → fuera (error de carga)
    ]
    obs, r = armar_poblacion(vidas, MODO)
    estados = [(o.edad, o.estado) for o in obs]
    assert estados == [(410, "F"), (300, "S"), (250, "S"), (520, "S"), (800, "I"), (450, "F")]
    assert (r.n_fallas, r.n_suspensiones, r.n_intervalo) == (2, 3, 1)
    assert r.n_estimadas == 2
    assert sum(r.excluidas.values()) == 4
    assert obs[4].edad_inf == 650


def test_en_servicio_solo_pronostico_y_excluida():
    vidas = [V(410, "FALLA", MODO), V(520, "EN_SERVICIO")]
    obs, r = armar_poblacion(vidas, MODO, en_servicio_solo_pronostico=True)
    assert obs[1].solo_pronostico and r.n_suspensiones == 0
    obs, r = armar_poblacion(vidas, MODO, incluir_en_servicio=False)
    assert len(obs) == 1


def test_edad_en_toneladas_es_igual_que_en_horas():
    """El motor acepta cualquier variable de uso monótona (Plan §4): la edad ya viene en la unidad del tipo."""
    obs_h, _ = armar_poblacion([V(410, "FALLA", MODO)], MODO)
    obs_t, _ = armar_poblacion([V(12.5, "FALLA", MODO)], MODO)
    assert obs_h[0].estado == obs_t[0].estado == "F"


def test_reparacion_minima_opcional():
    vidas = [V(410, "FALLA", MODO, reparacion_minima=True), V(500, "FALLA", MODO)]
    assert len(armar_poblacion(vidas, MODO)[0]) == 2
    assert len(armar_poblacion(vidas, MODO, excluir_reparacion_minima=True)[0]) == 1
