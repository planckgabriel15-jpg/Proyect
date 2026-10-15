"""Arma `docs/plantillas/carga_inicial_borrador_TP1.xlsx`: un BORRADOR para que el jefe revise.

Fuentes (no se inventan datos de la planta):
- Plan de desarrollo §4 y §1: códigos AGR-001/002, EXT-001, LAV-001, ENF-001/002, TRI-001 y horas
  promedio por día (8 h agrumadoras, mezcladora y extrusora; 6 h cuba y secadora; 4 h moledora,
  trituradora y enfardadoras).
- TP N.º 1 (relevamiento de máquinas, análisis de prioridad y AMFE): nombres, funciones, criterios
  de criticidad, componentes, modos de falla y valores G/O/D. Los valores G/O/D y los datos de
  fallas del TP son ILUSTRATIVOS (inventados para el TP): se marcan con origen TP1_ILUSTRATIVO.
- Códigos MOL-001, SEC-001 y MEZ-001: PROPUESTOS siguiendo el patrón del Plan; confirmar.

Uso:  python scripts/armar_borrador_tp1.py
"""

from __future__ import annotations

import csv
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from circularis_rel.servicios.importador.esquema import HOJAS_CARGA_INICIAL  # noqa: E402
from circularis_rel.servicios.importador.plantillas import escribir_libro  # noqa: E402

AMFE = RAIZ / "seeds" / "tp1" / "amfe_tp1.psv"
SALIDA = RAIZ / "docs" / "plantillas" / "carga_inicial_borrador_TP1.xlsx"

# Máquinas: (código, nombre, etapa, horas/día, unidad, nombre en el AMFE del TP, criterios TP)
# criterios = (uso, alternativa, influencia, calidad, ambiente, seguridad) del TP N.º 1.
MAQUINAS = [
    ("AGR-001", "Agrumadora 1", "PREPROCESADO", 8, None, None, (5, 2, 4, 4, 3, 5)),
    ("AGR-002", "Agrumadora 2", "PREPROCESADO", 8, None, None, (5, 2, 4, 4, 3, 5)),
    ("MOL-001", "Moledora (código a confirmar)", "PREPROCESADO", 4, None, "Moledora", (5, 2, 4, 4, 3, 5)),
    ("TRI-001", "Trituradora", "PREPROCESADO", 4, None, "Trituradora", (3, 2, 2, 2, 3, 5)),
    ("LAV-001", "Cuba de lavado", "LAVADO", 6, None, "Cuba de lavado", (5, 5, 4, 4, 3, 3)),
    ("SEC-001", "Secadora industrial (código a confirmar)", "SECADO", 6, None, "Secadora", (5, 5, 5, 5, 3, 3)),
    ("MEZ-001", "Mezcladora (código a confirmar)", "FORMULACION", 8, None, "Mezcladora", (5, 5, 4, 5, 1, 3)),
    ("EXT-001", "Línea de extrusión", "EXTRUSION", 8, "DURMIENTES", "Extrusora", (5, 5, 5, 5, 3, 5)),
    ("ENF-001", "Enfardadora hidráulica 1", "ACONDICIONAMIENTO", 4, "FARDOS", "Enfardadora", (3, 4, 2, 1, 1, 3)),
    ("ENF-002", "Enfardadora hidráulica 2", "ACONDICIONAMIENTO", 4, "FARDOS", "Enfardadora", (3, 4, 2, 1, 1, 3)),
]

FUNCIONES = {
    "AGR": "Disminuye el volumen de los fardos de bolsas de polipropileno; cuatro cuchillas a unas 3500 rpm (TP N.º 1).",
    "MOL": "Molienda previa de scrap y plásticos duros (bidones) antes del lavado y la extrusión (TP N.º 1).",
    "TRI": "Reducción de volumen de descartes y scrap industrial (TP N.º 1).",
    "LAV": "Cuba con paletas que lava el material plástico (TP N.º 1).",
    "SEC": "Elimina la humedad del material tras el lavado (TP N.º 1).",
    "MEZ": "Combina el material plástico seco con tintas y aditivos: fórmula final (TP N.º 1).",
    "EXT": "Funde el material y lo cuela en moldes para los durmientes T-WOOD (TP N.º 1).",
    "ENF": "Acondiciona y reduce el volumen de los materiales recuperados (TP N.º 1).",
}


def codigo(texto: str, largo: int = 40) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-").upper()
    return t[:largo].rstrip("-")


