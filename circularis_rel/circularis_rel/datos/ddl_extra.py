"""Triggers de SQLite para las reglas que un CHECK no puede expresar.

Regla: el modo de falla (y la causa, si la causa está restringida) debe pertenecer al tipo
de componente de la posición; además cada referencia al catálogo debe ser del tipo correcto
(un síntoma no puede usarse como modo). Se ejecutan al crear el esquema (tests) y en la
migración inicial (producción). Para PostgreSQL hay que portarlos (DECISIONES D-018).
"""

from __future__ import annotations

from sqlalchemy import DDL, event

from circularis_rel.datos.modelos import Base

_MODO_COHERENTE = """
    NEW.{modo} IS NOT NULL AND NEW.id_posicion IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM catalogo_aplica ca
        JOIN posicion_componente p ON p.id_tipo_componente = ca.id_tipo_componente
        WHERE p.id = NEW.id_posicion AND ca.id_catalogo = NEW.{modo}
    )
"""

_CAUSA_COHERENTE = """
    NEW.id_causa IS NOT NULL AND NEW.id_posicion IS NOT NULL
    AND EXISTS (SELECT 1 FROM catalogo_aplica WHERE id_catalogo = NEW.id_causa)
    AND NOT EXISTS (
        SELECT 1 FROM catalogo_aplica ca
        JOIN posicion_componente p ON p.id_tipo_componente = ca.id_tipo_componente
        WHERE p.id = NEW.id_posicion AND ca.id_catalogo = NEW.id_causa
    )
"""


def _tipo_incorrecto(columna: str, tipo: str) -> str:
    return (
        f"NEW.{columna} IS NOT NULL AND "
        f"(SELECT tipo FROM catalogo WHERE id = NEW.{columna}) <> '{tipo}'"
    )


def _trigger(nombre: str, tabla: str, evento: str, condicion: str, mensaje: str) -> str:
    return (
        f"CREATE TRIGGER IF NOT EXISTS {nombre} BEFORE {evento} ON {tabla} "
        f"FOR EACH ROW WHEN {condicion} "
        f"BEGIN SELECT RAISE(ABORT, '{mensaje}'); END"
    )


def sentencias_sqlite() -> list[str]:
    s: list[str] = []
    for ev, suf in (("INSERT", "ins"), ("UPDATE", "upd")):
        s.append(_trigger(f"trg_evento_modo_{suf}", "evento_falla", ev,
                          _MODO_COHERENTE.format(modo="id_modo"),
                          "El modo de falla no corresponde al tipo de componente"))
        s.append(_trigger(f"trg_evento_causa_{suf}", "evento_falla", ev, _CAUSA_COHERENTE,
                          "La causa no corresponde al tipo de componente"))
        s.append(_trigger(f"trg_evento_tipos_{suf}", "evento_falla", ev,
                          f"({_tipo_incorrecto('id_modo', 'MODO')}) OR ({_tipo_incorrecto('id_causa', 'CAUSA')}) "
                          f"OR ({_tipo_incorrecto('id_sintoma', 'SINTOMA')})",
                          "Referencia al catálogo de tipo incorrecto"))
        s.append(_trigger(f"trg_vida_modo_{suf}", "vida_componente", ev,
                          _MODO_COHERENTE.format(modo="id_modo_falla"),
                          "El modo de falla no corresponde al tipo de componente"))
        s.append(_trigger(f"trg_vida_tipo_{suf}", "vida_componente", ev,
                          _tipo_incorrecto("id_modo_falla", "MODO"),
                          "Referencia al catálogo de tipo incorrecto"))
        s.append(_trigger(f"trg_evento_posicion_activo_{suf}", "evento_falla", ev,
                          "NEW.id_posicion IS NOT NULL AND "
                          "(SELECT id_activo FROM posicion_componente WHERE id = NEW.id_posicion) <> NEW.id_activo",
                          "La posición no pertenece a la máquina del aviso"))
    # Un evento validado no se borra (se anula con motivo).
    s.append(
        "CREATE TRIGGER IF NOT EXISTS trg_evento_no_borrar_validado BEFORE DELETE ON evento_falla "
        "FOR EACH ROW WHEN OLD.estado = 'VALIDADO' "
        "BEGIN SELECT RAISE(ABORT, 'Un evento validado no se puede borrar: anularlo con motivo'); END"
    )
    return s


for _sql in sentencias_sqlite():
    event.listen(Base.metadata, "after_create", DDL(_sql).execute_if(dialect="sqlite"))
