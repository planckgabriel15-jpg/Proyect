// =============================================================
// impresion.js
// Vista de impresión (A4 vertical), con el mismo esquema que la nota en papel:
//   ORIGEN (grande)                     NP Nº · Fecha · Factura Nº
//   Cliente
//   Descripción | Código | Piezas | Cantidad (chapas)
//   … y debajo de cada renglón: dibujo 2D acotado (referencia oficial),
//   imagen 3D chica (ayuda visual, opcional por nota y por renglón), tramos,
//   pintura, corte láser y observaciones.
// Lo facturado (descripción, código, cantidad) sale de logica/fotoCalculo.js:
// en una nota emitida es la foto guardada al emitir; los dibujos, del renglón.
// Pie de página: vendedor, fecha y hora de emisión y "Página X de Y".
// Se imprime con window.print(); desde ahí se puede "Guardar como PDF".
// =============================================================

import { h, fechaCorta, fechaYHora, mostrarAviso } from './util.js';
import { etiquetaAtajo } from './atajos.js';
import { estado, nombreSucursal, nombreVendedor } from './estado.js';
import * as almacenamiento from '../datos/almacenamiento.js';
import { datosDelRenglon, mostrar3d } from '../logica/fotoCalculo.js';
import { textoDeTramos } from '../logica/descripcion.js';
import { describirCorteLaser } from '../logica/corteLaser.js';
import { formatearCorto } from '../logica/numeros.js';
import { detalleDeAccesorios } from '../logica/accesoriosCanaleta.js';
import { svgPlantaCanaleta } from '../vistas2d/plantaCanaletaSvg.js';
import { svgDelPerfil } from '../vistas2d/perfilSvg.js';
import { svgCorteLaser } from '../vistas2d/corteLaserSvg.js';
import { svgPendienteLateral } from '../vistas2d/pendienteSvg.js';
import { svgCaras, svgTapasConDetalle } from '../vistas2d/carasSvg.js';
import { detalleDeCortes } from '../logica/cortes.js';
import { tienePendiente, perfilFinal } from '../logica/pendiente.js';
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
    h('button', { type: 'button', class: 'boton', onclick: () => history.length > 1 ? history.back() : (location.hash = '#inicio') }, 'Volver'),
    h('button', { type: 'button', class: 'boton grande principal', onclick: () => window.print() }, 'Imprimir / Guardar PDF', etiquetaAtajo('Ctrl+P')),
    emitida ? null : h('a', { href: `#nota/${nota.id}`, class: 'boton' }, 'Seguir editando'),
    h('span', { class: 'texto-chico' }, 'Para PDF: en la ventana de impresión elegí "Guardar como PDF". Recomendado: Chrome o Edge.'));

  // ---------- encabezado (igual que el papel) ----------
  const marca = datos.config.marca || {};
  const encabezado = h('header', { class: 'hoja-encabezado' },
    h('div', { class: 'hoja-origen' },
      marca.logo ? h('img', { class: 'hoja-logo', src: marca.logo, alt: marca.nombre || 'Logo' }) : null,
      h('span', { class: 'rotulo' }, 'Origen'), h('span', { class: 'origen-grande' }, sucursal.toUpperCase())),
    h('div', { class: 'hoja-datos' },
      h('div', {}, h('span', { class: 'rotulo' }, 'NP Nº '), h('strong', { class: 'numero-np' }, emitida ? String(nota.numero) : 'BORRADOR')),
      h('div', {}, h('span', { class: 'rotulo' }, 'Fecha '), h('strong', {}, fechaNota)),
      h('div', {}, h('span', { class: 'rotulo' }, 'Factura Nº '), h('strong', {}, nota.factura || '—'))),
    h('div', { class: 'hoja-cliente' }, h('span', { class: 'rotulo' }, 'Cliente '), h('strong', {}, nota.cliente || '—')));

  // ---------- renglones ----------
  const tabla = h('table', { class: 'hoja-tabla' },
    h('thead', {}, h('tr', {},
      h('th', { class: 'col-descripcion' }, 'Descripción'),
      h('th', { class: 'col-codigo' }, 'Código'),
      h('th', { class: 'col-piezas' }, 'Piezas'),
      h('th', { class: 'col-cantidad', title: 'Cantidad de chapas = piezas × largo ÷ 2,44 m (los productos sin largo, en unidades)' }, 'Cantidad'))));

  nota.renglones.forEach((renglon, i) => {
    // Si la nota está emitida se usa lo calculado al emitir (no cambia aunque cambie la tabla de códigos).
    const { vivo, foto: c } = datosDelRenglon(renglon, datos);
    const con3d = mostrar3d(renglon, nota, datos);
    const usaPerfil = renglon.tipoPieza === 'plegada' || renglon.usaPerfil;
    const conPendiente = tienePendiente(renglon) && vivo.pendiente;
    const opcionesPerfil = { config: datos.config, ancho: 560, alto: conPendiente ? 250 : 340, ladoPintura: renglon.terminacion === 'P' ? renglon.ladoPintura : null };
    let dibujo2d;
    if (conPendiente) {
      // Con pendiente: los dos perfiles (punta izquierda arriba, derecha abajo).
      dibujo2d = `<p class="titulo-perfil">Punta izquierda (inicio)</p>${svgDelPerfil(renglon.perfil, opcionesPerfil)}`
        + `<p class="titulo-perfil">Punta derecha (final)</p>${svgDelPerfil(perfilFinal(renglon.perfil), opcionesPerfil)}`;
    } else {
      dibujo2d = usaPerfil ? svgDelPerfil(renglon.perfil, opcionesPerfil) : svgDeEspecial(renglon, 560, 360);
    }

    const detalles = [];
    if (conPendiente) {
      detalles.push(h('li', {}, h('strong', {}, 'Tramos punta izquierda: '), textoDeTramos(renglon.perfil.tramos)));
      detalles.push(h('li', {}, h('strong', {}, 'Tramos punta derecha: '), textoDeTramos(perfilFinal(renglon.perfil).tramos)));
      detalles.push(h('li', {}, h('strong', {}, 'Pendiente: '), c.pendienteTexto || vivo.pendiente.texto));
    } else if (usaPerfil && renglon.perfil?.tramos?.length) {
      detalles.push(h('li', {}, h('strong', {}, 'Tramos: '), textoDeTramos(renglon.perfil.tramos)));
    }
    if (!c.porUnidad && c.desarrolloCm) detalles.push(h('li', {}, h('strong', {}, 'Desarrollo: '), `${formatearCorto(c.desarrolloCm, 1)} cm${c.desarrolloEsManual ? ' (corregido a mano)' : ''}`));
    if (renglon.terminacion === 'P' && !renglon.sinMaterial) detalles.push(h('li', {}, h('strong', {}, 'Pintura: '), renglon.ladoPintura === 'ambos' ? 'DE LOS DOS LADOS' : (renglon.ladoPintura || '—').toUpperCase()));
    if (c.empalmeTexto) detalles.push(h('li', {}, h('strong', {}, 'Empalme: '), c.empalmeTexto));
    for (const linea of [...detalleDeAccesorios(renglon.accesorios, renglon, datos.config), ...detalleDeCortes(renglon, datos.config)]) detalles.push(h('li', {}, h('strong', {}, `${linea.split(':')[0]}: `), linea.split(':').slice(1).join(':').trim()));
    for (const tramo of (usaPerfil ? renglon.perfil.tramos : []).filter((t) => t.corteLaser)) {
      detalles.push(h('li', {}, h('strong', {}, `Tramo ${renglon.perfil.tramos.indexOf(tramo) + 1}: `), describirCorteLaser(tramo.corteLaser)));
    }
    (usaPerfil ? renglon.perfil.tramos : []).forEach((tramo, n) => {
      if (tramo.observacion) detalles.push(h('li', {}, h('strong', {}, `Tramo ${n + 1}: `), tramo.observacion));
    });
    if (!c.codigo) detalles.push(h('li', { class: 'resaltar-texto' }, h('strong', {}, 'CÓDIGO PENDIENTE: '), 'lo completa administración'));
    if (c.codigoGenerico) detalles.push(h('li', {}, h('strong', {}, 'Código genérico: '), 'confirmarlo con administración'));
    for (const aviso of (c.avisos || []).filter((a) => !a.startsWith('Código pendiente') && !a.startsWith('Código genérico'))) detalles.push(h('li', {}, h('strong', {}, 'Aviso: '), aviso));
    if (renglon.observaciones) detalles.push(h('li', {}, h('strong', {}, 'Observaciones: '), renglon.observaciones));

    const laseres = (conPendiente ? svgPendienteLateral(renglon, vivo.pendiente, { config: datos.config, ancho: 640, alto: 210 }) : '') + (usaPerfil
      ? renglon.perfil.tramos.map((t, n) => (t.corteLaser ? svgCorteLaser(t, n + 1, renglon.largoCm, datos.config, 560, 190) : '')).join('')
      : '') + svgPlantaCanaleta(renglon, 640, 170 + 22 * (renglon.accesorios?.boquetas?.length || 0))
      + svgCaras(renglon, datos.config) + svgTapasConDetalle(renglon, datos.config);

    tabla.append(h('tbody', { class: 'hoja-renglon' },
      h('tr', { class: 'fila-principal' },
        h('td', {}, h('span', { class: 'numero-en-hoja' }, `${i + 1}.`), ' ', c.descripcion),
        h('td', { class: 'col-codigo' }, c.codigo || 'PENDIENTE'),
        h('td', { class: 'col-piezas' }, String(c.cantidad.piezas)),
        h('td', { class: 'col-cantidad' }, c.cantidad.unidad === 'chapas' ? c.cantidad.texto : `${c.cantidad.texto} u.`)),
      // Tapas y boquetas puestas en la canaleta: se facturan con su propio código (pedido de la empresa).
      (c.codigosAdicionales || []).map((extra) => h('tr', { class: 'fila-adicional' },
        h('td', {}, `   + ${extra.descripcion} (puesta en la canaleta)`),
        h('td', { class: 'col-codigo' }, extra.codigo),
        h('td', { class: 'col-piezas' }, ''),
        h('td', { class: 'col-cantidad' }, `${extra.cantidad} u.`))),
      h('tr', { class: 'fila-dibujo' }, h('td', { colspan: 4 },
        h('div', { class: `hoja-dibujos${con3d ? '' : ' sin-3d'}` },
          h('div', { class: 'hoja-2d', html: dibujo2d }),
          con3d ? h('div', { class: 'hoja-3d', 'data-renglon': renglon.id }) : null,
          h('ul', { class: 'hoja-detalles' }, detalles)))),
      // Vistas extra (corte láser, desde arriba, caras con cortes, tapas) en otra fila:
      // así un renglón largo puede seguir en la hoja siguiente sin dejar la primera vacía.
      laseres ? h('tr', { class: 'fila-laser' }, h('td', { colspan: 4 }, h('div', { class: 'hoja-laser', html: laseres }))) : null));
  });

  const hoja = h('article', { class: 'hoja-a4' },
    emitida ? null : h('div', { class: 'marca-borrador' }, 'BORRADOR – NO EMITIDA'),
    encabezado,
    tabla,
    h('footer', { class: 'hoja-pie-pantalla no-imprimir' }, `Vendedor: ${vendedor} · ${emitida ? `Emitida: ${fechaYHora(nota.fechaEmision)}` : 'Sin emitir'}`));

  contenedor.replaceChildren(estiloPie, barra, hoja);
  document.title = `NP ${emitida ? nota.numero : 'borrador'} – ${sucursal}`;

  // Imágenes 3D chicas (ayuda visual), solo en los renglones que la llevan.
  const con3d = nota.renglones.filter((r) => mostrar3d(r, nota, datos));
  const modulo = con3d.length ? await cargar3d() : null;
  if (modulo) {
    for (const renglon of con3d) {
      const lugar = hoja.querySelector(`.hoja-3d[data-renglon="${renglon.id}"]`);
      try {
        const imagen = modulo.capturarRenglon(renglon, datos, 760, 520);
        lugar?.append(h('img', { src: imagen, alt: 'Vista 3D (ayuda visual)' }), h('div', { class: 'texto-chico' }, 'Vista 3D: solo ayuda visual'));
      } catch (error) {
        console.warn('Imagen 3D para imprimir:', error);
      }
    }
  } else if (con3d.length) {
    mostrarAviso('Sin 3D: se imprime solo el dibujo 2D (que es la referencia oficial).', 'info');
  }

  return () => { document.title = `Notas de pedido – ${datos.config.marca?.nombre || 'Zinguería'}`; };
}
