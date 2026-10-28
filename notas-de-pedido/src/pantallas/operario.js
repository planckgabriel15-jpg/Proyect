// =============================================================
// operario.js
// Pantalla del OPERARIO (pensada para el celular o una tablet en el taller):
// sus trabajos del día, en orden, con el dibujo; botones Iniciar / Pausar / Reanudar
// (opcionales) y la casilla HECHA, que guarda la hora sola.
// El jefe también puede abrirla para cualquier operario (#operario/<id>).
// =============================================================

import { h, selector, mostrarAviso, fechaCorta, textoMinutos, hoyIso } from './util.js';
import { estado, ir } from './estado.js';
import * as almacenamiento from '../datos/almacenamiento.js';
import { cargarContexto, quienSoy, esJefe, nombreMaquina } from './contextoProduccion.js';
import { marcarHecha, registrarEvento, registroVacio, capacidadDeOperario, diaDe } from '../logica/produccion.js';
import { svgDelPerfil } from '../vistas2d/perfilSvg.js';
import { svgDeEspecial } from '../vistas2d/especialSvg.js';

export const LIMITE_CASILLA = 'Si solo marcás HECHA (sin Iniciar), el tiempo real se estima desde tu HECHA anterior del día (o el inicio del turno): '
  + 'incluye pausas, esperas y lo que hayas hecho en el medio. Marcala apenas terminás cada trabajo, o usá Iniciar / Terminar para que el tiempo sea exacto.';

