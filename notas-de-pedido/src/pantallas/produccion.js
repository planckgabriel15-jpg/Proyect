// =============================================================
// produccion.js
// Centro de PRODUCCIÓN, con pestañas según el rol:
//   jefe de producción: tablero, lotes, asignación, operarios y eficiencia, material,
//     indicadores, incidencias, parámetros de tiempos, demo y notas emitidas;
//   comercial: tablero (solo mirar, para saber cuándo está lista una nota) y notas emitidas.
// El operario tiene su propia pantalla (#operario).
// =============================================================

import { h, selector, fechaYHora } from './util.js';
import { estado, nombreSucursal } from './estado.js';
import * as almacenamiento from '../datos/almacenamiento.js';
import { esJefe } from './contextoProduccion.js';
import { seccionTablero } from './produccionTablero.js';
import { seccionLotes } from './produccionLotes.js';
import { seccionAsignacion } from './produccionAsignacion.js';
import { seccionOperarios } from './produccionOperarios.js';
import { seccionMaterial, seccionIndicadores, seccionIncidencias } from './produccionIndicadores.js';
import { seccionParametros } from './produccionParametros.js';
import { seccionDemo } from './produccionDemo.js';

const PESTANAS_JEFE = [
  ['tablero', 'Tablero', seccionTablero],
  ['lotes', 'Lotes (agrupar)', seccionLotes],
  ['asignacion', 'Asignación', seccionAsignacion],
  ['operarios', 'Operarios y eficiencia', seccionOperarios],
  ['material', 'Material', seccionMaterial],
  ['indicadores', 'Indicadores', seccionIndicadores],
  ['incidencias', 'Incidencias', seccionIncidencias],
  ['parametros', 'Parámetros de tiempos', seccionParametros],
  ['demo', 'Datos de demostración', seccionDemo],
  ['emitidas', 'Notas emitidas', seccionEmitidas],
];
const PESTANAS_COMERCIAL = [
  ['tablero', 'Tablero', seccionTablero],
  ['emitidas', 'Notas emitidas', seccionEmitidas],
];

let ultimaPestana = 'tablero';

export async function pantallaProduccion(contenedor, pestanaPedida) {
  const pestanas = esJefe() ? PESTANAS_JEFE : PESTANAS_COMERCIAL;
  const cuerpo = h('div', { class: 'cuerpo-produccion' });
  const barra = h('div', { class: 'pestanas pestanas-produccion', role: 'tablist' }, pestanas.map(([id, texto]) =>
    h('button', { type: 'button', role: 'tab', class: 'pestana', 'data-id': id, onclick: () => mostrar(id) }, texto)));
  let limpiar = () => {};

  async function mostrar(id) {
    limpiar();
    limpiar = () => {};
    ultimaPestana = id;
    barra.querySelectorAll('.pestana').forEach((b) => b.classList.toggle('activa', b.dataset.id === id));
    cuerpo.replaceChildren(h('p', { class: 'texto-chico' }, 'Calculando…'));
    const [, , funcion] = pestanas.find(([p]) => p === id) || pestanas[0];
    try {
      limpiar = (await funcion(cuerpo, { refrescar: () => mostrar(id), ir: mostrar })) || (() => {});
    } catch (error) {
      console.error(error);
      cuerpo.replaceChildren(h('div', { class: 'aviso-caja error-caja' }, `Ocurrió un error: ${error.message}`));
    }
  }

  contenedor.replaceChildren(h('section', { class: 'panel' },
    h('div', { class: 'titulo-pantalla' }, h('h1', {}, 'Producción'),
      h('span', { class: 'texto-chico' }, esJefe() ? 'Jefe de producción' : 'Vista del área comercial (solo mirar)')),
    barra, cuerpo));
  const inicial = pestanas.some(([p]) => p === pestanaPedida) ? pestanaPedida : (pestanas.some(([p]) => p === ultimaPestana) ? ultimaPestana : 'tablero');
  await mostrar(inicial);
  return () => limpiar();
}

/** Lista de notas emitidas de todas las sucursales (lo que había antes en Producción). */
async function seccionEmitidas(contenedor) {
  const { datos } = estado;
  const selectorSucursal = selector([{ valor: '', texto: 'Todas las sucursales' }].concat(datos.sucursales.map((s) => ({ valor: s.id, texto: s.nombre }))), '', {
    'aria-label': 'Sucursal', onchange: () => llenar(),
  });
  const campoTexto = h('input', { type: 'search', class: 'buscador', placeholder: 'Buscar por número, cliente o factura', 'aria-label': 'Buscar', oninput: () => llenar() });
  const campoDesde = h('input', { type: 'date', 'aria-label': 'Desde', onchange: () => llenar() });
  const campoHasta = h('input', { type: 'date', 'aria-label': 'Hasta', onchange: () => llenar() });
  const lista = h('div', { class: 'lista-notas' });

  async function llenar() {
    const notas = await almacenamiento.listarNotas({
      estado: 'emitida',
      sucursalId: selectorSucursal.value || null,
      texto: campoTexto.value,
      desde: campoDesde.value || null,
      hasta: campoHasta.value || null,
    });
    lista.replaceChildren(notas.length
      ? h('table', { class: 'tabla-notas' },
        h('thead', {}, h('tr', {}, h('th', {}, 'Sucursal'), h('th', {}, 'NP Nº'), h('th', {}, 'Emitida'), h('th', {}, 'Cliente'), h('th', {}, 'Factura'), h('th', {}, 'Renglones'), h('th', {}, 'Piezas'), h('th', {}, ''))),
        h('tbody', {}, notas.slice(0, 300).map((n) => h('tr', {},
          h('td', {}, nombreSucursal(n.sucursalId)),
          h('td', {}, h('strong', {}, String(n.numero)), n.demo ? h('span', { class: 'etiqueta-demo' }, 'DEMO') : null),
          h('td', {}, fechaYHora(n.fechaEmision)),
          h('td', {}, n.cliente),
          h('td', {}, n.factura),
          h('td', {}, String(n.renglones.length)),
          h('td', {}, String(n.renglones.reduce((s, r) => s + (Number(r.cantidad) || 0), 0))),
          h('td', {}, h('a', { class: 'boton chico principal', href: `#imprimir/${n.id}` }, 'Abrir e imprimir'))))))
      : h('p', { class: 'vacio' }, 'No hay notas emitidas con esos filtros.'));
    if (notas.length > 300) lista.append(h('p', { class: 'texto-chico' }, `Se muestran 300 de ${notas.length}: usá los filtros.`));
  }

  contenedor.replaceChildren(h('h2', {}, 'Notas emitidas'),
    h('div', { class: 'filtros' }, selectorSucursal, campoTexto, h('label', {}, 'Desde ', campoDesde), h('label', {}, 'Hasta ', campoHasta)),
    lista);
  await llenar();
}
