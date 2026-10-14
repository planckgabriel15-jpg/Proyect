// =============================================================
// produccion.js
// Lista para producción: notas EMITIDAS de todas las sucursales, con filtros
// por sucursal y fecha y búsqueda por número o cliente. Cada una se abre e
// imprime. (Los estados "pendiente / en producción / terminado / entregado"
// quedan para la etapa 2.)
// =============================================================

import { h, selector, fechaYHora } from './util.js';
import { estado, nombreSucursal } from './estado.js';
import * as almacenamiento from '../datos/almacenamiento.js';

export async function pantallaProduccion(contenedor) {
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
        h('thead', {}, h('tr', {}, h('th', {}, 'Sucursal'), h('th', {}, 'NP Nº'), h('th', {}, 'Emitida'), h('th', {}, 'Cliente'), h('th', {}, 'Factura'), h('th', {}, 'Piezas'), h('th', {}, ''))),
        h('tbody', {}, notas.map((n) => h('tr', {},
          h('td', {}, nombreSucursal(n.sucursalId)),
          h('td', {}, h('strong', {}, String(n.numero))),
          h('td', {}, fechaYHora(n.fechaEmision)),
          h('td', {}, n.cliente),
          h('td', {}, n.factura),
          h('td', {}, String(n.renglones.length)),
          h('td', {}, h('a', { class: 'boton chico principal', href: `#imprimir/${n.id}` }, 'Abrir e imprimir'))))))
      : h('p', { class: 'vacio' }, 'No hay notas emitidas con esos filtros.'));
  }

  contenedor.replaceChildren(h('section', { class: 'panel' },
    h('h1', {}, 'Lista para producción'),
    h('div', { class: 'filtros' }, selectorSucursal, campoTexto, h('label', {}, 'Desde ', campoDesde), h('label', {}, 'Hasta ', campoHasta)),
    lista));
  await llenar();
  return () => {};
}
