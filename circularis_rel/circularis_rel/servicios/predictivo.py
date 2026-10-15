"""Mantenimiento predictivo [12.G] (plantilla MANT/PMRED001 de la UNIDAD 6; ultrasonido de la UNIDAD 3).

- Hasta 3 parámetros por máquina y especialidad (las tres columnas de la plantilla).
- Cada parámetro tiene línea base, límite de alerta y límite de acción. Si el límite de acción es menor que la
  línea base, el parámetro empeora cuando baja (por ejemplo, una aislación).
- Una medición fuera de límite genera una alerta; sobre el límite de acción, además, una OT de inspección
  (una por parámetro mientras esté abierta).
- Plantilla de ultrasonido en rodamientos: la medición se compara con la línea base en dB y se clasifica con la
  tabla de referencia de la UNIDAD 3 (`predictivo.ultrasonido_rodamientos_db`, editable; no es norma).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from circularis_rel.datos.enums import EstadoOT, TipoOT
from circularis_rel.datos.modelos import (
    Activo,
    OrdenTrabajo,
    OTTarea,
    PredictivoMedicion,
    PredictivoParametro,
    Usuario,
)
from circularis_rel.motor import tendencia
from circularis_rel.servicios import alertas
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios.ot import nuevo_numero
from circularis_rel.servicios.permisos import Accion, requerir
from circularis_rel.servicios.registro import ErrorRegistro

PLANTILLA_ULTRASONIDO = "ULTRASONIDO_RODAMIENTOS"
MAX_POR_ESPECIALIDAD = 3


def _usuario(s: Session, id_usuario: int, accion: Accion) -> Usuario:
    u = s.get(Usuario, id_usuario)
    if u is None or not u.activo:
        raise ErrorRegistro("Usuario no válido")
    requerir(u.rol, accion)
    return u


def crear_parametro(s: Session, id_usuario: int, id_activo: int, especialidad: str, nombre: str, unidad: str, *,
                    linea_base: float | None = None, limite_alerta: float | None = None, limite_accion: float | None = None,
                    plantilla: str | None = None, id_posicion: int | None = None) -> PredictivoParametro:
    _usuario(s, id_usuario, Accion.CONFIGURAR)
    especialidad, nombre = (especialidad or "").strip(), (nombre or "").strip()
    if not especialidad or not nombre or not (unidad or "").strip():
        raise ErrorRegistro("Faltan la especialidad, el nombre o la unidad")
    n = s.scalar(select(func.count()).select_from(PredictivoParametro).where(
        PredictivoParametro.id_activo == id_activo, PredictivoParametro.especialidad == especialidad,
        PredictivoParametro.activo.is_(True)))
    if n >= MAX_POR_ESPECIALIDAD:
        raise ErrorRegistro(f"La plantilla MANT/PMRED001 admite hasta {MAX_POR_ESPECIALIDAD} parámetros por máquina y especialidad")
    if plantilla == PLANTILLA_ULTRASONIDO:
        if linea_base is None:
            raise ErrorRegistro("El ultrasonido necesita la línea base en dB (medición en funcionamiento normal)")
        tabla = P.obtener(s, "predictivo.ultrasonido_rodamientos_db")
        if limite_alerta is None:
            limite_alerta = linea_base + min(f["desde_db"] for f in tabla)
        if limite_accion is None:
            limite_accion = linea_base + sorted(f["desde_db"] for f in tabla)[2]  # "falla: programar reemplazo"
    if limite_alerta is not None and limite_accion is not None and linea_base is not None:
        creciente = limite_accion >= linea_base
        if (creciente and limite_alerta > limite_accion) or (not creciente and limite_alerta < limite_accion):
            raise ErrorRegistro("El límite de alerta tiene que estar antes que el de acción")
    p = PredictivoParametro(id_activo=id_activo, id_posicion=id_posicion, especialidad=especialidad, nombre=nombre,
                            unidad=unidad.strip(), linea_base=linea_base, limite_alerta=limite_alerta,
                            limite_accion=limite_accion, plantilla=plantilla, activo=True)
    s.add(p)
    s.flush()
    return p


def creciente(p: PredictivoParametro) -> bool:
    if p.limite_accion is not None and p.linea_base is not None:
        return p.limite_accion >= p.linea_base
    return True


def _supera(p: PredictivoParametro, valor: float, limite: float | None) -> bool:
    if limite is None:
        return False
    return valor >= limite if creciente(p) else valor <= limite


@dataclass
class Evaluacion:
    nivel: str  # NORMAL | ALERTA | ACCION
    texto: str
    ot: OrdenTrabajo | None = None


def evaluar(s: Session, p: PredictivoParametro, valor: float) -> tuple[str, str]:
    if p.plantilla == PLANTILLA_ULTRASONIDO and p.linea_base is not None:
        fila = tendencia.clasificar_ultrasonido(valor - p.linea_base, P.obtener(s, "predictivo.ultrasonido_rodamientos_db"))
        if fila is not None:
            nivel = "ACCION" if _supera(p, valor, p.limite_accion) else "ALERTA"
            return nivel, f"+{valor - p.linea_base:g} dB sobre la base: {fila['estado']}. {fila['accion']} (referencia UNIDAD 3)"
    if _supera(p, valor, p.limite_accion):
        return "ACCION", f"Superó el límite de acción ({p.limite_accion:g} {p.unidad})"
    if _supera(p, valor, p.limite_alerta):
        return "ALERTA", f"Superó el límite de alerta ({p.limite_alerta:g} {p.unidad})"
    return "NORMAL", "Dentro de los límites"


def registrar(s: Session, id_usuario: int, id_parametro: int, fecha: datetime, valor: float,
              equipo: str | None = None) -> Evaluacion:
    u = _usuario(s, id_usuario, Accion.CERRAR_OT)
    p = s.get(PredictivoParametro, id_parametro)
    if p is None or not p.activo:
        raise ErrorRegistro("Parámetro no válido")
    s.add(PredictivoMedicion(id_parametro=p.id, fecha=fecha, valor=valor, equipo_medicion=(equipo or "").strip() or None,
                             id_usuario_controlo=u.id))
    s.flush()
    nivel, texto = evaluar(s, p, valor)
    activo = s.get(Activo, p.id_activo)
    clave = f"predictivo:{p.id}"
    ot = None
    if nivel == "NORMAL":
        alertas.resolver(s, clave)
    else:
        alertas.emitir(s, "PREDICTIVO", "alta" if nivel == "ACCION" else "media",
                       f"{activo.codigo} · {p.nombre}: {valor:g} {p.unidad}. {texto}", clave, id_activo=p.id_activo,
                       id_posicion=p.id_posicion, destinatarios="JEFE,ENCARGADO")
        if nivel == "ACCION":
            ot = _ot_inspeccion(s, p, valor, texto)
    return Evaluacion(nivel, texto, ot)


def _ot_inspeccion(s: Session, p: PredictivoParametro, valor: float, texto: str) -> OrdenTrabajo:
    marca = f"[predictivo {p.id}]"
    abierta = s.scalar(select(OrdenTrabajo).where(OrdenTrabajo.id_activo == p.id_activo, OrdenTrabajo.tipo == TipoOT.INSPECCION,
                                                  OrdenTrabajo.estado.in_([EstadoOT.SOLICITADA, EstadoOT.PLANIFICADA,
                                                                           EstadoOT.EN_EJECUCION]),
                                                  OrdenTrabajo.observaciones.like(f"%{marca}%")))
    if abierta is not None:
        return abierta
    ot = OrdenTrabajo(numero=nuevo_numero(s), tipo=TipoOT.INSPECCION, id_activo=p.id_activo, id_posicion=p.id_posicion,
                      estado=EstadoOT.SOLICITADA, prioridad=1, observaciones=f"{marca} {p.nombre} = {valor:g} {p.unidad}. {texto}")
    s.add(ot)
    s.flush()
    s.add(OTTarea(id_ot=ot.id, numero=1, descripcion=f"Inspeccionar por {p.nombre.lower()} fuera de límite y decidir la acción"))
    s.flush()
    return ot


def historia(s: Session, id_parametro: int) -> list[PredictivoMedicion]:
    return list(s.scalars(select(PredictivoMedicion).where(PredictivoMedicion.id_parametro == id_parametro)
                          .order_by(PredictivoMedicion.fecha)))


def tendencia_parametro(s: Session, p: PredictivoParametro) -> tendencia.Tendencia | None:
    medidas = historia(s, p.id)
    if len(medidas) < 3:
        return None
    t0 = medidas[0].fecha
    return tendencia.ajustar([(m.fecha - t0).total_seconds() / 86400 for m in medidas], [m.valor for m in medidas],
                             p.limite_accion, creciente(p))
