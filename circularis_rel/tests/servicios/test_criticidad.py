import pytest

from circularis_rel.asistente.criticidad import evaluar_tp, nivel_por_cortes

CORTES = {"Alta": 25, "Media": 20, "Baja": 15}
CLASES = {"Alta": "A", "Media": "B", "Baja": "C", "Muy baja": "C"}
PESOS = {"produccion": 0.30, "influencia": 0.20, "calidad": 0.15, "seguridad": 0.15, "ambiente": 0.10, "sustitucion": 0.10}


@pytest.mark.referencia
@pytest.mark.parametrize("maquina,valores,puntaje,nivel", [
    # Tabla de análisis de prioridad del TP N.º 1
    ("Agrumadora", (5, 2, 4, 4, 3, 5), 23, "Media"),
    ("Trituradoras", (3, 2, 2, 2, 3, 5), 17, "Baja"),
    ("Cuba de lavado", (5, 5, 4, 4, 3, 3), 24, "Media"),
    ("Secadora", (5, 5, 5, 5, 3, 3), 26, "Alta"),
    ("Enfardadoras", (3, 4, 2, 1, 1, 3), 14, "Muy baja"),
    ("Mezcladora", (5, 5, 4, 5, 1, 3), 23, "Media"),
    ("Extrusión", (5, 5, 5, 5, 3, 5), 28, "Alta"),
])
def test_reproduce_tabla_del_tp1(maquina, valores, puntaje, nivel):
    v = dict(zip(("uso", "alternativa", "influencia", "calidad", "ambiente", "seguridad"), valores, strict=True))
    r = evaluar_tp(v, CORTES, CLASES, PESOS)
    assert r.puntaje == puntaje and r.nivel == nivel and r.clase == CLASES[nivel]


def test_ponderado_del_plan():
    v = dict(uso=5, alternativa=5, influencia=5, calidad=5, ambiente=3, seguridad=5)
    assert evaluar_tp(v, CORTES, CLASES, PESOS).puntaje_ponderado == pytest.approx(4.8)


def test_cortes_en_el_borde():
    assert nivel_por_cortes(25, CORTES) == "Alta"
    assert nivel_por_cortes(24.9, CORTES) == "Media"
    assert nivel_por_cortes(14, CORTES) == "Muy baja"


def test_valor_fuera_de_escala():
    with pytest.raises(ValueError, match="escala"):
        evaluar_tp(dict(uso=4, alternativa=5, influencia=5, calidad=5, ambiente=3, seguridad=5), CORTES, CLASES)
