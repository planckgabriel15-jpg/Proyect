// =============================================================
// configuracion.js
// Configuración (protegida con una clave fija de prototipo, ver config.json):
// - Sucursales: nombre, letra y último número de NP (para seguir el talonario).
// - Códigos: ver la tabla e importar la lista real (JSON o CSV).
// - Materiales y plantillas: solo para ver.
// - Datos: bajar una copia de seguridad o borrar las notas de prueba.
// =============================================================

import { h, mostrarAviso, confirmar } from './util.js';
import { estado } from './estado.js';
import * as almacenamiento from '../datos/almacenamiento.js';
import { convertirCsvEnTabla } from '../logica/codigos.js';
import { calcularDesarrollo } from '../logica/desarrollo.js';
import { siguienteNumeroNP } from '../logica/numeracion.js';
import { formatearCorto } from '../logica/numeros.js';

let desbloqueada = false; // vale mientras no se recargue la página

export async function pantallaConfiguracion(contenedor) {
  if (!desbloqueada) {
    const campoClave = h('input', { type: 'password', class: 'selector-grande', placeholder: 'Clave', 'aria-label': 'Clave de configuración' });
    const entrar = () => {
      if (campoClave.value === estado.datos.config.claveConfiguracion) {
        desbloqueada = true;
        pantallaConfiguracion(contenedor);
      } else {
        mostrarAviso('Clave incorrecta', 'error');
      }
    };
    campoClave.addEventListener('keydown', (e) => { if (e.key === 'Enter') entrar(); });
    contenedor.replaceChildren(h('section', { class: 'panel panel-ingreso' },
      h('h1', {}, 'Configuración'), h('p', {}, 'Ingresá la clave de configuración.'), campoClave,
      h('button', { type: 'button', class: 'boton grande principal', onclick: entrar }, 'Entrar')));
    campoClave.focus();
    return () => {};
  }

  const pestanas = [
    ['sucursales', 'Sucursales'], ['codigos', 'Códigos'], ['materiales', 'Materiales'], ['plantillas', 'Plantillas'], ['datos', 'Datos'],
  ];
  const cuerpo = h('div', { class: 'cuerpo-config' });
  const barra = h('div', { class: 'pestanas', role: 'tablist' }, pestanas.map(([id, texto]) =>
    h('button', { type: 'button', role: 'tab', class: 'pestana', 'data-id': id, onclick: () => mostrar(id) }, texto)));

  async function mostrar(id) {
    barra.querySelectorAll('.pestana').forEach((b) => b.classList.toggle('activa', b.dataset.id === id));
    cuerpo.replaceChildren();
    if (id === 'sucursales') await seccionSucursales(cuerpo);
    if (id === 'codigos') seccionCodigos(cuerpo);
    if (id === 'materiales') seccionMateriales(cuerpo);
    if (id === 'plantillas') seccionPlantillas(cuerpo);
    if (id === 'datos') seccionDatos(cuerpo);
  }

  contenedor.replaceChildren(h('section', { class: 'panel' }, h('h1', {}, 'Configuración'), barra, cuerpo));
  await mostrar('sucursales');
  return () => {};
}

async function recargarDatos() {
  estado.datos = await almacenamiento.cargarDatosBase();
}

// ---------- Sucursales ----------
async function seccionSucursales(cuerpo) {
  const { datos } = estado;
  const contadores = await almacenamiento.leerContadores(datos.sucursales);
  const filas = datos.sucursales.map((s) => ({
    sucursal: { ...s },
    campoNombre: h('input', { type: 'text', value: s.nombre }),
    campoLetra: h('input', { type: 'text', value: s.letra, maxlength: 3, class: 'campo-angulo' }),
    campoUltimo: h('input', { type: 'text', inputmode: 'numeric', value: String(contadores[s.id] ?? 0), class: 'campo-medida' }),
  }));
  cuerpo.append(
    h('p', {}, 'El "último número usado" sirve para seguir desde el talonario de papel: la próxima nota sale con ese número + 1. ',
      h('strong', {}, 'Las letras son de ejemplo (SUPUESTO).')),
    h('div', { class: 'tabla-desplazable' }, h('table', { class: 'tabla-notas' },
      h('thead', {}, h('tr', {}, h('th', {}, 'Sucursal'), h('th', {}, 'Letra'), h('th', {}, 'Último NP usado'), h('th', {}, 'Próxima nota'))),
      h('tbody', {}, filas.map((f) => h('tr', {},
        h('td', {}, f.campoNombre), h('td', {}, f.campoLetra), h('td', {}, f.campoUltimo),
        h('td', {}, String(siguienteNumeroNP(contadores, f.sucursal.id)))))))),
    h('button', {
      type: 'button', class: 'boton grande principal',
      onclick: async () => {
        for (const f of filas) {
          const ultimo = Number(f.campoUltimo.value);
          if (!Number.isInteger(ultimo) || ultimo < 0) { mostrarAviso(`Número inválido en ${f.sucursal.nombre}`, 'error'); return; }
        }
        const nuevas = filas.map((f) => ({ ...f.sucursal, nombre: f.campoNombre.value.trim() || f.sucursal.nombre, letra: f.campoLetra.value.trim() }));
        await almacenamiento.guardarSucursales(nuevas);
        for (const f of filas) {
          const ultimo = Number(f.campoUltimo.value);
          if (ultimo !== contadores[f.sucursal.id]) await almacenamiento.fijarUltimoNumero(nuevas, f.sucursal.id, ultimo);
        }
        await recargarDatos();
        mostrarAviso('Sucursales guardadas', 'ok');
        cuerpo.replaceChildren();
        await seccionSucursales(cuerpo);
      },
    }, '💾 Guardar sucursales'));
}

