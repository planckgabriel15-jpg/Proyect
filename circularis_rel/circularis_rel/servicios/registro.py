"""Registro desde planta: parte de turno, aviso de falla y tarjetas TPM (Plan §4, §10; 12.F).

Reglas (Plan §11, "controles automáticos"):
- Parte: horas no operadas ≤ duración del turno, en pasos de 0,5 h; un parte por máquina y turno
  (si ya había uno ESTIMADO por el sistema, el del operario lo reemplaza); nada en el futuro.
- Aviso: hora no futura; el duplicado (misma máquina < 30 min) se advierte y se confirma.
- Operario: solo sus máquinas.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.db import ahora
from circularis_rel.datos.enums import (
    ColorTarjeta,
    EstadoEvento,
    EstadoParte,
    EstadoTarjeta,
    NivelHora,
    OrigenEvento,
    OrigenParte,
    Rol,
    TipoCatalogo,
)
from circularis_rel.datos.modelos import (
    Activo,
    Catalogo,
    EventoFalla,
    MotivoParada,
    ParteTurno,
    PosicionComponente,
    TarjetaTPM,
    Turno,
    Usuario,
    UsuarioActivo,
)
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios.permisos import Accion, requerir
from circularis_rel.servicios.turnos import ventana

# Listas cerradas de las tarjetas (UNIDAD 4, diap. 14: ejemplos de la cátedra + genéricas).
ANOMALIAS_AZUL = ["Tornillo flojo", "Falta arandela o traba", "Cable mal aislado", "Tapa o protección floja",
                  "Suciedad o derrame", "Falta de lubricación visible", "Otra anomalía simple"]
ANOMALIAS_ROJA = ["Pérdida de aceite o fluido", "Pieza desgastada o rota", "Ruido o vibración anormal",
                  "Calentamiento anormal", "Cilindro o actuador que no funciona", "Falla eléctrica", "Otra anomalía"]
MEJORAS_VERDE = ["Mejora de seguridad", "Mejora de orden y limpieza", "Mejora de acceso o visibilidad",
                 "Mejora para reducir tiempos", "Otra mejora"]


class ErrorRegistro(ValueError):
    """Dato que no se puede guardar; el mensaje es para mostrar en pantalla."""


@dataclass
class Advertencia:
    codigo: str
    texto: str


def _usuario(s: Session, id_usuario: int) -> Usuario:
    u = s.get(Usuario, id_usuario)
    if u is None or not u.activo:
        raise ErrorRegistro("Usuario no válido")
    return u


def maquinas_permitidas(s: Session, id_usuario: int) -> list[Activo]:
    """Operario: sus máquinas. Encargado y jefe: todas."""
    u = _usuario(s, id_usuario)
    consulta = select(Activo).where(Activo.activo.is_(True)).order_by(Activo.codigo)
    if u.rol == Rol.OPERARIO:
        consulta = consulta.join(UsuarioActivo, UsuarioActivo.id_activo == Activo.id).where(
            UsuarioActivo.id_usuario == u.id)
    return list(s.scalars(consulta))


def _verificar_maquina(s: Session, u: Usuario, id_activo: int, accion: Accion) -> Activo:
    a = s.get(Activo, id_activo)
    if a is None or not a.activo:
        raise ErrorRegistro("Máquina no válida")
    asignada = s.scalar(select(UsuarioActivo).where(UsuarioActivo.id_usuario == u.id,
                                                    UsuarioActivo.id_activo == id_activo)) is not None
    requerir(u.rol, accion, maquina_asignada=asignada if u.rol == Rol.OPERARIO else None)
    return a


# ---------------------------------------------------------------------------
# Parte de turno
# ---------------------------------------------------------------------------


def sugerencia_parte(s: Session, id_activo: int, fecha: date, turno: Turno, tz: ZoneInfo) -> dict:
    """Si hubo un aviso en el turno con parada, propone "parcial", motivo falla y las horas de parada."""
    ini, fin = ventana(fecha, turno, tz)
    avisos = list(s.scalars(select(EventoFalla).where(
        EventoFalla.id_activo == id_activo, EventoFalla.fecha_hora_falla >= ini, EventoFalla.fecha_hora_falla < fin,
        EventoFalla.estado != EstadoEvento.ANULADO)))
    if not avisos:
        return {}
    horas = 0.0
    for ev in avisos:
        if ev.parada_total is False:
            continue
        hasta = min(ev.fin_reparacion or ahora(), fin)
        horas += max(0.0, (hasta - max(ev.fecha_hora_falla, ini)).total_seconds() / 3600)
    horas = min(turno.duracion_h, round(horas * 2) / 2)
    motivo = s.scalar(select(MotivoParada.id).where(MotivoParada.codigo == "FALLA"))
    if horas <= 0:
        return {"hubo_aviso": True}
    estado = EstadoParte.NO_OPERO if horas >= turno.duracion_h else EstadoParte.PARCIAL
    return {"hubo_aviso": True, "estado": estado, "horas_no_operadas": horas, "id_motivo": motivo}


def lectura_anterior(s: Session, id_activo: int, fecha: date) -> float | None:
    """Última lectura de horómetro de la máquina antes de esa fecha (o del mismo día, en otro turno)."""
    return s.scalar(select(ParteTurno.lectura_horometro).where(
        ParteTurno.id_activo == id_activo, ParteTurno.lectura_horometro.is_not(None), ParteTurno.fecha <= fecha)
        .order_by(ParteTurno.fecha.desc(), ParteTurno.lectura_horometro.desc()).limit(1))


def registrar_parte(s: Session, id_usuario: int, id_activo: int, fecha: date, id_turno: int, estado: EstadoParte | str,
                    horas_no_operadas: float = 0.0, id_motivo: int | None = None, cantidad: float | None = None,
                    token: str | None = None, *, tz: ZoneInfo, hoy: date | None = None, rechazada: float | None = None,
                    lectura_horometro: float | None = None) -> ParteTurno:
    """Parte de turno. Con horómetro, si la diferencia con la lectura anterior coincide con las horas operadas
    (± `partes.tolerancia_horometro_h`), las horas quedan como medidas (nivel M); si no, quedan declaradas (D)."""
    u = _usuario(s, id_usuario)
    _verificar_maquina(s, u, id_activo, Accion.CARGAR_PARTE)
    turno = s.get(Turno, id_turno)
    if turno is None:
        raise ErrorRegistro("Turno no válido")
    if token and (previo := s.scalar(select(ParteTurno).where(ParteTurno.token_envio == token))):
        return previo  # doble toque o reenvío: ya estaba guardado
    hoy = hoy or ahora().astimezone(tz).date()
    if fecha > hoy:
        raise ErrorRegistro("La fecha del parte no puede ser futura")
    estado = EstadoParte(estado)
    dur = turno.duracion_h
    if estado == EstadoParte.TODO:
        horas_no_operadas, id_motivo = 0.0, None
    elif estado == EstadoParte.NO_OPERO:
        horas_no_operadas = dur
    if horas_no_operadas < 0 or horas_no_operadas > dur:
        raise ErrorRegistro(f"Las horas no operadas van de 0 a {dur:g}")
    if abs(horas_no_operadas * 2 - round(horas_no_operadas * 2)) > 1e-9:
        raise ErrorRegistro("Las horas no operadas van en pasos de media hora")
    if estado == EstadoParte.PARCIAL and not 0 < horas_no_operadas < dur:
        raise ErrorRegistro("En un parte parcial las horas no operadas tienen que ser más de 0 y menos que el turno")
    if horas_no_operadas > 0 and id_motivo is None:
        raise ErrorRegistro("Indicá el motivo de las horas no operadas")
    if id_motivo is not None and s.get(MotivoParada, id_motivo) is None:
        raise ErrorRegistro("Motivo no válido")
    if cantidad is not None and cantidad < 0:
        raise ErrorRegistro("La cantidad no puede ser negativa")
    if rechazada is not None and (rechazada < 0 or cantidad is None or rechazada > cantidad):
        raise ErrorRegistro("Las piezas rechazadas van de 0 a la cantidad procesada (cargá también la cantidad)")
    nivel = NivelHora.D
    if lectura_horometro is not None:
        anterior = lectura_anterior(s, id_activo, fecha)
        if lectura_horometro < 0 or (anterior is not None and lectura_horometro < anterior):
            raise ErrorRegistro(f"La lectura del horómetro no puede ser menor que la anterior ({anterior:g})")
        tolerancia = P.obtener(s, "partes.tolerancia_horometro_h")
        if anterior is not None and abs((lectura_horometro - anterior) - (dur - horas_no_operadas)) <= tolerancia:
            nivel = NivelHora.M
    existente = s.scalar(select(ParteTurno).where(ParteTurno.id_activo == id_activo, ParteTurno.fecha == fecha,
                                                  ParteTurno.id_turno == id_turno))
    if existente is not None and existente.origen != OrigenParte.ESTIMADO_SISTEMA:
        raise ErrorRegistro("Ya hay un parte de esa máquina en ese turno. Si está mal, pedile al jefe que lo corrija")
    valores = dict(horas_turno=dur, estado=estado, horas_no_operadas=horas_no_operadas,
                   horas_operadas=dur - horas_no_operadas, id_motivo=id_motivo, cantidad_procesada=cantidad,
                   cantidad_rechazada=rechazada, lectura_horometro=lectura_horometro,
                   nivel_hora=nivel, origen=OrigenParte.OPERARIO, id_usuario=u.id, token_envio=token)
    if existente is not None:  # reemplaza al estimado
        for k, v in valores.items():
            setattr(existente, k, v)
        s.flush()
        return existente
    parte = ParteTurno(id_activo=id_activo, fecha=fecha, id_turno=id_turno, **valores)
    s.add(parte)
    s.flush()
    return parte


# ---------------------------------------------------------------------------
# Aviso de falla
# ---------------------------------------------------------------------------


def avisos_recientes(s: Session, id_activo: int, momento: datetime, minutos: int | None = None) -> list[EventoFalla]:
    minutos = minutos if minutos is not None else int(P.obtener(s, "validacion.duplicado_aviso_min"))
    return list(s.scalars(select(EventoFalla).where(
        EventoFalla.id_activo == id_activo, EventoFalla.estado != EstadoEvento.ANULADO,
        EventoFalla.fecha_hora_falla.between(momento - timedelta(minutes=minutos), momento + timedelta(minutes=minutos)))))


def crear_aviso(s: Session, id_usuario: int, id_activo: int, id_sintoma: int, momento: datetime, paro: bool,
                foto: str | None = None, observaciones: str | None = None, token: str | None = None,
                origen: OrigenEvento = OrigenEvento.AVISO, id_tarjeta: int | None = None) -> EventoFalla:
    u = _usuario(s, id_usuario)
    _verificar_maquina(s, u, id_activo, Accion.CREAR_AVISO)
    if token and (previo := s.scalar(select(EventoFalla).where(EventoFalla.token_envio == token))):
        return previo
    if momento > ahora() + timedelta(minutes=5):
        raise ErrorRegistro("La hora de la falla no puede ser futura")
    sint = s.get(Catalogo, id_sintoma)
    if sint is None or sint.tipo != TipoCatalogo.SINTOMA:
        raise ErrorRegistro("Síntoma no válido")
    ev = EventoFalla(id_activo=id_activo, fecha_hora_falla=momento, id_sintoma=id_sintoma, parada_total=paro,
                     foto=foto, observaciones=(observaciones or "").strip() or None, estado=EstadoEvento.AVISADO,
                     origen=origen, id_usuario_alta=u.id, token_envio=token, id_tarjeta=id_tarjeta)
    s.add(ev)
    s.flush()
    return ev


# ---------------------------------------------------------------------------
# Tarjetas TPM (12.F)
# ---------------------------------------------------------------------------


def crear_tarjeta(s: Session, id_usuario: int, color: ColorTarjeta | str, id_activo: int, anomalia: str,
                  id_posicion: int | None = None, foto: str | None = None, observaciones: str | None = None,
                  token: str | None = None) -> TarjetaTPM:
    """Azul: la resuelve el operario. Roja: genera un aviso de falla para mantenimiento. Verde: mejora."""
    u = _usuario(s, id_usuario)
    _verificar_maquina(s, u, id_activo, Accion.CREAR_TARJETA)
    if token and (previa := s.scalar(select(TarjetaTPM).where(TarjetaTPM.token_envio == token))):
        return previa
    color = ColorTarjeta(color)
    opciones = {ColorTarjeta.AZUL: ANOMALIAS_AZUL, ColorTarjeta.ROJA: ANOMALIAS_ROJA, ColorTarjeta.VERDE: MEJORAS_VERDE}[color]
    if anomalia not in opciones:
        raise ErrorRegistro("Elegí una opción de la lista")
    if id_posicion is not None:
        pos = s.get(PosicionComponente, id_posicion)
        if pos is None or pos.id_activo != id_activo:
            raise ErrorRegistro("El componente no es de esa máquina")
    t = TarjetaTPM(color=color, id_activo=id_activo, id_posicion=id_posicion, anomalia=anomalia, foto=foto,
                   observaciones=(observaciones or "").strip() or None, id_usuario=u.id, token_envio=token)
    s.add(t)
    s.flush()
    if color == ColorTarjeta.ROJA:
        otro = s.scalar(select(Catalogo.id).where(Catalogo.tipo == TipoCatalogo.SINTOMA, Catalogo.codigo == "OTRO"))
        if otro is None:
            raise ErrorRegistro("Falta el síntoma 'OTRO' en el catálogo")
        ev = crear_aviso(s, id_usuario, id_activo, otro, ahora(), paro=False, foto=foto,
                         observaciones=f"Tarjeta roja: {anomalia}. {t.observaciones or ''}".strip(),
                         origen=OrigenEvento.TARJETA_ROJA, id_tarjeta=t.id)
        t.id_evento_generado = ev.id
        t.estado = EstadoTarjeta.DERIVADA
    return t


def cerrar_tarjeta(s: Session, id_usuario: int, id_tarjeta: int, resuelta: bool = True) -> None:
    u = _usuario(s, id_usuario)
    t = s.get(TarjetaTPM, id_tarjeta)
    if t is None:
        raise ErrorRegistro("Tarjeta no válida")
    _verificar_maquina(s, u, t.id_activo, Accion.CREAR_TARJETA)
    t.estado = EstadoTarjeta.RESUELTA if resuelta else EstadoTarjeta.DESCARTADA
