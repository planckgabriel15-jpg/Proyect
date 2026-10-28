// =============================================================
// produccionTablero.js
// Tablero de estados (pendiente / programada / en curso / hecha / demorada) con filtros,
// alertas de riesgo, cola con prioridades (arrastrar o flechas ↑ ↓) e historial por nota.
// =============================================================

import { h, selector, fechaCorta, fechaYHora, mostrarAviso, textoMinutos, textoPorcentaje } from './util.js';
import { estado, nombreSucursal } from './estado.js';
import * as almacenamiento from '../datos/almacenamiento.js';
import { cargarContexto, esJefe, nombreOperario } from './contextoProduccion.js';
import { ESTADOS, alertas, ordenarCola, registroVacio, estadoDeTrabajo } from '../logica/produccion.js';

export function etiquetaEstado(valor) {
  const e = ESTADOS.find((x) => x.valor === valor);
  return h('span', { class: `etiqueta-estado prod-${valor}`, title: e?.ayuda || '' }, e?.texto || valor);
}

export async function seccionTablero(contenedor, { refrescar }) {
  const ctx = await cargarContexto();
  const { datos, prod, hoy } = ctx;
  const jefe = esJefe();
  const filtros = { estado: 'abiertas', sucursal: '', operario: '', texto: '', origen: '' };

  const listaAlertas = alertas(ctx.notasEstado, ctx.trabajos, { hoy, prod, operarios: prod.operarios });
  const contador = (valor) => ctx.notasEstado.filter((n) => n.estado === valor).length;
  const chips = h('div', { class: 'chips-estado' }, ESTADOS.map((e) => h('button', {
    type: 'button', class: 'chip-estado', 'data-estado': e.valor,
    onclick: () => { filtros.estado = filtros.estado === e.valor ? 'abiertas' : e.valor; selectorEstado.value = filtros.estado; dibujar(); },
  }, etiquetaEstado(e.valor), ` ${contador(e.valor)}`)));

  const selectorEstado = selector([{ valor: 'abiertas', texto: 'Abiertas (sin las hechas)' }, { valor: '', texto: 'Todos los estados' }].concat(ESTADOS.map((e) => ({ valor: e.valor, texto: e.texto }))), 'abiertas', { 'aria-label': 'Estado', onchange: (e) => { filtros.estado = e.target.value; dibujar(); } });
  const selectorSucursal = selector([{ valor: '', texto: 'Todas las sucursales' }].concat(datos.sucursales.map((s) => ({ valor: s.id, texto: s.nombre }))), '', { 'aria-label': 'Sucursal', onchange: (e) => { filtros.sucursal = e.target.value; dibujar(); } });
  const selectorOperario = selector([{ valor: '', texto: 'Todos los operarios' }, { valor: '-', texto: 'Sin asignar' }].concat(prod.operarios.map((o) => ({ valor: o.id, texto: o.nombre }))), '', { 'aria-label': 'Operario', onchange: (e) => { filtros.operario = e.target.value; dibujar(); } });
  const selectorOrigen = selector([{ valor: '', texto: 'Reales y demo' }, { valor: 'real', texto: 'Solo reales' }, { valor: 'demo', texto: 'Solo demo' }], '', { 'aria-label': 'Origen', onchange: (e) => { filtros.origen = e.target.value; dibujar(); } });
  const campoTexto = h('input', { type: 'search', class: 'buscador', placeholder: 'NP o cliente', 'aria-label': 'Buscar', oninput: (e) => { filtros.texto = e.target.value.toLowerCase(); dibujar(); } });
  const tabla = h('div', { class: 'tabla-desplazable' });

  function visibles() {
    // Las hechas van al final (no ocupan lugar en la cola).
    const cola = ordenarCola(ctx.notasEstado);
    return cola.filter((n) => n.estado !== 'hecha').concat(cola.filter((n) => n.estado === 'hecha'))
      .filter((n) => (!filtros.estado || (filtros.estado === 'abiertas' ? n.estado !== 'hecha' : n.estado === filtros.estado))
      && (!filtros.sucursal || n.sucursalId === filtros.sucursal)
      && (!filtros.operario || (filtros.operario === '-' ? n.trabajos.some((t) => !t.hecha && !t.operarioId) : n.operarios.includes(filtros.operario)))
      && (!filtros.origen || (filtros.origen === 'demo') === n.demo)
      && (!filtros.texto || `${n.numeroNota} ${n.cliente}`.toLowerCase().includes(filtros.texto)));
  }

  async function guardarOrden(cola) {
    const lista = cola.map((n, i) => ({ ...(ctx.registros[n.notaId] || registroVacio(n.notaId, n.demo)), orden: i + 1 }));
    await almacenamiento.guardarRegistros(lista);
    lista.forEach((r) => { ctx.registros[r.notaId] = r; });
    cola.forEach((n, i) => { n.orden = i + 1; });
    dibujar();
  }

  /** Mueve una nota de lugar en la cola (entre las no terminadas). */
  function mover(notaId, hacia) {
    const cola = ordenarCola(ctx.notasEstado.filter((n) => n.estado !== 'hecha'));
    const desde = cola.findIndex((n) => n.notaId === notaId);
    const hasta = typeof hacia === 'number' ? hacia : cola.findIndex((n) => n.notaId === hacia);
    if (desde < 0 || hasta < 0 || desde === hasta) return;
    const [nota] = cola.splice(desde, 1);
    cola.splice(hasta, 0, nota);
    guardarOrden(cola);
  }

  function dibujar() {
    chips.querySelectorAll('.chip-estado').forEach((b) => b.classList.toggle('elegido', b.dataset.estado === filtros.estado));
    const lista = visibles();
    const cola = ordenarCola(ctx.notasEstado.filter((n) => n.estado !== 'hecha'));
    tabla.replaceChildren(lista.length ? h('table', { class: 'tabla-notas tabla-tablero' },
      h('thead', {}, h('tr', {},
        jefe ? h('th', { title: 'Arrastrá las filas o usá las flechas para cambiar el orden de la cola' }, 'Orden') : null,
        h('th', {}, 'NP'), h('th', {}, 'Cliente'), h('th', {}, 'Sucursal'), h('th', {}, 'Entrega'), h('th', {}, 'Estado'),
        h('th', {}, 'Avance'), h('th', {}, 'Pendiente'), h('th', {}, 'Operarios'), h('th', {}, ''))),
      h('tbody', {}, lista.slice(0, 400).map((n) => {
        const posicion = cola.findIndex((c) => c.notaId === n.notaId);
        const fila = h('tr', { class: `${n.prioridad === 'urgente' ? 'fila-urgente' : ''}`, draggable: jefe && n.estado !== 'hecha' ? 'true' : null, 'data-nota': n.notaId },
          jefe ? h('td', { class: 'celda-orden' }, n.estado === 'hecha' ? '✓' : [
            h('span', { class: 'asa-arrastre', 'aria-hidden': 'true' }, '⠿'), ` ${posicion + 1} `,
            h('button', { type: 'button', class: 'boton mini', 'aria-label': 'Subir', disabled: posicion === 0, onclick: () => mover(n.notaId, posicion - 1) }, '↑'),
            h('button', { type: 'button', class: 'boton mini', 'aria-label': 'Bajar', disabled: posicion === cola.length - 1, onclick: () => mover(n.notaId, posicion + 1) }, '↓')]) : null,
          h('td', {}, h('strong', {}, String(n.numeroNota)), n.prioridad === 'urgente' ? h('span', { class: 'etiqueta-urgente' }, 'URGENTE') : null, n.demo ? h('span', { class: 'etiqueta-demo' }, 'DEMO') : null),
          h('td', {}, n.cliente),
          h('td', {}, nombreSucursal(n.sucursalId)),
          h('td', {}, fechaCorta(`${n.fechaEntrega}T12:00:00`)),
          h('td', {}, etiquetaEstado(n.estado)),
          h('td', {}, h('span', { class: 'barra-avance', style: `--avance:${Math.round(n.avance * 100)}%` }), ` ${textoPorcentaje(n.avance)}`),
          h('td', {}, textoMinutos(n.minutosPendientes)),
          h('td', { class: 'texto-chico' }, n.operarios.map(nombreOperario).join(', ') || '—'),
          h('td', { class: 'acciones' },
            h('button', { type: 'button', class: 'boton chico', onclick: () => mostrarHistorial(n, ctx) }, 'Detalle'),
            h('a', { class: 'boton chico', href: `#imprimir/${n.notaId}` }, 'Nota')));
        if (jefe && n.estado !== 'hecha') {
          fila.addEventListener('dragstart', (e) => { e.dataTransfer.setData('text/plain', n.notaId); fila.classList.add('arrastrando'); });
          fila.addEventListener('dragend', () => fila.classList.remove('arrastrando'));
          fila.addEventListener('dragover', (e) => { e.preventDefault(); fila.classList.add('destino'); });
          fila.addEventListener('dragleave', () => fila.classList.remove('destino'));
          fila.addEventListener('drop', (e) => { e.preventDefault(); fila.classList.remove('destino'); mover(e.dataTransfer.getData('text/plain'), n.notaId); });
        }
        return fila;
      }))) : h('p', { class: 'vacio' }, ctx.notasEstado.length ? 'No hay notas con esos filtros.' : 'Todavía no hay notas emitidas. Podés cargar datos de demostración en la pestaña "Datos de demostración".'));
    if (lista.length > 400) tabla.append(h('p', { class: 'texto-chico' }, `Se muestran 400 de ${lista.length}: usá los filtros.`));
  }

  contenedor.replaceChildren(
    listaAlertas.length ? h('details', { class: 'aviso-caja caja-alertas', open: true },
      h('summary', {}, h('strong', {}, `Alertas (${listaAlertas.length})`), ' – notas en riesgo, vencidas o con sobrecarga'),
      h('ul', {}, listaAlertas.slice(0, 12).map((a) => h('li', { class: a.nivel === 'error' ? 'error' : 'aviso' }, a.texto))),
      listaAlertas.length > 12 ? h('p', { class: 'texto-chico' }, `… y ${listaAlertas.length - 12} más (filtrá por "Demorada").`) : null) : null,
    chips,
    h('div', { class: 'filtros' }, selectorEstado, selectorSucursal, selectorOperario, selectorOrigen, campoTexto),
    jefe ? h('p', { class: 'texto-chico' }, 'Orden de la cola: arrastrá una fila (computadora) o usá ↑ ↓ (celular). Las urgentes y las de entrega más cercana van primero mientras no se cambie el orden a mano. Para reprogramar días y operarios: pestaña "Asignación".') : null,
    tabla,
    h('div', { class: 'barra-botones' }, h('button', { type: 'button', class: 'boton', onclick: refrescar }, 'Actualizar')));
  dibujar();
}

