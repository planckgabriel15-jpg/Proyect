"""Configuración de la plantilla PF-IRAM-A3 (capas, estilos, formato y rótulo).

Todas las medidas en mm. En el espacio papel 1 unidad = 1 mm de lámina.
"""

# ---------------------------------------------------------------- proyecto
PROYECTO = {
    'encabezado': 'UTN — Facultad Regional Córdoba · Ingeniería Industrial · Proyecto Final',
    'sistema': 'Sistema de distribución de fertilizantes a granel — Redler — AGD Río Primero',
    'integrantes': 'Fernández · Planckensteiner · Quiroga Palacio · Solera',
    'dibujo': 'Gabriel Planckensteiner',
    'verifico': 'Ing. R. Bonaiuti',
    'tutor': 'C. D. Solera (AGD)',
    'n_proyecto': 'PF-26-AGD01',
    'archivo': 'PLANOS_AGD-2026.dwg',
    'fecha': '03/10/2026',
    'rev': 'E',
    'total_laminas': 14,
    'unidad': 'm / mm',
    'unidad_nota': 'cotas en m salvo indicación',
    'rev_desc': 'Emisión tercera entrega',
}

# ---------------------------------------------------------------- capas
# nombre: (color ACI, espesor mm o None = por defecto, tipo de línea, imprime, descripción)
CONT = 'Continuous'
ISO02 = 'ACAD_ISO02W100'
ISO04 = 'ACAD_ISO04W100'

CAPAS = [
    ('G-MARCO', 7, 0.70, CONT, True, 'Recuadro y marcas de centrado'),
    ('G-ROTULO', 7, 0.35, CONT, True, 'Rótulo, lista de materiales, tabla de revisiones'),
    ('G-VENTANAS', 8, 0.13, CONT, False, 'Viewports'),
    ('G-EJES', 1, 0.18, ISO04, True, 'Ejes de líneas, columnas, tabiques y piezas'),
    ('EX-HORMIGON-CORTE', 8, 0.35, CONT, True, 'H° existente cortado'),
    ('EX-HORMIGON-VISTA', 8, 0.25, CONT, True, 'H° existente en vista'),
    ('EX-MADERA', 32, 0.25, CONT, True, 'Machimbre, cabios, correas y viga de madera'),
    ('EX-CERRAMIENTO', 8, 0.25, CONT, True, 'Chapa de muros y cubierta'),
    ('EX-COLUMNAS', 8, 0.35, CONT, True, 'Columnas existentes'),
    ('EX-TERRENO', 8, 0.18, CONT, True, 'Terreno natural y relleno'),
    ('NU-REDLER-CONDUCTO', 5, 0.50, CONT, True, 'Conducto, bridas, tapa y divisor'),
    ('NU-REDLER-MECANICO', 4, 0.35, CONT, True, 'Cabezal, cola, ruedas, ejes, cadena, paletas y motorreductor'),
    ('NU-COMPUERTAS', 150, 0.35, CONT, True, 'Placa guillotina, guías, pantalón, brazos y actuador'),
    ('NU-ESTRUCT-CORTE', 1, 0.50, CONT, True, 'Perfiles y chapas nuevas cortadas'),
    ('NU-ESTRUCT-VISTA', 1, 0.35, CONT, True, 'Perfiles y chapas nuevas en vista'),
    ('NU-APOYOS', 1, 0.35, CONT, True, 'Placas, asientos, PTFE, cartelas y dados'),
    ('NU-PASARELA', 2, 0.35, CONT, True, 'Ménsulas, rejilla, larguero y rodapié'),
    ('NU-BARANDA', 2, 0.25, CONT, True, 'Montantes, pasamanos y travesaños'),
    ('NU-ESCALERA', 2, 0.35, CONT, True, 'Escalera exterior y marinera'),
    ('NU-PLATAFORMA', 2, 0.35, CONT, True, 'Plataforma exterior, postes y vigas'),
    ('NU-ELEVADOR', 1, 0.50, CONT, True, 'Bota, cuerpo, cabeza, desviador y chutes'),
    ('NU-RECEPCION', 6, 0.50, CONT, True, 'Fosa, tolva, reja, banda, tapa y sumidero'),
    ('NU-ELECTRICO', 3, 0.25, CONT, True, 'Bandejas portacables y sensores'),
    ('NU-BULONES-SOLD', 1, 0.18, CONT, True, 'Bulones, anclajes y símbolos de soldadura'),
    ('AN-OCULTO', 8, 0.25, ISO02, True, 'Aristas ocultas'),
    ('AN-RAYADO-EX', 9, 0.13, CONT, True, 'Rayados de elementos existentes'),
    ('AN-RAYADO-NU', 1, 0.13, CONT, True, 'Rayados de elementos nuevos'),
    ('AN-COTAS', 3, 0.18, CONT, True, 'Cotas'),
    ('AN-NIVELES', 3, 0.18, CONT, True, 'Símbolos de nivel'),
    ('AN-REFERENCIAS', 3, 0.18, CONT, True, 'Multileaders y globos'),
    ('AN-TEXTOS', 7, 0.25, CONT, True, 'Títulos de vista y notas técnicas'),
    ('AN-CORTES-LLAMADAS', 1, 0.18, ISO04, True, 'Líneas de corte y llamadas de detalle (extremos 0,70)'),
    ('AN-TABLAS', 7, 0.25, CONT, True, 'Tablas y listas'),
    ('AN-FLUJO', 1, 0.35, CONT, True, 'Flechas y numeración del recorrido del producto'),
    ('AN-IMAGENES', 7, None, CONT, True, 'Fotos del relevamiento'),
    ('AN-NOPLOT', 8, None, CONT, False, 'Auxiliares, zonas y verificación'),
    # sólidos de ISO-13 (mismo color que su sistema 2D)
    ('3D-GALPON', 8, 0.25, CONT, True, 'Sólidos ISO-13: galpón existente'),
    ('3D-REDLER', 5, 0.25, CONT, True, 'Sólidos ISO-13: conductos, cabezales y colas'),
    ('3D-COMPUERTAS', 150, 0.25, CONT, True, 'Sólidos ISO-13: compuertas y pantalones'),
    ('3D-ESTRUCT', 1, 0.25, CONT, True, 'Sólidos ISO-13: viga carrilera y apoyos'),
    ('3D-PASARELA', 2, 0.25, CONT, True, 'Sólidos ISO-13: pasarelas, plataforma y escalera'),
    ('3D-ELEVADOR', 1, 0.25, CONT, True, 'Sólidos ISO-13: elevador, desviador y chutes'),
    ('3D-RECEPCION', 6, 0.25, CONT, True, 'Sólidos ISO-13: fosa y tolva'),
]

