// =============================================================
// inicio.js
// Pantalla de inicio: vendedor y sucursal de hoy, botón "Nueva nota de
// pedido" y la lista de notas de la sucursal con buscador y filtro por fecha.
// También tiene la pantalla de ingreso (elegir vendedor).
// =============================================================

import { h, selector, fechaCorta, confirmar, mostrarAviso, logoDeEmpresa } from './util.js';
import { estado, ir, vendedorActual, sucursalActual, empresaActual } from './estado.js';
import { listaEmpresas, listaPlantas, sucursalesDeEmpresa, identificadorDeNota } from '../logica/empresas.js';
import { registrarAtajos, etiquetaAtajo } from './atajos.js';
import * as almacenamiento from '../datos/almacenamiento.js';

/**
 * Ingreso del prototipo: elegir el ROL y quién es. (Con Google será la cuenta de la empresa.)
 * - Comercial: elige su nombre (vendedor) → carga notas.
 * - Jefe de producción: clave fija del prototipo (datos/produccion.json) → tablero, lotes, asignación…
 * - Operario: elige su nombre → sus trabajos del día.
 * No es seguridad real: cualquiera que abra la página puede elegir (ver README, Roles).
 */
export async function pantallaIngreso(contenedor) {
  const { datos } = estado;
  // Vendedores agrupados por empresa y sucursal: el vendedor entra con la empresa de su sucursal.
  const grupos = listaEmpresas(datos).flatMap((empresa) => sucursalesDeEmpresa(datos, empresa.id).map((s) => ({
    rotulo: `${empresa.nombreCorto} · ${s.nombre}`,
    vendedores: datos.vendedores.filter((v) => v.sucursalHabitualId === s.id),
  }))).filter((g) => g.vendedores.length);
  const lista = h('select', { class: 'selector-grande', 'aria-label': 'Vendedor', size: 1 },
    h('option', { value: '' }, '— Elegí tu nombre —'),
    grupos.map((g) => h('optgroup', { label: g.rotulo },
      g.vendedores.map((v) => h('option', { value: v.id, selected: v.id === estado.sesion?.vendedorId }, v.nombre)))));
  const plantas = listaPlantas(datos);
  const operarios = datos.produccion.operarios.filter((o) => o.activo !== false);
  const listaOperarios = h('select', { class: 'selector-grande', 'aria-label': 'Operario' },
    h('option', { value: '' }, '— Elegí tu nombre —'),
    plantas.map((p) => h('optgroup', { label: p.nombreCorto || p.nombre },
      operarios.filter((o) => (o.planta || plantas[0].id) === p.id).map((o) => h('option', { value: o.id, selected: o.id === estado.sesion?.operarioId }, o.nombre)))));
  const listaPlantasJefe = selector(plantas.map((p) => ({ valor: p.id, texto: p.nombre })).concat([{ valor: '', texto: 'Todas las plantas del grupo' }]),
    estado.sesion?.plantaId ?? plantas[0]?.id, { class: 'selector-grande', 'aria-label': 'Planta' });
  const claveJefe = h('input', { type: 'password', class: 'selector-grande', placeholder: 'Clave del jefe de producción', 'aria-label': 'Clave del jefe de producción' });

  const entrar = async (sesion, destino) => {
    estado.sesion = { rol: null, vendedorId: null, sucursalHoyId: null, operarioId: null, ...sesion };
    await almacenamiento.guardarSesion(estado.sesion);
    ir(destino);
  };
  const entrarJefe = () => {
    if (claveJefe.value !== datos.produccion.claveJefeProduccion) { mostrarAviso('Clave incorrecta', 'error'); return; }
    entrar({ rol: 'jefe', plantaId: listaPlantasJefe.value || null }, '#produccion');
  };
  claveJefe.addEventListener('keydown', (e) => { if (e.key === 'Enter') entrarJefe(); });

  contenedor.replaceChildren(h('section', { class: 'panel panel-ingreso' },
    h('div', { class: 'empresas-ingreso' }, listaEmpresas(datos).map((e) => logoDeEmpresa(e, 'logo-ingreso'))),
    h('h1', {}, '¿Quién sos?'),
    h('div', { class: 'roles-ingreso' },
      h('div', { class: 'rol-ingreso' },
        h('h2', {}, 'Comercial'),
        h('p', {}, 'Cargás las notas de pedido de tu empresa. Se usa tu sucursal habitual (la podés cambiar por hoy).'),
        lista,
        h('button', {
          type: 'button', class: 'boton grande principal',
          onclick: async () => {
            const vendedor = datos.vendedores.find((v) => v.id === lista.value);
            if (!vendedor) { mostrarAviso('Elegí un nombre de la lista', 'error'); return; }
            await entrar({ rol: 'comercial', vendedorId: vendedor.id, sucursalHoyId: vendedor.sucursalHabitualId }, '#inicio');
          },
        }, 'Entrar')),
      h('div', { class: 'rol-ingreso' },
        h('h2', {}, 'Jefe de producción'),
        h('p', {}, 'Tablero, lotes, asignación a operarios, eficiencia, material e indicadores de tu planta.'),
        listaPlantasJefe,
        claveJefe,
        h('button', { type: 'button', class: 'boton grande principal', onclick: entrarJefe }, 'Entrar')),
      h('div', { class: 'rol-ingreso' },
        h('h2', {}, 'Operario'),
        h('p', {}, 'Tus trabajos del día: marcás HECHA (y si querés, Iniciar / Pausar / Terminar).'),
        listaOperarios,
        h('button', {
          type: 'button', class: 'boton grande principal',
          onclick: async () => {
            if (!listaOperarios.value) { mostrarAviso('Elegí tu nombre', 'error'); return; }
            await entrar({ rol: 'operario', operarioId: listaOperarios.value }, '#operario');
          },
        }, 'Entrar')))));
  return () => {};
}

