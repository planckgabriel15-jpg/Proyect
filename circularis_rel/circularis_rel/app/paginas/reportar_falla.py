"""Reportar falla: menos de 60 s (Plan §10). Máquina, síntoma, ¿paró?, hora, foto y observación."""

from datetime import timedelta

import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.app.componentes import formularios as F
from circularis_rel.datos.enums import TipoCatalogo
from circularis_rel.datos.modelos import Catalogo
from circularis_rel.servicios import fotos, registro

u = contexto.usuario()
db = contexto.db()
st.header("🛠️ Reportar falla")
F.mensaje_ok("aviso")

with db.lectura() as s:
    maquinas = registro.maquinas_permitidas(s, u["id"])
    sintomas = list(s.scalars(select(Catalogo).where(Catalogo.tipo == TipoCatalogo.SINTOMA, Catalogo.activo.is_(True))
                              .order_by(Catalogo.id)))
if not maquinas:
    st.warning("No tenés máquinas asignadas. Pedíselo al jefe de mantenimiento.")
    st.stop()

codigos = [a.codigo for a in maquinas]
codigo = st.selectbox("Máquina", codigos, index=F.indice_maquina(codigos),
                      format_func=lambda c: f"{c} · {next(a.nombre for a in maquinas if a.codigo == c)}")
etiquetas = {f"{x.icono or ''} {x.descripcion}".strip(): x.id for x in sintomas}
sintoma = st.pills("¿Qué pasa?", list(etiquetas), selection_mode="single")
paro = st.segmented_control("¿Paró la máquina?", ["Sí, paró", "No, sigue andando"], default="Sí, paró")
ahora = F.ahora_local()
hora = st.time_input("Hora de la falla", ahora.time().replace(second=0, microsecond=0), step=300)
foto = st.file_uploader("Foto (opcional)", type=["jpg", "jpeg", "png", "webp"])
obs = st.text_input("Observación (opcional)")

momento = F.combinar(ahora.date(), hora)
if momento > ahora + timedelta(minutes=5):  # hora de ayer (turno noche)
    momento -= timedelta(days=1)

if st.button("Enviar aviso", type="primary", width="stretch", disabled=sintoma is None):
    a = next(x for x in maquinas if x.codigo == codigo)
    with db.lectura() as s:
        recientes = registro.avisos_recientes(s, a.id, momento)
    if recientes and not st.session_state.get("confirmar_duplicado"):
        st.session_state["confirmar_duplicado"] = True
        st.warning(f"Ya hay un aviso de {codigo} de hace pocos minutos. Si es OTRA falla, tocá *Enviar aviso* de nuevo.")
        st.stop()
    try:
        ruta = fotos.guardar(foto.getvalue(), contexto.config().dir_fotos) if foto else None
        with db.escritura(usuario_id=u["id"]) as s:
            ev = registro.crear_aviso(s, u["id"], a.id, etiquetas[sintoma], momento, paro == "Sí, paró", ruta, obs,
                                      F.token("aviso"))
            numero = ev.id
        F.renovar_token("aviso")
        F.recordar_maquina(codigo)
        st.session_state.pop("confirmar_duplicado", None)
        F.guardar_mensaje_ok("aviso", f"Aviso n.º {numero} enviado. Le llega al encargado.")
        st.rerun()
    except (registro.ErrorRegistro, fotos.FotoInvalida, PermissionError) as e:
        st.error(str(e))