// ---------- Códigos ----------
function seccionCodigos(cuerpo) {
  const { datos } = estado;
  const campoFiltro = h('input', { type: 'search', class: 'buscador', placeholder: 'Filtrar (ej. CG05)', oninput: () => llenar() });
  const tablaZona = h('div', { class: 'tabla-desplazable alta' });
  function llenar() {
    const texto = campoFiltro.value.toLowerCase();
    const filas = datos.codigos.filter((f) => Object.values(f).join(' ').toLowerCase().includes(texto)).slice(0, 300);
    tablaZona.replaceChildren(h('table', { class: 'tabla-notas' },
      h('thead', {}, h('tr', {}, ['elemento', 'material', 'espesor', 'terminacion', 'banda', 'codigo'].map((c) => h('th', {}, c)))),
      h('tbody', {}, filas.map((f) => h('tr', {}, ['elemento', 'material', 'espesor', 'terminacion', 'banda', 'codigo'].map((c) => h('td', {}, String(f[c] ?? ''))))))));
  }

  const archivo = h('input', {
    type: 'file', accept: '.json,.csv,application/json,text/csv',
    onchange: async (e) => {
      const elegido = e.target.files[0];
      if (!elegido) return;
      const texto = await elegido.text();
      let filas = [];
      let errores = [];
      try {
        if (elegido.name.toLowerCase().endsWith('.json')) {
          filas = JSON.parse(texto);
          if (!Array.isArray(filas) || !filas.every((f) => f.codigo && f.material)) throw new Error('El JSON tiene que ser una lista de filas con material, espesor, terminacion, banda y codigo');
          filas = filas.map((f) => ({ elemento: f.elemento || '*', material: String(f.material), espesor: String(f.espesor), terminacion: String(f.terminacion), banda: String(f.banda), codigo: String(f.codigo) }));
        } else {
          ({ filas, errores } = convertirCsvEnTabla(texto));
        }
      } catch (error) {
        mostrarAviso(`No se pudo leer el archivo: ${error.message}`, 'error', 8);
        return;
      }
      if (!filas.length) { mostrarAviso(`El archivo no tiene filas válidas. ${errores.join(' · ')}`, 'error', 8); return; }
      const detalle = errores.length ? `\n${errores.length} línea(s) con problemas se van a saltear.` : '';
      if (!confirmar(`Se van a importar ${filas.length} códigos y reemplazar la tabla actual.${detalle}\n¿Seguir?`)) return;
      await almacenamiento.guardarTablaCodigos(filas);
      await recargarDatos();
      mostrarAviso(`Importados ${filas.length} códigos`, 'ok');
      cuerpo.replaceChildren();
      seccionCodigos(cuerpo);
    },
  });

  cuerpo.append(
    h('p', {}, `La tabla tiene ${datos.codigos.length} códigos. Columnas: elemento, material, espesor, terminacion, banda, codigo. `,
      'Un elemento "*" sirve para cualquier pieza. El programa siempre BUSCA el código acá (no lo arma).'),
    h('div', { class: 'barra-botones' },
      h('label', { class: 'boton' }, '📂 Importar JSON o CSV… ', archivo),
      h('button', {
        type: 'button', class: 'boton',
        onclick: async () => {
          if (!confirmar('¿Volver a la tabla de ejemplo (datos/codigos.json)?')) return;
          await almacenamiento.descartarTablaCodigosImportada();
          await recargarDatos();
          cuerpo.replaceChildren();
          seccionCodigos(cuerpo);
        },
      }, 'Volver a la tabla de ejemplo')),
    campoFiltro, tablaZona);
  llenar();
}