let quitarAtajosInicio = null;

export async function pantallaInicio(contenedor) {
  const { datos } = estado;
  const vendedor = vendedorActual();
  const sucursal = sucursalActual();

  // ---------- cabecera ----------
  // Solo las sucursales de su empresa (un vendedor de Abasto no emite notas de HIPER).
  const empresa = empresaActual();
  const sucursalesPropias = sucursalesDeEmpresa(datos, empresa?.id);
  const selectorSucursal = selector(sucursalesPropias.map((s) => ({ valor: s.id, texto: s.nombre })), estado.sesion.sucursalHoyId, {
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
      h('div', { class: 'texto-chico' }, `Sucursal de hoy · ${empresa?.nombre || ''}`),
      h('strong', { class: 'dato-grande' }, sucursal?.nombre || '—'), ' ',
      sucursalesPropias.length > 1 ? h('button', { type: 'button', class: 'boton chico', onclick: () => { selectorSucursal.hidden = !selectorSucursal.hidden; selectorSucursal.focus(); } }, 'Cambiar sucursal de hoy') : null,
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
      h('thead', {}, h('tr', {}, h('th', {}, 'Estado'), h('th', {}, 'NP Nº'), h('th', {}, 'Fecha'), h('th', {}, 'Cliente'), h('th', {}, 'Factura'), h('th', {}, 'Renglones'), h('th', {}, ''))),
      h('tbody', {}, notas.map((n) => h('tr', {},
        h('td', {}, h('span', { class: `etiqueta-estado ${n.estado}` }, n.estado === 'emitida' ? 'EMITIDA' : 'borrador')),
        h('td', { title: n.numero ? `Identificador completo: ${identificadorDeNota(n, datos)}` : '' }, n.numero ? String(n.numero) : '—', n.demo ? h('span', { class: 'etiqueta-demo' }, 'DEMO') : null),
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
    h('a', { href: '#nota/nueva', class: 'boton enorme principal' }, 'Nueva nota de pedido', etiquetaAtajo('Alt+N')),
    h('section', { class: 'panel' },
      h('h2', {}, `Notas de ${sucursal?.nombre || 'la sucursal'}`),
      h('div', { class: 'filtros' }, campoTexto, h('label', {}, 'Desde ', campoDesde), h('label', {}, 'Hasta ', campoHasta), selectorEstado),
      lista));
  await llenar();
  quitarAtajosInicio?.(); // si la pantalla se redibuja (cambio de sucursal), no se duplican
  quitarAtajosInicio = registrarAtajos('Inicio', [
    { teclas: 'Alt+N', descripcion: 'Nueva nota de pedido', accion: () => ir('#nota/nueva') },
    { teclas: 'Alt+K', descripcion: 'Buscar notas', accion: () => campoTexto.focus() },
  ]);
  return () => { quitarAtajosInicio?.(); quitarAtajosInicio = null; };
}
