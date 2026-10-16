// =============================================================
// plantaCanaletaSvg.js
// Vista DESDE ARRIBA de la canaleta con sus tapas y boquetas puestas:
// muestra en qué punta va cada tapa (y si es soldada o engrampada) y dónde
// va cada boqueta, acotada desde la punta izquierda hasta su centro.
// =============================================================

import { leerNumero, formatearCorto, formatearNumero } from '../logica/numeros.js';
import { medidaDeBoqueta } from '../logica/accesoriosCanaleta.js';
import { escaparTexto } from './perfilSvg.js';

const r1 = (n) => Math.round(n * 10) / 10;

/**
 * @param {object} renglon  renglón de una canaleta (con renglon.accesorios)
 * @returns {string} SVG, o '' si la canaleta no lleva tapas ni boquetas
 */
export function svgPlantaCanaleta(renglon, ancho = 640, alto = 200) {
  const acc = renglon.accesorios;
  if (!acc) return '';
  const hayTapas = acc.tapaIzquierda !== 'ninguna' || acc.tapaDerecha !== 'ninguna';
  if (!hayTapas && !(acc.boquetas || []).length) return '';

  const largo = leerNumero(renglon.largoCm) > 0 ? leerNumero(renglon.largoCm) : 100;
  const x0 = 95;
  const x1 = ancho - 105;
  const yArriba = 50;
  const yAbajo = 110;
  const X = (cm) => r1(x0 + (cm / largo) * (x1 - x0));
  const partes = [];
  partes.push(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${ancho} ${alto}" class="planta-svg" role="img" aria-label="Vista desde arriba con tapas y boquetas">`);
  partes.push(`<text class="laser-titulo" x="8" y="18">Vista desde arriba: tapas y boquetas (medidas en cm desde la punta izquierda)</text>`);
  partes.push(`<rect class="pieza" x="${x0}" y="${yArriba}" width="${x1 - x0}" height="${yAbajo - yArriba}"/>`);

  // Tapas: línea gruesa en la punta + texto.
  if (acc.tapaIzquierda !== 'ninguna') {
    partes.push(`<line class="pieza-ancha" x1="${x0}" y1="${yArriba}" x2="${x0}" y2="${yAbajo}"/>`);
    partes.push(`<text class="cota-texto" x="${x0 - 6}" y="${(yArriba + yAbajo) / 2 - 4}" text-anchor="end">tapa izq.</text>`);
    partes.push(`<text class="nota" x="${x0 - 6}" y="${(yArriba + yAbajo) / 2 + 14}" text-anchor="end">${escaparTexto(acc.tapaIzquierda)}</text>`);
  }
  if (acc.tapaDerecha !== 'ninguna') {
    partes.push(`<line class="pieza-ancha" x1="${x1}" y1="${yArriba}" x2="${x1}" y2="${yAbajo}"/>`);
    partes.push(`<text class="cota-texto" x="${x1 + 6}" y="${(yArriba + yAbajo) / 2 - 4}">tapa der.</text>`);
    partes.push(`<text class="nota" x="${x1 + 6}" y="${(yArriba + yAbajo) / 2 + 14}">${escaparTexto(acc.tapaDerecha)}</text>`);
  }

  // Boquetas con su cota desde la punta izquierda.
  (acc.boquetas || []).forEach((b, i) => {
    const posicion = leerNumero(b.posicionCm) || 0;
    const xc = X(posicion);
    const yc = (yArriba + yAbajo) / 2;
    if (b.forma === 'redonda') {
      partes.push(`<circle class="pieza-boqueta" cx="${xc}" cy="${yc}" r="14"/>`);
    } else {
      const w = b.forma === 'cuadrada' ? 28 : 36;
      const hgt = b.forma === 'cuadrada' ? 28 : 20;
      partes.push(`<rect class="pieza-boqueta" x="${xc - w / 2}" y="${yc - hgt / 2}" width="${w}" height="${hgt}"/>`);
    }
    partes.push(`<text class="cota-texto" x="${xc}" y="${yArriba - 8}" text-anchor="middle">B${i + 1} ${escaparTexto(medidaDeBoqueta(b))}</text>`);
    const yCota = yAbajo + 22 + i * 22;
    partes.push(`<line class="cota" x1="${x0}" y1="${yCota}" x2="${xc}" y2="${yCota}"/>`);
    partes.push(`<line class="cota-guia" x1="${xc}" y1="${yc}" x2="${xc}" y2="${yCota + 4}"/>`);
    partes.push(`<text class="cota-texto" x="${r1((x0 + xc) / 2)}" y="${yCota - 4}" text-anchor="middle">${formatearCorto(posicion)}</text>`);
  });

  // Largo total.
  partes.push(`<text class="nota" x="${x1}" y="${alto - 6}" text-anchor="end">largo ${formatearNumero(largo / 100, 2)} m</text>`);
  partes.push('</svg>');
  return partes.join('\n');
}
