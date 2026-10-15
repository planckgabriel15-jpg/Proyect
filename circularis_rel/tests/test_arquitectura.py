"""El motor no depende de la interfaz ni de la base (PLAN_TECNICO §3.2)."""

import ast
from pathlib import Path

PAQUETE = Path(__file__).resolve().parent.parent / "circularis_rel"

PROHIBIDOS = {
    "motor": {"streamlit", "sqlalchemy", "circularis_rel.datos", "circularis_rel.servicios", "circularis_rel.app", "circularis_rel.tareas"},
    "servicios": {"streamlit", "circularis_rel.app"},
    "datos": {"streamlit", "circularis_rel.app", "circularis_rel.motor", "circularis_rel.servicios"},
    "tareas": {"streamlit", "circularis_rel.app"},
    "asistente": {"streamlit", "circularis_rel.app"},
}


def _imports(archivo: Path) -> set[str]:
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    nombres: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres.update(a.name for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            nombres.add(nodo.module)
    return nombres


def test_capas_respetan_dependencias():
    violaciones = []
    for capa, prohibidos in PROHIBIDOS.items():
        for archivo in (PAQUETE / capa).rglob("*.py"):
            for nombre in _imports(archivo):
                if any(nombre == p or nombre.startswith(p + ".") for p in prohibidos):
                    violaciones.append(f"{archivo.relative_to(PAQUETE)} importa {nombre}")
    assert not violaciones, "\n".join(violaciones)
