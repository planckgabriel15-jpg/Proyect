"""Análisis de causa raíz [12.D]: 5 Porqués con ciclo PDCA y conversión en OT modificativa.

- 5 Porqués (UNIDAD 4): se parte del problema y se pregunta "¿por qué?" hasta llegar a una causa
  sobre la que se pueda actuar. No hace falta llegar a cinco: se corta cuando la causa es accionable.
- PDCA del pilar de mejoras enfocadas (UNIDAD 4, diap. 11): Planificar (dónde, qué, quién, cómo,
  cuándo), Hacer (ejecutar, revertir el deterioro, registrar), Chequear (desvío entre resultado y meta) y
  "A" = Analizar el fenómeno con 5W+1H y 5 Porqués. El análisis inicial se hace al crear; el paso A del
  sistema (ACTUAR) es volver a analizar si quedó desvío o estandarizar lo que funcionó (B-016).
  Cada paso queda registrado con fecha, usuario y nota.
- La acción correctiva puede convertirse en una OT MODIFICATIVO (mejora o rediseño) para que entre en
  el circuito normal de órdenes.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from circularis_rel.datos.db import ahora
from circularis_rel.datos.enums import EstadoOT, EstadoPDCA, OrigenAnalisis, TipoAnalisis, TipoOT
from circularis_rel.datos.modelos import AnalisisProblema, OrdenTrabajo, Usuario
from circularis_rel.servicios.ot import nuevo_numero
from circularis_rel.servicios.permisos import Accion, requerir
from circularis_rel.servicios.registro import ErrorRegistro

MAX_PORQUES = 5
ORDEN_PDCA = [EstadoPDCA.PLANIFICAR, EstadoPDCA.HACER, EstadoPDCA.CHEQUEAR, EstadoPDCA.ACTUAR, EstadoPDCA.CERRADO]
QUE_ES_PDCA = {
    EstadoPDCA.PLANIFICAR: "Planificar las acciones correctivas y preventivas: dónde, qué, quién, cómo y cuándo.",
    EstadoPDCA.HACER: "Ejecutar las acciones, revertir el deterioro, implementar las mejoras; registro y seguimiento.",
    EstadoPDCA.CHEQUEAR: "Chequear el desvío entre los resultados obtenidos y la meta fijada (¿dejó de fallar?).",
    EstadoPDCA.ACTUAR: "Analizar: si quedó desvío, volver a buscar la causa (5W+1H y 5 Porqués); si funcionó, estandarizarlo.",
    EstadoPDCA.CERRADO: "Análisis terminado.",
}
NOMBRE_PDCA = {EstadoPDCA.PLANIFICAR: "Planificar", EstadoPDCA.HACER: "Hacer", EstadoPDCA.CHEQUEAR: "Chequear",
               EstadoPDCA.ACTUAR: "Analizar / estandarizar", EstadoPDCA.CERRADO: "Cerrado"}


def _usuario(s: Session, id_usuario: int) -> Usuario:
    u = s.get(Usuario, id_usuario)
    if u is None or not u.activo:
        raise ErrorRegistro("Usuario no válido")
    requerir(u.rol, Accion.CARGAR_ANALISIS)
    return u


def _analisis(s: Session, id_analisis: int) -> AnalisisProblema:
    a = s.get(AnalisisProblema, id_analisis)
    if a is None:
        raise ErrorRegistro("El análisis no existe")
    return a


def crear(s: Session, id_usuario: int, problema: str, *, id_activo: int | None = None, id_tipo: int | None = None,
          id_modo: int | None = None, id_evento: int | None = None, origen: OrigenAnalisis = OrigenAnalisis.MANUAL,
          motivos_sugerencia: list[str] | None = None, tipo: TipoAnalisis = TipoAnalisis.CINCO_PORQUES) -> AnalisisProblema:
    u = _usuario(s, id_usuario)
    if not problema or not problema.strip():
        raise ErrorRegistro("Describí el problema")
    a = AnalisisProblema(tipo=tipo, id_activo=id_activo, id_tipo_componente=id_tipo, id_modo=id_modo, id_evento=id_evento,
                         origen=origen, contenido={"problema": problema.strip(), "porques": [],
                                                   "motivos_sugerencia": motivos_sugerencia or [],
                                                   "pdca": [_paso(EstadoPDCA.PLANIFICAR, u, "Análisis creado")]})
    s.add(a)
    s.flush()
    return a


def _paso(estado: EstadoPDCA, u: Usuario, nota: str) -> dict:
    return {"estado": estado.value, "fecha": ahora().isoformat(timespec="seconds"), "usuario": u.nombre, "nota": nota}


def guardar_porques(s: Session, id_usuario: int, id_analisis: int, porques: list[str], *, causa_raiz: str | None = None,
                    accion: str | None = None, responsable: str | None = None,
                    fecha_compromiso: date | None = None) -> AnalisisProblema:
    _usuario(s, id_usuario)
    a = _analisis(s, id_analisis)
    if a.estado_pdca == EstadoPDCA.CERRADO:
        raise ErrorRegistro("El análisis está cerrado")
    limpios = [p.strip() for p in porques if p and p.strip()]
    if len(limpios) > MAX_PORQUES:
        raise ErrorRegistro(f"Hasta {MAX_PORQUES} porqués")
    ultimo = max((i for i, p in enumerate(porques) if p and p.strip()), default=-1)
    if any(not (p and p.strip()) for p in porques[:ultimo]):
        raise ErrorRegistro("No dejes porqués vacíos en el medio")
    a.contenido = {**(a.contenido or {}), "porques": limpios}
    a.causa_raiz = (causa_raiz or "").strip() or (limpios[-1] if limpios else None)
    a.accion_correctiva = (accion or "").strip() or None
    a.responsable = (responsable or "").strip() or None
    a.fecha_compromiso = fecha_compromiso
    s.flush()
    return a


def avanzar(s: Session, id_usuario: int, id_analisis: int, nota: str = "") -> AnalisisProblema:
    """Pasa al siguiente paso del PDCA, con sus condiciones mínimas."""
    u = _usuario(s, id_usuario)
    a = _analisis(s, id_analisis)
    i = ORDEN_PDCA.index(a.estado_pdca)
    if i == len(ORDEN_PDCA) - 1:
        raise ErrorRegistro("El análisis ya está cerrado")
    siguiente = ORDEN_PDCA[i + 1]
    if siguiente == EstadoPDCA.HACER and not (a.causa_raiz and a.accion_correctiva and a.responsable):
        raise ErrorRegistro("Para pasar a Hacer hacen falta la causa raíz, la acción y el responsable")
    if siguiente in (EstadoPDCA.ACTUAR, EstadoPDCA.CERRADO) and not nota.strip():
        raise ErrorRegistro("Anotá qué se verificó o qué se estandarizó")
    a.estado_pdca = siguiente
    a.contenido = {**(a.contenido or {}), "pdca": [*(a.contenido or {}).get("pdca", []), _paso(siguiente, u, nota.strip())]}
    s.flush()
    return a


def convertir_en_ot(s: Session, id_usuario: int, id_analisis: int) -> OrdenTrabajo:
    """Crea una OT MODIFICATIVO con la acción correctiva (una sola por análisis)."""
    _usuario(s, id_usuario)
    a = _analisis(s, id_analisis)
    if a.id_ot_generada is not None:
        raise ErrorRegistro("Este análisis ya tiene una OT")
    if a.id_activo is None:
        raise ErrorRegistro("El análisis necesita una máquina para generar la OT")
    if not a.accion_correctiva:
        raise ErrorRegistro("Primero cargá la acción correctiva")
    ot = OrdenTrabajo(numero=nuevo_numero(s), tipo=TipoOT.MODIFICATIVO, id_activo=a.id_activo, estado=EstadoOT.PLANIFICADA,
                      responsable=a.responsable, fecha_programada=a.fecha_compromiso,
                      observaciones=f"Análisis de causa raíz n.º {a.id}: {a.accion_correctiva}")
    s.add(ot)
    s.flush()
    a.id_ot_generada = ot.id
    s.flush()
    return ot
