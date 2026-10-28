// =============================================================
// produccionDemo.js
// Cargar y borrar los DATOS DE DEMOSTRACIÓN (50 notas por local, semilla fija) y ver
// el resumen: tiempo estimado total, distribución por nota, lotes y ahorro de setup.
// No tocan las notas reales ni los contadores de numeración.
// =============================================================

import { h, mostrarAviso, confirmar, textoMinutos, textoPorcentaje } from './util.js';
import { estado } from './estado.js';
import * as almacenamiento from '../datos/almacenamiento.js';
import { cargarContexto } from './contextoProduccion.js';
import { generarDemo, resumirDemo, SEMILLA_DEMO, NOTAS_POR_LOCAL } from '../logica/demo.js';
import { proponerLotesProtegidos, totalesDeLotes } from '../logica/agrupamiento.js';
import { formatearCorto } from '../logica/numeros.js';
import { kpi } from './produccionLotes.js';

export async function seccionDemo(contenedor, { refrescar }) {
  const ctx = await cargarContexto();
  const hay = ctx.notas.some((n) => n.demo);
  const datos = { ...estado.datos };

  async function cargar() {
    const boton = contenedor.querySelector('.boton-cargar-demo');
    if (boton) { boton.disabled = true; boton.textContent = 'Generando…'; }
    try {
      const demo = generarDemo(datos, { modelo: ctx.modelo, prod: ctx.prod, operarios: ctx.prod.operarios });
      await almacenamiento.cargarDemo(demo);
      mostrarAviso(`Listo: ${demo.notas.length} notas de demostración`, 'ok');
      refrescar();
    } catch (error) {
      mostrarAviso(error.message, 'error', 10);
      if (boton) { boton.disabled = false; boton.textContent = 'Cargar datos de demostración'; }
    }
  }

  async function borrar() {
    if (!confirmar('¿Borrar los datos de demostración? Las notas reales no se tocan.')) return;
    const cuantas = await almacenamiento.borrarDemo();
    mostrarAviso(`Se borraron ${cuantas} notas de demostración`, 'ok');
    refrescar();
  }

  const partes = [
    h('p', {}, `Genera ${NOTAS_POR_LOCAL} notas emitidas por cada uno de los ${datos.sucursales.length} locales (semilla fija ${SEMILLA_DEMO}: siempre salen iguales), `
      + 'con productos repetidos y parecidos (para que se vean los lotes) y otros bien distintos. Las más viejas quedan terminadas con tiempo real simulado; las nuevas, pendientes. '
      + 'Están marcadas DEMO, tienen número propio (D-…) y no usan los contadores de las sucursales.'),
    h('div', { class: 'barra-botones' },
      h('button', { type: 'button', class: 'boton grande principal boton-cargar-demo', disabled: hay, onclick: cargar }, 'Cargar datos de demostración'),
      h('button', { type: 'button', class: 'boton grande peligro', disabled: !hay, onclick: borrar }, 'Borrar datos de demostración')),
  ];

  if (hay) {
    const notasDemo = ctx.notas.filter((n) => n.demo);
    const resumen = resumirDemo(notasDemo, datos, ctx.modelo);
    const pendientes = ctx.trabajos.filter((t) => t.demo && !t.hecha && t.cronometro === 'sin_empezar' && t.tiempoValido);
    const { lotes } = proponerLotesProtegidos(pendientes, ctx.prod.agrupamiento, Object.fromEntries(ctx.prod.maquinas.map((m) => [m.id, m.cantidad])));
    const totales = totalesDeLotes(lotes);
    partes.push(
      h('h2', {}, 'Resumen de la demostración'),
      h('div', { class: 'tarjetas-kpi' },
        kpi('Notas', String(resumen.notas), `${resumen.renglones} renglones · ${resumen.renglonesConError} con error`),
        kpi('Tiempo estimado total', `${formatearCorto(resumen.totalHoras, 1)} h`, 'tiempo estándar de todas las notas'),
        kpi('Por nota', textoMinutos(resumen.promedioMin), `mediana ${textoMinutos(resumen.medianaMin)} · 90 % < ${textoMinutos(resumen.p90Min)} · máx. ${textoMinutos(resumen.maximoMin)}`),
        kpi('Lotes formados (pendientes)', String(totales.lotesAgrupados), `${totales.trabajos} renglones por hacer`),
        kpi('Ahorro de setup', textoMinutos(totales.ahorroMin), `${textoPorcentaje(totales.ahorroPorcentaje, 1)} del total · ${textoPorcentaje(totales.ahorroSetupPorcentaje)} del setup`)),
      histograma(resumen.histograma),
      h('p', { class: 'texto-chico' }, 'El ahorro es con los criterios guardados en "Lotes (agrupar)"; ahí se pueden cambiar y aceptar los lotes.'));
  }
  contenedor.replaceChildren(...partes);
}

function histograma(barras) {
  const ancho = 560; const alto = 180; const margen = 30;
  const maximo = Math.max(1, ...barras.map((b) => b.notas));
  const paso = (ancho - 2 * margen) / barras.length;
  const svg = [`<svg viewBox="0 0 ${ancho} ${alto}" class="grafico-eficiencia" role="img" aria-label="Notas por tiempo estimado">`,
    `<text x="${margen}" y="14" class="grafico-titulo">Notas según su tiempo estándar</text>`];
  barras.forEach((b, i) => {
    const h0 = ((alto - 2 * margen) * b.notas) / maximo;
    const x = margen + i * paso + paso * 0.15;
    svg.push(`<rect x="${x}" y="${alto - margen - h0}" width="${paso * 0.7}" height="${h0}" class="grafico-barra ef-media"/>`);
    svg.push(`<text x="${x + paso * 0.35}" y="${alto - margen - h0 - 4}" text-anchor="middle" class="grafico-eje">${b.notas}</text>`);
    svg.push(`<text x="${x + paso * 0.35}" y="${alto - margen + 14}" text-anchor="middle" class="grafico-eje">${b.hasta === Infinity ? `≥ ${b.desde}` : `${b.desde}–${b.hasta}`} min</text>`);
  });
  svg.push('</svg>');
  return h('div', { class: 'grafico', html: svg.join('') });
}
