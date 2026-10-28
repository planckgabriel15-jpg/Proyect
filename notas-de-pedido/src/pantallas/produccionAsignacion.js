// =============================================================
// produccionAsignacion.js
// Asignación a operarios por día y turno, con la carga calculada con el tiempo estándar:
// - semana: operarios × días (minutos asignados ÷ capacidad) y capacidad por máquina;
// - pendientes sin asignar (por lote): asignar a mano o "Asignar automáticamente";
// - asignados: reprogramar (otro día u operario) o desasignar;
// - hoja de ruta imprimible por operario y día.
// =============================================================

import { h, selector, mostrarAviso, confirmar, fechaCorta, textoMinutos, textoPorcentaje } from './util.js';
import * as almacenamiento from '../datos/almacenamiento.js';
import { cargarContexto, quienSoy, nombreOperario, nombreMaquina } from './contextoProduccion.js';
import {
  asignarRenglon, asignarAutomaticamente, registroVacio, cargaPorOperarioYDia, cargaPorMaquinaYDia,
  capacidadDeOperario, capacidadDeMaquina, sumarDiasHabiles,
} from '../logica/produccion.js';

/** Guarda varias asignaciones juntas (una escritura por nota). */
export async function guardarAsignaciones(ctx, asignaciones) {
  const quien = quienSoy();
  const porNota = new Map();
  for (const a of asignaciones) {
    const registro = porNota.get(a.notaId) || ctx.registros[a.notaId] || registroVacio(a.notaId, ctx.porClave.get(a.clave)?.demo);
    porNota.set(a.notaId, asignarRenglon(registro, a.renglonId, a, quien));
  }
  await almacenamiento.guardarRegistros([...porNota.values()]);
}

