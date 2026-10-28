// =============================================================
// produccionIndicadores.js
// - Material: chapa necesaria para lo pendiente, por material, calibre y color.
// - Indicadores (KPIs) del período, con exportación a Excel (CSV) y PDF (imprimir).
// - Incidencias: retrabajos, demoras e incidentes con su causa.
// =============================================================

import { h, selector, mostrarAviso, fechaCorta, fechaYHora, textoMinutos, textoPorcentaje, descargarArchivo } from './util.js';
import { estado, nombreSucursal } from './estado.js';
import * as almacenamiento from '../datos/almacenamiento.js';
import { cargarContexto, nombreOperario, nombreMaquina } from './contextoProduccion.js';
import { materialConsolidado, indicadores, estadoDeTrabajo, diaDe, desviosPorNota } from '../logica/produccion.js';
import { armarCsv } from '../logica/exportar.js';
import { formatearCorto } from '../logica/numeros.js';
import { kpi } from './produccionLotes.js';

// ---------- material ----------

export async function seccionMaterial(contenedor) {
  const ctx = await cargarContexto();
  let hasta = '';
  const zona = h('div', { class: 'tabla-desplazable' });

  function dibujar() {
    const trabajos = ctx.trabajos.filter((t) => !t.hecha && (!hasta || (t.fecha && t.fecha <= hasta)));
    const filas = materialConsolidado(trabajos, ctx.datos);
    zona.replaceChildren(filas.length ? h('table', { class: 'tabla-notas' },
      h('thead', {}, h('tr', {},
        h('th', {}, 'Material'), h('th', {}, 'Renglones'),
        h('th', { title: 'Como en la nota: piezas × largo ÷ 2,44, en tiras de la banda del código' }, 'Chapas (regla de la nota)'),
        h('th', {}, 'Por banda'),
        h('th', { title: 'Las tiras de banda 30 son 1/4 de chapa y las de 60, 1/2' }, 'Chapas enteras 1,22 × 2,44'),
        h('th', { title: 'Tiras del desarrollo que entran a lo ancho y recortes a lo largo sin reutilizar' }, 'Estimación física'),
        h('th', {}, 'A pedir (enteras)'))),
      h('tbody', {}, filas.map((f) => h('tr', {},
        h('td', {}, f.nombre),
        h('td', {}, String(f.renglones)),
        h('td', {}, formatearCorto(f.chapas)),
        h('td', { class: 'texto-chico' }, Object.entries(f.porBanda).map(([b, v]) => `B${b}: ${formatearCorto(v)}`).join(' · ')),
        h('td', {}, formatearCorto(f.chapasEnteras)),
        h('td', {}, formatearCorto(f.fisicasEstimadas)),
        h('td', {}, h('strong', {}, String(f.chapasAComprar))))))) : h('p', { class: 'vacio' }, 'No hay chapa pendiente con ese filtro.'));
    return filas;
  }

  const campoHasta = h('input', { type: 'date', 'aria-label': 'Programado hasta', onchange: (e) => { hasta = e.target.value; dibujar(); } });
  contenedor.replaceChildren(
    h('p', {}, 'Chapa para los renglones que faltan hacer. La "cantidad" de la nota cuenta tiras de 2,44 m de la banda del código (canaleta de 2,44 m = 1). Para comprar sirve más la estimación física: cuántas tiras del desarrollo entran a lo ancho de la chapa de 1,22 m y cuánto recorte queda a lo largo (supone que los recortes no se reutilizan).'),
    h('div', { class: 'barra-botones' },
      h('label', {}, 'Solo lo programado hasta ', campoHasta),
      h('button', { type: 'button', class: 'boton', onclick: () => {
        const filas = dibujar();
        descargarArchivo('material-pendiente.csv', armarCsv(['Material', 'Renglones', 'Chapas (regla de la nota)', 'Chapas enteras', 'Estimación física', 'A pedir'], filas.map((f) => [f.nombre, f.renglones, f.chapas, f.chapasEnteras, f.fisicasEstimadas, f.chapasAComprar])));
      } }, 'Bajar a Excel (CSV)')),
    zona);
  dibujar();
}

// ---------- indicadores ----------