def armar() -> dict[str, list[dict]]:
    filas = list(csv.DictReader(AMFE.open(encoding="utf-8"), delimiter="|"))
    datos: dict[str, list[dict]] = {h.nombre: [] for h in HOJAS_CARGA_INICIAL}
    datos["lineas"].append({"codigo": "TWOOD", "nombre": "Línea T-WOOD (durmientes sintéticos)"})

    for cod, nombre, etapa, horas, unidad, _amfe, crit in MAQUINAS:
        datos["maquinas"].append({
            "codigo": cod, "nombre": nombre, "linea": "TWOOD", "etapa_proceso": etapa,
            "horas_promedio_dia": horas, "unidad_produccion": unidad, "funcion": FUNCIONES[cod[:3]],
            "ubicacion": "Planta Monte Cristo",
        })
        datos["criticidad"].append(dict(zip(
            ("maquina", "uso", "alternativa", "influencia", "calidad", "ambiente", "seguridad"),
            (cod, *crit), strict=True)) | {"metodo": "TP_6_CRITERIOS"})

    tipos: dict[str, str] = {}
    modos: dict[str, dict] = {}
    posiciones: set[tuple[str, str]] = set()

    def agregar_tipo(nombre: str) -> str:
        tc = codigo(nombre)
        tipos.setdefault(tc, nombre)
        return tc

    def agregar_modo(texto: str, tc: str, origen: str) -> str:
        mc = codigo(texto, 60)
        m = modos.setdefault(mc, {"codigo": mc, "descripcion": texto, "tipos": [], "origen": origen})
        if tc not in m["tipos"]:
            m["tipos"].append(tc)
        return mc

    # Agrumadoras: el TP N.º 1 no tiene AMFE. Componente y modo del ejemplo del Plan §15.
    tc_cuch = agregar_tipo("Cuchillas de agrumadora")
    agregar_modo("Pérdida de filo o rotura", tc_cuch, "PROPUESTA")
    for cod in ("AGR-001", "AGR-002"):
        datos["posiciones"].append({"maquina": cod, "codigo": "CUCHILLAS", "tipo_componente": tc_cuch,
                                    "cantidad": 4, "ubicacion": "Rotor"})

    for r in filas:
        maquinas = [m[0] for m in MAQUINAS if m[5] == r["maquina"]]
        tc = agregar_tipo(r["elemento"])
        mc = agregar_modo(r["modo"], tc, "TP1_ILUSTRATIVO")
        for cod in maquinas:
            pos = codigo(r["elemento"], 60)
            if (cod, pos) not in posiciones:
                posiciones.add((cod, pos))
                datos["posiciones"].append({"maquina": cod, "codigo": pos, "tipo_componente": tc})
            datos["amfe"].append({
                "maquina": cod, "tipo_componente": tc, "modo": mc, "requerimiento": r["requerimiento"],
                "efecto": r["efecto"], "causa": r["causa"], "control_prevencion": r["control_prevencion"],
                "control_deteccion": r["control_deteccion"], "g": int(r["G"]), "o": int(r["O"]), "d": int(r["D"]),
                "acciones": r["acciones"] or None, "origen": "TP1_ILUSTRATIVO",
            })

    datos["tipos_componente"] = [{"codigo": k, "nombre": v, "origen": "TP1_ILUSTRATIVO"} for k, v in sorted(tipos.items())]
    datos["modos"] = [{"codigo": m["codigo"], "descripcion": m["descripcion"],
                       "tipos_componente": ", ".join(m["tipos"]), "origen": m["origen"]}
                      for m in sorted(modos.values(), key=lambda m: m["codigo"])]
    return datos


NOTA = (
    "BORRADOR armado con el Plan de desarrollo y el TP N.º 1. REVISAR ANTES DE IMPORTAR.\n"
    "• Los valores G/O/D del AMFE y los datos de fallas del TP son ilustrativos (origen TP1_ILUSTRATIVO).\n"
    "• Códigos MOL-001, SEC-001 y MEZ-001: propuestos, confirmar con el listado real.\n"
    "• Falta cargar: turnos (hoja 'turnos' y 'maquina_turnos'), autonomía de pulmón, catastro (fabricante, modelo, "
    "n.º de serie…), repuestos con precio y fecha, y marcar las posiciones críticas.\n"
    "• El Plan §4 recomienda medir en toneladas la edad de cuchillas, dientes, contracuchillas, criba y tornillo: "
    "cambiar 'variable_edad' a TONELADAS cuando se cargue la cantidad procesada en el parte.\n"
    "• 'Flota y logística' (autoelevadores) del TP N.º 1 queda fuera del alcance del sistema."
)


def main() -> None:
    datos = armar()
    escribir_libro(SALIDA, HOJAS_CARGA_INICIAL, datos, nota=NOTA)
    print(f"Borrador generado: {SALIDA.relative_to(RAIZ)}")
    for hoja, filas in datos.items():
        if filas:
            print(f"  {hoja}: {len(filas)} filas")


if __name__ == "__main__":
    main()
