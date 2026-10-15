"""Modelos de datos (PLAN_TECNICO §5).

Jerarquía ISO 14224: línea → máquina (activo) → posición de componente → tipo de componente.
Las reglas que no pueden romperse están como restricciones de base (UNIQUE, CHECK, índice
parcial, triggers en `ddl_extra.py`) y también en los servicios.
"""

from __future__ import annotations

from datetime import date, datetime, time
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from circularis_rel.datos.db import FechaHoraUTC, ahora
from circularis_rel.datos.enums import (
    AccionAuditoria,
    AccionOT,
    Alcance,
    AparicionFalla,
    CapacidadFalla,
    Categoria6P,
    ClaseCriticidad,
    ClaseTriage,
    ColorTarjeta,
    Confianza,
    ConjuntoDatos,
    EfectoFalla,
    EstadoEtapa,
    EstadoEvento,
    EstadoOT,
    EstadoParte,
    EstadoPDCA,
    EstadoTarjeta,
    EtapaProceso,
    FuenteIntervalo,
    Interpretacion,
    MetodoCriticidad,
    MetodoIC,
    MetodoWeibull,
    Moneda,
    NivelHora,
    OrigenAnalisis,
    OrigenDato,
    OrigenEvento,
    OrigenParte,
    ReglaPlan,
    Rol,
    Semaforo,
    TipoAnalisis,
    TipoCatalogo,
    TipoFin,
    TipoOT,
    TipoParametro,
    TipoReparacion,
    UnidadProduccion,
    UsoRepuesto,
    VariableEdad,
)


def E(enum_cls: type[StrEnum], nombre: str) -> SAEnum:
    """Enum guardado como texto con CHECK (portable a PostgreSQL sin tipos nativos)."""
    return SAEnum(
        enum_cls,
        name=f"ck_{nombre}",
        native_enum=False,
        create_constraint=True,
        length=40,
        values_callable=lambda e: [m.value for m in e],
        validate_strings=True,
    )


class Base(DeclarativeBase):
    type_annotation_map = {datetime: FechaHoraUTC}