export async function pantallaOperario(contenedor, operarioPedido) {
  const prod = estado.datos.produccion;
  const sesion = estado.sesion || {};
  const operarioId = esJefe() ? (operarioPedido || prod.operarios[0]?.id) : sesion.operarioId;
  const operario = prod.operarios.find((o) => o.id === operarioId);
  if (!operario) {
    contenedor.replaceChildren(h('p', { class: 'aviso-caja' }, 'Elegí tu nombre para ver tus trabajos.'), h('a', { href: '#ingreso', class: 'boton principal' }, 'Ingresar'));
    return () => {};
  }
  let dia = hoyIso();
  const zona = h('div', { class: 'lista-tareas' });
  const cabecera = h('div');

  async function dibujar() {
    const ctx = await cargarContexto();
    const turno = prod.turnos.find((t) => t.id === operario.turno);
    const mios = ctx.trabajos.filter((t) => t.operarioId === operario.id);
    const delDia = mios.filter((t) => t.fecha === dia);
    const atrasados = dia === ctx.hoy ? mios.filter((t) => !t.hecha && t.fecha && t.fecha < dia) : [];
    const lista = atrasados.concat(delDia).sort((a, b) => (a.hecha - b.hecha) || String(a.loteActual || '~').localeCompare(String(b.loteActual || '~')) || String(a.fechaEntrega).localeCompare(String(b.fechaEntrega)));
    const carga = delDia.reduce((s, t) => s + t.minutosEnLote, 0);
    const hechas = delDia.filter((t) => t.hecha).length;
    cabecera.replaceChildren(h('div', { class: 'panel cabecera-operario' },
      h('div', {}, h('div', { class: 'texto-chico' }, 'Operario'), h('strong', { class: 'dato-grande' }, operario.nombre), ` · turno ${turno?.nombre || operario.turno}`),
      h('div', {}, h('label', {}, 'Día ', h('input', { type: 'date', value: dia, onchange: (e) => { dia = e.target.value || hoyIso(); dibujar(); } }))),
      h('div', {}, h('div', { class: 'texto-chico' }, 'Carga del día (tiempo estándar)'), h('strong', {}, `${textoMinutos(carga)} de ${capacidadDeOperario(operario, prod)} min · ${hechas}/${delDia.length} hechas`)),
      esJefe() ? selector(prod.operarios.map((o) => ({ valor: o.id, texto: o.nombre })), operario.id, { 'aria-label': 'Ver otro operario', onchange: (e) => ir(`#operario/${e.target.value}`) }) : null,
      h('a', { class: 'boton', href: `#hoja-ruta/operario/${operario.id}/${dia}` }, 'Hoja de ruta')));
    zona.replaceChildren(...(lista.length ? lista.map((t) => tarjeta(t, ctx, turno)) : [h('p', { class: 'vacio' }, 'No tenés trabajos asignados para este día.')]),
      h('p', { class: 'texto-chico aviso-caja' }, LIMITE_CASILLA));
  }

  async function guardar(ctx, t, cambio) {
    try {
      const registro = cambio(ctx.registros[t.notaId] || registroVacio(t.notaId, t.demo));
      await almacenamiento.guardarRegistros([registro]);
      await dibujar();
    } catch (error) {
      mostrarAviso(error.message, 'error', 6);
    }
  }

  function tarjeta(t, ctx, turno) {
    const quien = { ...quienSoy(), operarioId: operario.id };
    const renglon = t.renglon;
    const dibujo = renglon.tipoPieza === 'plegada' || renglon.usaPerfil
      ? svgDelPerfil(renglon.perfil, { config: estado.datos.config, ancho: 260, alto: 160, miniatura: true })
      : svgDeEspecial(renglon, 400, 260);
    const alternarHecha = (hecha) => guardar(ctx, t, (registro) => {
      const horas = ctx.trabajos.filter((x) => x.operarioId === operario.id && x.hecha && x.horaHecha && diaDe(x.horaHecha) === diaDe(new Date())).map((x) => x.horaHecha);
      return marcarHecha(registro, t.renglonId, { hecha, tiempoEstandarMin: t.minutosEnLote, ahorroLoteMin: t.ahorroLoteMin, horasAnterioresDelOperario: horas, inicioTurno: turno?.inicio }, quien);
    });
    const evento = (tipo) => guardar(ctx, t, (registro) => registrarEvento(registro, t.renglonId, tipo, quien));
    const c = t.cronometro;
    return h('article', { class: `tarjeta-tarea${t.hecha ? ' hecha' : ''}${t.prioridad === 'urgente' ? ' urgente' : ''}` },
      h('div', { class: 'tarea-dibujo', html: dibujo }),
      h('div', { class: 'tarea-datos' },
        h('div', {}, h('strong', {}, `NP ${t.numeroNota}`), ` · ${t.cliente}`, t.prioridad === 'urgente' ? h('span', { class: 'etiqueta-urgente' }, 'URGENTE') : null, t.loteActual ? h('span', { class: 'etiqueta-demo' }, `lote ${t.loteActual}`) : null),
        h('div', { class: 'descripcion-renglon' }, t.descripcion),
        h('div', {}, `Piezas: `, h('strong', {}, String(t.piezas)), ` · ${nombreMaquina(t.maquina)} · estándar `, h('strong', {}, textoMinutos(t.minutosEnLote)), t.operarios === 2 ? ' · 2 operarios' : '', ` · entrega ${fechaCorta(`${t.fechaEntrega}T12:00:00`)}`),
        t.fecha && t.fecha < dia ? h('div', { class: 'aviso' }, `Atrasado: estaba para el ${fechaCorta(`${t.fecha}T12:00:00`)}`) : null,
        t.hecha ? h('div', { class: 'texto-chico' }, `Hecha a las ${new Date(t.horaHecha).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })} · real ${textoMinutos(t.tiempoRealMin)} (${t.origenReal === 'cronometro' ? 'cronómetro' : 'casilla'})`) : null,
        h('div', { class: 'barra-botones' },
          !t.hecha && c === 'sin_empezar' ? h('button', { type: 'button', class: 'boton', onclick: () => evento('inicio') }, '▶ Iniciar') : null,
          !t.hecha && c === 'corriendo' ? h('button', { type: 'button', class: 'boton', onclick: () => evento('pausa') }, '❚❚ Pausar') : null,
          !t.hecha && c === 'pausado' ? h('button', { type: 'button', class: 'boton', onclick: () => evento('reanudar') }, '▶ Reanudar') : null,
          h('label', { class: 'casilla-hecha' }, h('input', { type: 'checkbox', checked: t.hecha, onchange: (e) => alternarHecha(e.target.checked) }), ' HECHA'),
          h('a', { class: 'boton chico', href: `#imprimir/${t.notaId}` }, 'Ver nota'),
          h('button', { type: 'button', class: 'boton chico', onclick: () => problema(t) }, 'Problema'))));
  }

  async function problema(t) {
    const causas = prod.causasIncidencia;
    const tipo = window.prompt(`Tipo de problema (${Object.keys(causas).join(', ')}):`, 'demora');
    if (!tipo || !causas[tipo]) { if (tipo) mostrarAviso('Tipo no reconocido', 'error'); return; }
    const causa = window.prompt(`Causa:\n${causas[tipo].map((c, i) => `${i + 1}. ${c}`).join('\n')}\n(escribí el número)`, '1');
    const elegida = causas[tipo][Number(causa) - 1];
    if (!elegida) { mostrarAviso('Causa no reconocida', 'error'); return; }
    const minutos = Number(window.prompt('Minutos perdidos (aprox.):', '0')) || 0;
    await almacenamiento.agregarIncidencia({ tipo, causa: elegida, notaId: t.notaId, renglonId: t.renglonId, operarioId: operario.id, minutosPerdidos: minutos, demo: t.demo });
    mostrarAviso('Problema registrado: le llega al jefe', 'ok');
  }

  contenedor.replaceChildren(cabecera, zona);
  await dibujar();
  return () => {};
}