/** Detalle de la nota: renglones con su estado y la trazabilidad (historial). */
export function mostrarHistorial(n, ctx) {
  const registro = ctx.registros[n.notaId] || registroVacio(n.notaId);
  const nota = ctx.notas.find((x) => x.id === n.notaId);
  const incidencias = ctx.incidencias.filter((i) => i.notaId === n.notaId);
  const eventos = [
    { hora: nota?.fechaEmision, accion: 'emitida', usuario: nota?.vendedorId ? estado.datos.vendedores.find((v) => v.id === nota.vendedorId)?.nombre : '', detalle: `NP ${n.numeroNota}` },
    ...registro.historial,
  ].filter((e) => e.hora).sort((a, b) => String(a.hora).localeCompare(String(b.hora)));
  const dialogo = h('dialog', { class: 'dialogo-historial' },
    h('h2', {}, `NP ${n.numeroNota} – ${n.cliente}`),
    h('p', {}, 'Entrega: ', h('strong', {}, fechaCorta(`${n.fechaEntrega}T12:00:00`)), ' · Estado: ', etiquetaEstado(n.estado), ' · Prioridad: ', n.prioridad),
    h('table', { class: 'tabla-notas' },
      h('thead', {}, h('tr', {}, h('th', {}, '#'), h('th', {}, 'Renglón'), h('th', {}, 'Estado'), h('th', {}, 'Operario'), h('th', {}, 'Día'), h('th', {}, 'Estándar'), h('th', {}, 'Real'))),
      h('tbody', {}, n.trabajos.map((t) => h('tr', {},
        h('td', {}, String(t.indice + 1)),
        h('td', {}, t.descripcion, t.loteActual ? h('span', { class: 'etiqueta-demo' }, t.loteActual) : null),
        h('td', {}, etiquetaEstado(estadoDeTrabajo(t))),
        h('td', {}, nombreOperario(t.operarioId)),
        h('td', {}, t.fecha ? fechaCorta(`${t.fecha}T12:00:00`) : '—'),
        h('td', {}, textoMinutos(t.tiempoEstandarMin ?? t.minutosEnLote)),
        h('td', {}, t.tiempoRealMin ? `${textoMinutos(t.tiempoRealMin)} (${t.origenReal})` : '—'))))),
    incidencias.length ? [h('h3', {}, 'Incidencias'), h('ul', {}, incidencias.map((i) => h('li', {}, `${fechaYHora(i.hora)} · ${i.tipo}: ${i.causa}${i.minutosPerdidos ? ` (${i.minutosPerdidos} min)` : ''}${i.descripcion ? ` – ${i.descripcion}` : ''}`)))] : null,
    h('h3', {}, 'Historial (trazabilidad)'),
    h('ol', { class: 'lista-historial' }, eventos.map((e) => h('li', {}, h('span', { class: 'texto-chico' }, fechaYHora(e.hora)), ' ', h('strong', {}, e.accion), e.usuario ? ` · ${e.usuario}` : '', e.detalle ? ` · ${e.detalle}` : ''))),
    h('div', { class: 'barra-botones' },
      h('a', { class: 'boton', href: `#imprimir/${n.notaId}` }, 'Ver la nota'),
      h('button', { type: 'button', class: 'boton principal', onclick: () => { dialogo.close(); dialogo.remove(); } }, 'Cerrar')));
  document.body.append(dialogo);
  dialogo.addEventListener('close', () => dialogo.remove());
  dialogo.showModal();
  if (!eventos.length) mostrarAviso('Sin historial todavía', 'info');
}
