"""Tarjetas de mantenimiento autónomo (UNIDAD 4): azul la resuelve el operario, roja va a mantenimiento,
verde es una mejora (no es una anomalía)."""

import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.app.componentes import formularios as F
from circularis_rel.datos.modelos import PosicionComponente, TipoComponente
from circularis_rel.servicios import fotos, registro

u = contexto.usuario()
db = contexto.db()
st.header("🏷️ Tarjeta")
F.mensaje_ok("tarjeta")

COLORES = {"🟦 Azul: la arreglo yo": "AZUL", "🟥 Roja: necesita a mantenimiento": "ROJA", "🟩 Verde: idea de mejora": "VERDE"}
LISTAS = {"AZUL": registro.ANOMALIAS_AZUL, "ROJA": registro.ANOMALIAS_ROJA, "VERDE": registro.MEJORAS_VERDE}

with db.lectura() as s:
    maquinas = registro.maquinas_permitidas(s, u["id"])
if not maquinas:
    st.warning("No tenés máquinas asignadas.")
    st.stop()
color_txt = st.segmented_control("Tipo de tarjeta", list(COLORES), default=list(COLORES)[0])
color = COLORES[color_txt or list(COLORES)[0]]
codigos = [a.codigo for a in maquinas]
codigo = st.selectbox("Máquina", codigos, index=F.indice_maquina(codigos))
a = next(x for x in maquinas if x.codigo == codigo)
anomalia = st.pills("¿Qué encontraste?" if color != "VERDE" else "¿Qué mejora proponés?", LISTAS[color], selection_mode="single")
with db.lectura() as s:
    posiciones = {f"{p.codigo} · {t.nombre}": p.id for p, t in s.execute(
        select(PosicionComponente, TipoComponente).join(TipoComponente, TipoComponente.id == PosicionComponente.id_tipo_componente)
        .where(PosicionComponente.id_activo == a.id).order_by(PosicionComponente.codigo))}
pos = st.selectbox("Componente (opcional)", ["—", *posiciones])
foto = st.file_uploader("Foto (opcional)", type=["jpg", "jpeg", "png", "webp"])
obs = st.text_input("Observación (opcional)")

if st.button("Guardar tarjeta", type="primary", width="stretch", disabled=anomalia is None):
    try:
        ruta = fotos.guardar(foto.getvalue(), contexto.config().dir_fotos) if foto else None
        with db.escritura(usuario_id=u["id"]) as s:
            t = registro.crear_tarjeta(s, u["id"], color, a.id, anomalia, posiciones.get(pos), ruta, obs, F.token("tarjeta"))
            texto = {"AZUL": "Tarjeta azul guardada.", "ROJA": f"Tarjeta roja guardada: generó el aviso n.º {t.id_evento_generado}.",
                     "VERDE": "Idea de mejora guardada. ¡Gracias!"}[color]
        F.renovar_token("tarjeta")
        F.guardar_mensaje_ok("tarjeta", texto)
        st.rerun()
    except (registro.ErrorRegistro, fotos.FotoInvalida, PermissionError) as e:
        st.error(str(e))
