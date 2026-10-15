"""Catastro de máquinas [12.B] y revisión del jefe (criterio de salida de la fase 0).

- Ficha imprimible "Plantilla de registro e histórico de máquinas" (UNIDAD 6, MANT/RHM001)
  y "Plantilla de repuestos por máquina" (MANT/RM001), con los campos unidos (B-010).
- Revisión: el jefe marca cada máquina como revisada (queda auditado con acción REVISION).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from circularis_rel.datos.db import ahora
from circularis_rel.datos.enums import EstadoEvento, EstadoOT, EtapaProceso, TipoOT
from circularis_rel.datos.modelos import (
    Activo,
    Catalogo,
    EventoFalla,
    Linea,
    OrdenTrabajo,
    PosicionComponente,
    PrecioRepuesto,
    Repuesto,
    RepuestoActivo,
    TipoComponente,
    Usuario,
)
from circularis_rel.servicios.formato import cantidad, fecha, numero
from circularis_rel.servicios.pdf import PDF

CAMPOS_CATASTRO = ("numero_serie", "fabricante", "modelo", "proveedor", "fecha_instalacion",
                   "caracteristicas_tecnicas")


@dataclass
class EstadoRevision:
    codigo: str
    nombre: str
    posiciones: int
    posiciones_criticas: int
    criticidad: str | None
    catastro_completo: float  # fracción de CAMPOS_CATASTRO cargados
    revisado: bool
    revisado_por: str | None
    faltantes: list[str]


def estado_revision(s: Session) -> list[EstadoRevision]:
    salida = []
    orden = {e: i for i, e in enumerate(EtapaProceso)}
    activos = sorted(s.scalars(select(Activo).where(Activo.activo.is_(True))),
                     key=lambda a: (orden[a.etapa_proceso], a.orden_proceso or 0, a.codigo))
    for a in activos:
        n_pos = s.scalar(select(func.count()).select_from(PosicionComponente).where(
            PosicionComponente.id_activo == a.id, PosicionComponente.activa.is_(True)))
        n_crit = s.scalar(select(func.count()).select_from(PosicionComponente).where(
            PosicionComponente.id_activo == a.id, PosicionComponente.critica.is_(True)))
        completos = sum(1 for c in CAMPOS_CATASTRO if getattr(a, c) not in (None, ""))
        faltantes = []
        if n_pos == 0:
            faltantes.append("sin componentes")
        if n_crit == 0:
            faltantes.append("ninguna posición marcada como crítica")
        if a.criticidad_clase is None:
            faltantes.append("sin criticidad")
        if a.horas_promedio_dia is None:
            faltantes.append("sin horas promedio por día")
        if a.autonomia_pulmon_h is None:
            faltantes.append("sin autonomía de pulmón")
        revisor = s.get(Usuario, a.id_usuario_revision).nombre if a.id_usuario_revision else None
        salida.append(EstadoRevision(a.codigo, a.nombre, n_pos, n_crit,
                                     a.criticidad_clase.value if a.criticidad_clase else None,
                                     completos / len(CAMPOS_CATASTRO), a.revisado_en is not None, revisor, faltantes))
    return salida


def marcar_revisado(s: Session, codigo: str, id_usuario: int, revisado: bool = True) -> None:
    a = s.scalar(select(Activo).where(Activo.codigo == codigo))
    if a is None:
        raise ValueError(f"No existe la máquina '{codigo}'")
    a.revisado_en = ahora() if revisado else None
    a.id_usuario_revision = id_usuario if revisado else None


def historial(s: Session, id_activo: int) -> list[list]:
    """Filas (tipo, fecha, tiempo de reparación, ficha de referencia) para MANT/RHM001."""
    filas: list[tuple] = []
    for ev in s.scalars(select(EventoFalla).where(EventoFalla.id_activo == id_activo,
                                                  EventoFalla.estado == EstadoEvento.VALIDADO)):
        modo = s.get(Catalogo, ev.id_modo) if ev.id_modo else None
        pos = s.get(PosicionComponente, ev.id_posicion) if ev.id_posicion else None
        tipo = f"Correctivo: {pos.codigo if pos else ''} – {modo.descripcion if modo else ''}"
        filas.append((ev.fecha_hora_falla.date(), tipo, ev.tiempo_reparacion_h, f"Aviso {ev.id}"))
    for ot in s.scalars(select(OrdenTrabajo).where(
            OrdenTrabajo.id_activo == id_activo, OrdenTrabajo.tipo != TipoOT.CORRECTIVA,
            OrdenTrabajo.estado.in_([EstadoOT.CERRADA, EstadoOT.VALIDADA]))):
        fecha = (ot.fin_real or ot.inicio_real).date() if (ot.fin_real or ot.inicio_real) else ot.fecha_programada
        filas.append((fecha, ot.tipo.value.capitalize(), ot.hh_propias, ot.numero))
    filas.sort(key=lambda f: f[0] or date.min, reverse=True)
    return [[t, f.strftime("%d/%m/%Y") if f else "", "" if h is None else f"{h:g} h", r] for f, t, h, r in filas]


def repuestos_de(s: Session, id_activo: int) -> list[list]:
    filas = []
    for rep, _ra in s.execute(select(Repuesto, RepuestoActivo).join(RepuestoActivo, RepuestoActivo.id_repuesto == Repuesto.id)
                             .where(RepuestoActivo.id_activo == id_activo).order_by(Repuesto.codigo)):
        precio = s.scalar(select(PrecioRepuesto).where(PrecioRepuesto.id_repuesto == rep.id)
                          .order_by(PrecioRepuesto.fecha.desc()).limit(1))
        costo = f"{precio.moneda.value} {numero(precio.precio)} ({fecha(precio.fecha)})" if precio else ""
        filas.append([rep.codigo, rep.descripcion, cantidad(rep.stock_minimo_manual), cantidad(rep.stock_actual), costo,
                      rep.ubicacion, rep.codigo_proveedor or rep.proveedor])
    return filas


def ficha_pdf(s: Session, codigo: str, *, con_costos: bool = True) -> bytes:
    a = s.scalar(select(Activo).where(Activo.codigo == codigo))
    if a is None:
        raise ValueError(f"No existe la máquina '{codigo}'")
    linea = s.get(Linea, a.id_linea)
    pdf = PDF("Plantilla de registro e histórico de máquinas", "MANT/RHM001")
    pdf.add_page()
    pdf.campo("Código máquina", a.codigo)
    pdf.campo("Máquina", a.nombre)
    pdf.campo("N.º de serie", a.numero_serie)
    pdf.campo("Fabricante", a.fabricante)
    pdf.campo("Modelo", a.modelo)
    pdf.campo("Proveedor", a.proveedor)
    pdf.campo("Localización", " · ".join(x for x in (linea.nombre, a.ubicacion, f"etapa {a.etapa_proceso.value.lower()}") if x))
    pdf.campo("Fecha de instalación", a.fecha_instalacion.strftime("%d/%m/%Y") if a.fecha_instalacion else None)
    pdf.campo("Planos, manuales y catálogos", a.ruta_documentos)
    dims = ", ".join(f"{n} {getattr(a, c):g} {u}" for n, c, u in (("ancho", "ancho_mm", "mm"), ("alto", "alto_mm", "mm"),
                                                                   ("largo", "largo_mm", "mm"), ("peso", "peso_kg", "kg"))
                     if getattr(a, c) is not None)
    pdf.campo("Dimensiones exteriores y peso", dims)
    pdf.campo("Condiciones de almacenamiento", a.condiciones_almacenamiento)
    pdf.campo("Características técnicas", a.caracteristicas_tecnicas)
    pdf.campo("Criticidad", f"{a.criticidad_clase.value} ({a.criticidad_nivel or ''}, {cantidad(a.criticidad_puntaje)} puntos)"
              if a.criticidad_clase else None)
    pdf.subtitulo("Componentes")
    filas_pos = [[p.codigo, t.nombre, p.cantidad, "Sí" if p.critica else ""]
                 for p, t in s.execute(select(PosicionComponente, TipoComponente)
                                       .join(TipoComponente, TipoComponente.id == PosicionComponente.id_tipo_componente)
                                       .where(PosicionComponente.id_activo == a.id).order_by(PosicionComponente.codigo))]
    pdf.tabla(["Posición", "Tipo de componente", "Cant.", "Crítica"], [60, 86, 15, 25], filas_pos)
    pdf.subtitulo("Histórico")
    pdf.tabla(["Tipo", "Fecha", "Tiempo de reparación", "Ficha de referencia"], [86, 25, 35, 40],
              historial(s, a.id), vacias=3)
    pdf.titulo, pdf.referencia = "Plantilla de repuestos por máquina", "MANT/RM001"
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 10)
    pdf.cell(0, 7, f"Código máquina: {a.codigo}    Máquina: {a.nombre}", new_x="LMARGIN", new_y="NEXT")
    filas = repuestos_de(s, a.id)
    if not con_costos:
        filas = [f[:4] + [""] + f[5:] for f in filas]
    pdf.tabla(["Cód. rep.", "Repuesto", "Mín.", "Stock", "Costo", "Ubicación", "Proveedor"],
              [28, 46, 11, 11, 48, 20, 22], filas, vacias=3)
    return pdf.a_bytes()


# Edición desde la pantalla de máquinas -------------------------------------------------------

CAMPOS_EDITABLES = {
    "nombre", "ubicacion", "funcion", "horas_promedio_dia", "unidad_produccion", "factor_toneladas",
    "autonomia_pulmon_h", "ciclo_teorico_s", "numero_serie", "fabricante", "modelo", "proveedor",
    "fecha_instalacion", "ancho_mm", "alto_mm", "largo_mm", "peso_kg", "condiciones_almacenamiento",
    "caracteristicas_tecnicas", "ruta_documentos",
}


def actualizar_catastro(s: Session, codigo: str, cambios: dict) -> list[str]:
    """Aplica los cambios permitidos y devuelve los campos que realmente cambiaron."""
    a = s.scalar(select(Activo).where(Activo.codigo == codigo))
    if a is None:
        raise ValueError(f"No existe la máquina '{codigo}'")
    desconocidos = set(cambios) - CAMPOS_EDITABLES
    if desconocidos:
        raise ValueError(f"Campos no editables: {', '.join(sorted(desconocidos))}")
    for campo in ("horas_promedio_dia",):
        v = cambios.get(campo)
        if v is not None and not 0 <= v <= 24:
            raise ValueError("Las horas por día van de 0 a 24")
    cambiados = []
    for campo, valor in cambios.items():
        if isinstance(valor, str):
            valor = valor.strip() or None
        if getattr(a, campo) != valor:
            setattr(a, campo, valor)
            cambiados.append(campo)
    return cambiados


def marcar_criticas(s: Session, codigo: str, criticas: dict[str, bool]) -> int:
    """criticas = {código de posición: crítica}. Devuelve cuántas cambiaron."""
    a = s.scalar(select(Activo).where(Activo.codigo == codigo))
    if a is None:
        raise ValueError(f"No existe la máquina '{codigo}'")
    cambios = 0
    for p in s.scalars(select(PosicionComponente).where(PosicionComponente.id_activo == a.id)):
        if p.codigo in criticas and p.critica != bool(criticas[p.codigo]):
            p.critica = bool(criticas[p.codigo])
            cambios += 1
    return cambios
