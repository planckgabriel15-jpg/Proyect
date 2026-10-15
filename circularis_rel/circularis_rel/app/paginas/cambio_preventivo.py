"""Registrar un cambio sin falla: preventivo u otro retiro (queda como suspensión para Weibull)."""

import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.app.componentes import formularios as F
from circularis_rel.datos.modelos import Activo, PosicionComponente, Repuesto, TipoComponente
from circularis_rel.servicios import ot, registro
from circularis_rel.servicios.permisos import Accion, requerir

u = contexto.usuario()
requerir(u["rol"], Accion.CERRAR_OT)
db = contexto.db()
st.header("🔁 Cambio preventivo o retiro")
st.caption("Para cambios hechos **sin falla**. Para Weibull cuentan como suspensión (el componente no llegó a fallar).")
F.mensaje_ok("cambio")
with db.lectura() as s:
    maquinas = list(s.scalars(select(Activo).where(Activo.activo.is_(True)).order_by(Activo.codigo)))
    repuestos = {f"{r.codigo} · {r.descripcion}": r.id for r in s.scalars(select(Repuesto).order_by(Repuesto.codigo))}
codigos = [a.codigo for a in maquinas]
codigo = st.selectbox("Máquina", codigos, index=F.indice_maquina(codigos))
a = next(x for x in maquinas if x.codigo == codigo)
with db.lectura() as s:
    posiciones = {f"{p.codigo} · {t.nombre}": p.id for p, t in s.execute(
        select(PosicionComponente, TipoComponente).join(TipoComponente, TipoComponente.id == PosicionComponente.id_tipo_componente)
        .where(PosicionComponente.id_activo == a.id).order_by(PosicionComponente.codigo))}
pos = st.selectbox("Componente", list(posiciones))
tipo = st.segmented_control("Tipo de cambio", ["Preventivo", "Otro retiro"], default="Preventivo")
ahora = F.ahora_local()
c1, c2 = st.columns(2)
fecha = c1.date_input("Fecha", ahora.date(), format="DD/MM/YYYY")
hora = c2.time_input("Hora", ahora.time().replace(second=0, microsecond=0), step=300)
hh = st.number_input("Horas-hombre", min_value=0.0, value=None, step=0.5)
usados = st.multiselect("Repuestos usados", list(repuestos))
if st.button("Registrar cambio", type="primary", width="stretch", disabled=pos is None):
    try:
        with db.escritura(usuario_id=u["id"]) as s:
            o = ot.registrar_cambio(s, u["id"], posiciones[pos], F.combinar(fecha, hora), preventivo=tipo != "Otro retiro",
                                    hh=hh, repuestos=[(repuestos[r], 1.0) for r in usados])
            numero = o.numero
        F.guardar_mensaje_ok("cambio", f"{numero} registrada. Queda para validar por el jefe.")
        st.rerun()
    except (registro.ErrorRegistro, PermissionError, ValueError) as e:
        st.error(str(e))
