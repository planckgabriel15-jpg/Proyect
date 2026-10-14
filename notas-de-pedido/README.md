# Notas de pedido – Zinguería (prototipo)

Programa web para reemplazar la nota de pedido en papel. El vendedor elige la pieza, carga las medidas y el programa calcula solo el desarrollo, la banda y el código. Después imprime una nota prolija para producción.

> **Estado:** Etapa A terminada (estructura, datos de ejemplo, lógica de cálculo y pruebas).
> Las pantallas llegan en las etapas B a F. La guía completa para usarlo llega en la Etapa G.

## Qué hace falta

- **Node.js 20 o más nuevo**, solo para correr las pruebas y el generador de códigos. No hay que instalar nada más: el proyecto no tiene dependencias.
- Un navegador moderno (Chrome o Edge recomendados).

## Cómo correr las pruebas

```bash
cd notas-de-pedido
npm test            # es lo mismo que: node --test
```

Tienen que salir todas en verde (`# fail 0`). Los 16 casos obligatorios de la especificación están en `tests/casos-obligatorios.test.js`.

## Cómo abrir el programa

Los módulos de JavaScript necesitan un servidor. No alcanza con hacer doble clic en `index.html`.

```bash
cd notas-de-pedido
npx serve .                 # o bien:  python3 -m http.server 8000
```

Después se abre en el navegador la dirección que muestra la terminal, por ejemplo http://localhost:3000 o http://localhost:8000.

## Cómo regenerar la tabla de códigos de ejemplo

```bash
npm run generar-codigos     # es lo mismo que: node herramientas/generar-codigos-ejemplo.js
```

Cuando llegue la lista real del sistema de facturación, se reemplaza `datos/codigos.json`. También se va a poder importar desde la pantalla Configuración (Etapa F).

## Cómo está organizado

| Carpeta | Qué tiene |
|---|---|
| `datos/` | Archivos JSON que el negocio puede cambiar sin tocar código: límites, materiales, catálogo, códigos, sucursales, vendedores y glosario |
| `src/logica/` | Cálculos puros: desarrollo, banda, código, geometría, corte láser, descripción, validaciones y numeración. No usan el navegador; se prueban con `node --test` |
| `src/datos/almacenamiento.js` | **Única puerta** para guardar y leer. Hoy usa el navegador (localStorage); mañana, Google Apps Script |
| `src/pantallas/`, `src/vistas2d/`, `src/vistas3d/`, `src/estilos/` | Interfaz (etapas B a F) |
| `herramientas/` | Script que arma la tabla de códigos de ejemplo |
| `tests/` | Pruebas automáticas |
| `docs/ESPECIFICACION.md` | La especificación original del proyecto |

## Supuestos

Todo valor que no confirmó la empresa está marcado como **SUPUESTO** en `PENDIENTES.md`, con el archivo donde se cambia.
