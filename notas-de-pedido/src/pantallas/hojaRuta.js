// =============================================================
// hojaRuta.js
// HOJA DE RUTA imprimible (A4): los trabajos de un operario en un día, o los de un lote,
// en el orden en que conviene hacerlos, con el dibujo chico, el material y una columna
// para anotar la hora y firmar. Se imprime con el navegador (también "Guardar como PDF").
//   #hoja-ruta/operario/<operarioId>/<aaaa-mm-dd>     #hoja-ruta/lote/<loteId>
// =============================================================

import { h, fechaCorta, textoMinutos, logoDeEmpresa } from './util.js';
import { estado, nombreSucursal, empresaActual } from './estado.js';
import { cargarContexto, nombreOperario, nombreMaquina } from './contextoProduccion.js';
import { svgDelPerfil } from '../vistas2d/perfilSvg.js';
import { svgDeEspecial } from '../vistas2d/especialSvg.js';

export async function pantallaHojaRuta(contenedor, tipo, id, dia) {
  const ctx = await cargarContexto();
  let trabajos;
  let titulo;
  if (tipo === 'lote') {
    const lote = ctx.lotes.find((l) => l.id === id);
    trabajos = lote ? lote.trabajos : [];
    titulo = `Lote ${id}${lote ? ` · ${nombreMaquina(lote.resumen.maquina)}` : ''}`;
  } else {
    trabajos = ctx.trabajos.filter((t) => t.operarioId === id && t.fecha === dia)
      .sort((a, b) => String(a.loteActual || '~').localeCompare(String(b.loteActual || '~')) || String(a.fechaEntrega).localeCompare(String(b.fechaEntrega)));
    titulo = `${nombreOperario(id)} · ${fechaCorta(`${dia}T12:00:00`)}`;
  }
  const total = trabajos.reduce((s, t) => s + t.minutosEnLote, 0);
  // La hoja de ruta es de la planta: lleva el logo de la empresa de esa planta.
  const empresa = empresaActual();
  const materialDe = (r) => {
    if (r.sinMaterial) return '—';
    const m = estado.datos.materiales.materiales.find((x) => x.id === r.materialId);
    return `${m?.abreviatura || r.materialId} ${r.calibreId}${r.terminacion === 'P' ? ` pp ${r.colorId || ''}` : ''}`;
  };

  contenedor.replaceChildren(
    h('div', { class: 'barra-botones no-imprimir barra-impresion' },
      h('button', { type: 'button', class: 'boton', onclick: () => history.back() }, 'Volver'),
      h('button', { type: 'button', class: 'boton grande principal', onclick: () => window.print() }, 'Imprimir / Guardar PDF')),
    h('article', { class: 'hoja-a4 hoja-ruta' },
      h('header', { class: 'hoja-encabezado' },
        h('div', { class: 'hoja-origen' }, logoDeEmpresa(empresa, 'hoja-logo'),
          h('span', { class: 'rotulo' }, 'Hoja de ruta'), h('span', { class: 'origen-grande' }, titulo)),
        h('div', { class: 'hoja-datos' }, h('div', {}, h('span', { class: 'rotulo' }, 'Trabajos '), h('strong', {}, String(trabajos.length))),
          h('div', {}, h('span', { class: 'rotulo' }, 'Tiempo estándar '), h('strong', {}, textoMinutos(total))))),
      trabajos.length ? h('table', { class: 'hoja-tabla' },
        h('thead', {}, h('tr', {}, h('th', {}, '#'), h('th', {}, 'NP / cliente'), h('th', {}, 'Trabajo'), h('th', {}, 'Dibujo'), h('th', {}, 'Material'), h('th', {}, 'Tiempo'), h('th', {}, 'Hecha (hora y firma)'))),
        h('tbody', {}, trabajos.map((t, i) => h('tr', { class: 'fila-ruta' },
          h('td', {}, String(i + 1)),
          h('td', {}, h('strong', {}, String(t.numeroNota)), h('div', { class: 'texto-chico' }, `${t.cliente} · ${nombreSucursal(t.sucursalId)}`),
            h('div', { class: 'texto-chico' }, `Entrega ${fechaCorta(`${t.fechaEntrega}T12:00:00`)}${t.prioridad === 'urgente' ? ' · URGENTE' : ''}`)),
          h('td', {}, t.descripcion, h('div', {}, `Piezas: ${String(t.piezas).replace('.', ',')} · ${t.cantidad.texto} ${t.cantidad.abreviatura ?? (t.cantidad.unidad === 'chapas' ? 'chapa(s)' : 'u.')}`), h('div', { class: 'texto-chico' }, nombreMaquina(t.maquina), t.loteActual ? ` · lote ${t.loteActual}` : '')),
          h('td', { class: 'ruta-dibujo', html: t.renglon.tipoPieza === 'plegada' || t.renglon.usaPerfil
            ? svgDelPerfil(t.renglon.perfil, { config: estado.datos.config, ancho: 200, alto: 120, miniatura: true })
            : svgDeEspecial(t.renglon, 300, 200) }),
          h('td', {}, materialDe(t.renglon)),
          h('td', {}, textoMinutos(t.minutosEnLote)),
          h('td', { class: 'ruta-firma' }, t.hecha ? `✓ ${new Date(t.horaHecha).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })}` : '☐'))))) : h('p', { class: 'vacio' }, 'No hay trabajos para esta hoja.'),
      h('p', { class: 'texto-chico' }, 'El dibujo acotado completo está en la nota de pedido. Tiempo estándar del modelo MTM (valores pendientes de validar con cronometraje).')));
  document.title = `Hoja de ruta – ${titulo}`;
  return () => { document.title = 'Notas de pedido'; };
}
