// =============================================================
// produccionOperarios.js
// Eficiencia por operario (tiempo estándar de lo terminado ÷ tiempo real) por día,
// semana o mes, con su evolución, y la lista de operarios (nombre, turno, máquinas).
// =============================================================

import { h, selector, mostrarAviso, textoMinutos, textoPorcentaje, descargarArchivo } from './util.js';
import { estado } from './estado.js';
import * as almacenamiento from '../datos/almacenamiento.js';
import { cargarContexto } from './contextoProduccion.js';
import { eficienciaPorPeriodo } from '../logica/produccion.js';
import { armarCsv } from '../logica/exportar.js';

export const ADVERTENCIA_EFICIENCIA = 'La eficiencia NO debe usarse como único criterio para evaluar a una persona: el estándar todavía tiene valores [SUPUESTO] y [A VALIDAR] (sin cronometrar en planta), '
  + 'no mide la calidad ni el retrabajo, cambia según el tipo de trabajo que le tocó a cada uno, los nuevos tienen curva de aprendizaje y, cuando el tiempo real sale solo de la casilla HECHA, '
  + 'incluye esperas y pausas. Usala para detectar problemas de método, de máquina o de material, y siempre junto con el jefe y el operario.';

export async function seccionOperarios(contenedor, { refrescar }) {
  const ctx = await cargarContexto();
  const { prod } = ctx;
  let periodo = 'semana';
  let elegido = '';
  const zonaTabla = h('div', { class: 'tabla-desplazable' });
  const zonaGrafico = h('div');

  function dibujar() {
    const datos = eficienciaPorPeriodo(ctx.trabajos, periodo);
    const periodos = [...new Set(datos.map((d) => d.periodo))].sort().slice(-8);
    const valor = (op, p) => datos.find((d) => d.operarioId === op && d.periodo === p);
    zonaTabla.replaceChildren(h('table', { class: 'tabla-notas' },
      h('thead', {}, h('tr', {}, h('th', {}, 'Operario'), periodos.map((p) => h('th', {}, p)), h('th', {}, 'Total'), h('th', {}, 'Trabajos'), h('th', {}, 'Por casilla'))),
      h('tbody', {}, prod.operarios.map((op) => {
        const propios = datos.filter((d) => d.operarioId === op.id);
        const est = propios.reduce((s, d) => s + d.estandarMin, 0);
        const real = propios.reduce((s, d) => s + d.realMin, 0);
        const trabajos = propios.reduce((s, d) => s + d.trabajos, 0);
        const casilla = propios.reduce((s, d) => s + d.porCasilla, 0);
        return h('tr', { class: elegido === op.id ? 'fila-elegida' : '' },
          h('th', {}, h('button', { type: 'button', class: 'boton-celda', onclick: () => { elegido = elegido === op.id ? '' : op.id; dibujar(); } }, op.nombre)),
          periodos.map((p) => { const v = valor(op.id, p); return h('td', { class: claseEficiencia(v?.eficiencia), title: v ? `${textoMinutos(v.estandarMin)} estándar en ${textoMinutos(v.realMin)} reales` : '' }, v ? textoPorcentaje(v.eficiencia) : '—'); }),
          h('td', { class: claseEficiencia(real ? est / real : null) }, real ? textoPorcentaje(est / real) : '—'),
          h('td', {}, String(trabajos)),
          h('td', {}, trabajos ? textoPorcentaje(casilla / trabajos) : '—'));
      }))));
    zonaGrafico.replaceChildren(graficoEvolucion(datos, periodos, elegido));
  }

  const selectorPeriodo = selector([{ valor: 'dia', texto: 'Por día' }, { valor: 'semana', texto: 'Por semana' }, { valor: 'mes', texto: 'Por mes' }], periodo, {
    'aria-label': 'Período', onchange: (e) => { periodo = e.target.value; dibujar(); },
  });

  contenedor.replaceChildren(
    h('div', { class: 'aviso-caja' }, h('strong', {}, 'Cuidado: '), ADVERTENCIA_EFICIENCIA),
    h('div', { class: 'barra-botones' }, selectorPeriodo,
      h('button', { type: 'button', class: 'boton', onclick: () => exportar(ctx, periodo) }, 'Bajar a Excel (CSV)')),
    h('p', { class: 'texto-chico' }, 'Eficiencia = tiempo estándar de lo terminado ÷ tiempo real (100 % = trabaja al ritmo del estándar). "Por casilla" = parte de los trabajos cuyo tiempo real se estimó solo con la casilla HECHA (menos confiable que el cronómetro). Tocá un nombre para ver su evolución.'),
    zonaTabla, zonaGrafico,
    h('h2', {}, 'Operarios'),
    editorOperarios(prod, refrescar));
  dibujar();
}

function claseEficiencia(valor) {
  if (!Number.isFinite(valor)) return '';
  if (valor >= 0.95) return 'ef-alta';
  if (valor >= 0.8) return 'ef-media';
  return 'ef-baja';
}

