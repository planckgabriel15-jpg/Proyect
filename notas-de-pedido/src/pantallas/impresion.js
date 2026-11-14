// =============================================================
// impresion.js
// Vista de impresión (A4 vertical). Cada dato aparece UNA sola vez:
//   Encabezado: empresa que emite · ORIGEN (grande) · NP Nº · Fecha · Factura · Cliente
//               (y la entrega comprometida y URGENTE, si se cargaron)
//   Tabla (lo que se factura): Descripción | Código | Piezas | Cantidad (chapas)
//   Debajo de cada renglón (lo que se fabrica): dibujo 2D acotado (referencia oficial),
//     ficha de material junto al dibujo, imagen 3D opcional y las notas que el dibujo no dice.
//   Pie de página: vendedor, hora de emisión y "Página X de Y".
// QUÉ va en la hoja lo decide logica/hojaImpresa.js (se prueba sin navegador);
// los dibujos los arma vistas2d/hojaSvg.js. Acá solo se pone en pantalla.
// Lo facturado sale de la foto guardada al emitir (logica/fotoCalculo.js).
// Se imprime con window.print(); desde ahí se puede "Guardar como PDF".
// =============================================================

import { h, mostrarAviso, logoDeEmpresa } from './util.js';
import { etiquetaAtajo } from './atajos.js';
import { estado } from './estado.js';
import * as almacenamiento from '../datos/almacenamiento.js';
import { armarHoja } from '../logica/hojaImpresa.js';
import { calcularRenglon } from '../logica/calculoRenglon.js';
import { dibujosDeRenglon } from '../vistas2d/hojaSvg.js';
import { cargar3d } from '../vistas3d/cargar3d.js';

/** Para meter texto dentro de una regla CSS (content: "…") sin romperla. */
function textoParaCss(texto) {
  return String(texto).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, ' ');
}