# ---------------------------------------------------------------- tipos de línea (acadiso.lin)
TIPOS_LINEA = [
    # nombre, descripción, patrón ezdxf [largo total, trazo, -hueco, ...]
    (ISO02, 'ISO dash __ __ __ __ __ __ __ __ __ __ __ __ __', [15.0, 12.0, -3.0]),
    (ISO04, 'ISO long-dash dot ____ . ____ . ____ . ____ . _', [30.0, 24.0, -3.0, 0.0, -3.0]),
]

# ---------------------------------------------------------------- texto (IRAM 4503 / ISO 3098 B)
FUENTE_TTF = 'isocpeur.ttf'      # TrueType: el PDF conserva el texto como texto
FAMILIA_TTF = 'ISOCPEUR'
H_TXT = 2.5        # cotas, referencias, tablas
H_TIT = 3.5        # títulos de vista y encabezados
H_ROT_TIT = 5.0    # título del rótulo
H_COD = 7.0        # código de lámina
AVANCE = 0.80      # avance medio estimado por carácter / altura (estimación conservadora)

# ---------------------------------------------------------------- formato A3 (IRAM 4504)
PAPEL = (420.0, 297.0)
MARGEN_IZQ, MARGEN = 25.0, 10.0
MARCO = (MARGEN_IZQ, MARGEN, PAPEL[0] - MARGEN, PAPEL[1] - MARGEN)   # x0, y0, x1, y1
ROT_ANCHO = 175.0
