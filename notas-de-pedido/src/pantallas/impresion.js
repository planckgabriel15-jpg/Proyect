// =============================================================
// impresion.js
// Vista de impresión (A4 vertical), con el mismo esquema que la nota en papel:
//   ORIGEN (grande)                     NP Nº · Fecha · Factura Nº
//   Cliente
//   Descripción | Código | Cantidad
//   … y debajo de cada renglón: dibujo 2D acotado (referencia oficial),
//   imagen 3D chica (ayuda visual), tramos, pintura, corte láser y observaciones.
// Pie de página: vendedor, fecha y hora de emisión y "Página X de Y".
// Se imprime con window.print(); desde ahí se puede "Guardar como PDF".
// =============================================================

import { h, fechaCorta, fechaYHora, mostrarAviso } from './util.js';
import { estado, nombreSucursal, nombreVendedor } from './estado.js';
import * as almacenamiento from '../datos/almacenamiento.js';
import { calcularRenglon } from '../logica/calculoRenglon.js';
import { textoDeTramos } from '../logica/descripcion.js';
import { describirCorteLaser } from '../logica/corteLaser.js';
import { formatearCorto } from '../logica/numeros.js';
import { accesoriosDe } from '../logica/renglones.js';
import { svgDelPerfil } from '../vistas2d/perfilSvg.js';
import { svgCorteLaser } from '../vistas2d/corteLaserSvg.js';
import { svgDeEspecial } from '../vistas2d/especialSvg.js';
import { cargar3d } from '../vistas3d/cargar3d.js';

/** Para meter texto dentro de una regla CSS (content: "…") sin romperla. */
function textoParaCss(texto) {
  return String(texto).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, ' ');
}

