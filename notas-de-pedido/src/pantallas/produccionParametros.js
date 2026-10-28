// =============================================================
// produccionParametros.js
// Tabla editable de los parámetros del modelo de tiempos (cada uno con unidad, fuente y
// estado), importación del CSV de la hoja PARAMETROS_API, tiempos de los productos sin
// perfil y RECALIBRACIÓN con lo real (desvío por nota terminada).
// Los cambios se guardan aparte (almacenamiento.guardarCambiosTiempos) y se pueden
// descartar para volver a los valores del estudio (datos/tiempos-mtm.json).
// =============================================================

import { h, selector, mostrarAviso, confirmar, textoMinutos, textoPorcentaje, descargarArchivo } from './util.js';
import { estado } from './estado.js';
import * as almacenamiento from '../datos/almacenamiento.js';
import { cargarContexto } from './contextoProduccion.js';
import { prepararModelo, calcularNotaMtm } from '../logica/tiempos.js';
import { desviosPorNota } from '../logica/produccion.js';
import { armarCsv, leerCsvParametros } from '../logica/exportar.js';
import { formatearCorto } from '../logica/numeros.js';

/** Ejemplo EJ1 de la planilla (canaleta americana 3 m × 4): sirve para ver el efecto de un cambio. */
function ejemploEj1(modelo) {
  const material = modelo.materiales.find((m) => m.codigo === 'GALV-C25');
  return calcularNotaMtm([{ tipoPerfil: 'ESTANDAR', largoM: 3, desarrolloMm: 333, material, cantidad: 4, pliegues: { SIMPLE: 4, CIERRE180: 1 } }], modelo).totalMin;
}

