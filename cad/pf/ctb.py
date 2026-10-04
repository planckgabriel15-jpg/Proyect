"""PF-IRAM-MONO.ctb: impresión monocroma con espesores por objeto (capa).

- Los 255 colores ACI se imprimen en negro, con el espesor del objeto ("use object").
- ACI 8 (existente: H°, cerramiento, columnas, terreno, ocultos) se imprime en gris (intensidad 60 %).
- ACI 9 (rayado de existentes) se imprime en gris (intensidad 50 %).
- ACI 10 (recorrido del producto: FLUJO y PASO-RECORRIDO) conserva su color: rojo.
"""
from ezdxf.addons import acadctb

from . import config as C


def crear_ctb(ruta):
    ctb = acadctb.new_ctb()
    ctb.description = 'PF IRAM monocromo — UTN FRC Proyecto Final Redler AGD'
    for aci in range(1, 256):
        st = ctb[aci]
        st.color = (0, 0, 0)
        st.set_lineweight(0.0)          # usar el espesor del objeto
        st.screen = 100
        st.dithering = True
        st.grayscale = False
    ctb[8].screen = 60
    ctb[9].screen = 50
    ctb[C.ACI_FLUJO].set_object_color()
    ctb.save(ruta)
    return ctb