export async function seccionAsignacion(contenedor, { refrescar }) {
  const ctx = await cargarContexto();
  const { prod, hoy } = ctx;
  const operarios = prod.operarios.filter((o) => o.activo !== false);
  let inicioSemana = sumarDiasHabiles(hoy, 0, prod.diasHabiles);
  const zonaSemana = h('div', { class: 'tabla-desplazable' });
  const zonaMaquinas = h('div', { class: 'tabla-desplazable' });
  const zonaPendientes = h('div');
  const zonaDia = h('div');

  const dias = () => Array.from({ length: 5 }, (_, i) => sumarDiasHabiles(inicioSemana, i, prod.diasHabiles));

  function celdaCarga(minutos, capacidad, alTocar) {
    const uso = capacidad ? minutos / capacidad : 0;
    const clase = uso > 1 ? 'carga-excedida' : uso > 0.85 ? 'carga-alta' : uso > 0 ? 'carga-normal' : 'carga-vacia';
    return h('td', { class: `celda-carga ${clase}` }, h('button', { type: 'button', class: 'boton-celda', onclick: alTocar, title: `${Math.round(minutos)} de ${capacidad} min` },
      h('span', { class: 'barra-carga', style: `--uso:${Math.min(100, Math.round(uso * 100))}%` }), `${textoMinutos(minutos)} · ${textoPorcentaje(uso)}`));
  }

  function dibujarSemana() {
    const carga = cargaPorOperarioYDia(ctx.trabajos);
    const lista = dias();
    zonaSemana.replaceChildren(h('table', { class: 'tabla-notas tabla-carga' },
      h('thead', {}, h('tr', {}, h('th', {}, 'Operario (turno)'), lista.map((d) => h('th', {}, fechaCorta(`${d}T12:00:00`))))),
      h('tbody', {}, operarios.map((op) => h('tr', {},
        h('th', {}, op.nombre, h('span', { class: 'texto-chico' }, ` (${prod.turnos.find((x) => x.id === op.turno)?.nombre || op.turno}) `), h('a', { class: 'enlace-chico', href: `#hoja-ruta/operario/${op.id}/${lista[0]}`, title: 'Hoja de ruta imprimible' }, 'hoja')),
        lista.map((d) => celdaCarga(carga[op.id]?.[d] || 0, capacidadDeOperario(op, prod), () => dibujarDia(op, d))))))));
    const porMaquina = cargaPorMaquinaYDia(ctx.trabajos);
    zonaMaquinas.replaceChildren(h('table', { class: 'tabla-notas tabla-carga' },
      h('thead', {}, h('tr', {}, h('th', {}, 'Máquina (cantidad)'), lista.map((d) => h('th', {}, fechaCorta(`${d}T12:00:00`))))),
      h('tbody', {}, prod.maquinas.map((m) => h('tr', {},
        h('th', {}, `${m.nombre} (${m.cantidad})`),
        lista.map((d) => celdaCarga(porMaquina[m.id]?.[d] || 0, capacidadDeMaquina(m, prod, operarios), () => {})))))));
  }

  function dibujarDia(op, dia) {
    const tareas = ctx.trabajos.filter((t) => t.operarioId === op.id && t.fecha === dia);
    zonaDia.replaceChildren(h('section', { class: 'panel-interno' },
      h('h3', {}, `${op.nombre} – ${fechaCorta(`${dia}T12:00:00`)}: ${textoMinutos(tareas.reduce((s, t) => s + t.minutosEnLote, 0))} de ${capacidadDeOperario(op, prod)} min`),
      tareas.length ? tablaAsignados(tareas) : h('p', { class: 'vacio' }, 'Sin trabajos ese día.'),
      h('a', { class: 'boton', href: `#hoja-ruta/operario/${op.id}/${dia}` }, 'Hoja de ruta para imprimir')));
    zonaDia.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function selectorOperario(maquina, actual) {
    const habilitados = operarios.filter((o) => o.maquinas.includes(maquina));
    return selector([{ valor: '', texto: '— operario —' }].concat((habilitados.length ? habilitados : operarios).map((o) => ({ valor: o.id, texto: o.nombre }))), actual || '', { 'aria-label': 'Operario' });
  }

  function tablaAsignados(tareas) {
    return h('table', { class: 'tabla-notas' },
      h('thead', {}, h('tr', {}, h('th', {}, 'NP'), h('th', {}, 'Renglón'), h('th', {}, 'Máquina'), h('th', {}, 'Tiempo'), h('th', {}, 'Estado'), h('th', {}, 'Reprogramar'))),
      h('tbody', {}, tareas.map((t) => {
        const op = selectorOperario(t.maquina, t.operarioId);
        const dia = h('input', { type: 'date', value: t.fecha || '', 'aria-label': 'Día' });
        return h('tr', {},
          h('td', {}, String(t.numeroNota)),
          h('td', {}, t.descripcion, t.loteActual ? h('span', { class: 'etiqueta-demo' }, t.loteActual) : null),
          h('td', {}, nombreMaquina(t.maquina)),
          h('td', {}, textoMinutos(t.minutosEnLote)),
          h('td', {}, t.hecha ? 'HECHA' : t.cronometro === 'sin_empezar' ? 'programada' : 'en curso'),
          h('td', { class: 'acciones' }, t.hecha ? '—' : [op, dia,
            h('button', { type: 'button', class: 'boton mini principal', onclick: async () => {
              if (!op.value || !dia.value) { mostrarAviso('Elegí operario y día', 'error'); return; }
              const operario = operarios.find((o) => o.id === op.value);
              await guardarAsignaciones(ctx, [{ ...t, operarioId: op.value, fecha: dia.value, turno: operario.turno }]);
              mostrarAviso('Reprogramado', 'ok'); refrescar();
            } }, 'Guardar'),
            h('button', { type: 'button', class: 'boton mini peligro', onclick: async () => {
              await guardarAsignaciones(ctx, [{ ...t, operarioId: null, fecha: null, turno: null }]);
              mostrarAviso('Desasignado', 'ok'); refrescar();
            } }, 'Quitar')]));
      })));
  }

  function dibujarPendientes() {
    const sinAsignar = ctx.trabajos.filter((t) => !t.hecha && !t.operarioId && t.tiempoValido);
    const porLote = new Map();
    for (const t of sinAsignar) {
      const clave = t.loteActual || t.clave;
      if (!porLote.has(clave)) porLote.set(clave, []);
      porLote.get(clave).push(t);
    }
    const grupos = [...porLote.entries()].sort((a, b) => String(a[1][0].fechaEntrega).localeCompare(String(b[1][0].fechaEntrega)));
    zonaPendientes.replaceChildren(
      h('div', { class: 'barra-botones' },
        h('strong', {}, `${sinAsignar.length} renglón(es) sin asignar (${textoMinutos(sinAsignar.reduce((s, t) => s + t.minutosEnLote, 0))})`),
        h('button', { type: 'button', class: 'boton principal', disabled: !sinAsignar.length, onclick: () => asignarTodo() }, 'Asignar automáticamente')),
      h('p', { class: 'texto-chico' }, 'Automático: los lotes enteros, urgentes y entregas más cercanas primero, al operario habilitado para esa máquina que los termina antes, desde hoy, sin pasar la capacidad del turno. Después podés reprogramar a mano.'),
      grupos.length ? h('table', { class: 'tabla-notas' },
        h('thead', {}, h('tr', {}, h('th', {}, 'Lote / NP'), h('th', {}, 'Renglones'), h('th', {}, 'Máquina'), h('th', {}, 'Entrega'), h('th', {}, 'Tiempo'), h('th', {}, 'Asignar'))),
        h('tbody', {}, grupos.slice(0, 150).map(([clave, lista]) => {
          const op = selectorOperario(lista[0].maquina);
          const dia = h('input', { type: 'date', value: hoy, 'aria-label': 'Día' });
          return h('tr', { class: lista.some((t) => t.prioridad === 'urgente') ? 'fila-urgente' : '' },
            h('td', {}, lista[0].loteActual ? h('strong', {}, `Lote ${lista[0].loteActual}`) : `NP ${lista[0].numeroNota}`),
            h('td', {}, lista.map((t) => `NP ${t.numeroNota}: ${t.descripcion}`).join(' · ')),
            h('td', {}, nombreMaquina(lista[0].maquina)),
            h('td', {}, fechaCorta(`${lista.map((t) => t.fechaEntrega).sort()[0]}T12:00:00`)),
            h('td', {}, textoMinutos(lista.reduce((s, t) => s + t.minutosEnLote, 0))),
            h('td', { class: 'acciones' }, op, dia, h('button', { type: 'button', class: 'boton mini principal', onclick: async () => {
              if (!op.value) { mostrarAviso('Elegí un operario', 'error'); return; }
              const operario = operarios.find((o) => o.id === op.value);
              await guardarAsignaciones(ctx, lista.map((t) => ({ ...t, operarioId: op.value, fecha: dia.value || hoy, turno: operario.turno, loteId: t.loteActual })));
              mostrarAviso(`Asignado a ${operario.nombre}`, 'ok'); refrescar();
            } }, 'Asignar')));
        }))) : h('p', { class: 'vacio' }, 'No hay renglones sin asignar.'));
  }

  async function asignarTodo() {
    const sinAsignar = ctx.trabajos.filter((t) => !t.hecha && !t.operarioId && t.tiempoValido);
    const lotes = ctx.lotes.map((l) => ({ ...l, trabajos: l.trabajos.filter((t) => sinAsignar.includes(t)) })).filter((l) => l.trabajos.length);
    const propuesta = asignarAutomaticamente(lotes, ctx.trabajos.filter((t) => t.operarioId), prod, operarios, hoy);
    if (!propuesta.length) { mostrarAviso('No hay operarios habilitados para esas máquinas', 'error'); return; }
    const ultimo = propuesta.map((a) => a.fecha).sort().pop();
    if (!confirmar(`Se asignan ${propuesta.length} renglones, hasta el ${fechaCorta(`${ultimo}T12:00:00`)}. ¿Seguir?`)) return;
    await guardarAsignaciones(ctx, propuesta);
    mostrarAviso('Asignación automática lista', 'ok');
    refrescar();
  }

  const navegar = (dias) => { inicioSemana = sumarDiasHabiles(inicioSemana, dias, prod.diasHabiles); dibujarSemana(); };
  contenedor.replaceChildren(
    h('div', { class: 'barra-botones' },
      h('button', { type: 'button', class: 'boton chico', onclick: () => { inicioSemana = restar(inicioSemana, prod); dibujarSemana(); } }, '← Semana anterior'),
      h('button', { type: 'button', class: 'boton chico', onclick: () => { inicioSemana = sumarDiasHabiles(hoy, 0, prod.diasHabiles); dibujarSemana(); } }, 'Hoy'),
      h('button', { type: 'button', class: 'boton chico', onclick: () => navegar(5) }, 'Semana siguiente →')),
    h('h2', {}, 'Carga por operario (tiempo estándar ÷ capacidad del turno)'),
    h('p', { class: 'texto-chico' }, 'Tocá una celda para ver y reprogramar los trabajos de ese día. Verde: con lugar · amarillo: más de 85 % · rojo: pasado de capacidad.'),
    zonaSemana, zonaDia,
    h('h2', {}, 'Capacidad por máquina'),
    zonaMaquinas,
    h('h2', {}, 'Sin asignar'),
    zonaPendientes);
  dibujarSemana();
  dibujarPendientes();
}

function restar(dia, prod) {
  const [a, m, d] = dia.split('-').map(Number);
  const f = new Date(a, m - 1, d - 7);
  return sumarDiasHabiles(`${f.getFullYear()}-${String(f.getMonth() + 1).padStart(2, '0')}-${String(f.getDate()).padStart(2, '0')}`, 0, prod.diasHabiles);
}