export async function seccionParametros(contenedor, { refrescar }) {
  const ctx = await cargarContexto();
  const tabla = estado.datos.tiemposMtm;
  const editados = { ...(ctx.cambios?.parametros || {}) };
  const sinPerfil = JSON.parse(JSON.stringify(ctx.cambios?.productosSinPerfil || tabla.productosSinPerfil));
  const filtros = { grupo: '', estado: '', texto: '' };
  const zonaTabla = h('div', { class: 'tabla-desplazable' });
  const vistaPrevia = h('strong', {});

  const valorActual = (p) => (p.clave in editados ? editados[p.clave] : p.valor);
  const modeloEditado = () => prepararModelo(tabla, estado.datos.config, { parametros: editados, productosSinPerfil: sinPerfil });
  const actualizarVista = () => {
    const minutos = ejemploEj1(modeloEditado());
    vistaPrevia.textContent = `${formatearCorto(minutos, 1)} min (estudio: 15,5 min)`;
  };

  function dibujar() {
    const lista = tabla.parametros.filter((p) => (!filtros.grupo || p.grupo === filtros.grupo)
      && (!filtros.estado || String(p.estado).includes(filtros.estado))
      && (!filtros.texto || `${p.clave} ${p.descripcion}`.toLowerCase().includes(filtros.texto)));
    zonaTabla.replaceChildren(h('table', { class: 'tabla-notas tabla-parametros' },
      h('thead', {}, h('tr', {}, h('th', {}, 'Parámetro'), h('th', {}, 'Valor'), h('th', {}, 'Unidad'), h('th', {}, 'Estado'), h('th', {}, 'Fuente'))),
      h('tbody', {}, lista.map((p) => {
        const cambiado = p.clave in editados && String(editados[p.clave]) !== String(p.valor);
        const campo = typeof p.valor === 'number'
          ? h('input', { type: 'number', step: 'any', value: valorActual(p), class: `campo-chico${cambiado ? ' cambiado' : ''}`, 'aria-label': p.clave, oninput: (e) => {
            const numero = Number(e.target.value);
            if (e.target.value === '' || !Number.isFinite(numero)) { e.target.classList.add('con-error'); return; }
            e.target.classList.remove('con-error');
            if (numero === p.valor) delete editados[p.clave]; else editados[p.clave] = numero;
            actualizarVista();
          } })
          : selector([{ valor: 'HIDRAULICA', texto: 'HIDRAULICA' }, { valor: 'MANUAL', texto: 'MANUAL' }], valorActual(p), { onchange: (e) => { if (e.target.value === p.valor) delete editados[p.clave]; else editados[p.clave] = e.target.value; actualizarVista(); } });
        return h('tr', {},
          h('td', {}, h('code', {}, p.clave), h('div', { class: 'texto-chico' }, p.descripcion)),
          h('td', {}, campo, cambiado ? h('div', { class: 'texto-chico' }, `estudio: ${p.valor}`) : null),
          h('td', {}, p.unidad),
          h('td', {}, h('span', { class: `estado-parametro ${/VALIDAR/.test(p.estado) ? 'validar' : /SUPUESTO/.test(p.estado) ? 'supuesto' : 'dato'}` }, p.estado)),
          h('td', { class: 'texto-chico celda-fuente' }, p.fuente));
      }))));
  }

  const grupos = [...new Set(tabla.parametros.map((p) => p.grupo))];
  const cuentas = (texto) => tabla.parametros.filter((p) => String(p.estado).includes(texto)).length;

  async function guardarTodo() {
    for (const f of sinPerfil) {
      if (!(f.setupS >= 0) || !(f.piezaS >= 0)) { mostrarAviso(`Tiempo inválido en el grupo "${f.grupo}"`, 'error'); return; }
    }
    await almacenamiento.guardarCambiosTiempos({ parametros: editados, productosSinPerfil: sinPerfil, fuente: 'editado en pantalla' });
    mostrarAviso('Parámetros guardados: los tiempos se recalculan con estos valores', 'ok');
    refrescar();
  }

  const archivo = h('input', { type: 'file', accept: '.csv,text/csv', hidden: true, onchange: async (e) => {
    const texto = await e.target.files[0]?.text();
    if (!texto) return;
    const { valores, errores } = leerCsvParametros(texto);
    const conocidas = new Set(tabla.parametros.map((p) => p.clave));
    const usados = Object.entries(valores).filter(([clave]) => conocidas.has(clave));
    if (!usados.length) { mostrarAviso(errores[0] || 'El archivo no tiene parámetros conocidos', 'error', 8); return; }
    if (!confirmar(`Se van a cargar ${usados.length} valores de la planilla${errores.length ? ` (${errores.length} filas con problemas)` : ''}. ¿Seguir?`)) return;
    for (const [clave, valor] of usados) {
      const original = tabla.parametros.find((p) => p.clave === clave).valor;
      if (valor === original) delete editados[clave]; else editados[clave] = valor;
    }
    await almacenamiento.guardarCambiosTiempos({ parametros: editados, productosSinPerfil: sinPerfil, fuente: 'importado de PARAMETROS_API' });
    mostrarAviso('Valores importados de PARAMETROS_API', 'ok');
    refrescar();
  } });

  // ---------- recalibración ----------
  const desvios = desviosPorNota(ctx.notasEstado).filter((d) => d.desvio !== null && d.realMin > 0);
  const totalEstandar = desvios.reduce((s, d) => s + d.estandarMin, 0);
  const totalReal = desvios.reduce((s, d) => s + d.realMin, 0);
  const sugerida = totalReal > 0 ? totalEstandar / totalReal : null;
  const p = ctx.modelo.p;
  const semaforo = (d) => (Math.abs(d) <= p.p_err_ok ? 'verde' : Math.abs(d) <= p.p_err_alerta ? 'amarillo' : 'rojo');
  const porColor = { verde: 0, amarillo: 0, rojo: 0 };
  desvios.forEach((d) => { porColor[semaforo(d.desvio)] += 1; });

  contenedor.replaceChildren(
    h('div', { class: 'aviso-caja' },
      h('strong', {}, `Valores iniciales del ${tabla.version}. `),
      `${cuentas('VALIDAR')} parámetros están [A VALIDAR] y ${cuentas('SUPUESTO')} son [SUPUESTO]: PENDIENTES DE VALIDAR CON CRONOMETRAJE en planta. `,
      'Hasta entonces el tiempo sirve para comparar notas entre sí y programar, no como estándar de pago ni plazo comprometido.'),
    h('p', {}, 'Con estos valores, el ejemplo EJ1 de la planilla (canaleta americana 3 m × 4) da: ', vistaPrevia),
    h('div', { class: 'filtros' },
      selector([{ valor: '', texto: 'Todos los grupos' }].concat(grupos.map((g) => ({ valor: g, texto: g }))), '', { 'aria-label': 'Grupo', onchange: (e) => { filtros.grupo = e.target.value; dibujar(); } }),
      selector([{ valor: '', texto: 'Todos los estados' }, { valor: 'VALIDAR', texto: '[A VALIDAR]' }, { valor: 'SUPUESTO', texto: '[SUPUESTO]' }, { valor: 'DATO', texto: 'DATO' }], '', { 'aria-label': 'Estado', onchange: (e) => { filtros.estado = e.target.value; dibujar(); } }),
      h('input', { type: 'search', class: 'buscador', placeholder: 'Buscar parámetro', oninput: (e) => { filtros.texto = e.target.value.toLowerCase(); dibujar(); } })),
    zonaTabla,
    h('details', { class: 'panel-interno' }, h('summary', {}, 'Valores calculados (no se editan: salen de otros)'),
      h('ul', {}, tabla.calculados.map((c) => h('li', {}, h('code', {}, c.clave), ` = ${c.formula} → `, h('strong', {}, formatearCorto(ctx.modelo.p[c.clave], 3)))))),
    h('h3', {}, 'Productos sin perfil plegado (tiempo por unidad, en segundos de tiempo normal)'),
    h('table', { class: 'tabla-notas' },
      h('thead', {}, h('tr', {}, h('th', {}, 'Grupo del catálogo'), h('th', {}, 'Setup (s)'), h('th', {}, 'Por pieza (s)'), h('th', {}, 'Estado'), h('th', {}, 'Fuente'))),
      h('tbody', {}, sinPerfil.map((f) => h('tr', {},
        h('td', {}, f.grupo === '*' ? 'cualquier otro' : f.grupo),
        h('td', {}, h('input', { type: 'number', min: 0, value: f.setupS, class: 'campo-chico', oninput: (e) => { f.setupS = Number(e.target.value); } })),
        h('td', {}, h('input', { type: 'number', min: 0, value: f.piezaS, class: 'campo-chico', oninput: (e) => { f.piezaS = Number(e.target.value); } })),
        h('td', {}, f.estado), h('td', { class: 'texto-chico' }, f.fuente))))),
    h('div', { class: 'barra-botones' },
      h('button', { type: 'button', class: 'boton grande principal', onclick: guardarTodo }, 'Guardar cambios'),
      h('button', { type: 'button', class: 'boton', onclick: () => archivo.click() }, 'Importar CSV de PARAMETROS_API'), archivo,
      h('button', { type: 'button', class: 'boton', onclick: () => descargarArchivo('parametros-tiempos.csv', armarCsv(['Clave', 'Valor', 'Unidad', 'Estado', 'Grupo', 'Descripción', 'Fuente'],
        tabla.parametros.map((x) => [x.clave, valorActual(x), x.unidad, x.estado, x.grupo, x.descripcion, x.fuente]))) }, 'Bajar a Excel (CSV)'),
      h('button', { type: 'button', class: 'boton peligro', disabled: !ctx.cambios, onclick: async () => {
        if (!confirmar('¿Volver a los valores del estudio? Se pierden los cambios guardados.')) return;
        await almacenamiento.descartarCambiosTiempos();
        mostrarAviso('Valores del estudio restaurados', 'ok');
        refrescar();
      } }, 'Volver a los valores del estudio')),
    ctx.cambios ? h('p', { class: 'texto-chico' }, `Cambios guardados el ${new Date(ctx.cambios.fecha).toLocaleString('es-AR')} (${ctx.cambios.fuente || 'editado'}).`) : null,
    h('h2', {}, 'Recalibración con lo real'),
    h('p', {}, `Notas terminadas con tiempo real: ${desvios.length}. Semáforo (±${textoPorcentaje(p.p_err_ok)} verde, ±${textoPorcentaje(p.p_err_alerta)} amarillo): `,
      h('span', { class: 'ef-alta' }, ` ${porColor.verde} verdes `), h('span', { class: 'ef-media' }, ` ${porColor.amarillo} amarillas `), h('span', { class: 'ef-baja' }, ` ${porColor.rojo} rojas `)),
    sugerida ? h('p', {}, `Real total ${textoMinutos(totalReal)} contra ${textoMinutos(totalEstandar)} estándar: eficiencia observada `, h('strong', {}, textoPorcentaje(sugerida, 1)),
      '. ', h('button', { type: 'button', class: 'boton chico', onclick: () => { editados.p_eficiencia = Math.round(sugerida * 1000) / 1000; dibujar(); actualizarVista(); mostrarAviso('p_eficiencia cargada: revisá y tocá "Guardar cambios"', 'info', 6); } }, 'Usar como p_eficiencia')) : null,
    h('ol', { class: 'texto-chico' },
      h('li', {}, 'Si una nota queda en rojo, primero ver si el método real coincide con el modelado (en el estudio de Almeida y Ferreira la mayoría de los desvíos fueron de método).'),
      h('li', {}, 'Si coincide, cronometrar el elemento (setup, corte, golpe, volteo, detalle) y cargar el valor medido acá: pasa de [A VALIDAR] a dato propio.'),
      h('li', {}, 'Con 30 o más notas terminadas, ajustar por regresión el tiempo real contra las variables del modelo (golpes × piezas, chapas, metros, detalles, setup), como recomienda el informe MTM (sección 11).'),
      h('li', {}, 'Ojo: los tiempos por casilla HECHA (sin cronómetro) incluyen esperas; para recalibrar conviene usar los del cronómetro.')));
  dibujar();
  actualizarVista();
}