export async function pantallaImpresion(contenedor, notaId) {
  const { datos } = estado;
  const nota = await almacenamiento.leerNota(notaId);
  if (!nota) {
    contenedor.replaceChildren(h('p', { class: 'aviso-caja' }, 'No se encontró la nota.'), h('a', { href: '#inicio', class: 'boton' }, 'Volver'));
    return () => {};
  }

  const emitida = nota.estado === 'emitida';
  const sucursal = nombreSucursal(nota.sucursalId);
  const vendedor = nombreVendedor(nota.vendedorId);
  const fechaNota = fechaCorta(nota.fechaEmision || nota.fechaCreacion);

  // Pie de página de cada hoja impresa (lo dibuja el navegador en el margen).
  const estiloPie = h('style', {}, `@page {
    @bottom-left { content: "Vendedor: ${textoParaCss(vendedor)} · Emitida: ${textoParaCss(emitida ? fechaYHora(nota.fechaEmision) : 'BORRADOR (sin emitir)')}"; font: 9pt system-ui, sans-serif; }
    @bottom-right { content: "Página " counter(page) " de " counter(pages); font: 9pt system-ui, sans-serif; }
  }`);

  const barra = h('div', { class: 'barra-botones no-imprimir barra-impresion' },
    h('button', { type: 'button', class: 'boton', onclick: () => history.length > 1 ? history.back() : (location.hash = '#inicio') }, '← Volver'),
    h('button', { type: 'button', class: 'boton grande principal', onclick: () => window.print() }, '🖨 Imprimir / Guardar PDF'),
    emitida ? null : h('a', { href: `#nota/${nota.id}`, class: 'boton' }, '✎ Seguir editando'),
    h('span', { class: 'texto-chico' }, 'Para PDF: en la ventana de impresión elegí "Guardar como PDF". Recomendado: Chrome o Edge.'));

  // ---------- encabezado (igual que el papel) ----------
  const encabezado = h('header', { class: 'hoja-encabezado' },
    h('div', { class: 'hoja-origen' }, h('span', { class: 'rotulo' }, 'Origen'), h('span', { class: 'origen-grande' }, sucursal.toUpperCase())),
    h('div', { class: 'hoja-datos' },
      h('div', {}, h('span', { class: 'rotulo' }, 'NP Nº '), h('strong', { class: 'numero-np' }, emitida ? String(nota.numero) : 'BORRADOR')),
      h('div', {}, h('span', { class: 'rotulo' }, 'Fecha '), h('strong', {}, fechaNota)),
      h('div', {}, h('span', { class: 'rotulo' }, 'Factura Nº '), h('strong', {}, nota.factura || '—'))),
    h('div', { class: 'hoja-cliente' }, h('span', { class: 'rotulo' }, 'Cliente '), h('strong', {}, nota.cliente || '—')));

  // ---------- renglones ----------
  const tabla = h('table', { class: 'hoja-tabla' },
    h('thead', {}, h('tr', {}, h('th', { class: 'col-descripcion' }, 'Descripción'), h('th', { class: 'col-codigo' }, 'Código'), h('th', { class: 'col-cantidad' }, 'Cantidad'))));

  nota.renglones.forEach((renglon, i) => {
    // Si la nota está emitida se usa lo calculado al emitir (no cambia aunque cambie la tabla de códigos).
    const vivo = calcularRenglon(renglon, datos);
    const c = renglon.calculado || {
      descripcion: vivo.descripcion,
      codigo: vivo.codigo.encontrado ? vivo.codigo.codigo : null,
      desarrolloCm: vivo.desarrolloCm,
      desarrolloEsManual: vivo.desarrolloEsManual,
      porUnidad: vivo.porUnidad,
      avisos: vivo.avisos,
    };
    const usaPerfil = renglon.tipoPieza === 'plegada' || renglon.usaPerfilVinculado;
    const dibujo2d = usaPerfil
      ? svgDelPerfil(renglon.perfil, { config: datos.config, ancho: 560, alto: 340, ladoPintura: renglon.terminacion === 'P' ? renglon.ladoPintura : null })
      : svgDeEspecial(renglon, 560, 360);

    const detalles = [];
    if (usaPerfil && renglon.perfil?.tramos?.length) detalles.push(h('li', {}, h('strong', {}, 'Tramos: '), textoDeTramos(renglon.perfil.tramos)));
    if (!c.porUnidad && c.desarrolloCm) detalles.push(h('li', {}, h('strong', {}, 'Desarrollo: '), `${formatearCorto(c.desarrolloCm, 1)} cm${c.desarrolloEsManual ? ' (corregido a mano)' : ''}`));
    if (renglon.terminacion === 'P') detalles.push(h('li', {}, h('strong', {}, 'Pintura: '), (renglon.ladoPintura || '—').toUpperCase()));
    if (renglon.vinculadoA) detalles.push(h('li', {}, h('strong', {}, 'Accesorio del renglón '), String(nota.renglones.findIndex((r) => r.id === renglon.vinculadoA) + 1)));
    const accesorios = accesoriosDe(nota.renglones, renglon.id);
    if (accesorios.length) detalles.push(h('li', {}, h('strong', {}, 'Lleva: '), accesorios.map((a) => `renglón ${nota.renglones.indexOf(a) + 1}`).join(', ')));
    for (const tramo of (usaPerfil ? renglon.perfil.tramos : []).filter((t) => t.corteLaser)) {
      detalles.push(h('li', {}, h('strong', {}, `Tramo ${renglon.perfil.tramos.indexOf(tramo) + 1}: `), describirCorteLaser(tramo.corteLaser)));
    }
    (usaPerfil ? renglon.perfil.tramos : []).forEach((tramo, n) => {
      if (tramo.observacion) detalles.push(h('li', {}, h('strong', {}, `Tramo ${n + 1}: `), tramo.observacion));
    });
    if (!c.codigo) detalles.push(h('li', { class: 'resaltar-texto' }, h('strong', {}, 'CÓDIGO PENDIENTE: '), 'lo completa administración'));
    for (const aviso of (c.avisos || []).filter((a) => !a.startsWith('Código pendiente'))) detalles.push(h('li', {}, `⚠ ${aviso}`));
    if (renglon.observaciones) detalles.push(h('li', {}, h('strong', {}, 'Observaciones: '), renglon.observaciones));

    const laseres = usaPerfil
      ? renglon.perfil.tramos.map((t, n) => (t.corteLaser ? svgCorteLaser(t, n + 1, renglon.largoCm, datos.config, 560, 190) : '')).join('')
      : '';

    tabla.append(h('tbody', { class: 'hoja-renglon' },
      h('tr', { class: 'fila-principal' },
        h('td', {}, h('span', { class: 'numero-en-hoja' }, `${i + 1}.`), ' ', c.descripcion),
        h('td', { class: 'col-codigo' }, c.codigo || 'PENDIENTE'),
        h('td', { class: 'col-cantidad' }, String(renglon.cantidad))),
      h('tr', { class: 'fila-dibujo' }, h('td', { colspan: 3 },
        h('div', { class: 'hoja-dibujos' },
          h('div', { class: 'hoja-2d', html: dibujo2d }),
          h('div', { class: 'hoja-3d', 'data-renglon': renglon.id }),
          h('ul', { class: 'hoja-detalles' }, detalles)),
        laseres ? h('div', { class: 'hoja-laser', html: laseres }) : null))));
  });

  const hoja = h('article', { class: 'hoja-a4' },
    emitida ? null : h('div', { class: 'marca-borrador' }, 'BORRADOR – NO EMITIDA'),
    encabezado,
    tabla,
    h('footer', { class: 'hoja-pie-pantalla no-imprimir' }, `Vendedor: ${vendedor} · ${emitida ? `Emitida: ${fechaYHora(nota.fechaEmision)}` : 'Sin emitir'}`));

  contenedor.replaceChildren(estiloPie, barra, hoja);
  document.title = `NP ${emitida ? nota.numero : 'borrador'} – ${sucursal}`;

  // Imágenes 3D chicas (ayuda visual).
  const modulo = await cargar3d();
  if (modulo) {
    for (const renglon of nota.renglones) {
      const lugar = hoja.querySelector(`.hoja-3d[data-renglon="${renglon.id}"]`);
      try {
        const imagen = modulo.capturarRenglon(renglon, accesoriosDe(nota.renglones, renglon.id), datos, 360, 260);
        lugar?.append(h('img', { src: imagen, alt: 'Vista 3D (ayuda visual)' }), h('div', { class: 'texto-chico' }, 'Vista 3D: solo ayuda visual'));
      } catch (error) {
        console.warn('Imagen 3D para imprimir:', error);
      }
    }
  } else {
    mostrarAviso('Sin 3D: se imprime solo el dibujo 2D (que es la referencia oficial).', 'info');
  }

  return () => { document.title = 'Notas de pedido – Zinguería'; };
}