/** Barras SVG: eficiencia del período (todos o el operario elegido), con la línea del 100 %. */
function graficoEvolucion(datos, periodos, operarioId) {
  if (!periodos.length) return h('p', { class: 'vacio' }, 'Todavía no hay trabajos terminados con tiempo real.');
  const valores = periodos.map((p) => {
    const filas = datos.filter((d) => d.periodo === p && (!operarioId || d.operarioId === operarioId));
    const est = filas.reduce((s, d) => s + d.estandarMin, 0);
    const real = filas.reduce((s, d) => s + d.realMin, 0);
    return real ? est / real : null;
  });
  const ancho = 640; const alto = 220; const margen = 34;
  const maximo = Math.max(1.3, ...valores.filter(Number.isFinite));
  const paso = (ancho - 2 * margen) / periodos.length;
  const y = (v) => alto - margen - (v / maximo) * (alto - 2 * margen);
  const partes = [`<svg viewBox="0 0 ${ancho} ${alto}" class="grafico-eficiencia" role="img" aria-label="Evolución de la eficiencia">`,
    `<text x="${margen}" y="16" class="grafico-titulo">Evolución ${operarioId ? `de ${estado.datos.produccion.operarios.find((o) => o.id === operarioId)?.nombre || operarioId}` : 'de todos'} (100 % = estándar)</text>`,
    `<line x1="${margen}" x2="${ancho - margen}" y1="${y(1)}" y2="${y(1)}" class="grafico-referencia"/>`,
    `<text x="${ancho - margen + 2}" y="${y(1) + 4}" class="grafico-eje">100 %</text>`];
  valores.forEach((v, i) => {
    const x = margen + i * paso + paso * 0.15;
    if (Number.isFinite(v)) {
      partes.push(`<rect x="${x}" y="${y(v)}" width="${paso * 0.7}" height="${alto - margen - y(v)}" class="grafico-barra ${claseEficiencia(v)}"><title>${Math.round(v * 100)} %</title></rect>`);
      partes.push(`<text x="${x + paso * 0.35}" y="${y(v) - 4}" text-anchor="middle" class="grafico-eje">${Math.round(v * 100)}</text>`);
    }
    partes.push(`<text x="${x + paso * 0.35}" y="${alto - margen + 14}" text-anchor="middle" class="grafico-eje">${periodos[i].replace(/^\d{4}-/, '')}</text>`);
  });
  partes.push('</svg>');
  return h('div', { class: 'grafico', html: partes.join('') });
}

function exportar(ctx, periodo) {
  const filas = eficienciaPorPeriodo(ctx.trabajos, periodo).map((d) => [d.operarioId, ctx.prod.operarios.find((o) => o.id === d.operarioId)?.nombre, d.periodo, d.estandarMin, d.realMin, d.eficiencia, d.trabajos, d.porCasilla]);
  descargarArchivo(`eficiencia-${periodo}.csv`, armarCsv(['Operario', 'Nombre', 'Período', 'Estándar (min)', 'Real (min)', 'Eficiencia', 'Trabajos', 'Por casilla'], filas));
}

function editorOperarios(prod, refrescar) {
  const lista = JSON.parse(JSON.stringify(prod.operarios));
  return h('div', {},
    h('table', { class: 'tabla-notas' },
      h('thead', {}, h('tr', {}, h('th', {}, 'Nombre'), h('th', {}, 'Turno'), h('th', {}, 'Máquinas que usa'), h('th', {}, 'Activo'))),
      h('tbody', {}, lista.map((op) => h('tr', {},
        h('td', {}, h('input', { type: 'text', value: op.nombre, oninput: (e) => { op.nombre = e.target.value; } })),
        h('td', {}, selector(prod.turnos.map((t) => ({ valor: t.id, texto: t.nombre })), op.turno, { onchange: (e) => { op.turno = e.target.value; } })),
        h('td', {}, prod.maquinas.map((m) => h('label', { class: 'casilla-chica' }, h('input', {
          type: 'checkbox', checked: op.maquinas.includes(m.id),
          onchange: (e) => { op.maquinas = e.target.checked ? [...new Set(op.maquinas.concat(m.id))] : op.maquinas.filter((x) => x !== m.id); },
        }), ` ${m.nombre}`))),
        h('td', {}, h('input', { type: 'checkbox', checked: op.activo !== false, onchange: (e) => { op.activo = e.target.checked; } })))))),
    h('button', { type: 'button', class: 'boton principal', onclick: async () => {
      if (lista.some((o) => !o.nombre.trim())) { mostrarAviso('Cada operario tiene que tener nombre', 'error'); return; }
      await almacenamiento.guardarOperarios(lista);
      estado.datos.produccion.operarios = lista;
      mostrarAviso('Operarios guardados', 'ok');
      refrescar();
    } }, 'Guardar operarios'));
}