export async function seccionIndicadores(contenedor) {
  const ctx = await cargarContexto();
  const { hoy } = ctx;
  let rango = '30';
  const zona = h('div');

  const desdeDe = (valor) => {
    const f = new Date();
    if (valor === 'mes') return `${hoy.slice(0, 7)}-01`;
    f.setDate(f.getDate() - Number(valor));
    return diaDe(f);
  };

  function dibujar() {
    const desde = desdeDe(rango);
    const k = indicadores(ctx.notasEstado, ctx.trabajos, ctx.incidencias, { desde, hasta: hoy, hoy });
    const desvios = desviosPorNota(ctx.notasEstado).filter((d) => d.desvio !== null);
    const medioDesvio = desvios.length ? desvios.reduce((s, d) => s + d.desvio, 0) / desvios.length : null;
    zona.replaceChildren(
      h('p', { class: 'texto-chico' }, `Del ${fechaCorta(`${desde}T12:00:00`)} al ${fechaCorta(`${hoy}T12:00:00`)}.`),
      h('div', { class: 'tarjetas-kpi' },
        kpi('Notas terminadas', String(k.notasTerminadas)),
        kpi('Entregas a tiempo', textoPorcentaje(k.entregasATiempo), 'terminadas antes o el día de la entrega'),
        kpi('Eficiencia del taller', textoPorcentaje(k.eficiencia), `${formatearCorto(k.horasEstandarHechas, 1)} h estándar en ${formatearCorto(k.horasReales, 1)} h reales`),
        kpi('Trabajo pendiente', textoMinutos(k.pendientesMin), `${k.notasAbiertas} notas abiertas`),
        kpi('Demoradas', String(k.demoradas), `${k.vencidasHoy} con la entrega vencida`),
        kpi('Ahorro por lotes', textoMinutos(k.ahorroLotesMin), 'en los trabajos terminados'),
        kpi('Incidencias', String(k.incidencias), `${k.retrabajos} retrabajos · ${textoMinutos(k.minutosPerdidos)} perdidos`),
        kpi('Desvío medio real vs estándar', textoPorcentaje(medioDesvio), `${desvios.length} notas terminadas (para recalibrar)`)),
      k.porCausa.length ? h('div', {}, h('h3', {}, 'Causas más frecuentes'), h('table', { class: 'tabla-notas' },
        h('tbody', {}, k.porCausa.map(([causa, n]) => h('tr', {}, h('td', {}, causa), h('td', {}, String(n))))))) : null);
  }

  const selectorRango = selector([{ valor: '7', texto: 'Últimos 7 días' }, { valor: '30', texto: 'Últimos 30 días' }, { valor: 'mes', texto: 'Este mes' }, { valor: '365', texto: 'Último año' }], rango, {
    'aria-label': 'Período', onchange: (e) => { rango = e.target.value; dibujar(); },
  });

  contenedor.replaceChildren(
    h('div', { class: 'barra-botones no-imprimir' }, selectorRango,
      h('button', { type: 'button', class: 'boton', onclick: () => exportarTrabajos(ctx) }, 'Bajar todos los trabajos (CSV para Excel)'),
      h('button', { type: 'button', class: 'boton', onclick: () => window.print() }, 'Imprimir / PDF')),
    zona);
  dibujar();
}

export function exportarTrabajos(ctx) {
  const columnas = ['NP', 'Sucursal', 'Cliente', 'Renglón', 'Descripción', 'Piezas', 'Cantidad', 'Unidad', 'Máquina', 'Entrega', 'Prioridad', 'Estado', 'Operario', 'Día', 'Lote',
    'Estándar (min)', 'En lote (min)', 'Setup (min)', 'Real (min)', 'Origen del real', 'Hecha', 'Demo'];
  const filas = ctx.trabajos.map((t) => [t.numeroNota, nombreSucursal(t.sucursalId), t.cliente, t.indice + 1, t.descripcion, t.piezas, t.cantidad.valor, t.cantidad.unidad,
    nombreMaquina(t.maquina), t.fechaEntrega, t.prioridad, estadoDeTrabajo(t), t.operarioId ? nombreOperario(t.operarioId) : '', t.fecha || '', t.loteActual || '',
    t.tiempoEstandarMin ?? t.minutos, t.minutosEnLote, t.setupMin, t.tiempoRealMin ?? '', t.origenReal || '', t.horaHecha ? fechaYHora(t.horaHecha) : '', t.demo ? 'sí' : '']);
  descargarArchivo(`trabajos-${ctx.hoy}.csv`, armarCsv(columnas, filas));
}

