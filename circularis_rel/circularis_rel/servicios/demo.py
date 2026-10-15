"""Datos DEMO: FICTICIOS y marcados como tales (P-07).

- Todo código empieza con "DEMO-" y todo usuario con "demo.". Mientras existan, la app muestra
  el cartel rojo "DATOS FICTICIOS".
- Se cargan por el mismo importador que los datos reales (así la demo también prueba el camino real).
- `borrar_demo` los elimina sin tocar nada más.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from circularis_rel.datos.db import BaseDatos
from circularis_rel.datos.modelos import (
    Activo,
    ActivoTurno,
    AmfeItem,
    Catalogo,
    CatalogoAplica,
    CriticidadEvaluacion,
    EtapaImplementacion,
    Importacion,
    Linea,
    PosicionComponente,
    PrecioRepuesto,
    Repuesto,
    RepuestoActivo,
    TipoComponente,
    Turno,
    Usuario,
    UsuarioActivo,
)
from circularis_rel.servicios import auth
from circularis_rel.servicios.importador.aplicar import Reporte, importar
from circularis_rel.servicios.importador.esquema import HOJAS_CARGA_INICIAL
from circularis_rel.servicios.importador.plantillas import escribir_libro

PREFIJO = "DEMO-"

# Usuarios de demostración. Las claves son públicas a propósito: borrar la demo antes de usar el
# sistema en serio (la app lo recuerda con el cartel rojo).
USUARIOS_DEMO = [
    ("demo.jefe", "Jefe DEMO", "JEFE", "demo-jefe-2026", None),
    ("demo.encargado", "Encargado DEMO", "ENCARGADO", "demo-encargado-2026", None),
    ("demo.gerencia", "Gerencia DEMO", "GERENCIA", "demo-gerencia-2026", None),
    ("demo.operario", "Operario DEMO", "OPERARIO", "1234", ["DEMO-AGR-001", "DEMO-EXT-001"]),
]

DATOS_DEMO: dict[str, list[dict]] = {
    "lineas": [{"codigo": "DEMO-TWOOD", "nombre": "Línea DEMO (datos ficticios)"}],
    "turnos": [
        {"codigo": "DEMO-M", "nombre": "Mañana (DEMO)", "hora_inicio": "06:00", "hora_fin": "14:00", "duracion_h": 8},
        {"codigo": "DEMO-T", "nombre": "Tarde (DEMO)", "hora_inicio": "14:00", "hora_fin": "22:00", "duracion_h": 8},
    ],
    "tipos_componente": [
        {"codigo": "DEMO-CUCHILLAS", "nombre": "Cuchillas (DEMO)", "hh_preventiva": 2, "hh_correctiva": 4, "uso": "ESPECIFICO",
         "intervalo_fabricante": 400, "unidad_intervalo_fabricante": "HORAS", "origen": "DEMO"},
        {"codigo": "DEMO-RULEMANES", "nombre": "Rulemanes (DEMO)", "hh_preventiva": 3, "hh_correctiva": 6, "uso": "COMUN",
         "origen": "DEMO"},
        {"codigo": "DEMO-HUSILLO", "nombre": "Tornillo sinfín (DEMO)", "hh_preventiva": 16, "hh_correctiva": 24,
         "uso": "ESPECIFICO", "origen": "DEMO", "beta_ref": 2.5,
         "fuente_ref": "DEMO: valor ficticio para mostrar Weibayes (no usar como referencia real)"},
        {"codigo": "DEMO-VALV-SEG", "nombre": "Válvula de seguridad (DEMO)", "falla_oculta": "SI", "funcion_seguridad": "SI",
         "uso": "COMUN", "origen": "DEMO"},
    ],
    "maquinas": [
        {"codigo": "DEMO-AGR-001", "nombre": "Agrumadora DEMO", "linea": "DEMO-TWOOD", "etapa_proceso": "PREPROCESADO",
         "horas_promedio_dia": 8, "autonomia_pulmon_h": 1, "numero_serie": "DEMO-SN-0001", "fabricante": "Fabricante DEMO",
         "modelo": "AG-DEMO", "proveedor": "Proveedor DEMO", "fecha_instalacion": "01/03/2022",
         "caracteristicas_tecnicas": "Ficticio: 4 cuchillas, 3500 rpm", "unidad_produccion": "FARDOS"},
        {"codigo": "DEMO-LAV-001", "nombre": "Cuba de lavado DEMO", "linea": "DEMO-TWOOD", "etapa_proceso": "LAVADO",
         "horas_promedio_dia": 6, "autonomia_pulmon_h": 2},
        {"codigo": "DEMO-EXT-001", "nombre": "Extrusora DEMO", "linea": "DEMO-TWOOD", "etapa_proceso": "EXTRUSION",
         "horas_promedio_dia": 8, "autonomia_pulmon_h": 0, "unidad_produccion": "DURMIENTES", "ciclo_teorico_s": 120},
    ],
    "maquina_turnos": [
        {"maquina": "DEMO-AGR-001", "turno": "DEMO-M"}, {"maquina": "DEMO-LAV-001", "turno": "DEMO-M"},
        {"maquina": "DEMO-EXT-001", "turno": "DEMO-M"}, {"maquina": "DEMO-EXT-001", "turno": "DEMO-T"},
    ],
    "posiciones": [
        {"maquina": "DEMO-AGR-001", "codigo": "CUCHILLAS", "tipo_componente": "DEMO-CUCHILLAS", "cantidad": 4, "critica": "SI"},
        {"maquina": "DEMO-AGR-001", "codigo": "RULEMANES", "tipo_componente": "DEMO-RULEMANES", "cantidad": 2, "critica": "SI"},
        {"maquina": "DEMO-LAV-001", "codigo": "RULEMANES", "tipo_componente": "DEMO-RULEMANES", "cantidad": 2, "critica": "SI"},
        {"maquina": "DEMO-EXT-001", "codigo": "HUSILLO", "tipo_componente": "DEMO-HUSILLO", "critica": "SI"},
        {"maquina": "DEMO-EXT-001", "codigo": "VALV-SEG", "tipo_componente": "DEMO-VALV-SEG"},
    ],
    "modos": [
        {"codigo": "DEMO-PERDIDA-FILO", "descripcion": "Pérdida de filo o rotura (DEMO)", "tipos_componente": "DEMO-CUCHILLAS", "origen": "DEMO"},
        {"codigo": "DEMO-RUIDO-DESGASTE", "descripcion": "Ruido y desgaste (DEMO)", "tipos_componente": "DEMO-RULEMANES", "origen": "DEMO"},
        {"codigo": "DEMO-DESGASTE-HUSILLO", "descripcion": "Desgaste del husillo (DEMO)", "tipos_componente": "DEMO-HUSILLO", "origen": "DEMO"},
        {"codigo": "DEMO-NO-ABRE", "descripcion": "No abre a la presión de tarado (DEMO)", "tipos_componente": "DEMO-VALV-SEG", "origen": "DEMO"},
    ],
    "repuestos": [
        {"codigo": "DEMO-REP-CUCH", "descripcion": "Juego de 4 cuchillas (DEMO)", "tipo_componente": "DEMO-CUCHILLAS", "uso": "ESPECIFICO",
         "stock_actual": 1, "stock_minimo": 1, "lead_time_dias": 15, "precio": 598000, "moneda": "ARS", "fecha_precio": "01/10/2026"},
        {"codigo": "DEMO-REP-HUS", "descripcion": "Tornillo sinfín (DEMO)", "tipo_componente": "DEMO-HUSILLO",
         "uso": "ESPECIFICO", "stock_actual": 0, "stock_minimo": 0, "lead_time_dias": 60, "precio": 9500000,
         "moneda": "ARS", "fecha_precio": "01/10/2026"},
        {"codigo": "DEMO-REP-ROD", "descripcion": "Rulemán 6310 (DEMO)", "tipo_componente": "DEMO-RULEMANES", "uso": "COMUN",
         "stock_actual": 4, "stock_minimo": 2, "lead_time_dias": 5, "precio": 85000, "moneda": "ARS", "fecha_precio": "01/10/2026"},
    ],
    "repuestos_por_maquina": [
        {"maquina": "DEMO-AGR-001", "repuesto": "DEMO-REP-CUCH", "cantidad_instalada": 1},
        {"maquina": "DEMO-AGR-001", "repuesto": "DEMO-REP-ROD", "cantidad_instalada": 2},
        {"maquina": "DEMO-LAV-001", "repuesto": "DEMO-REP-ROD", "cantidad_instalada": 2},
    ],
    "criticidad": [
        {"maquina": "DEMO-AGR-001", "uso": 5, "alternativa": 2, "influencia": 4, "calidad": 4, "ambiente": 3, "seguridad": 5},
        {"maquina": "DEMO-LAV-001", "uso": 5, "alternativa": 5, "influencia": 4, "calidad": 4, "ambiente": 3, "seguridad": 3},
        {"maquina": "DEMO-EXT-001", "uso": 5, "alternativa": 5, "influencia": 5, "calidad": 5, "ambiente": 3, "seguridad": 5},
    ],
    "amfe": [
        {"maquina": "DEMO-AGR-001", "tipo_componente": "DEMO-CUCHILLAS", "modo": "DEMO-PERDIDA-FILO", "g": 6, "o": 5, "d": 4,
         "efecto": "Caída de producción (DEMO)", "origen": "DEMO"},
    ],
}


def hay_demo(s: Session) -> bool:
    return (s.scalar(select(Activo.id).where(Activo.codigo.like(f"{PREFIJO}%")).limit(1)) is not None
            or s.scalar(select(Usuario.id).where(Usuario.usuario.like("demo.%")).limit(1)) is not None)


def cargar_demo(db: BaseDatos, usuario_id: int | None = None, tz: ZoneInfo | None = None) -> Reporte:
    """Carga el catálogo DEMO. Con `tz`, además la historia ficticia (partes, fallas validadas y
    preventivos de unos dos años y medio) y el recálculo, para ver el panel con datos."""
    with tempfile.TemporaryDirectory() as tmp:
        ruta = escribir_libro(Path(tmp) / "demo.xlsx", HOJAS_CARGA_INICIAL, DATOS_DEMO)
        reporte = importar(db, ruta, simular=False, usuario_id=usuario_id)
    if not reporte.aplicado:
        return reporte
    with db.escritura(usuario_id=usuario_id) as s:
        for usuario, nombre, rol, clave, maquinas in USUARIOS_DEMO:
            if s.scalar(select(Usuario).where(Usuario.usuario == usuario)) is None:
                auth.crear_usuario(s, usuario, nombre, rol, clave, maquinas=maquinas)
    if tz is not None:
        from circularis_rel.servicios.demo_historia import historia_demo_y_recalculo

        historia_demo_y_recalculo(db, tz)
    return reporte


def borrar_demo(db: BaseDatos, usuario_id: int | None = None) -> None:
    """Borra todo lo DEMO (máquinas, historia, resultados, usuarios y parámetros ficticios), fila por fila
    para que cada baja quede auditada."""
    from circularis_rel.datos.enums import EstadoEvento
    from circularis_rel.datos.modelos import (
        Alerta,
        AnalisisProblema,
        ConsumoRepuesto,
        EquivalenciaComponente,
        EstadoComponente,
        EventoFalla,
        IntervencionProgramada,
        OrdenTrabajo,
        OTTarea,
        Parametro,
        ParteTurno,
        PlanPreventivo,
        PredictivoMedicion,
        PredictivoParametro,
        RecalculoPendiente,
        ResultadoSistema,
        ResultadoWeibull,
        TarjetaTPM,
        VidaComponente,
        VidaHistorica,
    )

    with db.escritura(usuario_id=usuario_id, motivo="Borrado de los datos DEMO") as s:
        activos = select(Activo.id).where(Activo.codigo.like(f"{PREFIJO}%"))
        tipos = select(TipoComponente.id).where(TipoComponente.codigo.like(f"{PREFIJO}%"))
        repuestos = select(Repuesto.id).where(Repuesto.codigo.like(f"{PREFIJO}%"))
        catalogos = select(Catalogo.id).where(Catalogo.codigo.like(f"{PREFIJO}%"))
        usuarios = select(Usuario.id).where(Usuario.usuario.like("demo.%"))
        posiciones = select(PosicionComponente.id).where(PosicionComponente.id_activo.in_(activos))
        ots = select(OrdenTrabajo.id).where(OrdenTrabajo.id_activo.in_(activos))
        planes = select(PlanPreventivo.id).where(PlanPreventivo.id_posicion.in_(posiciones))
        parametros_pred = select(PredictivoParametro.id).where(PredictivoParametro.id_activo.in_(activos))

        def borrar(modelo, condicion) -> None:
            for obj in s.scalars(select(modelo).where(condicion)):
                s.delete(obj)
            s.flush()

        for ev in s.scalars(select(EventoFalla).where(EventoFalla.id_activo.in_(activos),
                                                      EventoFalla.estado == EstadoEvento.VALIDADO)):
            ev.estado = EstadoEvento.ANULADO  # un validado no se borra (trigger): primero se anula
        for t in s.scalars(select(TarjetaTPM).where(TarjetaTPM.id_activo.in_(activos))):
            t.id_evento_generado = None
        s.flush()
        borrar(EstadoComponente, EstadoComponente.id_posicion.in_(posiciones))
        borrar(ResultadoSistema, ResultadoSistema.id_activo.in_(activos))
        borrar(EquivalenciaComponente, EquivalenciaComponente.id_posicion.in_(posiciones))
        borrar(ResultadoWeibull, or_(ResultadoWeibull.id_tipo_componente.in_(tipos), ResultadoWeibull.id_activo.in_(activos)))
        borrar(RecalculoPendiente, or_(RecalculoPendiente.id_tipo_componente.in_(tipos), RecalculoPendiente.id_activo.in_(activos)))
        borrar(Alerta, Alerta.id_activo.in_(activos))
        borrar(AnalisisProblema, AnalisisProblema.id_activo.in_(activos))
        borrar(VidaComponente, VidaComponente.id_posicion.in_(posiciones))
        borrar(VidaHistorica, VidaHistorica.id_activo.in_(activos))
        borrar(ConsumoRepuesto, or_(ConsumoRepuesto.id_ot.in_(ots), ConsumoRepuesto.id_repuesto.in_(repuestos)))
        borrar(OTTarea, OTTarea.id_ot.in_(ots))
        borrar(IntervencionProgramada, IntervencionProgramada.id_plan.in_(planes))
        borrar(OrdenTrabajo, OrdenTrabajo.id.in_(ots))
        borrar(PlanPreventivo, PlanPreventivo.id.in_(planes))
        borrar(EventoFalla, EventoFalla.id_activo.in_(activos))
        borrar(TarjetaTPM, TarjetaTPM.id_activo.in_(activos))
        borrar(ParteTurno, ParteTurno.id_activo.in_(activos))
        borrar(PredictivoMedicion, PredictivoMedicion.id_parametro.in_(parametros_pred))
        borrar(PredictivoParametro, PredictivoParametro.id.in_(parametros_pred))
        borrar(Parametro, Parametro.fuente == "DEMO (ficticio)")
        borrar(AmfeItem, or_(AmfeItem.id_activo.in_(activos), AmfeItem.id_tipo_componente.in_(tipos)))
        borrar(CriticidadEvaluacion, CriticidadEvaluacion.id_activo.in_(activos))
        borrar(RepuestoActivo, or_(RepuestoActivo.id_activo.in_(activos), RepuestoActivo.id_repuesto.in_(repuestos)))
        borrar(PrecioRepuesto, PrecioRepuesto.id_repuesto.in_(repuestos))
        borrar(CatalogoAplica, or_(CatalogoAplica.id_catalogo.in_(catalogos), CatalogoAplica.id_tipo_componente.in_(tipos)))
        borrar(PosicionComponente, PosicionComponente.id_activo.in_(activos))
        borrar(ActivoTurno, ActivoTurno.id_activo.in_(activos))
        borrar(UsuarioActivo, or_(UsuarioActivo.id_activo.in_(activos), UsuarioActivo.id_usuario.in_(usuarios)))
        # Referencias simples a usuarios DEMO en datos reales: se desvinculan.
        s.execute(update(Activo).where(Activo.id_usuario_revision.in_(usuarios)).values(id_usuario_revision=None))
        s.execute(update(EtapaImplementacion).where(EtapaImplementacion.id_usuario_marco.in_(usuarios))
                  .values(id_usuario_marco=None))
        s.execute(update(Importacion).where(Importacion.id_usuario.in_(usuarios)).values(id_usuario=None))
        for modelo, condicion in (
            (Activo, Activo.codigo.like(f"{PREFIJO}%")),
            (Repuesto, Repuesto.codigo.like(f"{PREFIJO}%")),
            (TipoComponente, TipoComponente.codigo.like(f"{PREFIJO}%")),
            (Catalogo, Catalogo.codigo.like(f"{PREFIJO}%")),
            (Linea, Linea.codigo.like(f"{PREFIJO}%")),
            (Turno, Turno.codigo.like(f"{PREFIJO}%")),
            (Usuario, Usuario.usuario.like("demo.%")),
        ):
            borrar(modelo, condicion)
