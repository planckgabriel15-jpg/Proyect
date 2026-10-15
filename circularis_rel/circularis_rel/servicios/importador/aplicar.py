"""Importación de planillas: simular o aplicar, todo o nada, idempotente.

- Las hojas se procesan en orden de dependencia (líneas → … → AMFE) dentro de una sola
  transacción, así las referencias por código se resuelven aunque vengan en el mismo libro.
- Con cualquier error, nada se graba (D-021). `simular=True` corre lo mismo y revierte siempre.
- Solo se escriben los campos que cambian: re-importar el mismo libro da "sin cambios" y no
  ensucia la auditoría.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from circularis_rel.asistente.criticidad import evaluar_tp
from circularis_rel.datos.db import BaseDatos
from circularis_rel.datos.enums import (
    AccionAuditoria,
    ClaseCriticidad,
    ClaseTriage,
    MetodoCriticidad,
    NivelHora,
    OrigenDato,
    TipoCatalogo,
    TipoFin,
)
from circularis_rel.datos.modelos import (
    Activo,
    ActivoTurno,
    AmfeItem,
    Catalogo,
    CatalogoAplica,
    CriticidadEvaluacion,
    Importacion,
    Linea,
    Parametro,
    PosicionComponente,
    PrecioRepuesto,
    Repuesto,
    RepuestoActivo,
    TipoCambio,
    TipoComponente,
    Turno,
    VidaHistorica,
)
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios.importador.esquema import HOJA_HISTORICO, HOJAS_CARGA_INICIAL
from circularis_rel.servicios.importador.lector import FilaLeida, Mensaje, leer_libro
from circularis_rel.servicios.importador.triage import (
    parece_reconstruido,
    requisitos_faltantes,
    sugerir_clase,
)


@dataclass
class ResumenHoja:
    creados: int = 0
    actualizados: int = 0
    sin_cambios: int = 0


@dataclass
class Reporte:
    archivo: str
    simulado: bool
    hojas: dict[str, ResumenHoja] = field(default_factory=dict)
    errores: list[Mensaje] = field(default_factory=list)
    advertencias: list[Mensaje] = field(default_factory=list)
    aplicado: bool = False

    @property
    def ok(self) -> bool:
        return not self.errores

    def a_dict(self) -> dict:
        return {
            "archivo": self.archivo, "simulado": self.simulado, "aplicado": self.aplicado,
            "hojas": {k: vars(v) for k, v in self.hojas.items()},
            "errores": [str(e) for e in self.errores],
            "advertencias": [str(a) for a in self.advertencias],
        }

    def texto(self) -> str:
        lineas = [f"Archivo: {self.archivo}",
                  "Modo: SIMULACIÓN (no se grabó nada)" if self.simulado else
                  ("Resultado: APLICADO" if self.aplicado else "Resultado: NO APLICADO (hay errores, no se grabó nada)")]
        for nombre, r in self.hojas.items():
            lineas.append(f"  {nombre}: {r.creados} nuevos, {r.actualizados} actualizados, {r.sin_cambios} sin cambios")
        if self.errores:
            lineas.append(f"Errores ({len(self.errores)}):")
            lineas += [f"  - {e}" for e in self.errores]
        if self.advertencias:
            lineas.append(f"Advertencias ({len(self.advertencias)}):")
            lineas += [f"  - {a}" for a in self.advertencias]
        return "\n".join(lineas)


class _Contexto:
    def __init__(self, s: Session, reporte: Reporte):
        self.s = s
        self.r = reporte

    def resumen(self, hoja: str) -> ResumenHoja:
        return self.r.hojas.setdefault(hoja, ResumenHoja())

    def error(self, hoja: str, fila: FilaLeida | None, columna: str | None, texto: str) -> None:
        self.r.errores.append(Mensaje(hoja, fila.numero if fila else None, columna, texto))

    def advertencia(self, hoja: str, fila: FilaLeida | None, columna: str | None, texto: str) -> None:
        self.r.advertencias.append(Mensaje(hoja, fila.numero if fila else None, columna, texto))

    def upsert(self, hoja: str, modelo, claves: dict, valores: dict):
        obj = self.s.scalar(select(modelo).filter_by(**claves))
        res = self.resumen(hoja)
        if obj is None:
            obj = modelo(**claves, **valores)
            self.s.add(obj)
            self.s.flush()
            res.creados += 1
            return obj
        cambio = False
        for k, v in valores.items():
            if getattr(obj, k) != v:
                setattr(obj, k, v)
                cambio = True
        if cambio:
            self.s.flush()
            res.actualizados += 1
        else:
            res.sin_cambios += 1
        return obj

    # Búsquedas por código -------------------------------------------------
    def por_codigo(self, modelo, codigo: str):
        return self.s.scalar(select(modelo).where(modelo.codigo == codigo))

    def catalogo(self, tipo: TipoCatalogo, codigo: str):
        return self.s.scalar(select(Catalogo).where(Catalogo.tipo == tipo, Catalogo.codigo == codigo))

    def ref(self, hoja: str, fila: FilaLeida, columna: str, modelo, que: str):
        codigo = fila.valores.get(columna)
        if codigo is None:
            return None
        obj = self.por_codigo(modelo, codigo)
        if obj is None:
            self.error(hoja, fila, columna, f"no existe {que} con código '{codigo}'")
        return obj


def _sin_nulos(d: dict) -> dict:
    """Las celdas vacías no borran datos existentes (para borrar se edita en el sistema)."""
    return {k: v for k, v in d.items() if v is not None}


# ---------------------------------------------------------------------------
# Hojas
# ---------------------------------------------------------------------------


def _lineas(c: _Contexto, filas: list[FilaLeida]) -> None:
    for f in filas:
        c.upsert("lineas", Linea, {"codigo": f.valores["codigo"]}, {"nombre": f.valores["nombre"]})


def _turnos(c: _Contexto, filas):
    for f in filas:
        v = f.valores
        c.upsert("turnos", Turno, {"codigo": v["codigo"]},
                 {"nombre": v["nombre"], "hora_inicio": v["hora_inicio"], "hora_fin": v["hora_fin"],
                  "duracion_h": v["duracion_h"]})


def _tipos_componente(c: _Contexto, filas):
    for f in filas:
        v = dict(f.valores)
        if v.get("beta_ref") is not None and not v.get("fuente_ref"):
            c.error("tipos_componente", f, "fuente_ref", "un β de referencia exige declarar la fuente")
            continue
        codigo = v.pop("codigo")
        c.upsert("tipos_componente", TipoComponente, {"codigo": codigo}, _sin_nulos(v))


def _maquinas(c: _Contexto, filas):
    for f in filas:
        v = dict(f.valores)
        linea = c.ref("maquinas", f, "linea", Linea, "una línea")
        if linea is None:
            continue
        v.pop("linea")
        codigo = v.pop("codigo")
        v["id_linea"] = linea.id
        c.upsert("maquinas", Activo, {"codigo": codigo}, _sin_nulos(v))


def _maquina_turnos(c: _Contexto, filas):
    for f in filas:
        a = c.ref("maquina_turnos", f, "maquina", Activo, "una máquina")
        t = c.ref("maquina_turnos", f, "turno", Turno, "un turno")
        if a is None or t is None:
            continue
        dias = f.valores.get("dias") or "1,2,3,4,5"
        partes = [d.strip() for d in str(dias).split(",") if d.strip()]
        if not partes or any(not d.isdigit() or not 1 <= int(d) <= 7 for d in partes):
            c.error("maquina_turnos", f, "dias", "usar números del 1 (lunes) al 7 (domingo) separados por coma")
            continue
        c.upsert("maquina_turnos", ActivoTurno, {"id_activo": a.id, "id_turno": t.id}, {"dias": ",".join(partes)})


def _posiciones(c: _Contexto, filas):
    for f in filas:
        v = f.valores
        a = c.ref("posiciones", f, "maquina", Activo, "una máquina")
        t = c.ref("posiciones", f, "tipo_componente", TipoComponente, "un tipo de componente")
        if a is None or t is None:
            continue
        valores = {"id_tipo_componente": t.id, "ubicacion": v.get("ubicacion"), "cantidad": v.get("cantidad") or 1,
                   "critica": bool(v.get("critica"))}
        c.upsert("posiciones", PosicionComponente, {"id_activo": a.id, "codigo": v["codigo"]}, _sin_nulos(valores))


def _catalogo(tipo: TipoCatalogo, hoja: str, tipos_obligatorios: bool):
    def aplicar(c: _Contexto, filas):
        for f in filas:
            v = f.valores
            ids_tipos = []
            for codigo in v.get("tipos_componente") or []:
                t = c.por_codigo(TipoComponente, codigo)
                if t is None:
                    c.error(hoja, f, "tipos_componente", f"no existe el tipo de componente '{codigo}'")
                else:
                    ids_tipos.append(t.id)
            if tipos_obligatorios and not ids_tipos:
                continue
            valores = {"descripcion": v["descripcion"]}
            if v.get("icono"):
                valores["icono"] = v["icono"]
            valores["origen"] = OrigenDato(v["origen"]) if v.get("origen") else OrigenDato.IMPORTACION
            cat = c.upsert(hoja, Catalogo, {"tipo": tipo, "codigo": v["codigo"]}, valores)
            if v.get("tipos_componente") is not None:
                actuales = set(c.s.scalars(select(CatalogoAplica.id_tipo_componente)
                                           .where(CatalogoAplica.id_catalogo == cat.id)))
                if actuales != set(ids_tipos):
                    c.s.execute(delete(CatalogoAplica).where(CatalogoAplica.id_catalogo == cat.id))
                    c.s.add_all(CatalogoAplica(id_catalogo=cat.id, id_tipo_componente=i) for i in set(ids_tipos))
                    c.s.flush()
    return aplicar


def _repuestos(c: _Contexto, filas):
    for f in filas:
        v = dict(f.valores)
        tipo = None
        if v.get("tipo_componente"):
            tipo = c.ref("repuestos", f, "tipo_componente", TipoComponente, "un tipo de componente")
            if tipo is None:
                continue
        precio, moneda, fecha_precio = v.pop("precio"), v.pop("moneda"), v.pop("fecha_precio")
        if precio is not None and fecha_precio is None:
            c.error("repuestos", f, "fecha_precio", "todo precio se guarda con su fecha")
            continue
        v.pop("tipo_componente")
        codigo = v.pop("codigo")
        v["stock_minimo_manual"] = v.pop("stock_minimo")
        if tipo is not None:
            v["id_tipo_componente"] = tipo.id
        rep = c.upsert("repuestos", Repuesto, {"codigo": codigo}, _sin_nulos(v))
        if precio is not None:
            c.upsert("repuestos (precios)", PrecioRepuesto, {"id_repuesto": rep.id, "fecha": fecha_precio},
                     {"precio": precio, "moneda": moneda or "ARS"})


def _repuestos_por_maquina(c: _Contexto, filas):
    for f in filas:
        a = c.ref("repuestos_por_maquina", f, "maquina", Activo, "una máquina")
        r = c.ref("repuestos_por_maquina", f, "repuesto", Repuesto, "un repuesto")
        if a is None or r is None:
            continue
        c.upsert("repuestos_por_maquina", RepuestoActivo, {"id_repuesto": r.id, "id_activo": a.id},
                 _sin_nulos({"cantidad_instalada": f.valores.get("cantidad_instalada")}))


def _criticidad(c: _Contexto, filas):
    cortes = P.obtener(c.s, "criticidad.tp_cortes")
    nivel_a_clase = P.obtener(c.s, "criticidad.tp_nivel_a_clase")
    pesos = P.obtener(c.s, "criticidad.pesos_plan")
    for f in filas:
        v = f.valores
        a = c.ref("criticidad", f, "maquina", Activo, "una máquina")
        if a is None:
            continue
        metodo = MetodoCriticidad(v.get("metodo") or MetodoCriticidad.TP_6_CRITERIOS)
        criterios = {k: v[k] for k in ("uso", "alternativa", "influencia", "calidad", "ambiente", "seguridad")}
        if metodo == MetodoCriticidad.TP_6_CRITERIOS:
            try:
                res = evaluar_tp(criterios, cortes, nivel_a_clase, pesos)
            except ValueError as e:
                c.error("criticidad", f, None, str(e))
                continue
            puntaje, nivel, clase = res.puntaje, res.nivel, res.clase
            detalle = {**criterios, "puntaje_ponderado_plan": res.puntaje_ponderado}
            if v.get("clase") and v["clase"] != clase:
                c.advertencia("criticidad", f, "clase",
                              f"la clase indicada ({v['clase']}) difiere de la calculada ({clase}); se usa la indicada")
                clase = v["clase"]
        else:
            if not v.get("clase"):
                c.error("criticidad", f, "clase", "con el método PONDERACION_U1 hay que indicar la clase "
                                                  "(los cortes de la UNIDAD 1 están pendientes de verificar)")
                continue
            puntaje, nivel, clase = float(sum(criterios.values())), None, v["clase"]
            detalle = criterios
        fecha = v.get("fecha")
        if fecha is None:  # sin fecha: actualiza la evaluación vigente (re-importar no duplica)
            vigente = c.s.scalar(select(CriticidadEvaluacion).where(
                CriticidadEvaluacion.id_activo == a.id, CriticidadEvaluacion.metodo == metodo,
                CriticidadEvaluacion.vigente.is_(True)).order_by(CriticidadEvaluacion.fecha.desc()).limit(1))
            fecha = vigente.fecha if vigente else date.today()
        c.upsert("criticidad", CriticidadEvaluacion, {"id_activo": a.id, "metodo": metodo, "fecha": fecha},
                 {"criterios": detalle, "puntaje": puntaje, "nivel": nivel, "clase": ClaseCriticidad(clase),
                  "vigente": True})
        for previa in c.s.scalars(select(CriticidadEvaluacion).where(
                CriticidadEvaluacion.id_activo == a.id, CriticidadEvaluacion.fecha < fecha,
                CriticidadEvaluacion.vigente.is_(True))):
            previa.vigente = False
        cambios = {"criticidad_puntaje": puntaje, "criticidad_nivel": nivel,
                   "criticidad_clase": ClaseCriticidad(clase), "criticidad_metodo": metodo}
        for k, val in cambios.items():
            if getattr(a, k) != val:
                setattr(a, k, val)
        c.s.flush()


def _amfe(c: _Contexto, filas):
    for f in filas:
        v = f.valores
        activo = c.ref("amfe", f, "maquina", Activo, "una máquina") if v.get("maquina") else None
        if v.get("maquina") and activo is None:
            continue
        tipo = c.ref("amfe", f, "tipo_componente", TipoComponente, "un tipo de componente")
        modo = c.catalogo(TipoCatalogo.MODO, v["modo"])
        if modo is None:
            c.error("amfe", f, "modo", f"no existe el modo de falla '{v['modo']}'")
        if tipo is None or modo is None:
            continue
        aplica = c.s.scalar(select(CatalogoAplica).where(CatalogoAplica.id_catalogo == modo.id,
                                                         CatalogoAplica.id_tipo_componente == tipo.id))
        if aplica is None:
            c.error("amfe", f, "modo", f"el modo '{v['modo']}' no está asignado al tipo '{v['tipo_componente']}'")
            continue
        valores = {k: v.get(k) for k in ("requerimiento", "efecto", "causa", "control_prevencion",
                                          "control_deteccion", "acciones", "responsable")}
        valores.update(g=v["g"], o=v["o"], d=v["d"],
                       origen=OrigenDato(v["origen"]) if v.get("origen") else OrigenDato.IMPORTACION)
        c.upsert("amfe", AmfeItem,
                 {"id_activo": activo.id if activo else None, "id_tipo_componente": tipo.id, "id_modo": modo.id},
                 _sin_nulos(valores))


def _parametros_costos(c: _Contexto, filas):
    for f in filas:
        v = f.valores
        base = c.s.scalar(select(Parametro).where(Parametro.clave == v["clave"]).limit(1))
        if base is None:
            c.error("parametros_costos", f, "clave", f"parámetro desconocido '{v['clave']}'")
            continue
        c.upsert("parametros_costos", Parametro, {"clave": v["clave"], "vigente_desde": v["vigente_desde"]},
                 {"valor": str(v["valor"]), "tipo": base.tipo, "unidad": base.unidad, "grupo": base.grupo,
                  "descripcion": base.descripcion, "fuente": "Importado"})


def _tipos_cambio(c: _Contexto, filas):
    for f in filas:
        v = f.valores
        c.upsert("tipos_cambio", TipoCambio, {"fecha": v["fecha"]},
                 _sin_nulos({"ars_por_usd": v["ars_por_usd"], "fuente": v.get("fuente")}))


APLICADORES: dict[str, Callable] = {
    "lineas": _lineas,
    "turnos": _turnos,
    "tipos_componente": _tipos_componente,
    "maquinas": _maquinas,
    "maquina_turnos": _maquina_turnos,
    "posiciones": _posiciones,
    "sintomas": _catalogo(TipoCatalogo.SINTOMA, "sintomas", False),
    "modos": _catalogo(TipoCatalogo.MODO, "modos", True),
    "causas": _catalogo(TipoCatalogo.CAUSA, "causas", False),
    "repuestos": _repuestos,
    "repuestos_por_maquina": _repuestos_por_maquina,
    "criticidad": _criticidad,
    "amfe": _amfe,
    "parametros_costos": _parametros_costos,
    "tipos_cambio": _tipos_cambio,
}


def _historico(c: _Contexto, filas: list[FilaLeida], id_importacion_ref: list) -> None:
    fechas_por_posicion: dict[tuple, list] = {}
    for f in filas:
        v = f.valores
        a = c.ref("historico", f, "maquina", Activo, "una máquina")
        if a is None:
            continue
        pos = None
        if v.get("posicion"):
            pos = c.s.scalar(select(PosicionComponente).where(PosicionComponente.id_activo == a.id,
                                                              PosicionComponente.codigo == v["posicion"]))
            if pos is None:
                c.error("historico", f, "posicion", f"la máquina {a.codigo} no tiene la posición '{v['posicion']}'")
                continue
        modo = None
        if v.get("modo"):
            modo = c.catalogo(TipoCatalogo.MODO, v["modo"])
            if modo is None:
                c.error("historico", f, "modo", f"no existe el modo de falla '{v['modo']}'")
                continue
            if pos is not None and c.s.scalar(select(CatalogoAplica).where(
                    CatalogoAplica.id_catalogo == modo.id,
                    CatalogoAplica.id_tipo_componente == pos.id_tipo_componente)) is None:
                c.error("historico", f, "modo", "el modo no corresponde al tipo de componente de la posición")
                continue
        for desde, hasta, nombre in (("fecha_fin_desde", "fecha_fin_hasta", "fecha"), ("edad_desde_h", "edad_hasta_h", "edad")):
            if (v.get(desde) is None) != (v.get(hasta) is None):
                c.error("historico", f, desde, f"el rango de {nombre} necesita 'desde' y 'hasta'")
            elif v.get(desde) is not None and v[hasta] < v[desde]:
                c.error("historico", f, hasta, f"el rango de {nombre} está invertido")
        v_triage = dict(v, tipo_fin=TipoFin(v["tipo_fin"]))
        sugerida, motivo = sugerir_clase(v_triage, pos is not None, modo is not None)
        if v.get("clase"):
            clase = ClaseTriage(v["clase"])
            faltan = requisitos_faltantes(clase, v_triage, pos is not None, modo is not None)
            if faltan:
                c.error("historico", f, "clase", f"la clase {clase} exige: {', '.join(faltan)}")
                continue
            if clase != sugerida:
                c.advertencia("historico", f, "clase", f"el sistema propone {sugerida}: {motivo}")
                motivo = f"Indicada por el usuario (el sistema proponía {sugerida})"
        else:
            clase = sugerida
        clave = hashlib.sha256(json.dumps(
            [a.codigo, v.get("posicion"), v["tipo_fin"], v.get("modo"), str(v.get("fecha_instalacion")),
             str(v.get("fecha_fin")), str(v.get("fecha_fin_desde")), str(v.get("fecha_fin_hasta")),
             v.get("edad_horas"), v.get("descripcion_original")], ensure_ascii=False).encode()).hexdigest()
        valores = dict(
            id_activo=a.id, id_posicion=pos.id if pos else None, tipo_fin=TipoFin(v["tipo_fin"]),
            id_modo_falla=modo.id if modo else None, fecha_instalacion=v.get("fecha_instalacion"),
            fecha_fin=v.get("fecha_fin"), fecha_fin_inf=v.get("fecha_fin_desde"), fecha_fin_sup=v.get("fecha_fin_hasta"),
            edad_horas=v.get("edad_horas"), edad_inf_h=v.get("edad_desde_h"), edad_sup_h=v.get("edad_hasta_h"),
            clase_triage=clase, motivo_clase=motivo, fuente=v["fuente"], respaldo=v.get("respaldo"),
            descripcion_original=v.get("descripcion_original"), observaciones=v.get("observaciones"),
            nivel_hora=NivelHora.E,
        )
        c.upsert("historico", VidaHistorica, {"clave_importacion": clave}, valores)
        fechas_por_posicion.setdefault((a.codigo, v.get("posicion")), []).append(
            v.get("fecha_fin") or v.get("fecha_fin_desde"))
    for (maquina, posicion), fechas in fechas_por_posicion.items():
        if parece_reconstruido(fechas):
            c.advertencia("historico", None, None,
                          f"{maquina}/{posicion or 'sin posición'}: fechas con espaciado regular; "
                          "posibles valores reconstruidos (revisar la clase)")


def _hash_archivo(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def importar(db: BaseDatos, ruta: Path, *, simular: bool, usuario_id: int | None = None,
             historico: bool = False) -> Reporte:
    """Importa un libro de carga inicial (o el de histórico). Todo o nada."""
    ruta = Path(ruta)
    reporte = Reporte(archivo=ruta.name, simulado=simular)
    hojas = (HOJA_HISTORICO,) if historico else HOJAS_CARGA_INICIAL
    leidas = leer_libro(ruta, hojas, reporte.errores)
    if not leidas and not reporte.errores:
        reporte.errores.append(Mensaje(ruta.name, None, None, "el libro no tiene ninguna hoja reconocida"))

    class _Revertir(Exception):
        pass

    try:
        with db.escritura(usuario_id=usuario_id, motivo=f"Importación de {ruta.name}",
                          accion=AccionAuditoria.IMPORTACION) as s:
            c = _Contexto(s, reporte)
            if historico:
                if "historico" in leidas:
                    _historico(c, leidas["historico"].filas, [])
            else:
                for nombre in (h.nombre for h in hojas):
                    if nombre in leidas:
                        APLICADORES[nombre](c, leidas[nombre].filas)
            if simular or reporte.errores:
                raise _Revertir
            s.add(Importacion(archivo=ruta.name, hash=_hash_archivo(ruta), filas_ok=sum(
                r.creados + r.actualizados + r.sin_cambios for r in reporte.hojas.values()),
                filas_error=0, reporte=reporte.a_dict(), id_usuario=usuario_id))
    except _Revertir:
        return reporte
    reporte.aplicado = True
    return reporte