// ---------- incidencias ----------

export async function seccionIncidencias(contenedor, { refrescar }) {
  const ctx = await cargarContexto();
  const causas = estado.datos.produccion.causasIncidencia;
  const tipo = selector(Object.keys(causas).map((t) => ({ valor: t, texto: t })), 'retrabajo', { 'aria-label': 'Tipo', onchange: () => llenarCausas() });
  const causa = h('select', { 'aria-label': 'Causa' });
  const llenarCausas = () => causa.replaceChildren(h('option', { value: '' }, '— causa —'), ...causas[tipo.value].map((c) => h('option', { value: c }, c)));
  llenarCausas();
  const abiertas = ctx.notasEstado.slice(0, 600);
  const nota = h('select', { 'aria-label': 'Nota' }, h('option', { value: '' }, '— nota (opcional) —'), abiertas.map((n) => h('option', { value: n.notaId }, `NP ${n.numeroNota} · ${n.cliente}`)));
  const operario = selector([{ valor: '', texto: '— operario (opcional) —' }].concat(ctx.prod.operarios.map((o) => ({ valor: o.id, texto: o.nombre }))), '', { 'aria-label': 'Operario' });
  const minutos = h('input', { type: 'number', min: 0, step: 1, placeholder: 'min perdidos', class: 'campo-chico', 'aria-label': 'Minutos perdidos' });
  const descripcion = h('input', { type: 'text', placeholder: 'Qué pasó (opcional)', 'aria-label': 'Descripción' });

  async function registrar() {
    try {
      await almacenamiento.agregarIncidencia({
        tipo: tipo.value, causa: causa.value, notaId: nota.value || null, operarioId: operario.value || null,
        minutosPerdidos: Number(minutos.value) || 0, descripcion: descripcion.value.trim(),
      });
      mostrarAviso('Incidencia registrada', 'ok');
      refrescar();
    } catch (error) {
      mostrarAviso(error.message, 'error');
    }
  }

  const lista = [...ctx.incidencias].sort((a, b) => String(b.hora).localeCompare(String(a.hora)));
  contenedor.replaceChildren(
    h('section', { class: 'panel-interno' }, h('h3', {}, 'Registrar'),
      h('div', { class: 'filtros' }, tipo, causa, nota, operario, minutos, descripcion,
        h('button', { type: 'button', class: 'boton principal', onclick: registrar }, 'Registrar'))),
    h('div', { class: 'barra-botones' }, h('button', { type: 'button', class: 'boton', onclick: () => {
      descargarArchivo('incidencias.csv', armarCsv(['Fecha', 'Tipo', 'Causa', 'NP', 'Operario', 'Minutos perdidos', 'Descripción'],
        lista.map((i) => [fechaYHora(i.hora), i.tipo, i.causa, ctx.notasEstado.find((n) => n.notaId === i.notaId)?.numeroNota || '', i.operarioId ? nombreOperario(i.operarioId) : '', i.minutosPerdidos, i.descripcion])));
    } }, 'Bajar a Excel (CSV)')),
    lista.length ? h('table', { class: 'tabla-notas' },
      h('thead', {}, h('tr', {}, h('th', {}, 'Fecha'), h('th', {}, 'Tipo'), h('th', {}, 'Causa'), h('th', {}, 'NP'), h('th', {}, 'Operario'), h('th', {}, 'Min'), h('th', {}, 'Descripción'))),
      h('tbody', {}, lista.slice(0, 300).map((i) => h('tr', {},
        h('td', {}, fechaYHora(i.hora)), h('td', {}, i.tipo), h('td', {}, i.causa),
        h('td', {}, ctx.notasEstado.find((n) => n.notaId === i.notaId)?.numeroNota || '—'),
        h('td', {}, i.operarioId ? nombreOperario(i.operarioId) : '—'), h('td', {}, String(i.minutosPerdidos || 0)), h('td', {}, i.descripcion || ''))))) : h('p', { class: 'vacio' }, 'Sin incidencias registradas.'));
}
