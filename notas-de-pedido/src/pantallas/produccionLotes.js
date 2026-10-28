// =============================================================
// produccionLotes.js
// Agrupamiento de renglones de distintas notas en LOTES (ver logica/agrupamiento.js y
// docs/AGRUPAMIENTO.md). El jefe elige criterios y nivel de similitud, el programa
// propone, y el jefe acepta, mueve, divide o deshace. Cada cambio se guarda y se puede
// deshacer (vuelve a la versión anterior).
// =============================================================

import { h, mostrarAviso, confirmar, fechaCorta, textoMinutos, textoPorcentaje } from './util.js';
import { estado } from './estado.js';
import * as almacenamiento from '../datos/almacenamiento.js';
import { cargarContexto, nombreMaquina } from './contextoProduccion.js';
import { CRITERIOS, proponerLotesProtegidos, totalesDeLotes, resumirLote, rearmarLotes, secuenciarLote } from '../logica/agrupamiento.js';

export async function seccionLotes(contenedor, { refrescar }) {
  const ctx = await cargarContexto();
  const { prod } = ctx;
  const opciones = JSON.parse(JSON.stringify(prod.agrupamiento));
  const tolerancia = () => opciones.criterios.desarrollo?.toleranciaMm ?? 0;
  // Se agrupan los renglones que todavía no empezaron.
  const disponibles = ctx.trabajos.filter((t) => !t.hecha && t.cronometro === 'sin_empezar' && t.tiempoValido);
  let lotes = rearmarLotes(ctx.lotesGuardados, disponibles, tolerancia());
  let separadas = [];
  let verSueltos = false;

  // ---------- criterios ----------
  const filasCriterios = CRITERIOS.map((c) => {
    const valor = opciones.criterios[c.id] ||= { activo: false, peso: 1 };
    const extra = c.id === 'desarrollo'
      ? h('label', {}, '± ', h('input', { type: 'number', min: 0, step: 1, value: valor.toleranciaMm ?? 5, class: 'campo-chico', oninput: (e) => { valor.toleranciaMm = Number(e.target.value) || 0; } }), ' mm')
      : c.id === 'largo'
        ? h('label', {}, '± ', h('input', { type: 'number', min: 0, step: 1, value: valor.toleranciaCm ?? 20, class: 'campo-chico', oninput: (e) => { valor.toleranciaCm = Number(e.target.value) || 0; } }), ' cm')
        : null;
    return h('tr', {},
      h('td', {}, h('label', {}, h('input', { type: 'checkbox', checked: valor.activo, onchange: (e) => { valor.activo = e.target.checked; } }), ' ', c.nombre)),
      h('td', {}, h('input', { type: 'number', min: 0, max: 10, step: 1, value: valor.peso, class: 'campo-chico', 'aria-label': `Peso de ${c.nombre}`, oninput: (e) => { valor.peso = Number(e.target.value) || 0; } })),
      h('td', {}, extra));
  });
  const textoSimilitud = h('strong', {}, textoPorcentaje(opciones.similitudMinima));
  const campo = (etiqueta, clave, atributos) => h('label', { class: 'campo-parametro' }, h('span', {}, etiqueta),
    h('input', { type: 'number', value: opciones[clave], class: 'campo-chico', ...atributos, oninput: (e) => { opciones[clave] = Number(e.target.value) || 0; } }));
  const panelCriterios = h('details', { class: 'panel-interno', open: !ctx.lotesGuardados.length },
    h('summary', {}, h('strong', {}, 'Criterios y restricciones')),
    h('table', { class: 'tabla-notas tabla-criterios' }, h('thead', {}, h('tr', {}, h('th', {}, 'Criterio (qué tienen que compartir)'), h('th', {}, 'Peso'), h('th', {}, 'Tolerancia'))), h('tbody', {}, filasCriterios)),
    h('label', { class: 'campo-parametro' }, h('span', {}, 'Nivel de similitud mínimo (todos los del lote entre sí): '), textoSimilitud,
      h('input', { type: 'range', min: 0.3, max: 1, step: 0.05, value: opciones.similitudMinima, oninput: (e) => { opciones.similitudMinima = Number(e.target.value); textoSimilitud.textContent = textoPorcentaje(opciones.similitudMinima); } })),
    h('div', { class: 'fila-campos' },
      campo('Ventana de entregas (días)', 'ventanaDias', { min: 0, step: 1 }),
      campo('Máximo por lote (min)', 'maxMinutosPorLote', { min: 10, step: 10 }),
      campo('Máximo de renglones por lote', 'maxRenglonesPorLote', { min: 2, step: 1 })),
    h('label', {}, h('input', { type: 'checkbox', checked: opciones.urgentesSolas, onchange: (e) => { opciones.urgentesSolas = e.target.checked; } }), ' Las urgentes se agrupan solo con urgentes'),
    h('br'),
    h('label', {}, h('input', { type: 'checkbox', checked: opciones.respetarMaquina, onchange: (e) => { opciones.respetarMaquina = e.target.checked; } }), ' Solo trabajos de la misma máquina'),
    h('p', { class: 'texto-chico' }, 'Siempre se verifica que ninguna urgente termine más tarde que sin agrupar; si pasaría, se separa del lote lo que la empuja.'),
    h('div', { class: 'barra-botones' },
      h('button', { type: 'button', class: 'boton', onclick: async () => { await almacenamiento.guardarCriteriosAgrupamiento(opciones); estado.datos.produccion.agrupamiento = JSON.parse(JSON.stringify(opciones)); mostrarAviso('Criterios guardados', 'ok'); } }, 'Guardar criterios'),
      h('button', { type: 'button', class: 'boton grande principal', onclick: () => proponer() }, 'Proponer lotes')));

  const zonaTotales = h('div');
  const zonaLotes = h('div', { class: 'lista-lotes' });

  function proponer() {
    const aceptados = lotes.filter((l) => l.aceptado);
    const enAceptados = new Set(aceptados.flatMap((l) => l.claves));
    const maquinas = Object.fromEntries(prod.maquinas.map((m) => [m.id, m.cantidad]));
    const resultado = proponerLotesProtegidos(disponibles.filter((t) => !enAceptados.has(t.clave)), opciones, maquinas);
    separadas = resultado.separadas;
    lotes = aceptados.concat(resultado.lotes.map((l, i) => ({ ...l, id: `P${String(i + 1).padStart(3, '0')}`, aceptado: false })));
    guardar('Propuesta lista: revisala y aceptá los lotes que sirvan');
  }

  async function guardar(mensaje) {
    const conMiembros = lotes.filter((l) => l.trabajos.length);
    // Se guardan solo los lotes de más de un renglón (los demás se hacen solos).
    await almacenamiento.guardarLotes(conMiembros.filter((l) => l.trabajos.length > 1).map((l) => ({ id: l.id, nombre: l.nombre || null, claves: l.trabajos.map((t) => t.clave), aceptado: Boolean(l.aceptado) })));
    lotes = rearmarLotes(conMiembros.filter((l) => l.trabajos.length > 1).map((l) => ({ id: l.id, nombre: l.nombre, claves: l.trabajos.map((t) => t.clave), aceptado: l.aceptado })), disponibles, tolerancia());
    if (mensaje) mostrarAviso(mensaje, 'ok');
    dibujar();
  }

  const cambiarLote = (lote, trabajos) => { lote.trabajos = trabajos; lote.claves = trabajos.map((t) => t.clave); lote.resumen = resumirLote(trabajos, tolerancia()); };

  function sacar(lote, trabajo) {
    cambiarLote(lote, lote.trabajos.filter((t) => t !== trabajo));
    guardar('Renglón separado del lote');
  }

  function moverA(lote, trabajo, destinoId) {
    const destino = lotes.find((l) => l.id === destinoId);
    if (!destino) return;
    cambiarLote(lote, lote.trabajos.filter((t) => t !== trabajo));
    cambiarLote(destino, secuenciarLote(destino.trabajos.concat(trabajo), tolerancia()));
    guardar(`Renglón movido al lote ${destino.id}`);
  }

  function dividir(lote, desde) {
    const segunda = lote.trabajos.slice(desde);
    cambiarLote(lote, lote.trabajos.slice(0, desde));
    lotes.push({ id: `${lote.id}b`, aceptado: lote.aceptado, trabajos: segunda, claves: segunda.map((t) => t.clave), resumen: resumirLote(segunda, tolerancia()) });
    guardar('Lote dividido en dos');
  }

  function deshacerLote(lote) {
    if (!confirmar(`¿Deshacer el lote ${lote.id}? Sus ${lote.trabajos.length} renglones se hacen por separado.`)) return;
    cambiarLote(lote, []);
    guardar('Lote deshecho');
  }

  function aceptar(lote, valor = true) {
    lote.aceptado = valor;
    guardar(valor ? `Lote ${lote.id} aceptado` : `Lote ${lote.id} vuelve a propuesta`);
  }

  function dibujar() {
    const grupos = lotes.filter((l) => l.trabajos.length > 1);
    const totales = totalesDeLotes(lotes);
    zonaTotales.replaceChildren(h('div', { class: 'tarjetas-kpi' },
      kpi('Renglones por hacer', String(disponibles.length)),
      kpi('Lotes de 2 o más', String(grupos.length), `${grupos.filter((l) => l.aceptado).length} aceptados`),
      kpi('Tiempo sin agrupar', textoMinutos(totales.minutosSinAgrupar)),
      kpi('Tiempo con los lotes', textoMinutos(totales.minutosConLotes)),
      kpi('Ahorro de setup', textoMinutos(totales.ahorroMin), `${textoPorcentaje(totales.ahorroPorcentaje, 1)} del total · ${textoPorcentaje(totales.ahorroSetupPorcentaje)} del setup`)),
    separadas.length ? h('p', { class: 'aviso' }, `Para no demorar urgentes se separaron ${separadas.length} renglón(es) de sus lotes.`) : null,
    h('div', { class: 'barra-botones' },
      h('button', { type: 'button', class: 'boton', onclick: async () => { try { await almacenamiento.deshacerLotes(); mostrarAviso('Se deshizo el último cambio', 'ok'); refrescar(); } catch (error) { mostrarAviso(error.message, 'error'); } } }, 'Deshacer último cambio'),
      h('button', { type: 'button', class: 'boton', onclick: () => { grupos.forEach((l) => { l.aceptado = true; }); guardar('Todos los lotes aceptados'); } }, 'Aceptar todos'),
      h('button', { type: 'button', class: 'boton', onclick: () => { verSueltos = !verSueltos; dibujar(); } }, verSueltos ? 'Ocultar los que van solos' : 'Ver también los que van solos'),
      h('a', { class: 'boton', href: '#produccion/asignacion' }, 'Ir a asignar')));
    const mostrar = (verSueltos ? lotes : grupos).filter((l) => l.trabajos.length);
    zonaLotes.replaceChildren(...(mostrar.length ? mostrar.map((lote) => tarjetaLote(lote, grupos)) : [h('p', { class: 'vacio' }, ctx.trabajos.length ? 'Sin lotes todavía: elegí los criterios y tocá "Proponer lotes".' : 'No hay notas emitidas pendientes.')]));
  }

  function tarjetaLote(lote, grupos) {
    const r = lote.resumen;
    const otros = grupos.filter((l) => l !== lote && l.resumen.maquina === r.maquina);
    return h('article', { class: `tarjeta-lote${lote.aceptado ? ' aceptado' : ''}${lote.trabajos.length > 1 ? '' : ' suelto'}` },
      h('header', {},
        h('strong', {}, lote.trabajos.length > 1 ? `Lote ${lote.id}` : 'Solo'), ' · ', nombreMaquina(r.maquina),
        ' · entrega ', fechaCorta(`${r.fechaEntrega}T12:00:00`), r.prioridad === 'urgente' ? h('span', { class: 'etiqueta-urgente' }, 'URGENTE') : null,
        ' · ', h('strong', {}, `${lote.trabajos.length} renglón(es)`),
        lote.trabajos.length > 1 ? [' · ahorra ', h('strong', {}, textoMinutos(r.ahorroMin)), ` (${textoPorcentaje(r.ahorroPorcentaje)})`] : null,
        lote.aceptado ? h('span', { class: 'etiqueta-estado prod-hecha' }, 'aceptado') : null),
      lote.trabajos.length > 1 ? h('p', { class: 'texto-chico' }, `Setup una vez + unitarios: ${textoMinutos(r.setupConLoteMin)} de setup + ${textoMinutos(r.unitarioMin)} de trabajo = ${textoMinutos(r.minutosConLote)} (sin agrupar: ${textoMinutos(r.minutosSinAgrupar)}).`) : null,
      h('table', { class: 'tabla-notas' },
        h('thead', {}, h('tr', {}, h('th', {}, 'NP'), h('th', {}, 'Renglón'), h('th', {}, 'Entrega'), h('th', {}, 'Tiempo'), h('th', {}, 'Ahorra'), h('th', {}, ''))),
        h('tbody', {}, lote.trabajos.map((t, i) => h('tr', {},
          h('td', {}, String(t.numeroNota), t.prioridad === 'urgente' ? ' ⚑' : ''),
          h('td', {}, t.descripcion, ' ', h('span', { class: 'texto-chico' }, `× ${t.piezas}`)),
          h('td', {}, fechaCorta(`${t.fechaEntrega}T12:00:00`)),
          h('td', {}, textoMinutos(t.minutos)),
          h('td', {}, i && r.ahorros[i] ? textoMinutos(r.ahorros[i]) : '—'),
          h('td', { class: 'acciones' },
            lote.trabajos.length > 1 ? h('button', { type: 'button', class: 'boton mini', onclick: () => sacar(lote, t) }, 'Sacar') : null,
            lote.trabajos.length > 2 && i > 0 ? h('button', { type: 'button', class: 'boton mini', title: 'Dividir el lote desde este renglón', onclick: () => dividir(lote, i) }, 'Dividir aquí') : null,
            otros.length ? h('select', { class: 'selector-mini', 'aria-label': 'Mover a otro lote', onchange: (e) => moverA(lote, t, e.target.value) },
              h('option', { value: '' }, 'Mover a…'), otros.map((o) => h('option', { value: o.id }, `Lote ${o.id}`))) : null))))),
      lote.trabajos.length > 1 ? h('div', { class: 'barra-botones' },
        lote.aceptado ? h('button', { type: 'button', class: 'boton chico', onclick: () => aceptar(lote, false) }, 'Volver a propuesta') : h('button', { type: 'button', class: 'boton chico principal', onclick: () => aceptar(lote) }, 'Aceptar'),
        h('button', { type: 'button', class: 'boton chico peligro', onclick: () => deshacerLote(lote) }, 'Deshacer lote')) : null);
  }

  contenedor.replaceChildren(
    h('p', {}, 'Juntá renglones de distintas notas que comparten la preparación de la máquina para hacer el setup una sola vez. Cómo funciona y qué se descartó: ', h('code', {}, 'docs/AGRUPAMIENTO.md'), '.'),
    panelCriterios, zonaTotales, zonaLotes);
  dibujar();
}

export function kpi(titulo, valor, detalle = null) {
  return h('div', { class: 'tarjeta-kpi' }, h('span', { class: 'texto-chico' }, titulo), h('strong', { class: 'dato-grande' }, valor), detalle ? h('span', { class: 'texto-chico' }, detalle) : null);
}
