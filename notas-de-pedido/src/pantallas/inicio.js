// =============================================================
// inicio.js
// Pantalla de inicio: vendedor y sucursal de hoy, botón "Nueva nota de
// pedido" y la lista de notas de la sucursal con buscador y filtro por fecha.
// También tiene la pantalla de ingreso (elegir vendedor).
// =============================================================

import { h, selector, fechaCorta, confirmar, mostrarAviso } from './util.js';
import { estado, ir, vendedorActual, sucursalActual } from './estado.js';
import * as almacenamiento from '../datos/almacenamiento.js';

/** Ingreso del prototipo: elegir el vendedor de una lista. (Con Google será la cuenta de la empresa.) */
export async function pantallaIngreso(contenedor) {
  const { datos } = estado;
  const grupos = datos.sucursales.map((s) => ({
    sucursal: s,
    vendedores: datos.vendedores.filter((v) => v.sucursalHabitualId === s.id),
  }));
  const lista = h('select', { class: 'selector-grande', 'aria-label': 'Vendedor', size: 1 },
    h('option', { value: '' }, '— Elegí tu nombre —'),
    grupos.map((g) => h('optgroup', { label: g.sucursal.nombre },
      g.vendedores.map((v) => h('option', { value: v.id, selected: v.id === estado.sesion?.vendedorId }, v.nombre)))));
  contenedor.replaceChildren(h('section', { class: 'panel panel-ingreso' },
    h('h1', {}, '¿Quién sos?'),
    h('p', {}, 'Elegí tu nombre. Se va a usar tu sucursal habitual (la podés cambiar por hoy).'),
    lista,
    h('button', {
      type: 'button', class: 'boton grande principal',
      onclick: async () => {
        const vendedor = datos.vendedores.find((v) => v.id === lista.value);
        if (!vendedor) { mostrarAviso('Elegí un nombre de la lista', 'error'); return; }
        estado.sesion = { vendedorId: vendedor.id, sucursalHoyId: vendedor.sucursalHabitualId };
        await almacenamiento.guardarSesion(estado.sesion);
        ir('#inicio');
      },
    }, 'Entrar')));
  return () => {};
}

export async function pantallaInicio(contenedor) {
  const { datos } = estado;
  const vendedor = vendedorActual();
  const sucursal = sucursalActual();

  // ---------- cabecera ----------
  const selectorSucursal = selector(datos.sucursales.map((s) => ({ valor: s.id, texto: s.nombre })), estado.sesion.sucursalHoyId, {
    'aria-label': 'Sucursal de hoy',
    onchange: async (e) => {
      estado.sesion.sucursalHoyId = e.target.value;
      await almacenamiento.guardarSesion(estado.sesion);
      mostrarAviso(`Hoy trabajás en ${datos.sucursales.find((s) => s.id === e.target.value).nombre}`, 'ok');
      pantallaInicio(contenedor);
    },
  });
  selectorSucursal.hidden = true;

  const cabecera = h('section', { class: 'panel cabecera-inicio' },
    h('div', {},
      h('div', { class: 'texto-chico' }, 'Vendedor'),
      h('strong', { class: 'dato-grande' }, vendedor?.nombre || '—'),
      ' ', h('a', { href: '#ingreso', class: 'enlace-chico' }, 'cambiar')),
    h('div', {},
      h('div', { class: 'texto-chico' }, 'Sucursal de hoy'),
      h('strong', { class: 'dato-grande' }, sucursal?.nombre || '—'), ' ',
      h('button', { type: 'button', class: 'boton chico', onclick: () => { selectorSucursal.hidden = !selectorSucursal.hidden; selectorSucursal.focus(); } }, 'Cambiar sucursal de hoy'),
      selectorSucursal));

  // ---------- filtros y lista ----------
  const campoTexto = h('input', { type: 'search', class: 'buscador', placeholder: 'Buscar por cliente, número o factura', 'aria-label': 'Buscar notas', oninput: () => llenar() });
  const campoDesde = h('input', { type: 'date', 'aria-label': 'Desde', onchange: () => llenar() });
  const campoHasta = h('input', { type: 'date', 'aria-label': 'Hasta', onchange: () => llenar() });
  const selectorEstado = selector([{ valor: '', texto: 'Todas' }, { valor: 'borrador', texto: 'Borradores' }, { valor: 'emitida', texto: 'Emitidas' }], '', { 'aria-label': 'Estado', onchange: () => llenar() });
  const lista = h('div', { class: 'lista-notas' });

  async function llenar() {
    const notas = await almacenamiento.listarNotas({
      sucursalId: estado.sesion.sucursalHoyId,
      texto: campoTexto.value,
      desde: campoDesde.value || null,
      hasta: campoHasta.value || null,
      estado: selectorEstado.value || null,
    });
    lista.replaceChildren();
    if (!notas.length) {
      lista.append(h('p', { class: 'vacio' }, 'No hay notas con esos filtros.'));
      return;
    }
    lista.append(h('table', { class: 'tabla-notas' },
      h('thead', {}, h('tr', {}, h('th', {}, 'Estado'), h('th', {}, 'NP Nº'), h('th', {}, 'Fecha'), h('th', {}, 'Cliente'), h('th', {}, 'Factura'), h('th', {}, 'Piezas'), h('th', {}, ''))),
      h('tbody', {}, notas.map((n) => h('tr', {},
        h('td', {}, h('span', { class: `etiqueta-estado ${n.estado}` }, n.estado === 'emitida' ? 'EMITIDA' : 'borrador')),
        h('td', {}, n.numero ? String(n.numero) : '—'),
        h('td', {}, fechaCorta(n.fechaEmision || n.fechaModificacion || n.fechaCreacion)),
        h('td', {}, n.cliente || '(sin cliente)'),
        h('td', {}, n.factura || '—'),
        h('td', {}, String(n.renglones?.length || 0)),
        h('td', { class: 'acciones' },
          h('a', { class: 'boton chico', href: n.estado === 'emitida' ? `#imprimir/${n.id}` : `#nota/${n.id}` }, n.estado === 'emitida' ? 'Ver / imprimir' : 'Abrir'),
          n.estado === 'borrador' ? h('button', {
            type: 'button', class: 'boton chico peligro',
            onclick: async () => {
              if (!confirmar(`¿Borrar el borrador de "${n.cliente || 'sin cliente'}"?`)) return;
              await almacenamiento.borrarBorrador(n.id);
              llenar();
            },
          }, 'Borrar') : null))))));
  }

  contenedor.replaceChildren(
    cabecera,
    h('a', { href: '#nota/nueva', class: 'boton enorme principal' }, '+ Nueva nota de pedido'),
    h('section', { class: 'panel' },
      h('h2', {}, `Notas de ${sucursal?.nombre || 'la sucursal'}`),
      h('div', { class: 'filtros' }, campoTexto, h('label', {}, 'Desde ', campoDesde), h('label', {}, 'Hasta ', campoHasta), selectorEstado),
      lista));
  await llenar();
  return () => {};
}
