"""Parte de turno: menos de 30 s (Plan §4). "Operó todo" se guarda con un toque más."""

from datetime import timedelta

import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.app.componentes import formularios as F
from circularis_rel.datos.enums import EstadoParte, UnidadProduccion
from circularis_rel.datos.modelos import MotivoParada, Turno
from circularis_rel.servicios import registro, turnos

u = contexto.usuario()
db = contexto.db()
tz = contexto.config().zona_horaria
st.header("📝 Parte de turno")
F.mensaje_ok("parte")

with db.lectura() as s:
    maquinas = registro.maquinas_permitidas(s, u["id"])
    motivos = list(s.scalars(select(MotivoParada).where(MotivoParada.activo.is_(True), MotivoParada.codigo != "SIN_DATO")
                             .order_by(MotivoParada.orden)))
if not maquinas:
    st.warning("No tenés máquinas asignadas. Pedíselo al jefe de mantenimiento.")
    st.stop()

codigos = [a.codigo for a in maquinas]
codigo = st.selectbox("Máquina", codigos, index=F.indice_maquina(codigos),
                      format_func=lambda c: f"{c} · {next(a.nombre for a in maquinas if a.codigo == c)}")
a = next(x for x in maquinas if x.codigo == codigo)
hoy = F.hoy()
with db.lectura() as s:
    propios = [t for t, _d in turnos.turnos_de_activo(s, a.id)] or list(s.scalars(select(Turno).where(Turno.activo.is_(True))))
    if not propios:
        st.error("No hay turnos cargados. El jefe los carga en la planilla (hoja 'turnos').")
        st.stop()
    opciones = [(f, t) for f in (hoy, hoy - timedelta(days=1)) for t in sorted(propios, key=lambda t: t.hora_inicio)]
    defecto = turnos.turno_por_defecto(s, F.ahora_local(), tz, [t.id for t in propios])
indice = next((i for i, (f, t) in enumerate(opciones) if defecto and f == defecto[0] and t.id == defecto[1].id), 0)
fecha, turno = st.selectbox("Turno", opciones, index=indice, format_func=lambda o: turnos.etiqueta(o[0], o[1], hoy))

with db.lectura() as s:
    sugerencia = registro.sugerencia_parte(s, a.id, fecha, turno, tz)
if sugerencia.get("hubo_aviso"):
    st.info("Hubo un aviso de falla en este turno: te propongo las horas de parada.")
ESTADOS = {"Operó todo": EstadoParte.TODO, "Operó parcial": EstadoParte.PARCIAL, "No operó": EstadoParte.NO_OPERO}
defecto_estado = next((k for k, v in ESTADOS.items() if v == sugerencia.get("estado")), "Operó todo")
estado_txt = st.segmented_control("¿Cómo operó?", list(ESTADOS), default=defecto_estado, key=f"estado_{codigo}_{fecha}_{turno.id}")
estado = ESTADOS.get(estado_txt or "Operó todo")

horas, id_motivo = 0.0, None
nombres = {m.descripcion: m.id for m in motivos}
if estado == EstadoParte.PARCIAL:
    pasos = [x / 2 for x in range(1, int(turno.duracion_h * 2))]
    horas = st.select_slider("Horas sin operar", pasos, value=min(pasos, key=lambda x: abs(x - sugerencia.get("horas_no_operadas", 1.0))))
if estado != EstadoParte.TODO:
    sug_motivo = next((d for d, i in nombres.items() if i == sugerencia.get("id_motivo")), None)
    elegido = st.pills("Motivo", list(nombres), selection_mode="single", default=sug_motivo)
    id_motivo = nombres.get(elegido) if elegido else None
cantidad = None
if a.unidad_produccion != UnidadProduccion.NINGUNA:
    cantidad = st.number_input(f"Cantidad procesada ({a.unidad_produccion.value.lower()}, opcional)", min_value=0.0,
                               value=None, step=1.0)

if st.button("Guardar parte", type="primary", width="stretch"):
    try:
        with db.escritura(usuario_id=u["id"]) as s:
            registro.registrar_parte(s, u["id"], a.id, fecha, turno.id, estado, horas, id_motivo, cantidad,
                                     F.token("parte"), tz=tz)
        F.renovar_token("parte")
        F.recordar_maquina(codigo)
        F.guardar_mensaje_ok("parte", f"Parte de {codigo} guardado ({turnos.etiqueta(fecha, turno, hoy)}).")
        st.rerun()
    except (registro.ErrorRegistro, PermissionError) as e:
        st.error(str(e))
