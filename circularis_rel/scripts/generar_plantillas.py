"""Genera las plantillas Excel vacías y `docs/plantillas/FORMATO.md` desde el esquema.

Uso:  python scripts/generar_plantillas.py
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from circularis_rel.servicios.importador.esquema import HOJA_HISTORICO, HOJAS_CARGA_INICIAL  # noqa: E402
from circularis_rel.servicios.importador.plantillas import (  # noqa: E402
    plantilla_carga_inicial,
    plantilla_historico,
)

DESTINO = RAIZ / "docs" / "plantillas"


def formato_md() -> str:
    lineas = [
        "# Formato de las planillas de importación",
        "",
        "Generado por `scripts/generar_plantillas.py` desde `circularis_rel/servicios/importador/esquema.py`. "
        "No editar a mano.",
        "",
        "## Reglas generales",
        "",
        "- **Fila 1:** encabezados. No se cambian. **Fila 2:** ayuda, que se ignora al leer. Los datos empiezan en la **fila 3**.",
        "- Columnas obligatorias: encabezado en rojo y \"* obligatoria\" en la ayuda.",
        "- La clave es el **código**: re-importar el mismo libro actualiza lo que cambió y no duplica.",
        "- Una celda vacía **no borra** un dato existente. Para borrar se edita en el sistema, y queda auditado.",
        "- Fechas `DD/MM/AAAA`, horas `HH:MM`, números con coma o punto decimal. SI/NO para las casillas.",
        "- **Todo o nada:** si hay un error en cualquier fila no se graba nada y el reporte indica hoja, fila y columna.",
        "- Conviene usar primero **Simular**: hace todas las validaciones y no graba.",
        "- Se pueden importar solo algunas hojas: las ausentes se ignoran.",
        "",
        "## Archivos",
        "",
        "| Archivo | Uso |",
        "|---|---|",
        "| `carga_inicial.xlsx` | Plantilla vacía de la carga inicial |",
        "| `historico.xlsx` | Plantilla vacía del histórico con triage A/B/C |",
        "| `carga_inicial_borrador_TP1.xlsx` | Borrador precargado con el Plan y el TP N.º 1. **Revisar antes de importar** (ver hoja LEEME) |",
        "",
    ]
    for hoja in (*HOJAS_CARGA_INICIAL, HOJA_HISTORICO):
        archivo = "historico.xlsx" if hoja is HOJA_HISTORICO else "carga_inicial.xlsx"
        lineas += [f"## Hoja `{hoja.nombre}` ({archivo})", "", hoja.descripcion, "",
                   "| Columna | Tipo | Obligatoria | Ayuda / valores |", "|---|---|---|---|"]
        for c in hoja.columnas:
            ayuda = c.ayuda
            if c.opciones:
                ayuda = (ayuda + ". " if ayuda else "") + "Valores: " + ", ".join(f"`{o}`" for o in c.opciones)
            if c.minimo is not None or c.maximo is not None:
                ayuda += f" (rango {c.minimo if c.minimo is not None else '−∞'} a {c.maximo if c.maximo is not None else '∞'})"
            lineas.append(f"| `{c.nombre}` | {c.tipo} | {'sí' if c.obligatoria else ''} | {ayuda} |")
        lineas.append("")
    lineas += [
        "## Triage del histórico",
        "",
        "| Clase | Requisitos | Uso en el cálculo |",
        "|---|---|---|",
        "| A, confiable | posición, `fecha_fin` real, `respaldo` (OT, factura, parte) y `modo` si es FALLA | Vida con horas de nivel E |",
        "| B, parcial | posición y rango de fecha (`fecha_fin_desde`/`hasta`) o de edad (`edad_desde_h`/`hasta`) | Censura por intervalo, solo MLE |",
        "| C, no usable | cualquier otro caso | Fuera del ajuste; solo Pareto cualitativo |",
        "",
        "Si `clase` queda vacía, el sistema la propone. Si se indica una clase que no cumple los requisitos, es error. "
        "Las fechas con espaciado regular (por ejemplo cada 30 días) generan la advertencia \"posibles valores reconstruidos\".",
        "",
    ]
    return "\n".join(lineas)


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    plantilla_carga_inicial(DESTINO / "carga_inicial.xlsx")
    plantilla_historico(DESTINO / "historico.xlsx")
    (DESTINO / "FORMATO.md").write_text(formato_md(), encoding="utf-8")
    print("Plantillas generadas en", DESTINO.relative_to(RAIZ))


if __name__ == "__main__":
    main()