// ---------- Materiales ----------
function seccionMateriales(cuerpo) {
  const { materiales } = estado.datos;
  const marca = (supuesto) => (supuesto ? ' (SUPUESTO)' : '');
  cuerpo.append(
    h('p', {}, 'Para cambiar estos datos se edita datos/materiales.json.'),
    h('h3', {}, 'Materiales'),
    h('table', { class: 'tabla-notas' }, h('tbody', {}, materiales.materiales.map((m) =>
      h('tr', {}, h('td', {}, m.nombre), h('td', {}, m.codigo + marca(m.supuesto)), h('td', {}, `Terminaciones: ${m.terminaciones.join(', ')}`))))),
    h('h3', {}, 'Calibres'),
    h('table', { class: 'tabla-notas' }, h('tbody', {}, materiales.calibres.map((c) =>
      h('tr', {}, h('td', {}, `C${c.numero}`), h('td', {}, `${formatearCorto(c.espesorMm)} mm`), h('td', {}, `código ${c.codigoEspesor}${marca(c.supuesto)}`), h('td', { class: 'texto-chico' }, c.fuente))))),
    h('h3', {}, 'Colores de prepintado (SUPUESTO)'),
    h('div', { class: 'muestras-color' }, materiales.colores.map((c) => h('span', { class: 'muestra-color' }, h('span', { class: 'cuadradito', style: `background:${c.hex}` }), c.nombre))));
}

// ---------- Plantillas ----------
function seccionPlantillas(cuerpo) {
  const { catalogo } = estado.datos;
  cuerpo.append(
    h('p', {}, `${catalogo.plantillas.length} plantillas. Para cambiarlas se edita datos/catalogo.json. Las "medidas de ejemplo" las tiene que validar producción.`),
    h('div', { class: 'tabla-desplazable alta' }, h('table', { class: 'tabla-notas' },
      h('thead', {}, h('tr', {}, h('th', {}, 'Grupo'), h('th', {}, 'Pieza'), h('th', {}, 'Tipo'), h('th', {}, 'Desarrollo'), h('th', {}, 'Medidas'), h('th', {}, 'Referencia'))),
      h('tbody', {}, catalogo.plantillas.map((p) => h('tr', {},
        h('td', {}, catalogo.grupos.find((g) => g.id === p.grupo)?.nombre),
        h('td', {}, p.nombre),
        h('td', {}, p.tipoPieza === 'plegada' ? 'plegada' : 'especial'),
        h('td', {}, p.tipoPieza === 'plegada' ? `${formatearCorto(calcularDesarrollo(p.perfil.tramos))} cm` : (p.calculoDesarrollo === 'unidad' ? 'por unidad' : 'fórmula')),
        h('td', {}, p.supuesto ? 'de ejemplo' : 'confirmadas'),
        h('td', { class: 'texto-chico' }, p.referencia)))))));
}

// ---------- Datos ----------
function seccionDatos(cuerpo) {
  cuerpo.append(
    h('p', {}, 'Las notas de este prototipo se guardan en ESTE navegador. Bajá una copia de seguridad de vez en cuando.'),
    h('div', { class: 'barra-botones' },
      h('button', {
        type: 'button', class: 'boton principal',
        onclick: async () => {
          const copia = await almacenamiento.exportarTodo();
          const enlace = h('a', {
            href: URL.createObjectURL(new Blob([JSON.stringify(copia, null, 2)], { type: 'application/json' })),
            download: `copia-notas-${new Date().toISOString().slice(0, 10)}.json`,
          });
          document.body.append(enlace);
          enlace.click();
          enlace.remove();
        },
      }, '⬇ Bajar copia de seguridad'),
      h('button', {
        type: 'button', class: 'boton peligro',
        onclick: async () => {
          if (!confirmar('¿Borrar TODAS las notas y los contadores de este navegador? No se puede deshacer.')) return;
          if (!confirmar('¿Seguro? Se pierden todas las notas guardadas acá.')) return;
          await almacenamiento.borrarNotasYContadores();
          mostrarAviso('Notas y contadores borrados', 'ok');
        },
      }, 'Borrar notas de prueba')));
}