class ConFechas:
    creado_en: Mapped[datetime] = mapped_column(FechaHoraUTC, default=ahora, nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(
        FechaHoraUTC, default=ahora, onupdate=ahora, nullable=False
    )


# ---------------------------------------------------------------------------
# Estructura de planta
# ---------------------------------------------------------------------------


class Linea(ConFechas, Base):
    __tablename__ = "linea"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    activos: Mapped[list[Activo]] = relationship(back_populates="linea")


class Activo(ConFechas, Base):
    """Máquina. Incluye los campos de catastro de la UNIDAD 6 (MANT/RHM001) [12.B]."""

    __tablename__ = "activo"
    __table_args__ = (
        CheckConstraint("horas_promedio_dia IS NULL OR (horas_promedio_dia >= 0 AND horas_promedio_dia <= 24)", name="ck_activo_horas_dia"),
        CheckConstraint("autonomia_pulmon_h IS NULL OR autonomia_pulmon_h >= 0", name="ck_activo_pulmon"),
        CheckConstraint("factor_toneladas IS NULL OR factor_toneladas > 0", name="ck_activo_factor_t"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    id_linea: Mapped[int] = mapped_column(ForeignKey("linea.id"))
    etapa_proceso: Mapped[EtapaProceso] = mapped_column(E(EtapaProceso, "etapa_proceso"))
    orden_proceso: Mapped[int | None] = mapped_column(Integer)
    ubicacion: Mapped[str | None] = mapped_column(String(120))
    funcion: Mapped[str | None] = mapped_column(Text)
    horas_promedio_dia: Mapped[float | None] = mapped_column(Float)
    unidad_produccion: Mapped[UnidadProduccion] = mapped_column(
        E(UnidadProduccion, "unidad_produccion"), default=UnidadProduccion.NINGUNA
    )
    factor_toneladas: Mapped[float | None] = mapped_column(Float)
    criticidad_puntaje: Mapped[float | None] = mapped_column(Float)
    criticidad_nivel: Mapped[str | None] = mapped_column(String(20))  # p. ej. "Alta" del TP
    criticidad_clase: Mapped[ClaseCriticidad | None] = mapped_column(E(ClaseCriticidad, "clase_criticidad"))
    criticidad_metodo: Mapped[MetodoCriticidad | None] = mapped_column(E(MetodoCriticidad, "metodo_criticidad"))
    autonomia_pulmon_h: Mapped[float | None] = mapped_column(Float)
    ciclo_teorico_s: Mapped[float | None] = mapped_column(Float)
    # Catastro [12.B]
    numero_serie: Mapped[str | None] = mapped_column(String(80))
    fabricante: Mapped[str | None] = mapped_column(String(120))
    modelo: Mapped[str | None] = mapped_column(String(120))
    proveedor: Mapped[str | None] = mapped_column(String(120))
    fecha_instalacion: Mapped[date | None] = mapped_column(Date)
    ancho_mm: Mapped[float | None] = mapped_column(Float)
    alto_mm: Mapped[float | None] = mapped_column(Float)
    largo_mm: Mapped[float | None] = mapped_column(Float)
    peso_kg: Mapped[float | None] = mapped_column(Float)
    condiciones_almacenamiento: Mapped[str | None] = mapped_column(Text)
    caracteristicas_tecnicas: Mapped[str | None] = mapped_column(Text)
    ruta_documentos: Mapped[str | None] = mapped_column(String(400))
    # Revisión del jefe (criterio de salida de la fase 0, D-017)
    revisado_en: Mapped[datetime | None] = mapped_column(FechaHoraUTC)
    id_usuario_revision: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    linea: Mapped[Linea] = relationship(back_populates="activos")
    posiciones: Mapped[list[PosicionComponente]] = relationship(back_populates="activo_rel")


class TipoComponente(ConFechas, Base):
    __tablename__ = "tipo_componente"
    __table_args__ = (
        CheckConstraint("beta_ref IS NULL OR beta_ref > 0", name="ck_tc_beta_ref"),
        CheckConstraint("eta_ref IS NULL OR eta_ref > 0", name="ck_tc_eta_ref"),
        CheckConstraint("beta_ref IS NULL OR fuente_ref IS NOT NULL", name="ck_tc_fuente_ref"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    variable_edad: Mapped[VariableEdad] = mapped_column(E(VariableEdad, "variable_edad"), default=VariableEdad.HORAS)
    hh_preventiva: Mapped[float | None] = mapped_column(Float)
    hh_correctiva: Mapped[float | None] = mapped_column(Float)
    beta_ref: Mapped[float | None] = mapped_column(Float)
    eta_ref: Mapped[float | None] = mapped_column(Float)
    fuente_ref: Mapped[str | None] = mapped_column(Text)
    uso: Mapped[UsoRepuesto | None] = mapped_column(E(UsoRepuesto, "uso_tc"))
    intervalo_fabricante: Mapped[float | None] = mapped_column(Float)
    unidad_intervalo_fabricante: Mapped[VariableEdad | None] = mapped_column(E(VariableEdad, "unidad_int_fab"))
    falla_oculta: Mapped[bool] = mapped_column(Boolean, default=False)
    funcion_seguridad: Mapped[bool] = mapped_column(Boolean, default=False)
    intervalo_pf: Mapped[float | None] = mapped_column(Float)
    origen: Mapped[OrigenDato] = mapped_column(E(OrigenDato, "origen_tc"), default=OrigenDato.JEFE)


class PosicionComponente(ConFechas, Base):
    __tablename__ = "posicion_componente"
    __table_args__ = (
        UniqueConstraint("id_activo", "codigo", name="uq_posicion_activo_codigo"),
        CheckConstraint("cantidad >= 1", name="ck_posicion_cantidad"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    id_activo: Mapped[int] = mapped_column(ForeignKey("activo.id"))
    id_tipo_componente: Mapped[int] = mapped_column(ForeignKey("tipo_componente.id"))
    codigo: Mapped[str] = mapped_column(String(60))
    ubicacion: Mapped[str | None] = mapped_column(String(120))
    cantidad: Mapped[int] = mapped_column(Integer, default=1)
    critica: Mapped[bool] = mapped_column(Boolean, default=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)

    activo_rel: Mapped[Activo] = relationship(back_populates="posiciones")
    tipo: Mapped[TipoComponente] = relationship()


class Catalogo(ConFechas, Base):
    """Síntomas, modos y causas: listas cerradas."""

    __tablename__ = "catalogo"
    __table_args__ = (UniqueConstraint("tipo", "codigo", name="uq_catalogo_tipo_codigo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[TipoCatalogo] = mapped_column(E(TipoCatalogo, "tipo_catalogo"))
    codigo: Mapped[str] = mapped_column(String(60))
    descripcion: Mapped[str] = mapped_column(String(200))
    icono: Mapped[str | None] = mapped_column(String(20))
    origen: Mapped[OrigenDato] = mapped_column(E(OrigenDato, "origen_cat"), default=OrigenDato.JEFE)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class CatalogoAplica(Base):
    """A qué tipos de componente aplica un modo o causa.

    Regla (D-019): un MODO debe tener al menos un tipo; una CAUSA o SINTOMA sin filas aplica a todos.
    """

    __tablename__ = "catalogo_aplica"
    id_catalogo: Mapped[int] = mapped_column(ForeignKey("catalogo.id", ondelete="CASCADE"), primary_key=True)
    id_tipo_componente: Mapped[int] = mapped_column(ForeignKey("tipo_componente.id", ondelete="CASCADE"), primary_key=True)


class MotivoParada(ConFechas, Base):
    __tablename__ = "motivo_parada"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40), unique=True)
    descripcion: Mapped[str] = mapped_column(String(120))
    cuenta_como_requerida: Mapped[bool] = mapped_column(Boolean, default=True)
    es_falla: Mapped[bool] = mapped_column(Boolean, default=False)
    es_setup: Mapped[bool] = mapped_column(Boolean, default=False)
    categoria_6p: Mapped[Categoria6P | None] = mapped_column(E(Categoria6P, "categoria_6p"))
    orden: Mapped[int] = mapped_column(Integer, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Turno(ConFechas, Base):
    __tablename__ = "turno"
    __table_args__ = (CheckConstraint("duracion_h > 0 AND duracion_h <= 24", name="ck_turno_duracion"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(60))
    hora_inicio: Mapped[time] = mapped_column(Time)
    hora_fin: Mapped[time] = mapped_column(Time)
    duracion_h: Mapped[float] = mapped_column(Float)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class ActivoTurno(Base):
    """Turnos laborables de cada máquina; `dias` = días de la semana ISO separados por coma (1=lunes)."""

    __tablename__ = "activo_turno"
    id_activo: Mapped[int] = mapped_column(ForeignKey("activo.id", ondelete="CASCADE"), primary_key=True)
    id_turno: Mapped[int] = mapped_column(ForeignKey("turno.id", ondelete="CASCADE"), primary_key=True)
    dias: Mapped[str] = mapped_column(String(20), default="1,2,3,4,5")


class Feriado(Base):
    __tablename__ = "feriado"
    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, unique=True)
    descripcion: Mapped[str] = mapped_column(String(120))


class EquivalenciaComponente(Base):
    """Posiciones que el jefe declara equivalentes para agrupar como flota (PLAN §7.6)."""

    __tablename__ = "equivalencia_componente"
    id: Mapped[int] = mapped_column(primary_key=True)
    grupo: Mapped[str] = mapped_column(String(60))
    id_posicion: Mapped[int] = mapped_column(ForeignKey("posicion_componente.id"), unique=True)


# ---------------------------------------------------------------------------
# Usuarios
# ---------------------------------------------------------------------------


class Usuario(ConFechas, Base):
    __tablename__ = "usuario"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario: Mapped[str] = mapped_column(String(40), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    rol: Mapped[Rol] = mapped_column(E(Rol, "rol"))
    hash_password: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(200))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class UsuarioActivo(Base):
    """Máquinas asignadas a un operario."""

    __tablename__ = "usuario_activo"
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"), primary_key=True)
    id_activo: Mapped[int] = mapped_column(ForeignKey("activo.id", ondelete="CASCADE"), primary_key=True)


# ---------------------------------------------------------------------------
# Captura
# ---------------------------------------------------------------------------


class ParteTurno(ConFechas, Base):
    __tablename__ = "parte_turno"
    __table_args__ = (
        UniqueConstraint("id_activo", "fecha", "id_turno", name="uq_parte_activo_fecha_turno"),
        CheckConstraint("horas_turno > 0 AND horas_turno <= 24", name="ck_parte_horas_turno"),
        CheckConstraint("horas_no_operadas >= 0 AND horas_no_operadas <= horas_turno", name="ck_parte_horas_no_op"),
        CheckConstraint("abs(horas_no_operadas * 2 - round(horas_no_operadas * 2)) < 1e-9", name="ck_parte_paso_media_hora"),
        CheckConstraint("abs(horas_operadas - (horas_turno - horas_no_operadas)) < 1e-9", name="ck_parte_horas_operadas"),
        CheckConstraint("estado <> 'TODO' OR horas_no_operadas = 0", name="ck_parte_todo"),
        CheckConstraint("estado <> 'NO_OPERO' OR horas_no_operadas = horas_turno", name="ck_parte_no_opero"),
        CheckConstraint(
            "estado <> 'PARCIAL' OR (horas_no_operadas > 0 AND horas_no_operadas < horas_turno)",
            name="ck_parte_parcial",
        ),
        CheckConstraint("horas_no_operadas = 0 OR id_motivo IS NOT NULL", name="ck_parte_motivo"),
        CheckConstraint("cantidad_procesada IS NULL OR cantidad_procesada >= 0", name="ck_parte_cantidad"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    id_activo: Mapped[int] = mapped_column(ForeignKey("activo.id"))
    fecha: Mapped[date] = mapped_column(Date)
    id_turno: Mapped[int] = mapped_column(ForeignKey("turno.id"))
    horas_turno: Mapped[float] = mapped_column(Float)
    estado: Mapped[EstadoParte] = mapped_column(E(EstadoParte, "estado_parte"))
    horas_no_operadas: Mapped[float] = mapped_column(Float, default=0)
    horas_operadas: Mapped[float] = mapped_column(Float)
    id_motivo: Mapped[int | None] = mapped_column(ForeignKey("motivo_parada.id"))
    cantidad_procesada: Mapped[float | None] = mapped_column(Float)
    nivel_hora: Mapped[NivelHora] = mapped_column(E(NivelHora, "nivel_hora_parte"), default=NivelHora.D)
    origen: Mapped[OrigenParte] = mapped_column(E(OrigenParte, "origen_parte"), default=OrigenParte.OPERARIO)
    id_usuario: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    token_envio: Mapped[str | None] = mapped_column(String(64), unique=True)


class EventoFalla(ConFechas, Base):
    __tablename__ = "evento_falla"
    __table_args__ = (
        CheckConstraint("inicio_reparacion IS NULL OR inicio_reparacion >= fecha_hora_falla", name="ck_ev_inicio"),
        CheckConstraint("fin_reparacion IS NULL OR inicio_reparacion IS NULL OR fin_reparacion > inicio_reparacion", name="ck_ev_fin"),
        CheckConstraint("tiempo_espera_h IS NULL OR tiempo_espera_h >= 0", name="ck_ev_espera"),
        CheckConstraint("tiempo_reparacion_h IS NULL OR tiempo_reparacion_h >= 0", name="ck_ev_reparacion"),
        CheckConstraint("horas_parada IS NULL OR horas_parada >= 0", name="ck_ev_parada"),
        CheckConstraint(
            "estado NOT IN ('CERRADO','VALIDADO') OR (id_posicion IS NOT NULL AND id_modo IS NOT NULL "
            "AND id_causa IS NOT NULL AND inicio_reparacion IS NOT NULL AND fin_reparacion IS NOT NULL)",
            name="ck_ev_cierre_completo",
        ),
        Index("ix_evento_activo_fecha", "id_activo", "fecha_hora_falla"),
        Index("ix_evento_estado", "estado"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    id_activo: Mapped[int] = mapped_column(ForeignKey("activo.id"))
    id_posicion: Mapped[int | None] = mapped_column(ForeignKey("posicion_componente.id"))
    fecha_hora_falla: Mapped[datetime] = mapped_column(FechaHoraUTC)
    id_sintoma: Mapped[int | None] = mapped_column(ForeignKey("catalogo.id"))
    id_modo: Mapped[int | None] = mapped_column(ForeignKey("catalogo.id"))
    id_causa: Mapped[int | None] = mapped_column(ForeignKey("catalogo.id"))
    inicio_reparacion: Mapped[datetime | None] = mapped_column(FechaHoraUTC)
    fin_reparacion: Mapped[datetime | None] = mapped_column(FechaHoraUTC)
    tiempo_espera_h: Mapped[float | None] = mapped_column(Float)
    tiempo_reparacion_h: Mapped[float | None] = mapped_column(Float)
    parada_total: Mapped[bool | None] = mapped_column(Boolean)
    horas_parada: Mapped[float | None] = mapped_column(Float)
    efecto: Mapped[EfectoFalla | None] = mapped_column(E(EfectoFalla, "efecto_falla"))
    capacidad: Mapped[CapacidadFalla | None] = mapped_column(E(CapacidadFalla, "capacidad_falla"))
    aparicion: Mapped[AparicionFalla | None] = mapped_column(E(AparicionFalla, "aparicion_falla"))
    estado: Mapped[EstadoEvento] = mapped_column(E(EstadoEvento, "estado_evento"), default=EstadoEvento.AVISADO)
    origen: Mapped[OrigenEvento] = mapped_column(E(OrigenEvento, "origen_evento"), default=OrigenEvento.AVISO)
    foto: Mapped[str | None] = mapped_column(String(400))
    observaciones: Mapped[str | None] = mapped_column(Text)
    id_usuario_alta: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    id_usuario_cierre: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    id_usuario_validacion: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    validado_en: Mapped[datetime | None] = mapped_column(FechaHoraUTC)
    id_tarjeta: Mapped[int | None] = mapped_column(ForeignKey("tarjeta_tpm.id"))
    token_envio: Mapped[str | None] = mapped_column(String(64), unique=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    __mapper_args__ = {"version_id_col": version}


class OrdenTrabajo(ConFechas, Base):
    __tablename__ = "orden_trabajo"
    __table_args__ = (
        CheckConstraint("fin_real IS NULL OR inicio_real IS NULL OR fin_real >= inicio_real", name="ck_ot_fechas"),
        CheckConstraint("hh_propias IS NULL OR hh_propias >= 0", name="ck_ot_hh"),
        CheckConstraint("hh_externas IS NULL OR hh_externas >= 0", name="ck_ot_hh_ext"),
        CheckConstraint("tipo <> 'CORRECTIVA' OR id_evento IS NOT NULL", name="ck_ot_correctiva_evento"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(30), unique=True)
    tipo: Mapped[TipoOT] = mapped_column(E(TipoOT, "tipo_ot"))
    id_activo: Mapped[int] = mapped_column(ForeignKey("activo.id"))
    id_posicion: Mapped[int | None] = mapped_column(ForeignKey("posicion_componente.id"))
    id_evento: Mapped[int | None] = mapped_column(ForeignKey("evento_falla.id"), unique=True)
    id_plan: Mapped[int | None] = mapped_column(ForeignKey("plan_preventivo.id"))
    fecha_programada: Mapped[date | None] = mapped_column(Date)
    inicio_real: Mapped[datetime | None] = mapped_column(FechaHoraUTC)
    fin_real: Mapped[datetime | None] = mapped_column(FechaHoraUTC)
    estado: Mapped[EstadoOT] = mapped_column(E(EstadoOT, "estado_ot"), default=EstadoOT.SOLICITADA)
    responsable: Mapped[str | None] = mapped_column(String(120))
    hh_propias: Mapped[float | None] = mapped_column(Float)
    hh_externas: Mapped[float | None] = mapped_column(Float)
    costo_externo_ars: Mapped[float | None] = mapped_column(Float)
    prioridad: Mapped[int | None] = mapped_column(Integer)
    accion: Mapped[AccionOT | None] = mapped_column(E(AccionOT, "accion_ot"))
    herramientas: Mapped[str | None] = mapped_column(Text)
    observaciones: Mapped[str | None] = mapped_column(Text)


class OTTarea(Base):
    """Tareas numeradas de una OT (formato MANT/MPV001)."""

    __tablename__ = "ot_tarea"
    __table_args__ = (UniqueConstraint("id_ot", "numero", name="uq_ot_tarea"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    id_ot: Mapped[int] = mapped_column(ForeignKey("orden_trabajo.id", ondelete="CASCADE"))
    numero: Mapped[int] = mapped_column(Integer)
    descripcion: Mapped[str] = mapped_column(Text)
    observaciones: Mapped[str | None] = mapped_column(Text)
    tiempo_h: Mapped[float | None] = mapped_column(Float)


class VidaComponente(ConFechas, Base):
    """Período entre la instalación de un componente en una posición y su falla o retiro."""

    __tablename__ = "vida_componente"
    __table_args__ = (
        CheckConstraint(
            "(tipo_fin = 'EN_SERVICIO' AND fecha_fin IS NULL) OR (tipo_fin <> 'EN_SERVICIO' AND fecha_fin IS NOT NULL)",
            name="ck_vida_fin",
        ),
        CheckConstraint("fecha_fin IS NULL OR fecha_fin >= fecha_instalacion", name="ck_vida_fechas"),
        CheckConstraint("tipo_fin <> 'FALLA' OR id_modo_falla IS NOT NULL", name="ck_vida_modo"),
        CheckConstraint("edad_horas IS NULL OR edad_horas >= 0", name="ck_vida_edad_h"),
        CheckConstraint("edad_toneladas IS NULL OR edad_toneladas >= 0", name="ck_vida_edad_t"),
        # A lo sumo una vida en servicio por posición.
        Index(
            "uq_vida_en_servicio_por_posicion",
            "id_posicion",
            unique=True,
            sqlite_where=text("tipo_fin = 'EN_SERVICIO'"),
            postgresql_where=text("tipo_fin = 'EN_SERVICIO'"),
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    id_posicion: Mapped[int] = mapped_column(ForeignKey("posicion_componente.id"))
    fecha_instalacion: Mapped[datetime] = mapped_column(FechaHoraUTC)
    fecha_fin: Mapped[datetime | None] = mapped_column(FechaHoraUTC)
    tipo_fin: Mapped[TipoFin] = mapped_column(E(TipoFin, "tipo_fin"), default=TipoFin.EN_SERVICIO)
    id_modo_falla: Mapped[int | None] = mapped_column(ForeignKey("catalogo.id"))
    edad_horas: Mapped[float | None] = mapped_column(Float)
    edad_toneladas: Mapped[float | None] = mapped_column(Float)
    nivel_hora: Mapped[NivelHora] = mapped_column(E(NivelHora, "nivel_hora_vida"), default=NivelHora.D)
    edad_conocida: Mapped[bool] = mapped_column(Boolean, default=True)
    tipo_reparacion: Mapped[TipoReparacion] = mapped_column(E(TipoReparacion, "tipo_reparacion"), default=TipoReparacion.REEMPLAZO)
    id_ot_apertura: Mapped[int | None] = mapped_column(ForeignKey("orden_trabajo.id"))
    id_ot_cierre: Mapped[int | None] = mapped_column(ForeignKey("orden_trabajo.id"))
    id_evento_cierre: Mapped[int | None] = mapped_column(ForeignKey("evento_falla.id"), unique=True)
    validado: Mapped[bool] = mapped_column(Boolean, default=False)


class Repuesto(ConFechas, Base):
    __tablename__ = "repuesto"
    __table_args__ = (
        CheckConstraint("stock_actual IS NULL OR stock_actual >= 0", name="ck_rep_stock"),
        CheckConstraint("stock_minimo_manual IS NULL OR stock_minimo_manual >= 0", name="ck_rep_stock_min"),
        CheckConstraint("lead_time_dias IS NULL OR lead_time_dias >= 0", name="ck_rep_lead"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(60), unique=True)
    descripcion: Mapped[str] = mapped_column(String(200))
    id_tipo_componente: Mapped[int | None] = mapped_column(ForeignKey("tipo_componente.id"))
    uso: Mapped[UsoRepuesto | None] = mapped_column(E(UsoRepuesto, "uso_rep"))
    stock_actual: Mapped[float | None] = mapped_column(Float)
    stock_minimo_manual: Mapped[float | None] = mapped_column(Float)
    ubicacion: Mapped[str | None] = mapped_column(String(120))
    codigo_proveedor: Mapped[str | None] = mapped_column(String(60))
    proveedor: Mapped[str | None] = mapped_column(String(120))
    lead_time_dias: Mapped[float | None] = mapped_column(Float)
    familia_compra: Mapped[str | None] = mapped_column(String(60))
    intervalo_fabricante: Mapped[float | None] = mapped_column(Float)


class PrecioRepuesto(Base):
    __tablename__ = "precio_repuesto"
    __table_args__ = (
        UniqueConstraint("id_repuesto", "fecha", name="uq_precio_rep_fecha"),
        CheckConstraint("precio >= 0", name="ck_precio_pos"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    id_repuesto: Mapped[int] = mapped_column(ForeignKey("repuesto.id", ondelete="CASCADE"))
    fecha: Mapped[date] = mapped_column(Date)
    precio: Mapped[float] = mapped_column(Float)
    moneda: Mapped[Moneda] = mapped_column(E(Moneda, "moneda_precio"), default=Moneda.ARS)


class RepuestoActivo(Base):
    """Plantilla de repuestos por máquina (MANT/RM001)."""

    __tablename__ = "repuesto_activo"
    id_repuesto: Mapped[int] = mapped_column(ForeignKey("repuesto.id", ondelete="CASCADE"), primary_key=True)
    id_activo: Mapped[int] = mapped_column(ForeignKey("activo.id", ondelete="CASCADE"), primary_key=True)
    cantidad_instalada: Mapped[float | None] = mapped_column(Float)


class ConsumoRepuesto(ConFechas, Base):
    __tablename__ = "consumo_repuesto"
    __table_args__ = (CheckConstraint("cantidad > 0", name="ck_consumo_cant"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    id_ot: Mapped[int] = mapped_column(ForeignKey("orden_trabajo.id"))
    id_repuesto: Mapped[int] = mapped_column(ForeignKey("repuesto.id"))
    cantidad: Mapped[float] = mapped_column(Float)
    precio_unitario: Mapped[float | None] = mapped_column(Float)
    moneda: Mapped[Moneda | None] = mapped_column(E(Moneda, "moneda_consumo"))
    fecha: Mapped[date] = mapped_column(Date)


class TarjetaTPM(ConFechas, Base):
    """Tarjetas azul/roja/verde del mantenimiento autónomo (UNIDAD 4, diap. 14) [12.F]."""

    __tablename__ = "tarjeta_tpm"
    id: Mapped[int] = mapped_column(primary_key=True)
    color: Mapped[ColorTarjeta] = mapped_column(E(ColorTarjeta, "color_tarjeta"))
    id_activo: Mapped[int] = mapped_column(ForeignKey("activo.id"))
    id_posicion: Mapped[int | None] = mapped_column(ForeignKey("posicion_componente.id"))
    anomalia: Mapped[str | None] = mapped_column(String(120))
    observaciones: Mapped[str | None] = mapped_column(Text)
    foto: Mapped[str | None] = mapped_column(String(400))
    estado: Mapped[EstadoTarjeta] = mapped_column(E(EstadoTarjeta, "estado_tarjeta"), default=EstadoTarjeta.ABIERTA)
    id_evento_generado: Mapped[int | None] = mapped_column(ForeignKey("evento_falla.id", use_alter=True, name="fk_tarjeta_evento"))
    id_usuario: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    token_envio: Mapped[str | None] = mapped_column(String(64), unique=True)


class Adjunto(ConFechas, Base):
    __tablename__ = "adjunto"
    id: Mapped[int] = mapped_column(primary_key=True)
    entidad: Mapped[str] = mapped_column(String(40))
    id_entidad: Mapped[int] = mapped_column(Integer)
    ruta: Mapped[str] = mapped_column(String(400))
    tipo: Mapped[str | None] = mapped_column(String(40))


# ---------------------------------------------------------------------------
# Confiabilidad, análisis y plan
# ---------------------------------------------------------------------------


class ResultadoWeibull(ConFechas, Base):
    __tablename__ = "resultado_weibull"
    __table_args__ = (
        Index("ix_rw_par", "id_tipo_componente", "id_modo", "alcance", "id_activo", "vigente"),
        CheckConstraint("n_fallas >= 0 AND n_suspensiones >= 0 AND n_intervalo >= 0", name="ck_rw_n"),
        CheckConstraint("nivel_ic IS NULL OR (nivel_ic > 0 AND nivel_ic < 1)", name="ck_rw_nivel"),
        CheckConstraint("NOT forzado OR justificacion IS NOT NULL", name="ck_rw_forzado"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    id_tipo_componente: Mapped[int] = mapped_column(ForeignKey("tipo_componente.id"))
    id_modo: Mapped[int] = mapped_column(ForeignKey("catalogo.id"))
    alcance: Mapped[Alcance] = mapped_column(E(Alcance, "alcance"))
    id_activo: Mapped[int | None] = mapped_column(ForeignKey("activo.id"))
    ids_activos_flota: Mapped[list | None] = mapped_column(JSON)
    conjunto_datos: Mapped[ConjuntoDatos] = mapped_column(E(ConjuntoDatos, "conjunto_datos"), default=ConjuntoDatos.NUEVOS)
    fecha_calculo: Mapped[datetime] = mapped_column(FechaHoraUTC, default=ahora)
    n_fallas: Mapped[int] = mapped_column(Integer)
    n_suspensiones: Mapped[int] = mapped_column(Integer)
    n_intervalo: Mapped[int] = mapped_column(Integer, default=0)
    metodo: Mapped[MetodoWeibull | None] = mapped_column(E(MetodoWeibull, "metodo_weibull"))
    forzado: Mapped[bool] = mapped_column(Boolean, default=False)
    justificacion: Mapped[str | None] = mapped_column(Text)
    beta: Mapped[float | None] = mapped_column(Float)
    eta: Mapped[float | None] = mapped_column(Float)
    gamma: Mapped[float] = mapped_column(Float, default=0.0)
    beta_inf: Mapped[float | None] = mapped_column(Float)
    beta_sup: Mapped[float | None] = mapped_column(Float)
    eta_inf: Mapped[float | None] = mapped_column(Float)
    eta_sup: Mapped[float | None] = mapped_column(Float)
    metodo_ic: Mapped[MetodoIC] = mapped_column(E(MetodoIC, "metodo_ic"), default=MetodoIC.NINGUNO)
    nivel_ic: Mapped[float | None] = mapped_column(Float)
    r2: Mapped[float | None] = mapped_column(Float)
    r2_critico: Mapped[float | None] = mapped_column(Float)
    ad: Mapped[float | None] = mapped_column(Float)
    comparacion: Mapped[dict | None] = mapped_column(JSON)
    confianza: Mapped[Confianza] = mapped_column(E(Confianza, "confianza_rw"))
    interpretacion: Mapped[Interpretacion | None] = mapped_column(E(Interpretacion, "interpretacion"))
    version_motor: Mapped[str] = mapped_column(String(20))
    hash_datos: Mapped[str] = mapped_column(String(64))
    vigente: Mapped[bool] = mapped_column(Boolean, default=False)


class VidaHistorica(ConFechas, Base):
    """Histórico depurado por triage A/B/C. Separado de las vidas nuevas (PLAN §11)."""

    __tablename__ = "vida_historica"
    __table_args__ = (
        CheckConstraint("fecha_fin_inf IS NULL OR fecha_fin_sup IS NULL OR fecha_fin_sup >= fecha_fin_inf", name="ck_vh_rango_fecha"),
        CheckConstraint("edad_inf_h IS NULL OR edad_sup_h IS NULL OR edad_sup_h >= edad_inf_h", name="ck_vh_rango_edad"),
        CheckConstraint(
            "clase_triage <> 'A' OR (respaldo IS NOT NULL AND fecha_fin IS NOT NULL AND (tipo_fin <> 'FALLA' OR id_modo_falla IS NOT NULL))",
            name="ck_vh_clase_a",
        ),
        CheckConstraint(
            "clase_triage <> 'B' OR ((fecha_fin_inf IS NOT NULL AND fecha_fin_sup IS NOT NULL) OR (edad_inf_h IS NOT NULL AND edad_sup_h IS NOT NULL))",
            name="ck_vh_clase_b",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    id_activo: Mapped[int] = mapped_column(ForeignKey("activo.id"))
    id_posicion: Mapped[int | None] = mapped_column(ForeignKey("posicion_componente.id"))
    fecha_instalacion: Mapped[date | None] = mapped_column(Date)
    fecha_fin: Mapped[date | None] = mapped_column(Date)
    fecha_fin_inf: Mapped[date | None] = mapped_column(Date)
    fecha_fin_sup: Mapped[date | None] = mapped_column(Date)
    edad_horas: Mapped[float | None] = mapped_column(Float)
    edad_inf_h: Mapped[float | None] = mapped_column(Float)
    edad_sup_h: Mapped[float | None] = mapped_column(Float)
    tipo_fin: Mapped[TipoFin] = mapped_column(E(TipoFin, "tipo_fin_hist"))
    id_modo_falla: Mapped[int | None] = mapped_column(ForeignKey("catalogo.id"))
    descripcion_original: Mapped[str | None] = mapped_column(Text)
    clase_triage: Mapped[ClaseTriage] = mapped_column(E(ClaseTriage, "clase_triage"))
    motivo_clase: Mapped[str | None] = mapped_column(Text)
    fuente: Mapped[str] = mapped_column(String(120))
    respaldo: Mapped[str | None] = mapped_column(String(400))
    observaciones: Mapped[str | None] = mapped_column(Text)
    nivel_hora: Mapped[NivelHora] = mapped_column(E(NivelHora, "nivel_hora_hist"), default=NivelHora.E)
    id_importacion: Mapped[int | None] = mapped_column(ForeignKey("importacion.id"))
    clave_importacion: Mapped[str | None] = mapped_column(String(64), unique=True)


class EstadoComponente(Base):
    __tablename__ = "estado_componente"
    __table_args__ = (UniqueConstraint("id_posicion", "fecha", name="uq_estado_pos_fecha"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    id_posicion: Mapped[int] = mapped_column(ForeignKey("posicion_componente.id"))
    fecha: Mapped[date] = mapped_column(Date)
    edad: Mapped[float | None] = mapped_column(Float)
    delta: Mapped[float | None] = mapped_column(Float)
    p_falla_delta: Mapped[float | None] = mapped_column(Float)
    p_falla_delta_inf: Mapped[float | None] = mapped_column(Float)
    p_falla_delta_sup: Mapped[float | None] = mapped_column(Float)
    vida_rem_mediana: Mapped[float | None] = mapped_column(Float)
    vida_rem_90: Mapped[float | None] = mapped_column(Float)
    intervalo_vigente: Mapped[float | None] = mapped_column(Float)
    fuente_intervalo: Mapped[FuenteIntervalo] = mapped_column(E(FuenteIntervalo, "fuente_intervalo"), default=FuenteIntervalo.NINGUNO)
    semaforo: Mapped[Semaforo] = mapped_column(E(Semaforo, "semaforo"))
    confianza: Mapped[Confianza] = mapped_column(E(Confianza, "confianza_ec"))
    motivos: Mapped[list | None] = mapped_column(JSON)
    id_resultado_weibull: Mapped[int | None] = mapped_column(ForeignKey("resultado_weibull.id"))


class ResultadoSistema(ConFechas, Base):
    """Crow-AMSAA y Laplace por máquina (fase 4)."""

    __tablename__ = "resultado_sistema"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_activo: Mapped[int] = mapped_column(ForeignKey("activo.id"))
    fecha_calculo: Mapped[datetime] = mapped_column(FechaHoraUTC, default=ahora)
    periodo_desde: Mapped[date] = mapped_column(Date)
    periodo_hasta: Mapped[date] = mapped_column(Date)
    n_fallas: Mapped[int] = mapped_column(Integer)
    beta: Mapped[float | None] = mapped_column(Float)
    lambda_: Mapped[float | None] = mapped_column("lambda", Float)
    beta_inf: Mapped[float | None] = mapped_column(Float)
    beta_sup: Mapped[float | None] = mapped_column(Float)
    laplace_u: Mapped[float | None] = mapped_column(Float)
    laplace_p: Mapped[float | None] = mapped_column(Float)
    version_motor: Mapped[str] = mapped_column(String(20))


class AmfeItem(ConFechas, Base):
    __tablename__ = "amfe_item"
    __table_args__ = (
        CheckConstraint("g BETWEEN 1 AND 10 AND o BETWEEN 1 AND 10 AND d BETWEEN 1 AND 10", name="ck_amfe_escalas"),
        CheckConstraint("o_calculada IS NULL OR o_calculada BETWEEN 1 AND 10", name="ck_amfe_o_calc"),
        CheckConstraint("ap IS NULL OR ap IN ('H','M','L')", name="ck_amfe_ap"),
        UniqueConstraint("id_activo", "id_tipo_componente", "id_modo", name="uq_amfe_item"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    id_activo: Mapped[int | None] = mapped_column(ForeignKey("activo.id"))
    id_tipo_componente: Mapped[int] = mapped_column(ForeignKey("tipo_componente.id"))
    id_modo: Mapped[int] = mapped_column(ForeignKey("catalogo.id"))
    requerimiento: Mapped[str | None] = mapped_column(String(200))
    efecto: Mapped[str | None] = mapped_column(Text)
    causa: Mapped[str | None] = mapped_column(Text)
    control_prevencion: Mapped[str | None] = mapped_column(Text)
    control_deteccion: Mapped[str | None] = mapped_column(Text)
    g: Mapped[int] = mapped_column(Integer)
    o: Mapped[int] = mapped_column(Integer)
    d: Mapped[int] = mapped_column(Integer)
    o_calculada: Mapped[int | None] = mapped_column(Integer)
    ap: Mapped[str | None] = mapped_column(String(1))
    acciones: Mapped[str | None] = mapped_column(Text)
    responsable: Mapped[str | None] = mapped_column(String(120))
    fecha: Mapped[date | None] = mapped_column(Date)
    origen: Mapped[OrigenDato] = mapped_column(E(OrigenDato, "origen_amfe"), default=OrigenDato.JEFE)

    @property
    def npr(self) -> int:
        return self.g * self.o * self.d


class CriticidadEvaluacion(ConFechas, Base):
    __tablename__ = "criticidad_evaluacion"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_activo: Mapped[int] = mapped_column(ForeignKey("activo.id"))
    metodo: Mapped[MetodoCriticidad] = mapped_column(E(MetodoCriticidad, "metodo_crit_eval"))
    criterios: Mapped[dict] = mapped_column(JSON)
    puntaje: Mapped[float] = mapped_column(Float)
    nivel: Mapped[str | None] = mapped_column(String(20))
    clase: Mapped[ClaseCriticidad] = mapped_column(E(ClaseCriticidad, "clase_crit_eval"))
    fecha: Mapped[date] = mapped_column(Date)
    id_usuario: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    vigente: Mapped[bool] = mapped_column(Boolean, default=True)


class AnalisisProblema(ConFechas, Base):
    __tablename__ = "analisis_problema"
    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[TipoAnalisis] = mapped_column(E(TipoAnalisis, "tipo_analisis"))
    id_evento: Mapped[int | None] = mapped_column(ForeignKey("evento_falla.id"))
    id_activo: Mapped[int | None] = mapped_column(ForeignKey("activo.id"))
    id_tipo_componente: Mapped[int | None] = mapped_column(ForeignKey("tipo_componente.id"))
    id_modo: Mapped[int | None] = mapped_column(ForeignKey("catalogo.id"))
    contenido: Mapped[dict] = mapped_column(JSON, default=dict)
    causa_raiz: Mapped[str | None] = mapped_column(Text)
    accion_correctiva: Mapped[str | None] = mapped_column(Text)
    responsable: Mapped[str | None] = mapped_column(String(120))
    fecha_compromiso: Mapped[date | None] = mapped_column(Date)
    estado_pdca: Mapped[EstadoPDCA] = mapped_column(E(EstadoPDCA, "estado_pdca"), default=EstadoPDCA.PLANIFICAR)
    id_ot_generada: Mapped[int | None] = mapped_column(ForeignKey("orden_trabajo.id"))
    origen: Mapped[OrigenAnalisis] = mapped_column(E(OrigenAnalisis, "origen_analisis"), default=OrigenAnalisis.MANUAL)


class PlanPreventivo(ConFechas, Base):
    __tablename__ = "plan_preventivo"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_posicion: Mapped[int] = mapped_column(ForeignKey("posicion_componente.id"))
    regla: Mapped[ReglaPlan] = mapped_column(E(ReglaPlan, "regla_plan"))
    intervalo: Mapped[float | None] = mapped_column(Float)
    unidad: Mapped[VariableEdad] = mapped_column(E(VariableEdad, "unidad_plan"), default=VariableEdad.HORAS)
    t_optimo_calculado: Mapped[float | None] = mapped_column(Float)
    vigente_desde: Mapped[date] = mapped_column(Date)
    vigente: Mapped[bool] = mapped_column(Boolean, default=True)
    id_resultado_weibull: Mapped[int | None] = mapped_column(ForeignKey("resultado_weibull.id"))


class IntervencionProgramada(ConFechas, Base):
    __tablename__ = "intervencion_programada"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_plan: Mapped[int] = mapped_column(ForeignKey("plan_preventivo.id"))
    fecha_prevista: Mapped[date] = mapped_column(Date)
    ventana: Mapped[str | None] = mapped_column(String(60))
    id_ot: Mapped[int | None] = mapped_column(ForeignKey("orden_trabajo.id"))


class PredictivoParametro(ConFechas, Base):
    """Plantilla MANT/PMRED001 [12.G]."""

    __tablename__ = "predictivo_parametro"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_activo: Mapped[int] = mapped_column(ForeignKey("activo.id"))
    id_posicion: Mapped[int | None] = mapped_column(ForeignKey("posicion_componente.id"))
    especialidad: Mapped[str | None] = mapped_column(String(60))
    nombre: Mapped[str] = mapped_column(String(120))
    unidad: Mapped[str] = mapped_column(String(20))
    linea_base: Mapped[float | None] = mapped_column(Float)
    limite_alerta: Mapped[float | None] = mapped_column(Float)
    limite_accion: Mapped[float | None] = mapped_column(Float)
    plantilla: Mapped[str | None] = mapped_column(String(60))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class PredictivoMedicion(ConFechas, Base):
    __tablename__ = "predictivo_medicion"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_parametro: Mapped[int] = mapped_column(ForeignKey("predictivo_parametro.id"))
    fecha: Mapped[datetime] = mapped_column(FechaHoraUTC)
    valor: Mapped[float] = mapped_column(Float)
    equipo_medicion: Mapped[str | None] = mapped_column(String(120))
    id_usuario_controlo: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))


# ---------------------------------------------------------------------------
# Gestión, configuración y sistema
# ---------------------------------------------------------------------------


class Parametro(ConFechas, Base):
    """Todo número configurable del sistema. `valor` NULL = "falta dato" (nunca un cero)."""

    __tablename__ = "parametro"
    __table_args__ = (UniqueConstraint("clave", "vigente_desde", name="uq_parametro_clave_fecha"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(80))
    valor: Mapped[str | None] = mapped_column(Text)
    tipo: Mapped[TipoParametro] = mapped_column(E(TipoParametro, "tipo_parametro"))
    unidad: Mapped[str | None] = mapped_column(String(30))
    grupo: Mapped[str] = mapped_column(String(40))
    descripcion: Mapped[str] = mapped_column(Text)
    fuente: Mapped[str | None] = mapped_column(Text)
    vigente_desde: Mapped[date] = mapped_column(Date)


class TipoCambio(Base):
    __tablename__ = "tipo_cambio"
    __table_args__ = (CheckConstraint("ars_por_usd > 0", name="ck_tc_positivo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, unique=True)
    ars_por_usd: Mapped[float] = mapped_column(Float)
    fuente: Mapped[str | None] = mapped_column(String(200))


class DatoMensual(ConFechas, Base):
    __tablename__ = "dato_mensual"
    __table_args__ = (UniqueConstraint("periodo", "clave", name="uq_dato_mensual"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    periodo: Mapped[str] = mapped_column(String(7))  # AAAA-MM
    clave: Mapped[str] = mapped_column(String(60))
    valor: Mapped[float] = mapped_column(Float)


class IndicadorObjetivo(ConFechas, Base):
    __tablename__ = "indicador_objetivo"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    objetivo: Mapped[float | None] = mapped_column(Float)
    limite_inf: Mapped[float | None] = mapped_column(Float)
    limite_sup: Mapped[float | None] = mapped_column(Float)
    mayor_es_mejor: Mapped[bool] = mapped_column(Boolean, default=True)
    referencia_bibliografia: Mapped[str | None] = mapped_column(Text)


class EtapaImplementacion(ConFechas, Base):
    """Las 14 etapas de la UNIDAD 6 agrupadas en 3 fases [12.A]."""

    __tablename__ = "etapa_implementacion"
    __table_args__ = (CheckConstraint("fase BETWEEN 1 AND 3", name="ck_etapa_fase"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[int] = mapped_column(Integer, unique=True)
    fase: Mapped[int] = mapped_column(Integer)
    titulo: Mapped[str] = mapped_column(String(160))
    que_es: Mapped[str] = mapped_column(Text)
    por_que: Mapped[str] = mapped_column(Text)
    pantalla: Mapped[str | None] = mapped_column(String(120))
    criterio: Mapped[str | None] = mapped_column(String(60))  # clave del criterio automático
    estado: Mapped[EstadoEtapa] = mapped_column(E(EstadoEtapa, "estado_etapa"), default=EstadoEtapa.PENDIENTE)
    notas: Mapped[str | None] = mapped_column(Text)
    fecha_hecha: Mapped[datetime | None] = mapped_column(FechaHoraUTC)
    id_usuario_marco: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))


class ModuloHabilitado(Base):
    __tablename__ = "modulo_habilitado"
    codigo: Mapped[str] = mapped_column(String(10), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    habilitado: Mapped[bool] = mapped_column(Boolean, default=False)


class Alerta(ConFechas, Base):
    __tablename__ = "alerta"
    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(40))
    severidad: Mapped[str] = mapped_column(String(10))
    id_activo: Mapped[int | None] = mapped_column(ForeignKey("activo.id"))
    id_posicion: Mapped[int | None] = mapped_column(ForeignKey("posicion_componente.id"))
    mensaje: Mapped[str] = mapped_column(Text)
    clave_dedup: Mapped[str] = mapped_column(String(120))
    enviada_mail_en: Mapped[datetime | None] = mapped_column(FechaHoraUTC)
    resuelta_en: Mapped[datetime | None] = mapped_column(FechaHoraUTC)
    destinatarios: Mapped[str | None] = mapped_column(String(200))

    __table_args__ = (
        Index(
            "uq_alerta_abierta",
            "clave_dedup",
            unique=True,
            sqlite_where=text("resuelta_en IS NULL"),
            postgresql_where=text("resuelta_en IS NULL"),
        ),
    )


class Auditoria(Base):
    __tablename__ = "auditoria"
    __table_args__ = (Index("ix_auditoria_tabla_registro", "tabla", "id_registro"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[datetime] = mapped_column(FechaHoraUTC, default=ahora)
    id_usuario: Mapped[int | None] = mapped_column(Integer)  # sin FK: la auditoría sobrevive a bajas
    accion: Mapped[AccionAuditoria] = mapped_column(E(AccionAuditoria, "accion_auditoria"))
    tabla: Mapped[str] = mapped_column(String(60))
    id_registro: Mapped[int | None] = mapped_column(Integer)
    campo: Mapped[str | None] = mapped_column(String(60))
    valor_anterior: Mapped[str | None] = mapped_column(Text)
    valor_nuevo: Mapped[str | None] = mapped_column(Text)
    motivo: Mapped[str | None] = mapped_column(Text)


class RecalculoPendiente(Base):
    __tablename__ = "recalculo_pendiente"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_tipo_componente: Mapped[int] = mapped_column(ForeignKey("tipo_componente.id"))
    id_modo: Mapped[int] = mapped_column(ForeignKey("catalogo.id"))
    alcance: Mapped[Alcance] = mapped_column(E(Alcance, "alcance_recalc"), default=Alcance.MAQUINA)
    id_activo: Mapped[int | None] = mapped_column(ForeignKey("activo.id"))
    motivo: Mapped[str | None] = mapped_column(String(200))
    creado_en: Mapped[datetime] = mapped_column(FechaHoraUTC, default=ahora)
    tomado_en: Mapped[datetime | None] = mapped_column(FechaHoraUTC)
    terminado_en: Mapped[datetime | None] = mapped_column(FechaHoraUTC)
    error: Mapped[str | None] = mapped_column(Text)


class Importacion(Base):
    __tablename__ = "importacion"
    id: Mapped[int] = mapped_column(primary_key=True)
    archivo: Mapped[str] = mapped_column(String(260))
    hash: Mapped[str] = mapped_column(String(64))
    fecha: Mapped[datetime] = mapped_column(FechaHoraUTC, default=ahora)
    filas_ok: Mapped[int] = mapped_column(Integer, default=0)
    filas_error: Mapped[int] = mapped_column(Integer, default=0)
    reporte: Mapped[dict | None] = mapped_column(JSON)
    id_usuario: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))


# Tablas cuyos cambios se auditan (todas menos las de sistema).
TABLAS_NO_AUDITADAS = {"auditoria", "recalculo_pendiente", "estado_componente", "importacion"}