/** @param {boolean} imprimirYa  abre la ventana de impresión apenas la hoja está lista (viene de "Emitir e imprimir") */
export async function pantallaImpresion(contenedor, notaId, imprimirYa = false) {
  const { datos } = estado;
  const nota = await almacenamiento.leerNota(notaId);
  if (!nota) {
    contenedor.replaceChildren(h('p', { class: 'aviso-caja' }, 'No se encontró la nota.'), h('a', { href: '#inicio', class: 'boton' }, 'Volver'));
    return () => {};
  }
  const hoja = armarHoja(nota, datos);

  // Pie de página de cada hoja impresa (lo dibuja el navegador en el margen).
  const estiloPie = h('style', {}, `@page {
    @bottom-left { content: "Vendedor: ${textoParaCss(hoja.pie.vendedor)} · ${textoParaCss(hoja.pie.emision)}"; font: 9pt system-ui, sans-serif; }
    @bottom-right { content: "Página " counter(page) " de " counter(pages); font: 9pt system-ui, sans-serif; }
  }`);

  const barra = h('div', { class: 'barra-botones no-imprimir barra-impresion' },
    h('button', { type: 'button', class: 'boton', onclick: () => history.length > 1 ? history.back() : (location.hash = '#inicio') }, 'Volver'),
    h('button', { type: 'button', class: 'boton grande principal', onclick: () => window.print() }, 'Imprimir / Guardar PDF', etiquetaAtajo('Ctrl+P')),
    hoja.emitida ? h('a', { href: `#nota/repetir-${nota.id}`, class: 'boton', title: 'Nota nueva con el mismo cliente y las mismas piezas' }, 'Repetir esta nota')
      : h('a', { href: `#nota/${nota.id}`, class: 'boton' }, 'Seguir editando'),
    h('span', { class: 'texto-chico' }, 'Para PDF: en la ventana de impresión elegí "Guardar como PDF". Recomendado: Chrome o Edge.'));

  // ---------- encabezado ----------
  const encabezado = h('header', { class: 'hoja-encabezado' },
    h('div', { class: 'hoja-origen' },
      // Logo y nombre de la empresa del grupo que EMITE la nota (no la de quien la está mirando).
      h('div', { class: 'hoja-empresa' }, logoDeEmpresa(hoja.empresa, 'hoja-logo'), h('span', { class: 'hoja-empresa-nombre' }, hoja.empresa?.nombre || '')),
      h('span', { class: 'rotulo' }, 'Origen'), h('span', { class: 'origen-grande' }, hoja.origen.toUpperCase())),
    h('div', { class: 'hoja-datos' },
      h('div', {}, h('span', { class: 'rotulo' }, 'NP Nº '), h('strong', { class: 'numero-np' }, hoja.numero)),
      h('div', {}, h('span', { class: 'rotulo' }, 'Fecha '), h('strong', {}, hoja.fecha)),
      h('div', {}, h('span', { class: 'rotulo' }, 'Factura Nº '), h('strong', {}, hoja.factura)),
      hoja.entrega ? h('div', {}, h('span', { class: 'rotulo' }, 'Entrega '), h('strong', {}, hoja.entrega)) : null,
      hoja.urgente ? h('div', { class: 'hoja-urgente' }, 'URGENTE') : null),
    h('div', { class: 'hoja-cliente' }, h('span', { class: 'rotulo' }, 'Cliente '), h('strong', {}, hoja.cliente)));

  // ---------- renglones ----------
  const tabla = h('table', { class: 'hoja-tabla' },
    h('thead', {}, h('tr', {},
      h('th', { class: 'col-descripcion' }, 'Descripción'),
      h('th', { class: 'col-codigo' }, 'Código'),
      h('th', { class: 'col-piezas' }, 'Piezas'),
      h('th', { class: 'col-cantidad', title: 'Cantidad de chapas = piezas × largo ÷ 2,44 m (lo que no tiene largo, en su unidad)' }, 'Cantidad (chapas)'))));

  hoja.renglones.forEach((r, i) => {
    const renglon = nota.renglones[i];
    const pendiente = r.dibujo === 'pendiente' ? calcularRenglon(renglon, datos).pendiente : null;
    const dibujos = dibujosDeRenglon(renglon, r.dibujo, datos, pendiente);
    const ficha = r.ficha.length ? h('dl', { class: 'hoja-ficha' }, r.ficha.flatMap((dato) => [h('dt', {}, dato.rotulo), h('dd', {}, dato.valor)])) : null;
    const notas = r.notas.length ? h('ul', { class: 'hoja-detalles' }, r.notas.map((n) => h('li', {}, h('strong', {}, `${n.rotulo}: `), n.valor))) : null;
    const hayFabricacion = Boolean(r.dibujo || ficha || notas);

    tabla.append(h('tbody', { class: 'hoja-renglon' },
      h('tr', { class: 'fila-principal' },
        h('td', {}, h('span', { class: 'numero-en-hoja' }, `${r.numero}.`), ' ', r.descripcion),
        h('td', { class: 'col-codigo' }, r.codigo),
        h('td', { class: 'col-piezas' }, r.piezas),
        h('td', { class: 'col-cantidad' }, r.cantidad)),
      // Tapas y boquetas puestas en la canaleta: se facturan con su propio código (pedido de la empresa).
      r.adicionales.map((extra) => h('tr', { class: 'fila-adicional' },
        h('td', {}, `   ${extra.descripcion}`),
        h('td', { class: 'col-codigo' }, extra.codigo),
        h('td', { class: 'col-piezas' }, ''),
        h('td', { class: 'col-cantidad' }, extra.cantidad))),
      hayFabricacion ? h('tr', { class: 'fila-dibujo' }, h('td', { colspan: 4 },
        h('div', { class: `hoja-dibujos${r.con3d ? '' : ' sin-3d'}${r.dibujo ? '' : ' sin-dibujo'}` },
          r.dibujo ? h('div', { class: 'hoja-2d', html: dibujos.principal }) : null,
          // Ficha de material junto al dibujo; debajo, la imagen 3D si el renglón la lleva.
          (ficha || r.con3d) ? h('div', { class: 'hoja-lateral' }, ficha, r.con3d ? h('div', { class: 'hoja-3d', 'data-renglon': r.id }) : null) : null,
          notas))) : null,
      // Vistas extra (corte láser, desde arriba, caras con cortes, tapas) en otra fila:
      // así un renglón largo puede seguir en la hoja siguiente sin dejar la primera vacía.
      dibujos.extras ? h('tr', { class: 'fila-laser' }, h('td', { colspan: 4 }, h('div', { class: 'hoja-laser', html: dibujos.extras }))) : null));
  });

  const articulo = h('article', { class: 'hoja-a4' },
    hoja.emitida ? null : h('div', { class: 'marca-borrador' }, 'BORRADOR – NO EMITIDA'),
    encabezado,
    tabla,
    h('footer', { class: 'hoja-pie-pantalla no-imprimir' }, `Vendedor: ${hoja.pie.vendedor} · ${hoja.pie.emision}`));

  contenedor.replaceChildren(estiloPie, barra, articulo);
  // Nombre del archivo al guardar como PDF: identificador completo (empresa-sucursal-número).
  document.title = `NP ${hoja.identificador} – ${hoja.origen}`;

  // Imágenes 3D chicas (ayuda visual), solo en los renglones que la llevan.
  const con3d = hoja.renglones.filter((r) => r.con3d);
  const modulo = con3d.length ? await cargar3d() : null;
  if (modulo) {
    for (const r of con3d) {
      const lugar = articulo.querySelector(`.hoja-3d[data-renglon="${r.id}"]`);
      try {
        const imagen = modulo.capturarRenglon(nota.renglones.find((x) => x.id === r.id), datos, 760, 520);
        lugar?.append(h('img', { src: imagen, alt: 'Vista 3D (ayuda visual)' }), h('div', { class: 'texto-chico' }, 'Vista 3D: solo ayuda visual'));
      } catch (error) {
        console.warn('Imagen 3D para imprimir:', error);
      }
    }
  } else if (con3d.length) {
    mostrarAviso('Sin 3D: se imprime solo el dibujo 2D (que es la referencia oficial).', 'info');
  }

  if (imprimirYa) {
    // Se saca "/imprimir" de la dirección para que recargar o volver no abra la impresión otra vez.
    history.replaceState(null, '', `#imprimir/${nota.id}`);
    setTimeout(() => window.print(), 150);
  }
  return () => { document.title = 'Notas de pedido'; };
}
