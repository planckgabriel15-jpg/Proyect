"""Criticidad guiada desde la pantalla [12.C]: guarda la evaluación y actualiza la clase de la máquina.

El método del TP es el predeterminado (D-020). La ponderación U1 queda disponible con sus escalas "a verificar"
(P-10); su clase sale de los cortes que cargue el jefe o, si no hay, la elige él.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.asistente import criticidad as C
from circularis_rel.datos.enums import ClaseCriticidad, MetodoCriticidad
from circularis_rel.datos.modelos import Activo, CriticidadEvaluacion, Usuario
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios.permisos import Accion, requerir
from circularis_rel.servicios.registro import ErrorRegistro


def calcular(s: Session, metodo: MetodoCriticidad, valores: dict[str, int]) -> C.ResultadoCriticidad:
    if metodo == MetodoCriticidad.TP_6_CRITERIOS:
        return C.evaluar_tp(valores, P.obtener(s, "criticidad.tp_cortes"), P.obtener(s, "criticidad.tp_nivel_a_clase"),
                            P.obtener(s, "criticidad.pesos_plan"))
    return C.evaluar_u1(valores, P.obtener(s, "criticidad.u1_escalas"), P.obtener(s, "criticidad.u1_cortes"))


def guardar(s: Session, id_usuario: int, id_activo: int, metodo: MetodoCriticidad, valores: dict[str, int],
            clase_manual: str | None = None, fecha: date | None = None) -> CriticidadEvaluacion:
    u = s.get(Usuario, id_usuario)
    if u is None or not u.activo:
        raise ErrorRegistro("Usuario no válido")
    requerir(u.rol, Accion.CONFIGURAR)
    try:
        r = calcular(s, metodo, valores)
    except ValueError as e:
        raise ErrorRegistro(str(e)) from e
    clase = clase_manual or r.clase
    if not clase:
        raise ErrorRegistro("Sin cortes cargados para este método: elegí la clase A, B o C")
    fecha = fecha or date.today()
    for previa in s.scalars(select(CriticidadEvaluacion).where(CriticidadEvaluacion.id_activo == id_activo,
                                                               CriticidadEvaluacion.vigente.is_(True))):
        previa.vigente = False
    detalle = {**valores, "puntaje_ponderado_plan": r.puntaje_ponderado, "clase_calculada": r.clase or None,
               "clase_manual": clase_manual}
    ev = CriticidadEvaluacion(id_activo=id_activo, metodo=metodo, criterios=detalle, puntaje=r.puntaje, nivel=r.nivel or None,
                              clase=ClaseCriticidad(clase), fecha=fecha, id_usuario=id_usuario, vigente=True)
    s.add(ev)
    a = s.get(Activo, id_activo)
    a.criticidad_puntaje, a.criticidad_nivel = r.puntaje, r.nivel or None
    a.criticidad_clase, a.criticidad_metodo = ClaseCriticidad(clase), metodo
    s.flush()
    return ev


def historial(s: Session, id_activo: int) -> list[CriticidadEvaluacion]:
    return list(s.scalars(select(CriticidadEvaluacion).where(CriticidadEvaluacion.id_activo == id_activo)
                          .order_by(CriticidadEvaluacion.fecha.desc(), CriticidadEvaluacion.id.desc())))
